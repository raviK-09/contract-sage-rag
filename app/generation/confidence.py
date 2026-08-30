"""
Three-signal confidence scorer (retrieval quality, context coverage, citation usage).
Returns a score 0–1 and triggers decline-to-answer when score < configured threshold.
"""


import logging
from dataclasses import dataclass

from app.config import settings
from app.generation.citation_builder import CitedAnswer
from app.retrieval.hybrid_retriever import RetrievedChunk

logger = logging.getLogger(__name__)

# Signal weights — must sum to 1.0
_RETRIEVAL_WEIGHT = 0.40
_COVERAGE_WEIGHT  = 0.35
_CITATION_WEIGHT  = 0.25


@dataclass
class ConfidenceResult:
    """Complete confidence assessment with breakdown for transparency."""
    score: float                 # Combined score 0.0 – 1.0
    should_decline: bool         # True if score < threshold
    decline_reason: str          # Human-readable reason for decline

    # Signal breakdown (for UI display and debugging)
    retrieval_score: float       # Avg cosine similarity of retrieved chunks
    coverage_score: float        # Fraction of chunks above min threshold
    citation_score: float        # Citation usage quality

    # Thresholds used (for display)
    threshold_used: float
    min_similarity_used: float

    @property
    def label(self) -> str:
        """Human-readable confidence label."""
        if self.score >= 0.70:
            return "High"
        elif self.score >= 0.40:
            return "Medium"
        else:
            return "Low"

    @property
    def color(self) -> str:
        """Streamlit-friendly color for UI display."""
        if self.score >= 0.70:
            return "green"
        elif self.score >= 0.40:
            return "orange"
        else:
            return "red"

    @property
    def emoji(self) -> str:
        """Quick visual indicator."""
        return {"High": "🟢", "Medium": "🟡", "Low": "🔴"}[self.label]


def compute_confidence(
    retrieved_chunks: list[RetrievedChunk],
    cited_answer: CitedAnswer,
    threshold: float | None = None,
    min_similarity: float | None = None,
) -> ConfidenceResult:
    """
    Compute a multi-signal confidence score for a RAG answer.

    Called AFTER generation so we can factor in citation quality.
    The score determines whether to return the answer or decline.

    Args:
        retrieved_chunks : Chunks from the hybrid retriever.
        cited_answer     : Parsed answer with citations from citation_builder.
        threshold        : Override confidence threshold (default from settings).
        min_similarity   : Override min similarity threshold (default from settings).

    Returns:
        ConfidenceResult with score, decline decision, and signal breakdown.
    """
    thr     = threshold     if threshold     is not None else settings.CONFIDENCE_THRESHOLD
    min_sim = min_similarity if min_similarity is not None else settings.MIN_SIMILARITY_THRESHOLD

    # ── Signal 1: Retrieval score ────────────────────────────────────────────
    # Average cosine similarity of ALL retrieved chunks
    # High average → the document genuinely contains relevant content
    retrieval_score = _compute_retrieval_score(retrieved_chunks)

    # ── Signal 2: Coverage score ──────────────────────────────────────────────
    # Fraction of chunks that meet the minimum similarity bar
    # Low coverage (few chunks above threshold) → weak retrieval
    coverage_score = _compute_coverage_score(retrieved_chunks, min_sim)

    # ── Signal 3: Citation score ──────────────────────────────────────────────
    # Measures: did the LLM actually USE the retrieved context?
    # Low citation score → LLM may be generating from prior knowledge (hallucination risk)
    citation_score = _compute_citation_score(cited_answer, retrieved_chunks)

    # ── LLM self-reported insufficiency ──────────────────────────────────────
    # If the LLM itself signalled insufficient context, force a decline
    # regardless of scores. The LLM has the highest-quality signal here.
    if cited_answer.is_insufficient:
        logger.info("LLM signalled INSUFFICIENT_CONTEXT — forcing decline.")
        return ConfidenceResult(
            score=0.0,
            should_decline=True,
            decline_reason=(
                f"The LLM determined the uploaded documents don't contain "
                f"enough information: {cited_answer.insufficient_reason}"
            ),
            retrieval_score=retrieval_score,
            coverage_score=coverage_score,
            citation_score=citation_score,
            threshold_used=thr,
            min_similarity_used=min_sim,
        )

    # ── Combined weighted score ───────────────────────────────────────────────
    combined = (
        _RETRIEVAL_WEIGHT * retrieval_score
        + _COVERAGE_WEIGHT  * coverage_score
        + _CITATION_WEIGHT  * citation_score
    )
    combined = round(combined, 4)

    # ── Decline decision ──────────────────────────────────────────────────────
    should_decline = combined < thr
    reason = _build_decline_reason(
        combined, thr, retrieval_score, coverage_score, citation_score
    ) if should_decline else ""

    logger.info(
        f"Confidence: {combined:.3f} (retrieval={retrieval_score:.2f}, "
        f"coverage={coverage_score:.2f}, citation={citation_score:.2f}) "
        f"→ {'DECLINE' if should_decline else 'ANSWER'}"
    )

    return ConfidenceResult(
        score=combined,
        should_decline=should_decline,
        decline_reason=reason,
        retrieval_score=retrieval_score,
        coverage_score=coverage_score,
        citation_score=citation_score,
        threshold_used=thr,
        min_similarity_used=min_sim,
    )


