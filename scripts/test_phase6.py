"""Quick import check for Phase 6 UI files."""
import sys
from pathlib import Path

# Always resolve relative to this file's location — works from any directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
print(f"Project root: {PROJECT_ROOT}")

print("Checking UI imports...")
from app.ui.api_client import get_health, get_documents, post_query, upload_pdf, delete_document
print("  api_client.py     OK")

from app.ui.components.sidebar import render_sidebar
print("  sidebar.py        OK")

from app.ui.pages.chat import render as chat_render
print("  pages/chat.py     OK")

from app.ui.pages.documents import render as docs_render
print("  pages/documents.py OK")

from app.ui.pages.evaluation import render as eval_render, EVAL_QUESTIONS
print(f"  pages/evaluation.py OK  ({len(EVAL_QUESTIONS)} eval questions loaded)")

print("\nAll Phase 6 imports successful!")
