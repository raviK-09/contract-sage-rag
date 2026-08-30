"""Pydantic request/response models for all API endpoints."""


from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


# ── Request Schemas ───────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Request body for POST /query"""
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language question about the uploaded contracts.",
        examples=["What is the notice period for terminating the lease?"],
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of chunks to retrieve. Defaults to settings.TOP_K.",
    )
    reasoning_mode: bool = Field(
        default=False,
        description=(
            "Enable chain-of-thought reasoning. Improves accuracy on complex "
            "questions but increases latency by ~30%."
        ),
    )


class IngestUrlRequest(BaseModel):
    """Request body for POST /ingest/url"""
    url: str = Field(
        ...,
        description="Public HTTP/HTTPS URL to scrape and ingest.",
        examples=["https://example.com/contract.html"],
    )


# ── Response Schemas ──────────────────────────────────────────────────────────

class CitationSchema(BaseModel):
    """A single source citation returned in the query response."""
    source_num: int
    file_name: str
    page: int
    doc_type: str
    relevant_snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ConfidenceSchema(BaseModel):
    """Confidence score breakdown for the query response."""
    score: float = Field(ge=0.0, le=1.0, description="Combined confidence score.")
    label: str   = Field(description="'High', 'Medium', or 'Low'")
    retrieval_score: float
    coverage_score: float
    citation_score: float
    threshold_used: float


class QueryResponse(BaseModel):
    """Response body for POST /query"""
    question: str
    answer: str
    is_declined: bool = Field(
        description="True if system declined to answer due to low confidence."
    )
    confidence: ConfidenceSchema
    citations: list[CitationSchema]
    sources_cited: list[str] = Field(
        description="Unique document filenames that were cited."
    )
    latency_ms: float
    retrieval_ms: float
    generation_ms: float


class IngestionResponse(BaseModel):
    """Response body for POST /ingest/pdf and POST /ingest/url"""
    success: bool
    source: str
    pages_loaded: int
    chunks_created: int
    processing_time_ms: float
    doc_type: str
    total_chunks_in_store: int
    message: str


class DocumentInfo(BaseModel):
    """Metadata about a single ingested document."""
    file_name: str
    source: str
    doc_type: str
    total_pages: int
    chunk_count: int
    loaded_at: str


class DocumentListResponse(BaseModel):
    """Response body for GET /documents"""
    documents: list[DocumentInfo]
    total_documents: int
    total_chunks: int


class DeleteResponse(BaseModel):
    """Response body for DELETE /documents/{source}"""
    success: bool
    source: str
    chunks_deleted: int
    message: str


class HealthResponse(BaseModel):
    """Response body for GET /health"""
    status: str
    ollama_running: bool
    primary_model_available: bool
    fallback_model_available: bool
    vector_store_chunks: int
    available_models: list[str]
    app_name: str
    version: str
