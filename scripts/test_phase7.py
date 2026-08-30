"""Phase 7 import check — no API needed, just verifies code is wired up."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("Checking Phase 7 imports...")

from app.evaluation.eval_dataset import EVAL_DATASET
print(f"  eval_dataset.py   OK  ({len(EVAL_DATASET)} questions)")

from app.evaluation.metrics import (
    compute_context_precision,
    compute_context_recall,
    compute_faithfulness_keyword,
    compute_answer_relevance,
    compute_keyword_hit_rate,
    compute_source_accuracy,
    compute_decline_correctness,
    EvalResult,
    MetricResult,
)
print("  metrics.py        OK  (7 metric functions)")

from app.evaluation.evaluator import run_evaluation, EvalSummary
print("  evaluator.py      OK")

# Quick unit test of metrics — no API needed
print("\nRunning quick metric unit tests...")

# Context precision
chunks = [{"file_name": "residential_rental_agreement.pdf", "dense_score": 0.6}]
r = compute_context_precision(chunks, "residential_rental_agreement.pdf")
assert r.score == 1.0, f"Expected 1.0 got {r.score}"
print(f"  context_precision : {r.score:.0%} PASS")

# Context recall
r2 = compute_context_recall(
    [{"page_content": "The monthly rent is Rs 28,000 due on the 5th"}],
    expected_keywords=["28,000", "5th"],
)
assert r2.score == 1.0, f"Expected 1.0 got {r2.score}"
print(f"  context_recall    : {r2.score:.0%} PASS")

# Faithfulness
r3 = compute_faithfulness_keyword(
    generated_answer="The rent is Rs 28,000 payable by bank transfer.",
    retrieved_chunks=[{"page_content": "rent is Rs 28,000 payable by bank transfer monthly"}],
)
print(f"  faithfulness      : {r3.score:.0%} (score)")

# Keyword hit rate
r4 = compute_keyword_hit_rate("The rent is Rs 28,000", ["28,000"])
assert r4.score == 1.0
print(f"  keyword_hit_rate  : {r4.score:.0%} PASS")

# Decline correctness
r5 = compute_decline_correctness(is_declined=True, should_decline=True)
assert r5.passed
print(f"  decline_correct   : {r5.score:.0%} PASS")

r6 = compute_decline_correctness(is_declined=False, should_decline=True)
assert not r6.passed
print(f"  decline_incorrect : {r6.score:.0%} PASS (correctly penalised)")

print("\nAll Phase 7 imports and unit tests passed!")
print("\nTo run the full evaluation (needs API + Ollama):")
print("  .venv\\Scripts\\python.exe scripts/run_evaluation.py")
