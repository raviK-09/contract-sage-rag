"""
Ingests all sample PDFs into ChromaDB. Run once before starting the API.
Usage: python scripts/seed_data.py
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, ".")
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

from app.ingestion.embedder import reset_embedder
from app.retrieval.vector_store import VectorStore
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.pipeline import ingest_source

reset_embedder()

PDF_DIR = Path("data/sample_pdfs")
pdfs = sorted(PDF_DIR.glob("*.pdf"))

if not pdfs:
    print(f"No PDFs found in {PDF_DIR}. Run the generate scripts first.")
    sys.exit(1)

print(f"ContractSage - Seed Data Script")
print(f"=" * 50)
print(f"Found {len(pdfs)} PDF(s) to ingest\n")

store  = VectorStore()
sparse = SparseRetriever()

# Wipe existing data for a clean seed
store.delete_collection()
print("Cleared existing vector store.\n")

total_chunks = 0
for i, pdf_path in enumerate(pdfs, 1):
    print(f"[{i}/{len(pdfs)}] Ingesting: {pdf_path.name}")
    result = ingest_source(
        source=pdf_path,
        vector_store=store,
        sparse_retriever=sparse,
        rebuild_bm25=(i == len(pdfs)),  # Only rebuild BM25 once at the end
    )
    total_chunks += result.chunks_created
    print(f"         Pages: {result.pages_loaded} | Chunks: {result.chunks_created} | Time: {result.processing_time_ms:.0f}ms")

print(f"\nDone! {total_chunks} total chunks across {len(pdfs)} documents.")
print(f"Vector store ready at: {store._persist_dir}")
print(f"\nNext steps:")
print(f"  Start API : .venv\\Scripts\\uvicorn.exe app.api.main:app --reload --port 8000")
print(f"  Open docs : http://localhost:8000/docs")
