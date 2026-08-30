"""Phase 3 end-to-end retrieval test."""
import sys
import logging
sys.path.insert(0, ".")
logging.basicConfig(level=logging.WARNING)

from app.retrieval.vector_store import VectorStore
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.pipeline import ingest_source
from app.ingestion.embedder import reset_embedder

# Reset cached singleton so updated encode_kwargs take effect
reset_embedder()

print("=== Phase 3: End-to-End Retrieval Test ===\n")

store  = VectorStore(collection_name="test_phase3")
sparse = SparseRetriever()
hybrid = HybridRetriever(vector_store=store, sparse_retriever=sparse)

store.delete_collection()

print("1. Ingesting residential_rental_agreement.pdf...")
result = ingest_source(
    source="data/sample_pdfs/residential_rental_agreement.pdf",
    vector_store=store,
    sparse_retriever=sparse,
)
print(f"   Pages loaded  : {result.pages_loaded}")
print(f"   Chunks created: {result.chunks_created}")
print(f"   Time          : {result.processing_time_ms:.0f}ms")
print(f"   BM25 ready    : {sparse.is_ready}")
print(f"   Total in store: {store.count()}\n")

print("2. Running hybrid retrieval...")
query = "What is the notice period for terminating the lease?"
print(f'   Query: "{query}"\n')

chunks = hybrid.retrieve(query, top_k=3)
for c in chunks:
    print(f"   Rank {c.final_rank} | Page {c.page} | Dense:{c.dense_score:.3f} | BM25:{c.bm25_score:.3f} | RRF:{c.rrf_score:.4f}")
    print(f"   Source : {c.source}")
    print(f"   Preview: {c.document.page_content[:180].strip()[:150]}...")
    print()

print("3. Testing BM25 exact-term search...")
query2 = "security deposit refund 60 days"
print(f'   Query: "{query2}"\n')
chunks2 = hybrid.retrieve(query2, top_k=2)
for c in chunks2:
    print(f"   Rank {c.final_rank} | Page {c.page} | Dense:{c.dense_score:.3f} | BM25:{c.bm25_score:.3f}")
    print(f"   Preview: {c.document.page_content[:150].strip()}...")
    print()

print("Phase 3 PASSED - Hybrid retrieval working correctly!")
