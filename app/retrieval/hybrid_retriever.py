"""
Hybrid retriever combining dense (ChromaDB) and sparse (BM25) search
using Reciprocal Rank Fusion (RRF) followed by MMR re-ranking.
"""


import logging
from dataclasses import dataclass
from typing import Optional

from langchain_core.documents import Document

from app.config import settings
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)

# RRF constant k — value of 60 is from the original 2009 paper
# Higher k → smooths rank differences, lower k → top ranks matter more
RRF_K = 60


@dataclass
class RetrievedChunk:
    """A retrieved chunk with all scoring information for transparency."""
    document: Document
    dense_score: float      # Cosine similarity from vector store (0-1)
    bm25_score: float       # Normalised BM25 score (0-1), 0 if not in BM25 results
    rrf_score: float        # Combined RRF score (higher = better)
    dense_rank: int         # Rank in dense results (0 = not found)
    bm25_rank: int          # Rank in BM25 results (0 = not found)
    final_rank: int         # Final rank after RRF fusion and MMR

    @property
    def source(self) -> str:
        return self.document.metadata.get("file_name", "unknown")

    @property
    def page(self) -> int:
        return self.document.metadata.get("page", 0)

    @property
    def chunk_id(self) -> str:
        return self.document.metadata.get("chunk_id", "")


