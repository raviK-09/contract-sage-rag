"""
Chat Page — the main Q&A interface.
Users type questions, get cited answers with confidence indicators.
"""

import streamlit as st
from app.ui.api_client import post_query
from app.ui.components.sidebar import render_sidebar


def render():
    render_sidebar()

    st.title("Ask Your Contract")
    st.caption(
        "Ask any question about your uploaded contracts in plain English. "
        "Every answer comes with exact clause citations so you can verify it yourself."
    )

    # ── Chat history display ──────────────────────────────────────────────────
    history = st.session_state.get("chat_history", [])

    if not history:
        # Welcome state
        st.info(
            "**Get started:** Upload a contract in the sidebar, then ask a question.\n\n"
            "**Example questions:**\n"
            "- *What is the notice period for terminating the lease?*\n"
            "- *Can the landlord enter without giving notice?*\n"
            "- *What happens to my deposit if I leave early?*\n"
            "- *What is my non-compete obligation after leaving?*"
        )
    else:
        for msg in history:
            _render_message(msg)

    # ── Input bar ─────────────────────────────────────────────────────────────
    question = st.chat_input(
        "Ask a question about your contracts...",
        key="chat_input",
    )

    if question:
        # Add user message immediately
        user_msg = {"role": "user", "content": question}
        st.session_state["chat_history"].append(user_msg)

        # Show spinner while waiting for LLM
        with st.spinner("Searching contracts and generating answer..."):
            response = post_query(
                question=question,
                top_k=st.session_state.get("top_k", 5),
                reasoning_mode=st.session_state.get("reasoning_mode", False),
            )

        if "error" in response:
            error_msg = {
                "role": "assistant",
                "content": f"Error: {response['error']}",
                "is_error": True,
            }
            st.session_state["chat_history"].append(error_msg)
        else:
            assistant_msg = {
                "role": "assistant",
                "content": response["answer"],
                "is_declined": response.get("is_declined", False),
                "confidence": response.get("confidence", {}),
                "citations": response.get("citations", []),
                "latency_ms": response.get("latency_ms", 0),
                "retrieval_ms": response.get("retrieval_ms", 0),
                "generation_ms": response.get("generation_ms", 0),
            }
            st.session_state["chat_history"].append(assistant_msg)

        st.rerun()


def _render_message(msg: dict):
    """Render a single chat message with all its metadata."""
    role = msg["role"]

    with st.chat_message(role, avatar="🧑" if role == "user" else "🏛️"):
        if msg.get("is_error"):
            st.error(msg["content"])
            return

        if role == "user":
            st.markdown(msg["content"])
            return

        # ── Assistant message ─────────────────────────────────────────────────
        is_declined = msg.get("is_declined", False)
        confidence  = msg.get("confidence", {})
        citations   = msg.get("citations", [])

        # Confidence badge
        if not is_declined and confidence:
            score = confidence.get("score", 0)
            label = confidence.get("label", "")
            _render_confidence_badge(score, label)

        # Answer text
        if is_declined:
            st.warning(msg["content"])
        else:
            st.markdown(msg["content"])

        # Citations section
        if citations and not is_declined:
            _render_citations(citations)

        # Confidence breakdown (collapsed)
        if confidence and not is_declined:
            with st.expander("Confidence breakdown", expanded=False):
                _render_confidence_breakdown(confidence)

        # Timing footer
        latency = msg.get("latency_ms", 0)
        ret_ms  = msg.get("retrieval_ms", 0)
        gen_ms  = msg.get("generation_ms", 0)
        if latency:
            st.caption(
                f"Total: {latency:.0f}ms  |  "
                f"Retrieval: {ret_ms:.0f}ms  |  "
                f"Generation: {gen_ms:.0f}ms"
            )


def _render_confidence_badge(score: float, label: str):
    """Render a coloured confidence pill."""
    color_map = {"High": "green", "Medium": "orange", "Low": "red"}
    color = color_map.get(label, "gray")
    pct   = f"{score:.0%}"
    st.markdown(
        f'<span style="background:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-size:0.8rem;font-weight:600;">'
        f'Confidence: {pct} ({label})</span>',
        unsafe_allow_html=True,
    )
    st.write("")  # Spacing


def _render_citations(citations: list):
    """Render the reference list below the answer."""
    st.markdown("---")
    st.markdown("**References**")
    for cite in citations:
        label_type = "Page" if cite.get("doc_type") == "pdf" else "Section"
        relevance  = cite.get("relevance_score", 0)
        st.markdown(
            f"**[{cite['source_num']}]** {cite['file_name']} — "
            f"{label_type} {cite['page']}  "
            f"*(relevance: {relevance:.0%})*"
        )
        with st.expander(f"View snippet [Source {cite['source_num']}]", expanded=False):
            st.caption(cite.get("relevant_snippet", "")[:400])


def _render_confidence_breakdown(confidence: dict):
    """Render a visual bar chart of the 3 confidence signals."""
    col1, col2, col3 = st.columns(3)

    def _signal_col(col, label, value, help_text):
        col.metric(label, f"{value:.0%}")
        col.progress(value, text=None)
        col.caption(help_text)

    _signal_col(
        col1, "Retrieval Quality",
        confidence.get("retrieval_score", 0),
        "Avg semantic similarity of retrieved chunks",
    )
    _signal_col(
        col2, "Context Coverage",
        confidence.get("coverage_score", 0),
        "Fraction of chunks above relevance threshold",
    )
    _signal_col(
        col3, "Citation Usage",
        confidence.get("citation_score", 0),
        "How much the LLM used the retrieved context",
    )

    threshold = confidence.get("threshold_used", 0.4)
    combined  = confidence.get("score", 0)
    st.caption(
        f"Combined score: **{combined:.0%}** | "
        f"Decline threshold: **{threshold:.0%}**"
    )
