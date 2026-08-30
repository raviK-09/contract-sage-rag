"""Runs curated evaluation questions and displays retrieval + generation quality metrics."""


import time
import streamlit as st
from app.ui.api_client import get_documents, post_query
from app.ui.components.sidebar import render_sidebar


# Curated evaluation questions with expected source document
EVAL_QUESTIONS = [
    {
        "question": "What is the monthly rent amount and the grace period for payment?",
        "expected_doc": "residential_rental_agreement.pdf",
        "category": "Rent & Payment",
    },
    {
        "question": "What is the notice period required to terminate the lease?",
        "expected_doc": "residential_rental_agreement.pdf",
        "category": "Termination",
    },
    {
        "question": "What happens to the security deposit if the tenant breaks the lock-in period?",
        "expected_doc": "residential_rental_agreement.pdf",
        "category": "Termination",
    },
    {
        "question": "What is the employee's annual CTC and basic salary?",
        "expected_doc": "employment_agreement.pdf",
        "category": "Compensation",
    },
    {
        "question": "What is the non-compete restriction period after leaving the company?",
        "expected_doc": "employment_agreement.pdf",
        "category": "Restrictions",
    },
    {
        "question": "How long does the confidentiality obligation survive after employment ends?",
        "expected_doc": "mutual_nda_agreement.pdf",
        "category": "Confidentiality",
    },
    {
        "question": "What is the annual rent escalation rate in the commercial lease?",
        "expected_doc": "commercial_lease_agreement.pdf",
        "category": "Rent & Payment",
    },
    {
        "question": "Who owns the intellectual property for rejected work in the freelance agreement?",
        "expected_doc": "freelance_service_agreement.pdf",
        "category": "IP Rights",
    },
    {
        "question": "What is the weather forecast for Bangalore tomorrow?",
        "expected_doc": None,  # Should be declined
        "category": "Out-of-scope",
    },
]


def render():
    render_sidebar()

    st.title("Evaluation Metrics")
    st.caption(
        "Run a curated set of test questions to measure retrieval and generation quality. "
        "This is a lightweight proxy evaluation — for full RAGAS metrics, see Phase 7."
    )

    # Check if documents are loaded
    doc_data = get_documents()
    docs = doc_data.get("documents", [])
    loaded_names = {d["file_name"] for d in docs}

    if not docs:
        st.warning("No documents loaded. Run `seed_data.py` first or upload contracts via the sidebar.")
        return

    # ── Info about what will run ───────────────────────────────────────────────
    st.info(
        f"**{len(EVAL_QUESTIONS)} test questions** ready to run  |  "
        f"**{len(docs)} documents** loaded  |  "
        f"**{doc_data.get('total_chunks', 0)} chunks** indexed"
    )

    # Filter questions to only those whose expected doc is loaded
    runnable = [
        q for q in EVAL_QUESTIONS
        if q["expected_doc"] is None or q["expected_doc"] in loaded_names
    ]
    skipped = len(EVAL_QUESTIONS) - len(runnable)
    if skipped:
        st.warning(
            f"{skipped} question(s) skipped — their source documents are not loaded. "
            "Run `seed_data.py` to load all 5 sample contracts."
        )

    col_run, col_info = st.columns([1, 3])
    run_btn = col_run.button("Run Evaluation", type="primary", use_container_width=True)
    col_info.caption(
        "Each question is sent to the API. Results show whether the system "
        "answered correctly, declined appropriately, and cited the right document."
    )

    if not run_btn:
        _show_sample_results()
        return

    # ── Run evaluation ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Evaluation Results")
    progress = st.progress(0, text="Starting evaluation...")

    results = []
    for i, q_item in enumerate(runnable):
        progress.progress(
            (i + 1) / len(runnable),
            text=f"Running Q{i+1}/{len(runnable)}: {q_item['question'][:50]}...",
        )

        t_start = time.perf_counter()
        response = post_query(q_item["question"], top_k=5)
        elapsed  = (time.perf_counter() - t_start) * 1000

        if "error" in response:
            results.append({**q_item, "error": response["error"]})
            continue

        is_declined     = response.get("is_declined", False)
        should_decline  = q_item["expected_doc"] is None
        correct_decline = should_decline and is_declined
        answered        = not is_declined
        sources_cited   = response.get("sources_cited", [])
        correct_source  = (
            q_item["expected_doc"] in sources_cited
            if q_item["expected_doc"] else True
        )
        confidence      = response.get("confidence", {})

        results.append({
            **q_item,
            "is_declined":     is_declined,
            "should_decline":  should_decline,
            "correct_decline": correct_decline,
            "answered":        answered,
            "correct_source":  correct_source,
            "sources_cited":   sources_cited,
            "confidence_score": confidence.get("score", 0),
            "confidence_label": confidence.get("label", ""),
            "retrieval_score": confidence.get("retrieval_score", 0),
            "coverage_score":  confidence.get("coverage_score", 0),
            "citation_score":  confidence.get("citation_score", 0),
            "latency_ms":      elapsed,
            "answer_preview":  response.get("answer", "")[:200],
        })

    progress.empty()

    # ── Summary metrics ────────────────────────────────────────────────────────
    _render_summary(results)

    # ── Per-question results ───────────────────────────────────────────────────
    st.divider()
    st.subheader("Per-Question Results")
    for i, r in enumerate(results):
        _render_result_card(i + 1, r)


