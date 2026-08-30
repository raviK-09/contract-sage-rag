"""
Wraps sentence-transformers (all-MiniLM-L6-v2) to generate dense vector embeddings.
Exposed as a singleton via get_embedder() to avoid reloading the model on every call.
"""

import logging
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — model is loaded once and reused
# Trade-off: loading takes 1-5 seconds but inference is then fast
_embedder_instance: Optional[HuggingFaceEmbeddings] = None


def get_embedder(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
) -> HuggingFaceEmbeddings:
    """
    Return a cached HuggingFaceEmbeddings instance.

    Singleton pattern: the model is downloaded and loaded into memory
    only on first call. Subsequent calls reuse the same object.

    This is important because:
    - Loading a 80-400MB model takes 2-10 seconds
    - Each FastAPI request shouldn't reload the model
    - Memory: keeping one instance avoids OOM from multiple copies

    Args:
        model_name: Override the default embedding model from settings.
        device    : Override the compute device ('cpu', 'cuda', 'mps').

    Returns:
        A LangChain-compatible HuggingFaceEmbeddings object.
    """
    global _embedder_instance

    target_model  = model_name or settings.EMBEDDING_MODEL
    target_device = device     or settings.EMBEDDING_DEVICE

    # Return cached instance if model/device matches
    if _embedder_instance is not None:
        return _embedder_instance

    logger.info(
        f"Loading embedding model '{target_model}' on device='{target_device}' "
        f"(first load — this may take a few seconds)..."
    )

    _embedder_instance = HuggingFaceEmbeddings(
        model_name=target_model,
        model_kwargs={"device": target_device},
        encode_kwargs={
            # normalize_embeddings=True → cosine similarity == dot product
            # Trade-off: normalization adds a tiny compute cost but is
            # REQUIRED for correct cosine similarity in ChromaDB
            "normalize_embeddings": True,
            "batch_size": settings.EMBEDDING_BATCH_SIZE,
            # Note: do NOT pass show_progress_bar here —
            # langchain_huggingface 1.x passes it internally, causing
            # a duplicate keyword argument error with sentence-transformers 6.x
        },
        # Cache downloaded model in HuggingFace's default cache dir
        # (~/.cache/huggingface on Windows: C:\Users\<user>\.cache\huggingface)
        cache_folder=None,
    )

    logger.info(f"Embedding model loaded: '{target_model}'")
    return _embedder_instance


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of plain text strings.

    Convenience wrapper for direct text embedding (e.g. query embedding).

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (each is a list of floats).
    """
    embedder = get_embedder()
    return embedder.embed_documents(texts)


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string.

    Some models use different instructions for query vs document embeddings
    (e.g. BGE models prefix queries with "Represent this sentence for searching:").
    HuggingFaceEmbeddings handles this distinction automatically.

    Args:
        query: The user's question.

    Returns:
        Single embedding vector.
    """
    embedder = get_embedder()
    return embedder.embed_query(query)


def reset_embedder() -> None:
    """
    Clear the cached embedder instance.

    Useful in tests to reset state between test cases that use
    different model configurations.
    """
    global _embedder_instance
    _embedder_instance = None
    logger.debug("Embedder instance reset.")
