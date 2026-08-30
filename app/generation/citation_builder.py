"""
Citation Builder — Phase 4: Generation
========================================
Parses [Source N] references from LLM output and maps them back
to the original document metadata.

Why citations matter:
  Without citations, the user has to trust the LLM blindly.
  With citations, every claim links to an exact page/clause — the user
  can verify the answer themselves. This is the key differentiator
  between a toy demo and a production-grade legal tool.

Design: Parse → Map → Structure
  1. Parse: find all [Source N] patterns in the LLM response
  2. Map  : look up each source number in the BuiltContext source_map
  3. Build: return structured Citation objects with full metadata

Trade-off — Regex parsing vs structured output (JSON mode):
  Structured output (Ollama/OpenAI JSON mode) would guarantee parseable
  citations but:
  - Not all local models support JSON mode reliably
  - Constraining output format reduces answer quality on smaller models
  - Regex parsing is robust enough for [Source N] patterns
  We use regex with a graceful fallback (empty citations list) so the
  answer is still returned even if parsing fails partially.
"""

import logging
import re
from dataclasses import dataclass, field

from app.generation.prompt_templates import BuiltContext
from app.retrieval.hybrid_retriever import RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """A single source citation with full document metadata."""
    source_num: int          # The [Source N] number from LLM output
    file_name: str           # Document filename
    page: int                # Page number (1-indexed)
    doc_type: str            # "pdf" or "url"
    source_url: str          # Full path or URL
    relevant_snippet: str    # First 300 chars of the chunk text
    relevance_score: float   # Cosine similarity score from retrieval
    chunk_id: str            # Stable chunk ID for deduplication


@dataclass
class CitedAnswer:
    """The complete structured answer from the generation pipeline."""
    answer_text: str                     # Clean answer text (citations intact)
    citations: list[Citation]            # Structured citation objects
    is_insufficient: bool                # True if LLM flagged INSUFFICIENT_CONTEXT
    insufficient_reason: str             # Reason if insufficient
    raw_response: str                    # Unmodified LLM response
    reasoning: str = ""                  # Chain-of-thought reasoning (if used)
    cited_source_nums: list[int] = field(default_factory=list)  # [1, 3, 5] etc.

    @property
    def has_citations(self) -> bool:
        return len(self.citations) > 0

    @property
    def unique_documents(self) -> list[str]:
        """List of unique document filenames cited."""
        return list(dict.fromkeys(c.file_name for c in self.citations))


# ── Citation Parser ───────────────────────────────────────────────────────────

# Matches: [Source 1], [Source 12], [Source 1, 2], [Sources 1 and 2]
_SOURCE_PATTERN = re.compile(
    r"\[(?:Source[s]?\s*)(\d+(?:[,\s]+\d+)*)\]",
    re.IGNORECASE,
)

# Detects INSUFFICIENT_CONTEXT signal from LLM
_INSUFFICIENT_PATTERN = re.compile(
    r"INSUFFICIENT_CONTEXT\s*:\s*(.+?)(?:\n|$)",
    re.IGNORECASE | re.DOTALL,
)

# Splits REASONING: ... ANSWER: ... format (chain-of-thought mode)
_REASONING_PATTERN = re.compile(
    r"REASONING\s*:\s*(.+?)\s*ANSWER\s*:\s*(.+)",
    re.IGNORECASE | re.DOTALL,
)


