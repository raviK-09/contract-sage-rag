"""
Evaluator Orchestrator — Phase 7: RAGAS Evaluation Harness
===========================================================
Runs the full evaluation pipeline:
  dataset → API calls → metric computation → results → save to JSON/CSV
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import requests

from app.evaluation.eval_dataset import EVAL_DATASET
from app.evaluation.metrics import (
    EvalResult,
    MetricResult,
    compute_answer_relevance,
    compute_context_precision,
    compute_context_recall,
    compute_decline_correctness,
    compute_faithfulness_keyword,
    compute_keyword_hit_rate,
    compute_source_accuracy,
)

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"


@dataclass
class EvalSummary:
    """Aggregate statistics across all evaluated questions."""
    total_questions: int
    answered: int
    declined: int
    errors: int
    correct_declines: int

    # Average metric scores (only over answerable questions)
    avg_context_precision: float
    avg_context_recall: float
    avg_faithfulness: float
    avg_answer_relevance: float
    avg_keyword_hit_rate: float
    avg_source_accuracy: float
    avg_overall_score: float
    avg_confidence: float
    avg_latency_ms: float

    # Pass rates
    answer_rate: float          # answered / (total - should_decline)
    decline_accuracy: float     # correct_declines / total_should_decline
    source_accuracy_rate: float # correct source / answered

    results: list[dict] = field(default_factory=list)

    def print_report(self):
        sep = "=" * 65
        print(f"\n{sep}")
        print("  ContractSage — Evaluation Report")
        print(sep)
        print(f"  Questions   : {self.total_questions} total | {self.answered} answered | {self.declined} declined | {self.errors} errors")
        print()
        print("  Retrieval Metrics:")
        print(f"    Context Precision  : {self.avg_context_precision:.1%}  (relevance of retrieved chunks)")
        print(f"    Context Recall     : {self.avg_context_recall:.1%}  (coverage of needed info)")
        print()
        print("  Generation Metrics:")
        print(f"    Faithfulness       : {self.avg_faithfulness:.1%}  (grounded in context?)")
        print(f"    Answer Relevance   : {self.avg_answer_relevance:.1%}  (addresses the question?)")
        print(f"    Keyword Hit Rate   : {self.avg_keyword_hit_rate:.1%}  (expected terms present?)")
        print()
        print("  System Metrics:")
        print(f"    Source Accuracy    : {self.source_accuracy_rate:.1%}  (cited correct document?)")
        print(f"    Answer Rate        : {self.answer_rate:.1%}  (answered in-scope questions)")
        print(f"    Decline Accuracy   : {self.decline_accuracy:.1%}  (correctly refused out-of-scope)")
        print(f"    Avg Confidence     : {self.avg_confidence:.1%}")
        print(f"    Avg Latency        : {self.avg_latency_ms:.0f}ms per query")
        print()
        print(f"  Overall Score        : {self.avg_overall_score:.1%}")
        print(sep)


def run_evaluation(
    api_base: str = API_BASE,
    dataset: list[dict] | None = None,
    top_k: int = 5,
    output_dir: str | Path = "data/eval_results",
    verbose: bool = True,
) -> EvalSummary:
    """
    Run the full evaluation pipeline against the FastAPI backend.

    For each question in the dataset:
    1. POST /query to the API
    2. Extract retrieved chunks metadata from the response
    3. Compute all 7 metrics
    4. Aggregate into a summary report

    Args:
        api_base  : FastAPI server URL.
        dataset   : Override default EVAL_DATASET (for custom questions).
        top_k     : Chunks to retrieve per question.
        output_dir: Directory to save JSON + CSV results.
        verbose   : Print per-question progress.

    Returns:
        EvalSummary with all scores and per-question results.
    """
    data = dataset or EVAL_DATASET
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Running evaluation: {len(data)} questions against {api_base}")
        print("-" * 65)

    results: list[EvalResult] = []

    for i, item in enumerate(data, 1):
        question     = item["question"]
        ground_truth = item["ground_truth"]
        expected_doc = item.get("expected_doc")
        expected_kw  = item.get("expected_keywords", [])
        category     = item.get("category", "General")
        should_dec   = item.get("should_decline", False)

        if verbose:
            print(f"[{i:2d}/{len(data)}] {category:20s} | {question[:55]}...")

        # ── Call the API ───────────────────────────────────────────────────────
        t_start  = time.perf_counter()
        api_resp = _call_query_api(api_base, question, top_k)
        latency  = (time.perf_counter() - t_start) * 1000

        if "error" in api_resp:
            results.append(EvalResult(
                question=question, ground_truth=ground_truth,
                generated_answer="", expected_doc=expected_doc,
                category=category, should_decline=should_dec,
                error=api_resp["error"], latency_ms=latency,
            ))
            if verbose:
                print(f"         ERROR: {api_resp['error']}")
            continue

        # ── Extract response fields ───────────────────────────────────────────
        generated_answer  = api_resp.get("answer", "")
        is_declined       = api_resp.get("is_declined", False)
        sources_cited     = api_resp.get("sources_cited", [])
        confidence        = api_resp.get("confidence", {})
        confidence_score  = confidence.get("score", 0.0)

        # The API returns citation objects — build chunk-like dicts for metrics
        citations    = api_resp.get("citations", [])
        chunk_dicts  = _citations_to_chunk_dicts(citations)

        # ── Compute metrics ───────────────────────────────────────────────────
        result = EvalResult(
            question=question,
            ground_truth=ground_truth,
            generated_answer=generated_answer,
            expected_doc=expected_doc,
            category=category,
            should_decline=should_dec,
            is_declined=is_declined,
            confidence_score=confidence_score,
            latency_ms=latency,
        )

        result.decline_correct = compute_decline_correctness(is_declined, should_dec)

        if not is_declined and not should_dec:
            # Only run content metrics on non-declined, in-scope questions
            result.context_precision = compute_context_precision(chunk_dicts, expected_doc)
            result.context_recall    = compute_context_recall(chunk_dicts, expected_kw)
            result.faithfulness      = compute_faithfulness_keyword(generated_answer, chunk_dicts)
            result.answer_relevance  = compute_answer_relevance(question, generated_answer, expected_kw)
            result.keyword_hit_rate  = compute_keyword_hit_rate(generated_answer, expected_kw)
            result.source_accuracy   = compute_source_accuracy(sources_cited, expected_doc)
        elif is_declined and not should_dec:
            # False decline — penalise all content metrics
            for attr in ("context_precision", "context_recall", "faithfulness",
                         "answer_relevance", "keyword_hit_rate", "source_accuracy"):
                setattr(result, attr, MetricResult(
                    name=attr.replace("_", " ").title(),
                    score=0.0,
                    explanation="Penalised — system declined when it should have answered.",
                    passed=False,
                ))

        results.append(result)

        if verbose:
            status = "DECLINED" if is_declined else f"conf={confidence_score:.0%}"
            overall = f"score={result.overall_score:.0%}" if result.all_metrics else ""
            print(f"         {status:12s} | {overall} | {latency:.0f}ms")

    # ── Aggregate summary ─────────────────────────────────────────────────────
    summary = _aggregate(results)

    # ── Save results ──────────────────────────────────────────────────────────
    _save_results(results, summary, output_path)

    if verbose:
        summary.print_report()

    return summary


def _call_query_api(api_base: str, question: str, top_k: int) -> dict:
    """POST /query and return the JSON response or an error dict."""
    try:
        r = requests.post(
            f"{api_base}/query",
            json={"question": question, "top_k": top_k},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API. Is `uvicorn app.api.main:app` running?"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out after 120s. LLM too slow."}
    except Exception as exc:
        return {"error": str(exc)}


def _citations_to_chunk_dicts(citations: list[dict]) -> list[dict]:
    """Convert API citation objects to the chunk dict format metrics expect."""
    return [
        {
            "file_name":    c.get("file_name", ""),
            "page_content": c.get("relevant_snippet", ""),
            "dense_score":  c.get("relevance_score", 0.0),
            "page":         c.get("page", 0),
        }
        for c in citations
    ]


def _aggregate(results: list[EvalResult]) -> EvalSummary:
    """Compute aggregate statistics from all EvalResult objects."""
    answered   = [r for r in results if not r.is_declined and not r.error]
    declined   = [r for r in results if r.is_declined]
    errors     = [r for r in results if r.error]
    should_dec = [r for r in results if r.should_decline]
    correct_dec = [r for r in results if r.decline_correct and r.decline_correct.passed]

    def _avg(items, attr):
        vals = [getattr(r, attr).score for r in items if getattr(r, attr) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    in_scope    = [r for r in results if not r.should_decline]
    answer_rate = len(answered) / len(in_scope) if in_scope else 0.0
    dec_acc     = len(correct_dec) / len(should_dec) if should_dec else 1.0
    src_acc     = _avg(answered, "source_accuracy")

    return EvalSummary(
        total_questions=len(results),
        answered=len(answered),
        declined=len(declined),
        errors=len(errors),
        correct_declines=len(correct_dec),
        avg_context_precision=_avg(answered, "context_precision"),
        avg_context_recall=_avg(answered, "context_recall"),
        avg_faithfulness=_avg(answered, "faithfulness"),
        avg_answer_relevance=_avg(answered, "answer_relevance"),
        avg_keyword_hit_rate=_avg(answered, "keyword_hit_rate"),
        avg_source_accuracy=src_acc,
        avg_overall_score=sum(r.overall_score for r in results) / len(results) if results else 0.0,
        avg_confidence=sum(r.confidence_score for r in answered) / len(answered) if answered else 0.0,
        avg_latency_ms=sum(r.latency_ms for r in results) / len(results) if results else 0.0,
        answer_rate=answer_rate,
        decline_accuracy=dec_acc,
        source_accuracy_rate=src_acc,
        results=[_result_to_dict(r) for r in results],
    )


def _result_to_dict(r: EvalResult) -> dict:
    return {
        "question": r.question,
        "category": r.category,
        "should_decline": r.should_decline,
        "is_declined": r.is_declined,
        "confidence_score": r.confidence_score,
        "latency_ms": round(r.latency_ms, 1),
        "overall_score": round(r.overall_score, 4),
        "error": r.error,
        "metrics": {m.name: {"score": m.score, "passed": m.passed, "explanation": m.explanation}
                    for m in r.all_metrics},
        "answer_preview": r.generated_answer[:300] if r.generated_answer else "",
    }


def _save_results(results: list[EvalResult], summary: EvalSummary, output_dir: Path):
    """Save evaluation results as JSON and a simple CSV."""
    ts = time.strftime("%Y%m%d_%H%M%S")

    # JSON — full results
    json_path = output_dir / f"eval_{ts}.json"
    payload = {
        "timestamp": ts,
        "summary": {
            k: v for k, v in vars(summary).items() if k != "results"
        },
        "results": summary.results,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # CSV — quick overview
    csv_path = output_dir / f"eval_{ts}.csv"
    headers  = ["question", "category", "should_decline", "is_declined",
                 "overall_score", "confidence", "latency_ms", "passed"]
    rows = []
    for r in results:
        rows.append([
            r.question[:60],
            r.category,
            r.should_decline,
            r.is_declined,
            round(r.overall_score, 3),
            round(r.confidence_score, 3),
            round(r.latency_ms, 0),
            all(m.passed for m in r.all_metrics),
        ])

    csv_lines = [",".join(str(h) for h in headers)]
    for row in rows:
        csv_lines.append(",".join(f'"{v}"' for v in row))
    csv_path.write_text("\n".join(csv_lines), encoding="utf-8")

    print(f"\n  Results saved:")
    print(f"    JSON: {json_path}")
    print(f"    CSV : {csv_path}")
