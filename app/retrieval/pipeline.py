"""
Ingestion Pipeline Orchestrator — Phase 3: Retrieval
======================================================
High-level function that wires together:
  loader → chunker → vector_store + sparse_retriever

This is the single function called by the API route (POST /ingest/pdf)
and the seed_data script. It encapsulates the full ingestion flow.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from app.ingestion.chunker import chunk_documents
from app.ingestion.loader import load_documents
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Summary of a completed ingestion run."""
    source: str
    pages_loaded: int
    chunks_created: int
    processing_time_ms: float
    doc_type: str       # "pdf" or "url"


def ingest_source(
    source: Union[str, Path],
    vector_store: VectorStore,
    sparse_retriever: SparseRetriever,
    rebuild_bm25: bool = True,
) -> IngestionResult:
    """
    Full ingestion pipeline: source → load → chunk → embed → store.

    Steps:
    1. load_documents()   : parse PDF / scrape URL
    2. chunk_documents()  : split into overlapping chunks with metadata
    3. vector_store.add_documents()  : embed + persist to ChromaDB
    4. sparse_retriever.build_index(): rebuild BM25 over ALL stored docs

    Args:
        source           : Path to PDF or HTTP(S) URL.
        vector_store     : VectorStore instance to persist chunks.
        sparse_retriever : SparseRetriever to rebuild BM25 index after ingestion.
        rebuild_bm25     : If False, skip BM25 rebuild (use when batch-ingesting
                           multiple docs — rebuild once at the end).

    Returns:
        IngestionResult with stats for display in the UI/API.
    """
    start_time = time.perf_counter()
    source_str = str(source)

    logger.info(f"Starting ingestion: {source_str}")

    # Step 1: Load
    raw_docs = load_documents(source)
    doc_type = raw_docs[0].metadata.get("doc_type", "unknown") if raw_docs else "unknown"
    pages_loaded = len(raw_docs)

    # Step 2: Chunk
    chunks = chunk_documents(raw_docs)
    chunks_created = len(chunks)

    # Step 3: Store in ChromaDB (vector store handles embedding internally)
    vector_store.add_documents(chunks)

    # Step 4: Rebuild BM25 index over ALL docs in the store
    # We rebuild from scratch because BM25Okapi doesn't support incremental updates.
    # Trade-off: O(n) rebuild each time — acceptable at our scale.
    if rebuild_bm25:
        all_docs = vector_store.get_all_documents()
        sparse_retriever.build_index(all_docs)
        logger.info(f"BM25 index rebuilt with {len(all_docs)} total chunks.")

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    result = IngestionResult(
        source=source_str,
        pages_loaded=pages_loaded,
        chunks_created=chunks_created,
        processing_time_ms=round(elapsed_ms, 1),
        doc_type=doc_type,
    )

    logger.info(
        f"Ingestion complete: {pages_loaded} pages → {chunks_created} chunks "
        f"in {elapsed_ms:.0f}ms"
    )
    return result
