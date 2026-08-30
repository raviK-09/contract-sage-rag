r"""
ContractSage Streamlit UI — Main Entry Point
=============================================
Run with:
    .venv\Scripts\streamlit.exe run app/ui/app.py

Architecture: Multi-page app using st.navigation (Streamlit 1.36+)
  - All pages share state via st.session_state
  - API calls go to the FastAPI backend (http://localhost:8000)
  - No direct database/model access from UI — always via API

Trade-off — Streamlit vs React/Next.js:
  Streamlit  : Build in Python in hours, no JS knowledge needed, limited customisation
  React      : Full control, production-grade UX, requires frontend skills + time
  For a portfolio project, Streamlit is the right choice — it lets you focus on
  AI/ML concepts rather than CSS and bundlers.
"""

import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH so we can import app.*
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

# ── Page Configuration (must be first Streamlit call) ─────────────────────────
st.set_page_config(
    page_title="ContractSage",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": (
            "**ContractSage** — AI-powered legal contract Q&A\n\n"
            "Built with Ollama + LangChain + ChromaDB + FastAPI + Streamlit\n\n"
            "*Zero API cost. Runs entirely on local models.*"
        ),
    },
)

# ── Session state initialisation ───────────────────────────────────────────────
def _init_session_state():
    defaults = {
        "chat_history": [],          # list of {role, content, metadata}
        "api_base": "http://localhost:8000",
        "selected_page": "chat",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session_state()

# ── Navigation ─────────────────────────────────────────────────────────────────
# All page modules expose a function named `render`. Without explicit url_path,
# Streamlit infers the URL from the callable name -- all three would map to
# "/render" causing a "duplicate URL pathname" error.
# Fix: give each page a unique url_path explicitly.
from app.ui.pages import chat, documents, evaluation

pages = [
    st.Page(chat.render,       title="Ask a Question",     icon="💬", url_path="chat",       default=True),
    st.Page(documents.render,  title="Manage Documents",   icon="📄", url_path="documents"),
    st.Page(evaluation.render, title="Evaluation Metrics", icon="📊", url_path="evaluation"),
]

pg = st.navigation(pages)
pg.run()
