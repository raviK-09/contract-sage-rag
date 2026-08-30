"""
Phase 4 end-to-end test: Ingest a contract → ask questions → get cited answers.
Run this AFTER Ollama is running and llama3.1:8b is pulled.
"""
import sys
import logging
sys.path.insert(0, ".")
logging.basicConfig(level=logging.WARNING)

from app.generation.llm_client import check_ollama_connection
from app.generation.generator import answer_question
from app.ingestion.embedder import reset_embedder
from app.retrieval.vector_store import VectorStore
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.pipeline import ingest_source

reset_embedder()

print("=== Phase 4: Generation Pipeline Test ===\n")

# ── Step 0: Check Ollama ──────────────────────────────────────────────────────
print("0. Checking Ollama connection...")
status = check_ollama_connection()
print(f"   Ollama running       : {status['ollama_running']}")
print(f"   Primary model ready  : {status['primary_model_available']}")
print(f"   Available models     : {status['available_models']}")

if not status["ollama_running"]:
    print("\n   [ERROR] Ollama is not running!")
    print("   Please start it: run 'ollama serve' in a separate terminal")
    print("   Then pull the model: ollama pull llama3.1:8b")
    sys.exit(1)

if not status["primary_model_available"]:
    print("\n   [WARN] llama3.1:8b not found. Trying with whatever model is available...")
    if status["available_models"]:
        available_model = status["available_models"][0]
        print(f"   Using: {available_model}")
        import os
        os.environ["LLM_MODEL"] = available_model
    else:
        print("   No models available. Run: ollama pull llama3.1:8b")
        sys.exit(1)

print("\n1. Setting up retrieval pipeline...")
store   = VectorStore(collection_name="test_phase4")
sparse  = SparseRetriever()
hybrid  = HybridRetriever(vector_store=store, sparse_retriever=sparse)
store.delete_collection()

# Ingest the residential rental agreement
result = ingest_source(
    source="data/sample_pdfs/residential_rental_agreement.pdf",
    vector_store=store,
    sparse_retriever=sparse,
)
print(f"   Ingested: {result.chunks_created} chunks in {result.processing_time_ms:.0f}ms")

# ---- Test questions ----------------------------------------------------------
questions = [
    "What is the monthly rent and when is it due?",
    "What is the notice period for terminating the lease?",
    "What happens to the security deposit if I break the lease early?",
    "Can the landlord enter the property without notice?",
    "What is the weather like in Bangalore?",    # Should trigger decline
]

print(f"\n2. Asking {len(questions)} questions...\n")
print("=" * 70)

for i, q in enumerate(questions, 1):
    print(f"\nQ{i}: {q}")
    print("-" * 60)

    response = answer_question(question=q, retriever=hybrid)

    if response.is_declined:
        status_icon = "DECLINED"
    else:
        status_icon = f"ANSWERED ({response.confidence.label} confidence)"

    print(f"Status    : {status_icon} ({response.confidence.score:.0%})")
    print(f"Timing    : retrieval={response.retrieval_ms:.0f}ms | generation={response.generation_ms:.0f}ms | total={response.latency_ms:.0f}ms")

    if not response.is_declined:
        print(f"Scores    : retrieval={response.confidence.retrieval_score:.2f} | coverage={response.confidence.coverage_score:.2f} | citation={response.confidence.citation_score:.2f}")
        print(f"Citations : {response.cited_answer.cited_source_nums}")

    print(f"\nAnswer:\n{response.answer[:500]}")
    if response.formatted_citations:
        print(response.formatted_citations[:400])
    print("=" * 70)

print("\nPhase 4 test complete!")