def parse_cited_answer(
    raw_response: str,
    built_context: BuiltContext,
) -> CitedAnswer:
    """
    Parse the LLM's raw response into a structured CitedAnswer.

    Handles three response formats:
    1. Normal answer with [Source N] citations
    2. INSUFFICIENT_CONTEXT: explanation
    3. REASONING: ... ANSWER: ... (chain-of-thought mode)

    Args:
        raw_response  : The raw string output from the LLM.
        built_context : Context mapping from prompt_templates.build_context_from_chunks().

    Returns:
        CitedAnswer with structured citations and metadata.
    """
    raw = raw_response.strip()
    reasoning = ""
    answer_text = raw

    # ── Handle chain-of-thought format ───────────────────────────────────────
    cot_match = _REASONING_PATTERN.search(raw)
    if cot_match:
        reasoning   = cot_match.group(1).strip()
        answer_text = cot_match.group(2).strip()

    # ── Handle INSUFFICIENT_CONTEXT signal ───────────────────────────────────
    insuf_match = _INSUFFICIENT_PATTERN.search(answer_text)
    if insuf_match:
        reason = insuf_match.group(1).strip()
        logger.info(f"LLM signalled insufficient context: {reason}")
        return CitedAnswer(
            answer_text=answer_text,
            citations=[],
            is_insufficient=True,
            insufficient_reason=reason,
            raw_response=raw,
            reasoning=reasoning,
            cited_source_nums=[],
        )

    # ── Parse [Source N] citations ────────────────────────────────────────────
    cited_nums = _extract_source_numbers(answer_text)
    citations  = _build_citations(cited_nums, built_context)

    if cited_nums and not citations:
        # LLM cited sources but they weren't in our context map
        logger.warning(
            f"LLM cited sources {cited_nums} but none found in context map "
            f"(available: {list(built_context.source_map.keys())})"
        )

    return CitedAnswer(
        answer_text=answer_text,
        citations=citations,
        is_insufficient=False,
        insufficient_reason="",
        raw_response=raw,
        reasoning=reasoning,
        cited_source_nums=cited_nums,
    )


def _extract_source_numbers(text: str) -> list[int]:
    """
    Extract all [Source N] numbers from text, deduplicating and sorting.

    Handles:
      [Source 1]          → [1]
      [Source 1, 2]       → [1, 2]
      [Sources 1 and 2]   → [1, 2]
      [Source 1][Source 3]→ [1, 3]
    """
    nums: set[int] = set()
    for match in _SOURCE_PATTERN.finditer(text):
        # Extract all digit sequences from the match group
        for num_str in re.findall(r"\d+", match.group(1)):
            nums.add(int(num_str))
    return sorted(nums)


def _build_citations(
    source_nums: list[int],
    built_context: BuiltContext,
) -> list[Citation]:
    """
    Build Citation objects for each source number found in the answer.

    Args:
        source_nums   : List of [Source N] numbers cited by the LLM.
        built_context : Maps source numbers to RetrievedChunk objects.

    Returns:
        List of Citation objects (skips any source nums not in context map).
    """
    citations: list[Citation] = []
    seen_chunk_ids: set[str] = set()

    for num in source_nums:
        chunk = built_context.source_map.get(num)
        if chunk is None:
            continue  # LLM hallucinated a source number — skip silently

        chunk_id = chunk.document.metadata.get("chunk_id", f"chunk_{num}")

        # Deduplicate — same chunk cited multiple times → one citation
        if chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk_id)

        citations.append(
            Citation(
                source_num=num,
                file_name=chunk.document.metadata.get("file_name", "Unknown"),
                page=int(chunk.document.metadata.get("page", 0)),
                doc_type=chunk.document.metadata.get("doc_type", "pdf"),
                source_url=chunk.document.metadata.get("source", ""),
                relevant_snippet=chunk.document.page_content[:300].strip(),
                relevance_score=chunk.dense_score,
                chunk_id=chunk_id,
            )
        )

    return citations


def format_citations_for_display(citations: list[Citation]) -> str:
    """
    Format citations as a readable reference list (for terminal/API output).

    Example output:
        References:
        [1] residential_rental_agreement.pdf — Page 3
            "Either party must give 2 months' written notice..."
        [2] residential_rental_agreement.pdf — Page 2
            "The security deposit shall be refunded within 60 days..."
    """
    if not citations:
        return ""

    lines = ["", "**References:**"]
    for cite in citations:
        label_type = "Page" if cite.doc_type == "pdf" else "Section"
        lines.append(f"[{cite.source_num}] {cite.file_name} — {label_type} {cite.page}")
        lines.append(f'    "{cite.relevant_snippet[:120]}..."')
        lines.append(f"    Relevance: {cite.relevance_score:.1%}")
        lines.append("")

    return "\n".join(lines)
