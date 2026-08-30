"""Ingestion routes — POST /ingest/pdf  and  POST /ingest/url"""
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import (
    get_sparse_retriever,
    get_vector_store,
    invalidate_retriever_cache,
)
from app.api.schemas import IngestionResponse, IngestUrlRequest
from app.ingestion.loader import DocumentLoadError
from app.retrieval.pipeline import ingest_source
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# Max upload size: 50 MB — reasonable for multi-page legal documents
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.post(
    "/pdf",
    response_model=IngestionResponse,
    summary="Upload and ingest a PDF contract",
)
async def ingest_pdf(
    file: UploadFile = File(..., description="PDF file to ingest (max 50 MB)"),
    store:  VectorStore    = Depends(get_vector_store),
    sparse: SparseRetriever = Depends(get_sparse_retriever),
) -> IngestionResponse:
    """
    Upload a PDF contract for ingestion into the vector store.

    The file is:
    1. Validated (must be a .pdf file, max 50 MB)
    2. Saved to a temporary file
    3. Loaded page-by-page and split into chunks
    4. Embedded and stored in ChromaDB
    5. BM25 index rebuilt to include the new document

    Re-uploading the same file is **idempotent** — chunks are upserted,
    not duplicated, thanks to stable SHA-256 chunk IDs.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422,
            detail="Only PDF files are supported. Please upload a .pdf file.",
        )

    # Read file content and check size
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content) / 1024 / 1024:.1f} MB). Maximum is 50 MB.",
        )

    # Save to a temp file — ingestion pipeline expects a file path
    # Trade-off: temp file vs in-memory stream
    #   pypdf works best with file paths; in-memory BytesIO adds complexity.
    #   Temp files are cleaned up automatically when context exits.
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = ingest_source(
            source=tmp_path,
            vector_store=store,
            sparse_retriever=sparse,
        )
    except DocumentLoadError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception(f"Ingestion failed for {file.filename}: {exc}")
        raise HTTPException(status_code=500, detail="Ingestion failed. See server logs.")
    finally:
        tmp_path.unlink(missing_ok=True)  # Always clean up temp file

    # Invalidate cached retriever so next query uses the updated BM25 index
    invalidate_retriever_cache()

    return IngestionResponse(
        success=True,
        source=file.filename,
        pages_loaded=result.pages_loaded,
        chunks_created=result.chunks_created,
        processing_time_ms=result.processing_time_ms,
        doc_type="pdf",
        total_chunks_in_store=store.count(),
        message=f"Successfully ingested '{file.filename}' — {result.chunks_created} chunks added.",
    )


@router.post(
    "/url",
    response_model=IngestionResponse,
    summary="Ingest a contract from a public URL",
)
def ingest_url(
    request: IngestUrlRequest,
    store:  VectorStore     = Depends(get_vector_store),
    sparse: SparseRetriever = Depends(get_sparse_retriever),
) -> IngestionResponse:
    """
    Scrape and ingest a legal document from a public HTTP/HTTPS URL.

    Works best for:
    - Static HTML legal document portals
    - Government legislation pages
    - Public contract templates

    **Limitation**: JavaScript-rendered pages are not supported.
    For those, download the page as PDF and use the /ingest/pdf endpoint.
    """
    try:
        result = ingest_source(
            source=request.url,
            vector_store=store,
            sparse_retriever=sparse,
        )
    except DocumentLoadError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception(f"URL ingestion failed for {request.url}: {exc}")
        raise HTTPException(status_code=500, detail="URL ingestion failed. See server logs.")

    invalidate_retriever_cache()

    return IngestionResponse(
        success=True,
        source=request.url,
        pages_loaded=result.pages_loaded,
        chunks_created=result.chunks_created,
        processing_time_ms=result.processing_time_ms,
        doc_type="url",
        total_chunks_in_store=store.count(),
        message=f"Successfully ingested URL — {result.chunks_created} chunks added.",
    )
