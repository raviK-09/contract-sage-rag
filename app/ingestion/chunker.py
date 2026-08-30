"""
Splits loaded Documents into smaller chunks using RecursiveCharacterTextSplitter.
Preserves source metadata on every chunk and adds a stable SHA-256 chunk ID.
"""

import hashlib
import logging
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)


def chunk_documents(
    documents: list[Document],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[Document]:
    """
    Split a list of Documents into smaller chunks using recursive character splitting.

    Each output chunk inherits the full metadata of its parent document plus:
      - chunk_index  : 0-based index within chunks from the SAME source+page
      - chunk_total  : total chunks from this source+page combination
      - chunk_id     : stable unique ID  (sha256 of source+page+chunk_index)
      - char_start   : approximate character offset in original page text
      - char_length  : length of this chunk's text

    Args:
        documents    : List of Documents from the loader (one per PDF page / URL).
        chunk_size   : Override the default chunk size from settings.
        chunk_overlap: Override the default overlap from settings.

    Returns:
        List of chunk Documents ready for embedding.
    """
    size    = chunk_size    or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if overlap >= size:
        raise ValueError(
            f"chunk_overlap ({overlap}) must be less than chunk_size ({size})"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        # Separator hierarchy (tries each in order until chunks are small enough)
        # Trade-off: paragraph breaks first → keeps legal clauses together.
        # Falling back to word boundaries ensures no chunk exceeds size.
        separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
        length_function=len,
        is_separator_regex=False,
        add_start_index=True,   # Adds 'start_index' to metadata (char offset)
    )

    logger.info(
        f"Chunking {len(documents)} document(s) "
        f"[chunk_size={size}, overlap={overlap}]"
    )

    all_chunks: list[Document] = []

    for doc in documents:
        # Split this single document
        raw_chunks = splitter.split_documents([doc])

        # Enrich metadata on every chunk
        for idx, chunk in enumerate(raw_chunks):
            # Generate a stable, unique chunk ID for deduplication
            chunk_id = _make_chunk_id(
                source=chunk.metadata.get("source", ""),
                page=chunk.metadata.get("page", 0),
                chunk_index=idx,
            )

            chunk.metadata.update(
                {
                    "chunk_index": idx,
                    "chunk_total": len(raw_chunks),
                    "chunk_id": chunk_id,
                    "char_length": len(chunk.page_content),
                    # 'start_index' already added by splitter (char offset in original)
                }
            )
            all_chunks.append(chunk)

    logger.info(
        f"Produced {len(all_chunks)} chunks from {len(documents)} document(s) "
        f"(avg {len(all_chunks)//max(len(documents),1)} chunks/doc)"
    )

    return all_chunks


def _make_chunk_id(source: str, page: int, chunk_index: int) -> str:
    """
    Generate a deterministic, stable chunk ID.

    Using SHA-256 of (source + page + index) gives us:
    - Deduplication: same chunk → same ID regardless of re-ingestion order
    - Stability: IDs don't change between runs as long as content doesn't change
    - Uniqueness: practically collision-free across all documents

    Trade-off vs UUID4: UUID4 is simpler but not deterministic — re-ingesting
    the same document would create duplicate entries in ChromaDB. SHA-256 IDs
    allow idempotent ingestion (safe to re-run without duplicating).
    """
    raw = f"{source}::page={page}::chunk={chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]   # 32 hex chars (128-bit)
