"""Query route — POST /query"""
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_hybrid_retriever
from app.api.schemas import CitationSchema, ConfidenceSchema, QueryRequest, QueryResponse
from app.generation.generator import answer_question
from app.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse, summary="Ask a question about your contracts")
def query_endpoint(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
) -> QueryResponse:
    """
    Ask a natural language question about the ingested contracts.

    The system will:
    1. Retrieve the most relevant chunks using hybrid search (dense + BM25)
    2. Generate an answer with source citations using a local LLM
    3. Compute a confidence score — if below threshold, decline to answer
    4. Return the answer, citations, and confidence breakdown

    **Decline-to-answer**: If confidence < threshold (configurable in .env),
    the system returns `is_declined: true` with a helpful message explaining why.
    This prevents hallucinations on out-of-scope questions.
    """
    try:
        result = answer_question(
            question=request.question,
            retriever=retriever,
            top_k=request.top_k,
            reasoning_mode=request.reasoning_mode,
        )
    except RuntimeError as exc:
        # LLM not available (Ollama not running / model not pulled)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Unexpected error during query: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error during query.")

    # Map internal dataclasses → API schemas
    return QueryResponse(
        question=result.question,
        answer=result.answer,
        is_declined=result.is_declined,
        confidence=ConfidenceSchema(
            score=result.confidence.score,
            label=result.confidence.label,
            retrieval_score=result.confidence.retrieval_score,
            coverage_score=result.confidence.coverage_score,
            citation_score=result.confidence.citation_score,
            threshold_used=result.confidence.threshold_used,
        ),
        citations=[
            CitationSchema(
                source_num=c.source_num,
                file_name=c.file_name,
                page=c.page,
                doc_type=c.doc_type,
                relevant_snippet=c.relevant_snippet,
                relevance_score=c.relevance_score,
            )
            for c in result.cited_answer.citations
        ],
        sources_cited=result.sources_cited,
        latency_ms=result.latency_ms,
        retrieval_ms=result.retrieval_ms,
        generation_ms=result.generation_ms,
    )