# ── Signal Calculators ────────────────────────────────────────────────────────

def _compute_retrieval_score(chunks: list[RetrievedChunk]) -> float:
    """
    Average cosine similarity score across all retrieved chunks.

    Trade-off: Mean vs Max
      Max → reflects the single best match (optimistic)
      Mean → reflects overall retrieval quality (more honest)
    We use mean because a high max with low mean suggests only ONE
    chunk is relevant — not enough context for a reliable answer.
    """
    if not chunks:
        return 0.0
    scores = [c.dense_score for c in chunks]
    return sum(scores) / len(scores)


def _compute_coverage_score(
    chunks: list[RetrievedChunk],
    min_similarity: float,
) -> float:
    """
    Fraction of chunks that meet the minimum similarity threshold.

    Example:
      5 chunks, 3 above threshold → coverage = 0.60
      5 chunks, 0 above threshold → coverage = 0.00 (very bad)
      5 chunks, 5 above threshold → coverage = 1.00 (excellent)
    """
    if not chunks:
        return 0.0
    above_threshold = sum(1 for c in chunks if c.dense_score >= min_similarity)
    return above_threshold / len(chunks)


def _compute_citation_score(
    cited_answer: CitedAnswer,
    chunks: list[RetrievedChunk],
) -> float:
    """
    Measures whether the LLM actually used the retrieved context.

    Scoring logic:
      - No citations at all    → 0.0  (LLM ignored context entirely)
      - Some citations         → citations_used / total_chunks_provided
      - All chunks cited       → 1.0  (max citation usage)

    Trade-off: This rewards citation quantity, not quality. A LLM could
    cite all sources but still hallucinate the content between citations.
    For a more robust measure, you'd use an NLI model to check if each
    sentence is entailed by its cited source — but that's too expensive
    for a local-only setup. The citation count is a good proxy.
    """
    if not chunks:
        return 0.5  # Neutral when no chunks (edge case)

    num_chunks    = len(chunks)
    num_cited     = len(cited_answer.cited_source_nums)

    if num_cited == 0:
        # LLM produced an answer with zero citations — high hallucination risk
        return 0.0

    # Ratio of cited sources to available sources
    ratio = min(num_cited / num_chunks, 1.0)

    # Bonus: if LLM cited at least half the sources, that's a good sign
    if ratio >= 0.5:
        return min(ratio + 0.1, 1.0)

    return ratio


def _build_decline_reason(
    score: float,
    threshold: float,
    retrieval: float,
    coverage: float,
    citation: float,
) -> str:
    """Build a human-readable reason for decline, identifying the weakest signal."""
    scores = {
        "retrieval quality": retrieval,
        "context coverage": coverage,
        "citation usage": citation,
    }
    weakest = min(scores, key=scores.get)

    reason_map = {
        "retrieval quality": (
            "The uploaded documents don't appear to contain information "
            "closely related to your question."
        ),
        "context coverage": (
            "Only a small portion of the retrieved content is relevant — "
            "the answer might be in a document that hasn't been uploaded yet."
        ),
        "citation usage": (
            "The response couldn't be grounded in the document text with "
            "sufficient confidence."
        ),
    }

    return (
        f"{reason_map[weakest]} "
        f"(Confidence: {score:.0%}, threshold: {threshold:.0%})"
    )
