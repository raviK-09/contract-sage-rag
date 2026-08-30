"""
ChromaDB abstraction layer for storing, searching, and managing document chunks.
The rest of the codebase never imports chromadb directly — only this module does.
"""


import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_core.documents import Document

from app.config import settings
from app.ingestion.embedder import get_embedder

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB-backed vector store with a clean interface.

    Responsibilities:
      - add_documents()      : embed chunks and persist them
      - similarity_search()  : find top-k similar chunks for a query
      - get_all_documents()  : retrieve all stored chunks (for BM25 corpus)
      - delete_collection()  : wipe and reset the store
      - count()              : number of stored chunks
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_dir: Optional[Path] = None,
    ) -> None:
        self._collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self._persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR

        # Ensure persist directory exists
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # Persistent ChromaDB client
        # Trade-off: PersistentClient vs EphemeralClient (in-memory)
        #   PersistentClient → survives restarts, needed for production
        #   EphemeralClient  → faster for tests, data lost on exit
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create the collection
        # Trade-off: cosine vs l2 vs ip distance
        #   cosine → best for normalised embeddings (what we produce)
        #   l2     → Euclidean, works with unnormalised embeddings
        #   ip     → inner product, fastest but requires unit vectors
        # We normalise embeddings in embedder.py → cosine is correct here
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self._embedder = get_embedder()
        logger.info(
            f"VectorStore ready: collection='{self._collection_name}' "
            f"persist_dir='{self._persist_dir}' "
            f"existing_docs={self._collection.count()}"
        )

    # ── Write Operations ──────────────────────────────────────────────────────

    def add_documents(self, documents: list[Document]) -> int:
        """
        Embed and store a list of chunked Documents.

        Uses the stable chunk_id from metadata as the ChromaDB document ID.
        This makes ingestion IDEMPOTENT — adding the same document twice
        will upsert (update) rather than duplicate.

        Trade-off: upsert vs insert
          - insert → fails on duplicate IDs (safer but fragile for re-ingestion)
          - upsert → overwrites duplicates (safe for re-running seed scripts)
          We chose upsert because re-ingesting a corrected PDF should update
          the chunks, not fail.

        Args:
            documents: List of chunked Documents with metadata.

        Returns:
            Number of documents added/updated.
        """
        if not documents:
            logger.warning("add_documents called with empty list.")
            return 0

        texts    = [doc.page_content for doc in documents]
        ids      = [doc.metadata.get("chunk_id", f"chunk_{i}") for i, doc in enumerate(documents)]
        metadatas = [_serialize_metadata(doc.metadata) for doc in documents]

        logger.info(f"Embedding {len(texts)} chunks...")
        embeddings = self._embedder.embed_documents(texts)

        # Upsert in batches of 500 to avoid memory spikes
        batch_size = 500
        for i in range(0, len(texts), batch_size):
            self._collection.upsert(
                ids=ids[i : i + batch_size],
                documents=texts[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )
            logger.debug(f"Upserted batch {i//batch_size + 1}")

        logger.info(f"Stored {len(documents)} chunks. Total in store: {self._collection.count()}")
        return len(documents)

    # ── Read Operations ───────────────────────────────────────────────────────

    def similarity_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        where: Optional[dict] = None,
    ) -> list[tuple[Document, float]]:
        """
        Find the top-k most similar chunks for a query using cosine similarity.

        Returns (Document, score) tuples where score is in [0, 1].
        Higher score = more similar.

        Note on ChromaDB distances:
          ChromaDB returns DISTANCES (lower = more similar) for cosine space.
          We convert to SIMILARITY = 1 - distance so higher = better,
          which is the intuitive mental model and consistent with our
          confidence scoring logic.

        Args:
            query  : The user's question.
            top_k  : Number of results (default from settings).
            where  : Optional metadata filter dict (ChromaDB filter syntax).

        Returns:
            List of (Document, similarity_score) sorted by score descending.
        """
        k = top_k or settings.TOP_K

        if self._collection.count() == 0:
            logger.warning("similarity_search called on empty collection.")
            return []

        query_embedding = self._embedder.embed_query(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self._collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        output: list[tuple[Document, float]] = []
        for text, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Convert cosine distance → similarity score
            # distance ∈ [0, 2] for cosine → similarity ∈ [-1, 1]
            # For normalised embeddings distance ∈ [0, 1] → similarity ∈ [0, 1]
            similarity = max(0.0, 1.0 - distance)
            doc = Document(page_content=text, metadata=metadata)
            output.append((doc, round(similarity, 4)))

        # Sort by similarity descending (highest first)
        output.sort(key=lambda x: x[1], reverse=True)
        return output

    def get_all_documents(self) -> list[Document]:
        """
        Retrieve ALL documents from the store.

        Used by the BM25 retriever to build its keyword index.

        Trade-off: Fetching all docs for BM25 index is O(n) memory.
        For our scale (hundreds of contract chunks) this is fine.
        At millions of documents, you'd want a separate BM25 index
        persisted alongside the vector store (e.g. Elasticsearch).
        """
        if self._collection.count() == 0:
            return []

        results = self._collection.get(include=["documents", "metadatas"])
        return [
            Document(page_content=text, metadata=meta)
            for text, meta in zip(results["documents"], results["metadatas"])
        ]

    def delete_by_source(self, source: str) -> int:
        """
        Delete all chunks from a specific source file/URL.

        Useful for "re-upload" functionality — user re-uploads a corrected
        contract, we delete old chunks and insert new ones.

        Args:
            source: The 'source' metadata value (file path or URL).

        Returns:
            Number of chunks deleted.
        """
        results = self._collection.get(
            where={"source": source},
            include=["documents"],
        )
        ids_to_delete = results.get("ids", [])

        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for source: {source}")

        return len(ids_to_delete)

    def delete_collection(self) -> None:
        """Wipe the entire collection. Used for testing and full resets."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning(f"Collection '{self._collection_name}' wiped and recreated.")

    def count(self) -> int:
        """Return the number of stored chunks."""
        return self._collection.count()


# ── Module-level singleton ────────────────────────────────────────────────────

_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Return a cached singleton VectorStore instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = VectorStore()
    return _store_instance


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_metadata(metadata: dict) -> dict:
    """
    Ensure all metadata values are ChromaDB-compatible types.

    ChromaDB only accepts: str, int, float, bool
    Converts Path objects, lists, and None to strings.
    """
    serialized = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            serialized[key] = value
        elif value is None:
            serialized[key] = ""
        else:
            serialized[key] = str(value)
    return serialized
