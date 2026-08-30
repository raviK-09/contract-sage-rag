"""
Shared API Client — used by all UI pages to call the FastAPI backend.
All HTTP calls live here — pages never call requests/httpx directly.
"""

import requests
from typing import Optional


def _base() -> str:
    import streamlit as st
    return st.session_state.get("api_base", "http://localhost:8000")


def get_health() -> dict:
    try:
        r = requests.get(f"{_base()}/health", timeout=5)
        return r.json()
    except Exception:
        return {"status": "unreachable", "ollama_running": False,
                "vector_store_chunks": 0, "available_models": [],
                "primary_model_available": False}


def get_documents() -> dict:
    try:
        r = requests.get(f"{_base()}/documents", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"documents": [], "total_documents": 0, "total_chunks": 0, "error": str(e)}


def post_query(question: str, top_k: int = 5, reasoning_mode: bool = False) -> dict:
    try:
        r = requests.post(
            f"{_base()}/query",
            json={"question": question, "top_k": top_k, "reasoning_mode": reasoning_mode},
            timeout=120,   # LLM generation can take up to 2 min on CPU
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. The LLM is taking too long — try a shorter question or check if Ollama is running."}
    except Exception as e:
        return {"error": str(e)}


def upload_pdf(file_bytes: bytes, filename: str) -> dict:
    try:
        r = requests.post(
            f"{_base()}/ingest/pdf",
            files={"file": (filename, file_bytes, "application/pdf")},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def ingest_url(url: str) -> dict:
    try:
        r = requests.post(
            f"{_base()}/ingest/url",
            json={"url": url},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_document(source: str) -> dict:
    try:
        from urllib.parse import quote
        encoded = quote(source, safe="")
        r = requests.delete(f"{_base()}/documents/{encoded}", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
