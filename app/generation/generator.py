"""
Answer Generator — Phase 4: Generation
========================================
Top-level orchestrator that wires together:
  retriever → prompt builder → LLM → citation parser → confidence scorer

This is the single function called by the FastAPI route (POST /query)
and the Streamlit UI. It returns a clean, fully-structured response.
"""

import logging
import time
from dataclasses import dataclass, field

from app.config import settings
from app.generation.citation_builder import CitedAnswer, parse_cited_answer, format_citations_for_display
from app.generation.confidence import ConfidenceResult, compute_confidence
from app.generation.llm_client import get_primary_llm
from app.generation.prompt_templates import build_decline_message, build_messages
from app.retrieval.hybrid_retriever import HybridRetriever, RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class QueryResponse:
    """
    The complete, structured response from the generation pipeline.
    This is what the FastAPI endpoint returns as JSON.
    """
    # Core answer fields
    question: str
    answer: str                          # Final answer to show the user
    is_declined: bool                    # True if system declined to answer

    # Confidence
    confidence: ConfidenceResult

    # Citations
    cited_answer: CitedAnswer
    formatted_citations: str            # Ready-to-display citation list

    # Retrieval context (for debugging / eval)
    retrieved_chunks: list[RetrievedChunk]

    # Performance
    latency_ms: float
    retrieval_ms: float
    generation_ms: float

    @property
    def confidence_score(self) -> float:
        return self.confidence.score

    @property
    def sources_cited(self) -> list[str]:
        return self.cited_answer.unique_documents


def answer_question(
    question: str,
    retriever: HybridRetriever,
    top_k: int | None = None,
    reasoning_mode: bool = False,
) -> QueryResponse:
    """
    Full RAG pipeline: question → retrieve → generate → cite → score.

    Steps:
    1. Hybrid retrieval (dense + BM25 + RRF + MMR)
    2. Build prompt with numbered [Source N] context
    3. Call Ollama LLM
    4. Parse citations from LLM response
    5. Compute confidence score
    6. Return answer or decline message

    Args:
        question      : The user's natural language question.
        retriever     : Configured HybridRetriever instance.
        top_k         : Override number of chunks to retrieve.
        reasoning_mode: Use chain-of-thought prompting (slower, more accurate).

    Returns:
        QueryResponse with answer, citations, confidence, and timing.
    """
    t_total_start = time.perf_counter()
    k = top_k or settings.TOP_K

    # ── Step 1: Retrieve relevant chunks ──────────────────────────────────────
    t_retrieval_start = time.perf_counter()
    chunks: list[RetrievedChunk] = retriever.retrieve(question, top_k=k)
    retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000

    logger.info(f"Retrieved {len(chunks)} chunks in {retrieval_ms:.0f}ms")

    # ── Step 2: Early decline if no chunks retrieved ───────────────────────────
    if not chunks:
        logger.warning("No chunks retrieved — declining immediately.")
        empty_cited = CitedAnswer(
            answer_text="",
            citations=[],
            is_insufficient=True,
            insufficient_reason="No documents have been ingested yet. Please upload a contract first.",
            raw_response="",
        )
        empty_conf = compute_confidence([], empty_cited)
        return QueryResponse(
            question=question,
            answer=build_decline_message(empty_conf.decline_reason),
            is_declined=True,
            confidence=empty_conf,
            cited_answer=empty_cited,
            formatted_citations="",
            retrieved_chunks=[],
            latency_ms=0.0,
            retrieval_ms=retrieval_ms,
            generation_ms=0.0,
        )

    # ── Step 3: Build prompt and call LLM ─────────────────────────────────────
    t_gen_start = time.perf_counter()
    messages, built_context = build_messages(
        query=question,
        chunks=chunks,
        reasoning_mode=reasoning_mode,
    )

    llm = get_primary_llm()
    logger.info(f"Calling LLM ({settings.LLM_MODEL})...")

    try:
        ai_message = llm.invoke(messages)
        raw_response = ai_message.content
    except Exception as exc:
        logger.error(f"LLM call failed: {exc}")
        # Graceful degradation: return a clear error rather than crashing
        raise RuntimeError(
            f"LLM call failed. Make sure Ollama is running: "
            f"`ollama serve` and model is pulled: `ollama pull {settings.LLM_MODEL}`"
        ) from exc

    generation_ms = (time.perf_counter() - t_gen_start) * 1000
    logger.info(f"LLM responded in {generation_ms:.0f}ms")

    # ── Step 4: Parse citations ────────────────────────────────────────────────
    cited_answer = parse_cited_answer(raw_response, built_context)
    formatted_citations = format_citations_for_display(cited_answer.citations)

    logger.info(
        f"Citations found: {cited_answer.cited_source_nums} | "
        f"Insufficient: {cited_answer.is_insufficient}"
    )

    # ── Step 5: Compute confidence ─────────────────────────────────────────────
    confidence = compute_confidence(
        retrieved_chunks=chunks,
        cited_answer=cited_answer,
    )

    # ── Step 6: Decide answer vs decline ──────────────────────────────────────
    is_declined = confidence.should_decline

    if is_declined:
        final_answer = build_decline_message(confidence.decline_reason)
        logger.info(f"Declined: {confidence.decline_reason}")
    else:
        final_answer = cited_answer.answer_text
        logger.info(
            f"Answered: confidence={confidence.score:.2f} ({confidence.label}) "
            f"citations={len(cited_answer.citations)}"
        )

    total_ms = (time.perf_counter() - t_total_start) * 1000

    return QueryResponse(
        question=question,
        answer=final_answer,
        is_declined=is_declined,
        confidence=confidence,
        cited_answer=cited_answer,
        formatted_citations=formatted_citations,
        retrieved_chunks=chunks,
        latency_ms=round(total_ms, 1),
        retrieval_ms=round(retrieval_ms, 1),
        generation_ms=round(generation_ms, 1),
    )
