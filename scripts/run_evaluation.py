"""
Runs the evaluation harness against the FastAPI backend and saves results
to data/eval_results/ as JSON and CSV.

Requires the API to be running: uvicorn app.api.main:app --port 8000
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")

import requests
from app.evaluation.evaluator import run_evaluation

# ── Pre-flight check ──────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"

print("ContractSage — Evaluation Harness")
print("=" * 65)
print(f"API: {API_BASE}")

try:
    health = requests.get(f"{API_BASE}/health", timeout=5).json()
    chunks = health.get("vector_store_chunks", 0)
    model  = health.get("primary_model_available", False)
    ollama = health.get("ollama_running", False)
    print(f"API status   : {health.get('status', 'unknown')}")
    print(f"Ollama       : {'running' if ollama else 'OFFLINE - start Ollama first!'}")
    print(f"Model ready  : {'yes' if model else 'NO - run: ollama pull llama3.1:8b'}")
    print(f"Vector store : {chunks} chunks")

    if not ollama or not model:
        print("\nCannot run evaluation - Ollama or model not ready.")
        sys.exit(1)
    if chunks == 0:
        print("\nNo documents in vector store. Run first:")
        print("  .venv\\Scripts\\python.exe scripts/seed_data.py")
        sys.exit(1)

except Exception as e:
    print(f"\nCannot reach API: {e}")
    print("Start the backend first:")
    print("  .venv\\Scripts\\uvicorn.exe app.api.main:app --port 8000")
    sys.exit(1)

print()

# ── Run evaluation ────────────────────────────────────────────────────────────
summary = run_evaluation(
    api_base=API_BASE,
    top_k=5,
    output_dir=PROJECT_ROOT / "data" / "eval_results",
    verbose=True,
)
