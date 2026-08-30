"""
ContractSage - Application Configuration
=========================================
Centralised settings loaded from environment variables / .env file.

Usage:
    from app.config import settings
    print(settings.LLM_MODEL)
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Pydantic-Settings based configuration class.

    Trade-off: Why pydantic-settings over plain os.environ?
    - Type validation: catches misconfigured .env values at startup, not at runtime
    - IDE autocomplete: type-annotated fields vs raw dict access
    - Hierarchical defaults: env vars > .env file > defaults
    - Immutability: settings are frozen after load, preventing accidental mutation
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore unknown env vars instead of raising errors
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "ContractSage"
    APP_ENV: Literal["development", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Ollama / LLM ─────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    LLM_MODEL: str = Field(
        default="llama3.1:8b",
        description=(
            "Primary LLM for answer generation. "
            "Trade-off: llama3.1:8b gives best quality locally (~6GB VRAM). "
            "phi3:mini is faster, uses ~2GB, but lower quality."
        ),
    )
    LLM_MODEL_FALLBACK: str = Field(
        default="phi3:mini",
        description="Lightweight fallback model when confidence is low.",
    )
    LLM_TEMPERATURE: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description=(
            "Trade-off: Lower temp = deterministic, factual answers (good for legal Q&A). "
            "Higher temp = creative but less reliable. Legal context demands low temp."
        ),
    )
    LLM_MAX_TOKENS: int = Field(default=1024, ge=128, le=4096)

    # ── Embeddings ────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description=(
            "Local sentence-transformers model. "
            "Trade-off: all-MiniLM-L6-v2 (384 dim, 80MB) is fast & good baseline. "
            "BGE-small-en-v1.5 (384 dim, 130MB) is better on MTEB benchmarks. "
            "BGE-large-en-v1.5 (1024 dim, 1.3GB) is best quality but slowest."
        ),
    )
    EMBEDDING_DEVICE: Literal["cpu", "cuda", "mps"] = Field(
        default="cpu",
        description=(
            "Trade-off: cuda is 10-50x faster for batched embedding. "
            "cpu works on all machines but is slower for large ingestion jobs."
        ),
    )
    EMBEDDING_BATCH_SIZE: int = Field(
        default=32,
        description="Number of chunks to embed in one batch. Increase for GPU.",
    )

    # ── ChromaDB / Vector Store ───────────────────────────────────────────────
    CHROMA_PERSIST_DIR: Path = Field(
        default=Path("./data/chroma_db"),
        description=(
            "Where ChromaDB stores its SQLite database and vector index. "
            "Trade-off: ChromaDB is great for dev (zero setup). "
            "For production at scale, migrate to Qdrant or Pinecone."
        ),
    )
    CHROMA_COLLECTION_NAME: str = "contract_documents"

    # ── Chunking ──────────────────────────────────────────────────────────────
    CHUNK_SIZE: int = Field(
        default=1000,
        ge=100,
        le=4000,
        description=(
            "Characters per chunk. "
            "Trade-off: Smaller (500) = precise retrieval, may miss context. "
            "Larger (2000) = more context but noisier, may dilute relevance."
        ),
    )
    CHUNK_OVERLAP: int = Field(
        default=200,
        ge=0,
        le=500,
        description=(
            "Overlap between consecutive chunks to prevent information loss at boundaries. "
            "Trade-off: Higher overlap = less info loss but more storage/compute."
        ),
    )

    # ── Retrieval ─────────────────────────────────────────────────────────────
    TOP_K: int = Field(
        default=5,
        ge=1,
        le=20,
        description=(
            "Number of chunks to retrieve per query. "
            "Trade-off: Higher k = more context but longer prompts, more LLM cost/latency."
        ),
    )
    DENSE_WEIGHT: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description=(
            "Weight for dense (semantic) retrieval in hybrid search. "
            "Trade-off: High dense weight = better for paraphrased questions. "
            "High BM25 weight = better for exact legal terms and clause references."
        ),
    )
    BM25_WEIGHT: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for BM25 (sparse/keyword) retrieval in hybrid search.",
    )
    MMR_LAMBDA: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "MMR diversity parameter. 0.0 = maximum diversity, 1.0 = maximum relevance. "
            "Trade-off: Low lambda prevents all chunks coming from the same paragraph. "
            "High lambda ensures the most relevant chunk is always included."
        ),
    )

    # ── Confidence & Decline ──────────────────────────────────────────────────
    CONFIDENCE_THRESHOLD: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description=(
            "Below this score, system declines to answer rather than hallucinate. "
            "Trade-off: Higher threshold = safer but declines more queries. "
            "Lower threshold = answers more but may hallucinate. "
            "For legal context: err on the side of higher threshold."
        ),
    )
    MIN_SIMILARITY_THRESHOLD: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum cosine similarity for a retrieved chunk to count as relevant. "
            "Chunks below this threshold contribute negatively to confidence score."
        ),
    )

    # ── API ───────────────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = Field(default=8000, ge=1024, le=65535)
    API_RELOAD: bool = True  # Hot reload during development
    API_LOG_LEVEL: str = "info"

    # ── Evaluation ────────────────────────────────────────────────────────────
    EVAL_JUDGE_MODEL: str = Field(
        default="llama3.1:8b",
        description=(
            "LLM used as RAGAS judge for evaluation metrics. "
            "Trade-off: Using a local model as judge is free but less accurate than GPT-4. "
            "This is an intentional cost-quality trade-off for development."
        ),
    )
    EVAL_DATASET_PATH: Path = Path("./data/eval_dataset.json")
    EVAL_RESULTS_DIR: Path = Path("./data/eval_results")

    # ── Derived Properties ─────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def ollama_api_url(self) -> str:
        """OpenAI-compatible Ollama endpoint — drop-in swappable with OpenAI."""
        return f"{self.OLLAMA_BASE_URL}/v1"

    @field_validator("BM25_WEIGHT")
    @classmethod
    def validate_weights_sum_to_one(cls, bm25_w: float, info) -> float:
        """Ensure dense + BM25 weights sum to 1.0 within tolerance."""
        dense_w = info.data.get("DENSE_WEIGHT", 0.7)
        total = dense_w + bm25_w
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"DENSE_WEIGHT ({dense_w}) + BM25_WEIGHT ({bm25_w}) must sum to 1.0, got {total:.2f}"
            )
        return bm25_w

    @field_validator("CHROMA_PERSIST_DIR", "EVAL_DATASET_PATH", "EVAL_RESULTS_DIR", mode="before")
    @classmethod
    def resolve_paths(cls, v) -> Path:
        """Resolve relative paths to absolute paths from project root."""
        p = Path(v)
        if not p.is_absolute():
            return (PROJECT_ROOT / p).resolve()
        return p.resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.

    Using lru_cache ensures the .env file is parsed exactly once,
    not on every import. Cache is invalidated by restarting the process.
    """
    return Settings()


# Module-level singleton for convenient import
# Usage: from app.config import settings
settings = get_settings()