def _render_summary(results: list):
    """Show headline metrics at the top."""
    answered       = [r for r in results if not r.get("should_decline") and r.get("answered")]
    declined_ok    = [r for r in results if r.get("correct_decline")]
    correct_source = [r for r in answered if r.get("correct_source")]
    errors         = [r for r in results if "error" in r]

    n_total     = len(results)
    n_answered  = len(answered)
    n_dec_ok    = len(declined_ok)
    n_correct   = len(correct_source)

    answer_rate     = n_answered / max(n_total - sum(1 for r in results if r.get("should_decline")), 1)
    decline_acc     = n_dec_ok   / max(sum(1 for r in results if r.get("should_decline")), 1)
    source_acc      = n_correct  / max(n_answered, 1)
    avg_confidence  = sum(r.get("confidence_score", 0) for r in answered) / max(n_answered, 1)
    avg_latency     = sum(r.get("latency_ms", 0) for r in results) / max(len(results), 1)

    st.subheader("Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Answer Rate",     f"{answer_rate:.0%}",    help="Fraction of in-scope questions answered")
    c2.metric("Decline Accuracy",f"{decline_acc:.0%}",   help="Correctly declined out-of-scope questions")
    c3.metric("Source Accuracy", f"{source_acc:.0%}",    help="Answer cited the expected source document")
    c4.metric("Avg Confidence",  f"{avg_confidence:.0%}",help="Average confidence score for answered questions")
    c5.metric("Avg Latency",     f"{avg_latency:.0f}ms", help="Average end-to-end response time")

    if errors:
        st.error(f"{len(errors)} question(s) failed with errors — check the API logs.")


def _render_result_card(num: int, r: dict):
    """Render a single evaluation result as a card."""
    is_error        = "error" in r
    should_decline  = r.get("should_decline", False)
    is_declined     = r.get("is_declined", False)
    correct_source  = r.get("correct_source", False)

    # Determine pass/fail
    if is_error:
        status, color = "ERROR", "red"
    elif should_decline:
        status, color = ("PASS (Correctly declined)", "green") if is_declined else ("FAIL (Should have declined)", "red")
    elif not is_declined and correct_source:
        status, color = "PASS", "green"
    elif not is_declined and not correct_source:
        status, color = "PARTIAL (Wrong source cited)", "orange"
    else:
        status, color = "FAIL (Declined instead of answering)", "red"

    with st.expander(
        f"Q{num}: {r['question'][:80]}  |  [{r['category']}]  |  {status}",
        expanded=False,
    ):
        cols = st.columns([2, 1, 1, 1])
        cols[0].markdown(f"**Category**: {r['category']}")
        cols[0].markdown(f"**Expected doc**: {r.get('expected_doc') or 'None (out-of-scope)'}")

        if not is_error and not should_decline:
            cols[1].metric("Confidence", f"{r.get('confidence_score', 0):.0%}")
            cols[2].metric("Retrieval",  f"{r.get('retrieval_score', 0):.0%}")
            cols[3].metric("Latency",    f"{r.get('latency_ms', 0):.0f}ms")

        if is_error:
            st.error(f"Error: {r['error']}")
        else:
            st.markdown(f"**Sources cited**: {', '.join(r.get('sources_cited', [])) or 'None'}")
            st.markdown("**Answer preview:**")
            if is_declined:
                st.warning(r.get("answer_preview", "")[:200])
            else:
                st.info(r.get("answer_preview", "")[:200] + "...")


def _show_sample_results():
    """Show placeholder metrics before evaluation is run."""
    st.divider()
    st.subheader("Expected Performance (before running)")
    st.caption("These are indicative targets. Run the evaluation to see actual results.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Answer Rate",      "~85-90%",  delta="in-scope questions")
    c2.metric("Decline Accuracy", "~90-100%", delta="out-of-scope questions")
    c3.metric("Source Accuracy",  "~75-85%",  delta="correct document cited")
    c4.metric("Avg Confidence",   "~55-70%",  delta="combined score")

    st.markdown("""
    ### What these metrics mean

    | Metric | What we measure | Why it matters |
    |--------|----------------|----------------|
    | **Answer Rate** | Fraction of answerable questions the system answered | Should be high for in-scope questions |
    | **Decline Accuracy** | Correctly refusing out-of-scope questions | Prevents hallucination |
    | **Source Accuracy** | Did the answer cite the right document? | Validates retrieval quality |
    | **Avg Confidence** | Average combined confidence score | Calibration — should track with correctness |

    ### RAGAS Metrics (Phase 7)
    When RAGAS is installed, we'll also measure:
    - **Context Precision**: What % of retrieved chunks are actually relevant?
    - **Context Recall**: Did we retrieve all necessary information?
    - **Faithfulness**: Are all claims in the answer grounded in the context?
    - **Answer Relevance**: Does the answer actually address the question?
    """)
