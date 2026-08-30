"""
Documents Page — manage all ingested contracts.
Shows a detailed table of documents with upload and delete controls.
"""

import streamlit as st
from app.ui.api_client import get_documents, upload_pdf, ingest_url, delete_document
from app.ui.components.sidebar import render_sidebar


def render():
    render_sidebar()

    st.title("Manage Documents")
    st.caption(
        "All contracts currently loaded in the vector store. "
        "Upload new ones, or remove documents you no longer need."
    )

    # ── Upload section ────────────────────────────────────────────────────────
    with st.expander("Upload a New Contract", expanded=False):
        tab_pdf, tab_url = st.tabs(["PDF Upload", "From URL"])

        with tab_pdf:
            st.markdown("**Supported:** Legal contracts, NDAs, lease agreements, employment agreements")
            uploaded = st.file_uploader(
                "Choose a PDF file",
                type=["pdf"],
                help="Maximum 50 MB. Re-uploading the same file is safe — it updates existing chunks.",
                key="doc_page_uploader",
            )
            if uploaded:
                col1, col2 = st.columns([2, 1])
                col1.markdown(
                    f"**Selected:** {uploaded.name}  \n"
                    f"Size: {uploaded.size / 1024:.1f} KB"
                )
                if col2.button("Ingest PDF", type="primary"):
                    with st.spinner(f"Processing {uploaded.name}..."):
                        result = upload_pdf(uploaded.read(), uploaded.name)
                    if result.get("success"):
                        st.success(
                            f"Ingested **{uploaded.name}** successfully!\n\n"
                            f"- Pages loaded: {result['pages_loaded']}\n"
                            f"- Chunks created: {result['chunks_created']}\n"
                            f"- Processing time: {result['processing_time_ms']:.0f}ms\n"
                            f"- Total chunks in store: {result['total_chunks_in_store']}"
                        )
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {result.get('error', 'Unknown error')}")

        with tab_url:
            st.markdown("**Works for:** Static HTML pages, government portals, public contract templates")
            st.warning("JavaScript-rendered pages are not supported. Download as PDF instead.")
            url_input = st.text_input(
                "Contract URL",
                placeholder="https://example.com/terms.html",
                key="doc_page_url",
            )
            if st.button("Fetch and Ingest"):
                if url_input.startswith("http"):
                    with st.spinner("Fetching page content..."):
                        result = ingest_url(url_input)
                    if result.get("success"):
                        st.success(f"Ingested URL: {result['chunks_created']} chunks added")
                        st.rerun()
                    else:
                        st.error(result.get("error", "Failed"))
                else:
                    st.error("Please enter a valid http(s):// URL")

    st.divider()

    # ── Document table ────────────────────────────────────────────────────────
    doc_data = get_documents()
    docs     = doc_data.get("documents", [])
    total_chunks = doc_data.get("total_chunks", 0)

    col_h1, col_h2 = st.columns([3, 1])
    col_h1.subheader(f"Loaded Documents ({len(docs)})")
    col_h2.metric("Total Chunks", total_chunks, help="Number of text chunks across all documents")

    if not docs:
        st.info(
            "No documents loaded yet. Upload a contract above to get started.\n\n"
            "Or run the seed script to load sample contracts:\n"
            "```\n.venv\\Scripts\\python.exe scripts/seed_data.py\n```"
        )
        return

    # Render each document as a card
    for doc in docs:
        with st.container(border=True):
            col_icon, col_info, col_actions = st.columns([1, 6, 2])

            icon = "📄" if doc["doc_type"] == "pdf" else "🌐"
            col_icon.markdown(f"<h1 style='text-align:center'>{icon}</h1>", unsafe_allow_html=True)

            col_info.markdown(f"**{doc['file_name']}**")
            col_info.caption(
                f"Type: {doc['doc_type'].upper()}  |  "
                f"Pages: {doc['total_pages']}  |  "
                f"Chunks: {doc['chunk_count']}  |  "
                f"Ingested: {doc['loaded_at'][:10] if doc.get('loaded_at') else 'Unknown'}"
            )
            if doc["doc_type"] != "pdf":
                col_info.caption(f"Source: {doc['source']}")

            if col_actions.button(
                "Remove",
                key=f"remove_{doc['source']}",
                type="secondary",
                use_container_width=True,
                help="Remove all chunks from this document",
            ):
                with st.spinner(f"Removing {doc['file_name']}..."):
                    result = delete_document(doc["source"])
                if result.get("success"):
                    st.success(f"Removed {result['chunks_deleted']} chunks")
                    st.rerun()
                else:
                    st.error(result.get("error", "Remove failed"))

    st.divider()
    st.caption(
        "**Note on re-ingestion**: Uploading the same document again is safe. "
        "Chunks are identified by a SHA-256 hash of their source + position, "
        "so re-ingestion updates existing chunks without creating duplicates."
    )
