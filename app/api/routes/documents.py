"""Documents management routes — GET /documents  and  DELETE /documents/{source}"""
import logging
from collections import defaultdict
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_sparse_retriever,
    get_vector_store,
    invalidate_retriever_cache,
)
from app.api.schemas import DeleteResponse, DocumentInfo, DocumentListResponse
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all ingested documents",
)
def list_documents(
    store: VectorStore = Depends(get_vector_store),
) -> DocumentListResponse:
    """
    List all documents currently in the vector store.

    Returns one entry per unique source document, with chunk count,
    page count, and the timestamp when it was first ingested.
    Used by the Streamlit UI to show the "Uploaded Documents" sidebar.
    """
    all_docs = store.get_all_documents()

    if not all_docs:
        return DocumentListResponse(documents=[], total_documents=0, total_chunks=0)

    # Group chunks by source to build per-document summaries
    # Trade-off: O(n) pass over all chunks — acceptable at our scale.
    # At 100k+ chunks, you'd maintain a separate document registry.
    doc_groups: dict[str, dict] = defaultdict(lambda: {
        "file_name": "",
        "source": "",
        "doc_type": "",
        "pages": set(),
        "chunk_count": 0,
        "loaded_at": "",
    })

    for doc in all_docs:
        m = doc.metadata
        source = m.get("source", "unknown")
        grp = doc_groups[source]
        grp["file_name"]   = m.get("file_name", source)
        grp["source"]      = source
        grp["doc_type"]    = m.get("doc_type", "pdf")
        grp["chunk_count"] += 1
        grp["loaded_at"]   = m.get("loaded_at", "")
        if m.get("page"):
            grp["pages"].add(int(m["page"]))

    documents = [
        DocumentInfo(
            file_name=g["file_name"],
            source=g["source"],
            doc_type=g["doc_type"],
            total_pages=len(g["pages"]),
            chunk_count=g["chunk_count"],
            loaded_at=g["loaded_at"],
        )
        for g in doc_groups.values()
    ]

    # Sort by file name for consistent UI display
    documents.sort(key=lambda d: d.file_name)

    return DocumentListResponse(
        documents=documents,
        total_documents=len(documents),
        total_chunks=store.count(),
    )


@router.delete(
    "/{source}",
    response_model=DeleteResponse,
    summary="Remove a document from the vector store",
)
def delete_document(
    source: str,
    store:  VectorStore     = Depends(get_vector_store),
    sparse: SparseRetriever = Depends(get_sparse_retriever),
) -> DeleteResponse:
    """
    Remove all chunks for a specific source document.

    The `source` parameter should be the URL-encoded file path or URL.
    After deletion, the BM25 index is rebuilt to reflect the removal.

    Use case: User uploaded the wrong contract and wants to remove it,
    or an updated version of a contract needs to replace the old one
    (delete old → upload new).
    """
    # URL-decode the source path (handles spaces and special chars in filenames)
    decoded_source = unquote(source)

    try:
        deleted_count = store.delete_by_source(decoded_source)
    except Exception as exc:
        logger.exception(f"Delete failed for source '{decoded_source}': {exc}")
        raise HTTPException(status_code=500, detail="Delete operation failed.")

    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No document found with source: '{decoded_source}'",
        )

    # Rebuild BM25 index without the deleted document
    all_remaining = store.get_all_documents()
    if all_remaining:
        sparse.build_index(all_remaining)
    else:
        # Store is now empty — reset the sparse retriever
        sparse.build_index([])

    invalidate_retriever_cache()

    return DeleteResponse(
        success=True,
        source=decoded_source,
        chunks_deleted=deleted_count,
        message=f"Removed {deleted_count} chunks for '{decoded_source}'.",
    )
