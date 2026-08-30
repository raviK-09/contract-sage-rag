"""
BM25 keyword retrieval using rank-bm25 (BM25Okapi variant).
Complements dense vector search for exact term matching — clause numbers,
defined legal terms, and precise references that embeddings often miss.
"""


import logging
import string
from dataclasses import dataclass, field
from typing import Optional

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


@dataclass
class BM25Result:
    """A single BM25 search result with its rank and normalised score."""
    document: Document
    bm25_score: float        # Raw BM25 score (not bounded)
    normalised_score: float  # Normalised to [0, 1] for RRF fusion
    rank: int                # 1-based rank in BM25 result list


class SparseRetriever:
    """
    BM25-based keyword retriever.

    Maintains an in-memory BM25 index over all stored documents.
    The index is rebuilt whenever documents are added (or on first use).

    Trade-off: In-memory index vs persistent index
      In-memory → simple, fast to query, must rebuild on restart
      Persistent → needs serialisation (pickle), adds complexity
      For our scale (hundreds of chunks) in-memory is perfectly fine.
      At millions of docs, you'd use Elasticsearch as the BM25 backend.
    """

    def __init__(self) -> None:
        self._documents: list[Document] = []
        self._tokenised_corpus: list[list[str]] = []
        self._bm25_index: Optional[BM25Okapi] = None
        self._is_built = False

    # ── Index management ──────────────────────────────────────────────────────

    def build_index(self, documents: list[Document]) -> None:
        """
        Build the BM25 index from a list of Documents.

        Called after ingestion to sync BM25 with the vector store.

        Args:
            documents: All documents currently in the vector store.
        """
        if not documents:
            logger.warning("build_index called with empty document list.")
            return

        self._documents = documents
        self._tokenised_corpus = [_tokenise(doc.page_content) for doc in documents]
        self._bm25_index = BM25Okapi(
            self._tokenised_corpus,
            # BM25 hyperparameters (defaults are well-studied across many corpora)
            # k1 (1.5): term frequency saturation. Higher → rewards repeated terms more
            # b  (0.75): length normalisation. 1.0 = full normalisation, 0 = no normalisation
            # These defaults work well for most legal document retrieval tasks
            k1=1.5,
            b=0.75,
        )
        self._is_built = True
        logger.info(f"BM25 index built with {len(documents)} documents.")

    def add_documents(self, new_documents: list[Document]) -> None:
        """
        Add documents to the existing BM25 index (incremental update).

        Trade-off: BM25Okapi doesn't support incremental updates —
        we must rebuild the entire index. This is O(n) in total corpus size.
        For our scale this is fine. For large-scale production, use
        Elasticsearch which supports incremental indexing.
        """
        all_docs = self._documents + new_documents
        self.build_index(all_docs)

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[BM25Result]:
        """
        Search the BM25 index for the most relevant documents.

        Args:
            query: The user's question.
            top_k: Number of top results to return.

        Returns:
            List of BM25Result objects sorted by score descending.
        """
        if not self._is_built or self._bm25_index is None:
            logger.warning("BM25 index not built yet. Call build_index() first.")
            return []

        tokenised_query = _tokenise(query)
        if not tokenised_query:
            logger.warning("Query tokenised to empty list — no BM25 results.")
            return []

        # Get scores for all documents in the corpus
        scores: list[float] = self._bm25_index.get_scores(tokenised_query).tolist()

        # Pair each score with its document index and sort
        indexed_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        top_results = indexed_scores[:top_k]

        # Normalise scores to [0, 1] for fusion with dense scores
        max_score = top_results[0][1] if top_results else 1.0
        normalised = _normalise_scores([s for _, s in top_results], max_score)

        results: list[BM25Result] = []
        for rank, ((doc_idx, raw_score), norm_score) in enumerate(
            zip(top_results, normalised), start=1
        ):
            results.append(
                BM25Result(
                    document=self._documents[doc_idx],
                    bm25_score=raw_score,
                    normalised_score=norm_score,
                    rank=rank,
                )
            )

        logger.debug(f"BM25 returned {len(results)} results for query: '{query[:50]}...'")
        return results

    @property
    def is_ready(self) -> bool:
        """True if the index has been built and is ready to query."""
        return self._is_built and self._bm25_index is not None

    @property
    def document_count(self) -> int:
        """Number of documents in the BM25 index."""
        return len(self._documents)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> list[str]:
    """
    Simple whitespace + punctuation tokeniser for BM25.

    Steps:
    1. Lowercase (case-insensitive matching)
    2. Remove punctuation
    3. Split on whitespace
    4. Filter out very short tokens (< 2 chars)

    Trade-off: We deliberately keep this simple.
    - No stemming: "termination" ≠ "terminate" (fine for legal terms)
    - No stop words: "the lease" still matches "the" (BM25 handles low-IDF naturally)
    - No lemmatisation: adds NLTK dependency for marginal gain
    """
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    return [t for t in tokens if len(t) > 1]   # Filter single-char noise


def _normalise_scores(scores: list[float], max_score: float) -> list[float]:
    """
    Normalise BM25 scores to [0, 1] range using min-max normalisation.

    Required for Reciprocal Rank Fusion — raw BM25 scores are unbounded
    and not directly comparable to cosine similarity scores (which are in [0, 1]).

    If max_score is 0 (no relevant documents), return zeros.
    """
    if max_score <= 0:
        return [0.0] * len(scores)
    return [s / max_score for s in scores]
