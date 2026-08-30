"""
Shared Sidebar — rendered on every page.
Shows: API health, Ollama status, document list, upload widget.
"""

import streamlit as st
from app.ui.api_client import get_health, get_documents, upload_pdf, ingest_url, delete_document


def render_sidebar():
    """Render the full left sidebar. Call from any page."""

    with st.sidebar:
        st.title("🏛️ ContractSage")
        st.caption("AI-powered legal contract Q&A")
        st.divider()

        # ── System Health ─────────────────────────────────────────────────────
        with st.expander("System Status", expanded=True):
            health = get_health()

            api_ok    = health.get("status") not in ("unreachable",)
            ollama_ok = health.get("ollama_running", False)
            model_ok  = health.get("primary_model_available", False)
            chunks    = health.get("vector_store_chunks", 0)

            col1, col2 = st.columns(2)
            col1.metric("API",    "Online"  if api_ok    else "Offline",  delta=None)
            col2.metric("Ollama", "Running" if ollama_ok else "Offline",  delta=None)

            if model_ok:
                models = health.get("available_models", [])
                st.success(f"Model: {models[0] if models else 'ready'}")
            else:
                st.warning("llama3.1:8b not found — run `ollama pull llama3.1:8b`")

            st.caption(f"Vector store: **{chunks}** chunks indexed")

        st.divider()

        # ── Upload Documents ───────────────────────────────────────────────────
        st.subheader("Upload Contract")

        tab_pdf, tab_url = st.tabs(["PDF File", "URL"])

        with tab_pdf:
            uploaded = st.file_uploader(
                "Choose a PDF",
                type=["pdf"],
                help="Max 50 MB. Re-uploading the same file updates it safely.",
            )
            if uploaded:
                if st.button("Ingest PDF", type="primary", use_container_width=True):
                    with st.spinner(f"Ingesting {uploaded.name}..."):
                        result = upload_pdf(uploaded.read(), uploaded.name)

                    if result.get("success"):
                        st.success(
                            f"Done! {result['chunks_created']} chunks added "
                            f"in {result['processing_time_ms']:.0f}ms"
                        )
                        st.rerun()
                    else:
                        st.error(result.get("error", "Upload failed"))

        with tab_url:
            url = st.text_input(
                "Document URL",
                placeholder="https://example.com/contract.html",
            )
            if st.button("Ingest URL", use_container_width=True):
                if url.startswith("http"):
                    with st.spinner("Fetching and ingesting..."):
                        result = ingest_url(url)
                    if result.get("success"):
                        st.success(f"Done! {result['chunks_created']} chunks added")
                        st.rerun()
                    else:
                        st.error(result.get("error", "URL ingestion failed"))
                else:
                    st.error("Please enter a valid http(s):// URL")

        st.divider()

        # ── Loaded Documents ──────────────────────────────────────────────────
        st.subheader("Loaded Documents")
        doc_data = get_documents()
        docs = doc_data.get("documents", [])

        if not docs:
            st.info("No documents ingested yet. Upload a PDF to get started.")
        else:
            for doc in docs:
                col_name, col_del = st.columns([4, 1])
                icon = "📄" if doc["doc_type"] == "pdf" else "🌐"
                col_name.markdown(
                    f"{icon} **{doc['file_name']}**  \n"
                    f"<small>{doc['chunk_count']} chunks · {doc['total_pages']} pages</small>",
                    unsafe_allow_html=True,
                )
                if col_del.button("✕", key=f"del_{doc['source']}", help="Remove this document"):
                    with st.spinner("Removing..."):
                        res = delete_document(doc["source"])
                    if res.get("success"):
                        st.success(f"Removed {res['chunks_deleted']} chunks")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Delete failed"))

        st.divider()

        # ── Settings ──────────────────────────────────────────────────────────
        with st.expander("Query Settings"):
            st.session_state["top_k"] = st.slider(
                "Chunks to retrieve (top_k)",
                min_value=1, max_value=15,
                value=st.session_state.get("top_k", 5),
                help="Higher = more context, slower response",
            )
            st.session_state["reasoning_mode"] = st.toggle(
                "Chain-of-thought mode",
                value=st.session_state.get("reasoning_mode", False),
                help="More accurate but ~30% slower",
            )
            if st.button("Clear Chat History", use_container_width=True):
                st.session_state["chat_history"] = []
                st.rerun()
