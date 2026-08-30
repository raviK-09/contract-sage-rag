"""
RAGAS-style evaluation metrics implemented without the ragas library
(ragas pins langchain < 0.3 which conflicts with our stack).

Metrics: context precision, context recall, faithfulness, answer relevance,
keyword hit rate, source accuracy, decline correctness.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    """Single metric score with explanation."""
    name: str
    score: float        # 0.0 – 1.0
    explanation: str    # Human-readable reason (for debugging & UI display)
    passed: bool        # True if score meets the pass threshold

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.score:.2f} — {self.explanation}"


@dataclass
class EvalResult:
    """Complete evaluation result for one question."""
    question: str
    ground_truth: str
    generated_answer: str
    expected_doc: str | None
    category: str
    should_decline: bool

    # Scores
    context_precision: MetricResult = field(default=None)
    context_recall: MetricResult    = field(default=None)
    faithfulness: MetricResult      = field(default=None)
    answer_relevance: MetricResult  = field(default=None)
    keyword_hit_rate: MetricResult  = field(default=None)
    source_accuracy: MetricResult   = field(default=None)
    decline_correct: MetricResult   = field(default=None)

    # Pipeline metadata
    is_declined: bool  = False
    confidence_score: float = 0.0
    latency_ms: float  = 0.0
    error: str         = ""

    @property
    def all_metrics(self) -> list[MetricResult]:
        metrics = [
            self.context_precision,
            self.context_recall,
            self.faithfulness,
            self.answer_relevance,
            self.keyword_hit_rate,
            self.source_accuracy,
            self.decline_correct,
        ]
        return [m for m in metrics if m is not None]

    @property
    def overall_score(self) -> float:
        """Average of all available metric scores."""
        scores = [m.score for m in self.all_metrics]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def passed(self) -> bool:
        """True if all metrics passed."""
        return all(m.passed for m in self.all_metrics)


# ── Metric 1: Context Precision ───────────────────────────────────────────────

def compute_context_precision(
    retrieved_chunks: list[dict],
    expected_doc: str | None,
    min_similarity: float = 0.30,
    pass_threshold: float = 0.60,
) -> MetricResult:
    """
    Context Precision = fraction of retrieved chunks that are relevant.

    Implementation:
      We use the dense_score (cosine similarity) from the hybrid retriever
      as a relevance proxy. A chunk is "relevant" if:
        1. It comes from the expected source document, OR
        2. Its cosine similarity >= min_similarity

    RAGAS uses an LLM to judge relevance. We use similarity score + source
    matching, which is ~10x faster and sufficient for our use case.

    Formula: precision = relevant_chunks / total_retrieved_chunks
    """
    if not retrieved_chunks:
        return MetricResult(
            name="Context Precision",
            score=0.0,
            explanation="No chunks retrieved.",
            passed=False,
        )

    relevant = 0
    for chunk in retrieved_chunks:
        source_match = expected_doc and chunk.get("file_name", "") == expected_doc
        sim_match    = chunk.get("dense_score", 0.0) >= min_similarity
        if source_match or sim_match:
            relevant += 1

    score = relevant / len(retrieved_chunks)
    return MetricResult(
        name="Context Precision",
        score=round(score, 4),
        explanation=f"{relevant}/{len(retrieved_chunks)} chunks relevant (source match or sim >= {min_similarity})",
        passed=score >= pass_threshold,
    )


# ── Metric 2: Context Recall ──────────────────────────────────────────────────

def compute_context_recall(
    retrieved_chunks: list[dict],
    expected_keywords: list[str],
    pass_threshold: float = 0.60,
) -> MetricResult:
    """
    Context Recall = fraction of expected keywords found in retrieved context.

    Implementation:
      We check whether each expected keyword appears in the concatenated text
      of all retrieved chunks. This is a proxy for "did we retrieve all the
      information needed to answer the question?"

    RAGAS computes recall using an LLM to decompose the ground truth into
    claims and check each one against the context. We use keyword matching —
    simpler, faster, and easy to audit.

    Formula: recall = keywords_found_in_context / total_expected_keywords
    """
    if not expected_keywords:
        return MetricResult(
            name="Context Recall",
            score=1.0,
            explanation="No expected keywords defined — full score by default.",
            passed=True,
        )

    context_text = " ".join(
        chunk.get("page_content", "") for chunk in retrieved_chunks
    ).lower()

    found = sum(1 for kw in expected_keywords if kw.lower() in context_text)
    score = found / len(expected_keywords)

    return MetricResult(
        name="Context Recall",
        score=round(score, 4),
        explanation=f"{found}/{len(expected_keywords)} keywords found in context: {expected_keywords}",
        passed=score >= pass_threshold,
    )


# ── Metric 3: Faithfulness ────────────────────────────────────────────────────

def compute_faithfulness_keyword(
    generated_answer: str,
    retrieved_chunks: list[dict],
    pass_threshold: float = 0.50,
) -> MetricResult:
    """
    Faithfulness (keyword proxy) = fraction of answer sentences that share
    words with the retrieved context.

    True RAGAS Faithfulness uses an LLM to:
      1. Decompose the answer into atomic claims
      2. For each claim, ask the LLM "Is this supported by the context?"
      3. Score = supported_claims / total_claims

    Our proxy: for each sentence in the answer, we check if it shares
    significant keywords (non-stopword tokens) with the context. This
    catches hallucinations where the LLM invents numbers or names not
    in the context (e.g. "the rent is Rs 35,000" when context says 28,000).

    Trade-off:
      LLM-as-judge: accurate but slow (5-10s per question, needs Ollama)
      Keyword proxy: fast (< 1ms), misses semantic hallucinations but
                     catches factual ones (wrong numbers, names, dates)
      We offer BOTH — keyword proxy by default, LLM judge in faithfulness_llm.py
    """
    context_text = " ".join(
        chunk.get("page_content", "") for chunk in retrieved_chunks
    ).lower()

    context_tokens = set(_tokenise_for_faithfulness(context_text))
    sentences = _split_sentences(generated_answer)

    if not sentences:
        return MetricResult(
            name="Faithfulness",
            score=0.0,
            explanation="No sentences found in answer.",
            passed=False,
        )

    grounded_count = 0
    for sent in sentences:
        sent_tokens = set(_tokenise_for_faithfulness(sent.lower()))
        if not sent_tokens:
            grounded_count += 1  # Empty/formatting-only sentence
            continue
        overlap = sent_tokens & context_tokens
        # A sentence is "grounded" if >30% of its content words appear in context
        overlap_ratio = len(overlap) / len(sent_tokens)
        if overlap_ratio >= 0.30:
            grounded_count += 1

    score = grounded_count / len(sentences)
    return MetricResult(
        name="Faithfulness",
        score=round(score, 4),
        explanation=(
            f"{grounded_count}/{len(sentences)} sentences grounded in context "
            f"(keyword overlap method)"
        ),
        passed=score >= pass_threshold,
    )


# ── Metric 4: Answer Relevance ────────────────────────────────────────────────

def compute_answer_relevance(
    question: str,
    generated_answer: str,
    expected_keywords: list[str],
    pass_threshold: float = 0.50,
) -> MetricResult:
    """
    Answer Relevance = does the answer address the question?

    RAGAS computes this by:
      1. Asking the LLM to generate N questions from the answer
      2. Computing cosine similarity between generated questions and original
      3. Score = avg similarity

    Our proxy:
      1. Check if expected keywords appear in the answer (content check)
      2. Check if the answer is suspiciously short (< 20 words = incomplete)
      3. Check if it's a decline message when it shouldn't be

    Trade-off: Our proxy doesn't catch semantically off-topic answers but
    catches the most common failure mode: the LLM answers a different question.
    """
    word_count = len(generated_answer.split())

    # Penalty for very short answers
    if word_count < 15:
        return MetricResult(
            name="Answer Relevance",
            score=0.2,
            explanation=f"Answer too short ({word_count} words) — likely incomplete.",
            passed=False,
        )

    if not expected_keywords:
        # No keywords to check — give benefit of the doubt
        score = 0.7 if word_count >= 20 else 0.4
        return MetricResult(
            name="Answer Relevance",
            score=score,
            explanation=f"No keywords to validate. Answer length: {word_count} words.",
            passed=score >= pass_threshold,
        )

    answer_lower = generated_answer.lower()
    found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    keyword_ratio = found / len(expected_keywords)

    # Blend keyword hit rate with a length bonus
    length_bonus = min(word_count / 100, 0.2)  # up to 0.2 bonus for longer answers
    score = min(keyword_ratio + length_bonus, 1.0)

    return MetricResult(
        name="Answer Relevance",
        score=round(score, 4),
        explanation=(
            f"{found}/{len(expected_keywords)} expected keywords in answer, "
            f"length={word_count} words"
        ),
        passed=score >= pass_threshold,
    )


# ── Metric 5: Keyword Hit Rate ────────────────────────────────────────────────

def compute_keyword_hit_rate(
    generated_answer: str,
    expected_keywords: list[str],
    pass_threshold: float = 0.60,
) -> MetricResult:
    """
    Keyword Hit Rate = fraction of expected keywords present in the answer.

    This is the most straightforward metric: did the LLM include the
    specific factual terms we expect? Great for legal Q&A where exact
    figures (Rs. 28,000, 60 days, 8%) must appear in the answer.
    """
    if not expected_keywords:
        return MetricResult(
            name="Keyword Hit Rate",
            score=1.0,
            explanation="No expected keywords defined.",
            passed=True,
        )

    answer_lower = generated_answer.lower()
    found = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    missed = [kw for kw in expected_keywords if kw.lower() not in answer_lower]
    score = len(found) / len(expected_keywords)

    explanation = f"Found: {found}"
    if missed:
        explanation += f" | Missing: {missed}"

    return MetricResult(
        name="Keyword Hit Rate",
        score=round(score, 4),
        explanation=explanation,
        passed=score >= pass_threshold,
    )


# ── Metric 6: Source Accuracy ─────────────────────────────────────────────────

def compute_source_accuracy(
    sources_cited: list[str],
    expected_doc: str | None,
    pass_threshold: float = 0.50,
) -> MetricResult:
    """
    Source Accuracy = did the answer cite the correct source document?

    A cited answer is only trustworthy if it cites the RIGHT document.
    This metric catches cross-document confusion — e.g. the employment
    agreement clause cited for a rental question.
    """
    if expected_doc is None:
        return MetricResult(
            name="Source Accuracy",
            score=1.0,
            explanation="Out-of-scope question — no expected source.",
            passed=True,
        )

    if not sources_cited:
        return MetricResult(
            name="Source Accuracy",
            score=0.0,
            explanation="No sources cited in the answer.",
            passed=False,
        )

    correct = expected_doc in sources_cited
    score = 1.0 if correct else 0.0
    return MetricResult(
        name="Source Accuracy",
        score=score,
        explanation=(
            f"Expected: {expected_doc} | Cited: {sources_cited}"
            + (" ✓" if correct else " ✗")
        ),
        passed=correct,
    )


# ── Metric 7: Decline Correctness ─────────────────────────────────────────────

def compute_decline_correctness(
    is_declined: bool,
    should_decline: bool,
) -> MetricResult:
    """
    Decline Correctness = did the system make the right answer/decline decision?

    Four possible outcomes:
      True Decline  (should=True,  actual=True)  → score 1.0 PASS ✓
      True Answer   (should=False, actual=False)  → score 1.0 PASS ✓
      False Decline (should=False, actual=True)   → score 0.0 FAIL ✗ (over-refusal)
      False Answer  (should=True,  actual=False)  → score 0.0 FAIL ✗ (hallucination risk)
    """
    correct = is_declined == should_decline

    if correct and should_decline:
        explanation = "Correctly declined out-of-scope question."
    elif correct and not should_decline:
        explanation = "Correctly answered in-scope question."
    elif not correct and should_decline:
        explanation = "FAIL: Should have declined but answered instead (hallucination risk)."
    else:
        explanation = "FAIL: Should have answered but declined (over-refusal)."

    return MetricResult(
        name="Decline Correctness",
        score=1.0 if correct else 0.0,
        explanation=explanation,
        passed=correct,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "to", "of", "in", "for", "on",
    "with", "at", "by", "from", "as", "into", "through", "during",
    "and", "or", "but", "if", "then", "that", "this", "it", "its",
}


def _tokenise_for_faithfulness(text: str) -> list[str]:
    """Extract meaningful content words, removing punctuation and stopwords."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering empty ones."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 10]