class HybridRetriever:
    """
    Combines dense vector search and BM25 keyword search using RRF.
    Applies MMR re-ranking for diversity in the final result set.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        sparse_retriever: SparseRetriever,
    ) -> None:
        self._vector_store = vector_store
        self._sparse_retriever = sparse_retriever

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        dense_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None,
        use_mmr: bool = True,
    ) -> list[RetrievedChunk]:
        """
        Run hybrid retrieval: Dense + BM25 → RRF fusion → MMR re-ranking.

        Args:
            query        : The user's question.
            top_k        : Number of final results to return.
            dense_weight : Weight for dense scores in RRF (default from settings).
            bm25_weight  : Weight for BM25 scores in RRF (default from settings).
            use_mmr      : Whether to apply MMR diversity re-ranking.

        Returns:
            List of RetrievedChunk objects sorted by final_rank ascending.
        """
        k = top_k or settings.TOP_K
        dw = dense_weight if dense_weight is not None else settings.DENSE_WEIGHT
        bw = bm25_weight  if bm25_weight  is not None else settings.BM25_WEIGHT

        # Retrieve more candidates than needed — we'll prune after fusion
        # Trade-off: fetch_k must be > top_k to give RRF enough candidates to fuse
        fetch_k = max(k * 3, 15)

        # ── Step 1: Dense retrieval ───────────────────────────────────────────
        dense_results = self._vector_store.similarity_search(query, top_k=fetch_k)
        # dense_results: list[(Document, similarity_score)]

        # ── Step 2: BM25 retrieval ────────────────────────────────────────────
        bm25_results = []
        if self._sparse_retriever.is_ready:
            bm25_results = self._sparse_retriever.search(query, top_k=fetch_k)
        else:
            logger.warning("BM25 index not ready — using dense-only retrieval.")

        # ── Step 3: RRF fusion ────────────────────────────────────────────────
        fused = _reciprocal_rank_fusion(
            dense_results=dense_results,
            bm25_results=bm25_results,
            dense_weight=dw,
            bm25_weight=bw,
            top_k=fetch_k,
        )

        # ── Step 4: MMR re-ranking for diversity ──────────────────────────────
        if use_mmr and len(fused) > k:
            fused = _mmr_rerank(
                candidates=fused,
                top_k=k,
                lambda_mult=settings.MMR_LAMBDA,
            )
        else:
            fused = fused[:k]

        # ── Step 5: Assign final ranks ────────────────────────────────────────
        for rank, chunk in enumerate(fused, start=1):
            chunk.final_rank = rank

        logger.info(
            f"Hybrid retrieval: {len(dense_results)} dense + "
            f"{len(bm25_results)} BM25 → {len(fused)} final chunks"
        )
        return fused


# ── Reciprocal Rank Fusion ────────────────────────────────────────────────────

def _reciprocal_rank_fusion(
    dense_results: list[tuple[Document, float]],
    bm25_results: list,           # list[BM25Result]
    dense_weight: float,
    bm25_weight: float,
    top_k: int,
) -> list[RetrievedChunk]:
    """
    Combine dense and BM25 rankings using Reciprocal Rank Fusion.

    RRF formula:
        score(d) = Σ_i  w_i / (k + rank_i(d))

    Where:
        - rank_i(d) is the rank of document d in retrieval system i
        - k = 60 (empirically optimal, from Cormack et al. 2009)
        - w_i is the weight for retrieval system i

    Documents that appear in BOTH systems get boosted scores.
    Documents in only one system get partial scores.

    Why RRF works:
        - Rank-based (not score-based) → robust to different score scales
        - No training data needed
        - Simple to implement and explain
        - Consistently beats score normalisation approaches in benchmarks
    """
    # Build lookup: chunk_id → (Document, dense_score, dense_rank)
    dense_lookup: dict[str, tuple[Document, float, int]] = {}
    for rank, (doc, score) in enumerate(dense_results, start=1):
        chunk_id = doc.metadata.get("chunk_id", f"dense_{rank}")
        dense_lookup[chunk_id] = (doc, score, rank)

    # Build lookup: chunk_id → (Document, bm25_score, bm25_rank)
    bm25_lookup: dict[str, tuple[Document, float, int]] = {}
    for result in bm25_results:
        chunk_id = result.document.metadata.get("chunk_id", f"bm25_{result.rank}")
        bm25_lookup[chunk_id] = (result.document, result.normalised_score, result.rank)

    # Collect all unique chunk IDs from both systems
    all_ids = set(dense_lookup.keys()) | set(bm25_lookup.keys())

    chunks: list[RetrievedChunk] = []
    for chunk_id in all_ids:
        dense_entry = dense_lookup.get(chunk_id)
        bm25_entry  = bm25_lookup.get(chunk_id)

        # RRF contribution from dense retriever
        dense_rrf = (dense_weight / (RRF_K + dense_entry[2])) if dense_entry else 0.0
        # RRF contribution from BM25 retriever
        bm25_rrf  = (bm25_weight  / (RRF_K + bm25_entry[2]))  if bm25_entry  else 0.0

        rrf_score = dense_rrf + bm25_rrf

        # Use the document from whichever system found it (prefer dense for metadata)
        doc = dense_entry[0] if dense_entry else bm25_entry[0]

        chunks.append(
            RetrievedChunk(
                document=doc,
                dense_score=dense_entry[1] if dense_entry else 0.0,
                bm25_score=bm25_entry[1]   if bm25_entry  else 0.0,
                rrf_score=rrf_score,
                dense_rank=dense_entry[2]  if dense_entry else 0,
                bm25_rank=bm25_entry[2]    if bm25_entry  else 0,
                final_rank=0,  # Set after MMR
            )
        )

    # Sort by RRF score descending
    chunks.sort(key=lambda c: c.rrf_score, reverse=True)
    return chunks[:top_k]


# ── MMR Re-ranking ────────────────────────────────────────────────────────────

def _mmr_rerank(
    candidates: list[RetrievedChunk],
    top_k: int,
    lambda_mult: float,
) -> list[RetrievedChunk]:
    """
    Maximal Marginal Relevance (MMR) re-ranking for diversity.

    Problem MMR solves:
        Without MMR, the top-5 chunks from a 8-page contract might all come
        from page 3 (where the relevant clause is). This wastes context window
        and misses supporting clauses from other pages.

    MMR formula:
        MMR(d) = λ * relevance(d, query) - (1-λ) * max_similarity(d, selected)

    Where:
        - λ (lambda_mult): 0 = max diversity, 1 = max relevance
        - relevance: RRF score (how relevant is this chunk to the query)
        - max_similarity: how similar is this chunk to already-selected chunks

    We approximate similarity between chunks using RRF score proximity
    and chunk source (same page = similar). A full implementation would
    use embedding cosine similarity between chunks, but that requires
    storing/computing pairwise embeddings — expensive for our use case.

    Trade-off: Our simplified MMR uses source+page as a diversity proxy.
    Full embedding-based MMR is better but 5-10x slower.
    """
    if not candidates:
        return []

    selected: list[RetrievedChunk] = []
    remaining = list(candidates)

    # Always include the highest-scoring chunk first
    selected.append(remaining.pop(0))

    while len(selected) < top_k and remaining:
        best_chunk = None
        best_score = float("-inf")

        for candidate in remaining:
            # Relevance score (from RRF)
            relevance = candidate.rrf_score

            # Diversity penalty: count how many selected chunks share
            # the same source document and page
            overlap_count = sum(
                1 for s in selected
                if s.source == candidate.source and s.page == candidate.page
            )
            # Penalty increases with overlap — encourages cross-page diversity
            diversity_penalty = overlap_count * (1 - lambda_mult) * 0.1

            mmr_score = lambda_mult * relevance - diversity_penalty

            if mmr_score > best_score:
                best_score = mmr_score
                best_chunk = candidate

        if best_chunk:
            selected.append(best_chunk)
            remaining.remove(best_chunk)

    return selected
