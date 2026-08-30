"""
Shared singleton dependencies for FastAPI routes.
Uses lru_cache so VectorStore, SparseRetriever, and HybridRetriever
are created once at startup and reused across all requests.
"""


from functools import lru_cache

from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.vector_store import VectorStore


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """Singleton VectorStore — created once, reused on every request."""
    return VectorStore()


@lru_cache(maxsize=1)
def get_sparse_retriever() -> SparseRetriever:
    """
    Singleton SparseRetriever with BM25 index pre-built from stored docs.

    On first call, fetches all documents from ChromaDB and builds the BM25 index.
    Trade-off: cold start ~1-5s depending on corpus size, but subsequent requests
    are instant (~1ms for BM25 lookup).
    """
    store   = get_vector_store()
    sparse  = SparseRetriever()
    all_docs = store.get_all_documents()
    if all_docs:
        sparse.build_index(all_docs)
    return sparse


@lru_cache(maxsize=1)
def get_hybrid_retriever() -> HybridRetriever:
    """Singleton HybridRetriever wired to the shared store and BM25 index."""
    return HybridRetriever(
        vector_store=get_vector_store(),
        sparse_retriever=get_sparse_retriever(),
    )


def invalidate_retriever_cache() -> None:
    """
    Clear the lru_cache after ingestion so the next request gets a
    fresh BM25 index that includes newly added documents.

    Called by the ingestion routes after successfully adding documents.
    """
    get_sparse_retriever.cache_clear()
    get_hybrid_retriever.cache_clear()
