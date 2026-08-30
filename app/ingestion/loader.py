"""
Loads documents from PDF files and URLs into LangChain Document objects.
Each Document includes page_content and metadata (source, page, doc_type, loaded_at).
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Union
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class DocumentLoadError(Exception):
    """Raised when a document cannot be loaded (bad file, unreachable URL, etc.)."""
    pass

from langchain_core.documents import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)



def load_pdf(file_path: Union[str, Path]) -> list[Document]:
    """
    Load a PDF file and return one Document per page.

    Each document's metadata includes:
      - source      : absolute path to the PDF
      - file_name   : just the filename (used in citations)
      - page        : 1-indexed page number
      - total_pages : total pages in the document
      - doc_type    : "pdf"
      - loaded_at   : ISO timestamp

    Args:
        file_path: Path to the PDF file.

    Returns:
        List of Document objects, one per page with non-empty text.

    Raises:
        DocumentLoadError: If the file doesn't exist or can't be parsed.
    """
    path = Path(file_path).resolve()

    if not path.exists():
        raise DocumentLoadError(f"PDF file not found: {path}")
    if not path.suffix.lower() == ".pdf":
        raise DocumentLoadError(f"File is not a PDF: {path}")

    logger.info(f"Loading PDF: {path.name}")

    try:
        reader = PdfReader(str(path))
        total_pages = len(reader.pages)
        documents: list[Document] = []
        loaded_at = datetime.now(timezone.utc).isoformat()

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = _clean_text(text)

            if not text.strip():
                logger.debug(f"Skipping empty page {page_idx + 1} in {path.name}")
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(path),
                        "file_name": path.name,
                        "page": page_idx + 1,          # 1-indexed (human-friendly)
                        "total_pages": total_pages,
                        "doc_type": "pdf",
                        "loaded_at": loaded_at,
                    },
                )
            )

        logger.info(
            f"Loaded {len(documents)} pages from '{path.name}' "
            f"(skipped {total_pages - len(documents)} empty pages)"
        )
        return documents

    except Exception as exc:
        raise DocumentLoadError(f"Failed to parse PDF '{path}': {exc}") from exc


def load_url(url: str, timeout: int = 15) -> list[Document]:
    """
    Scrape a URL and return its main text content as a single Document.

    Strips navigation, scripts, and boilerplate using BeautifulSoup.
    Returns the cleaned article/body text with source URL metadata.

    Trade-off note: This approach works for legal document portals (e.g.,
    government acts, court orders) that serve plain HTML. For JavaScript-
    heavy portals, we'd need Playwright — but that adds ~500MB dependency.

    Args:
        url    : HTTP/HTTPS URL to scrape.
        timeout: Request timeout in seconds.

    Returns:
        List with a single Document containing the scraped text.

    Raises:
        DocumentLoadError: If the URL can't be fetched or parsed.
    """
    _validate_url(url)
    logger.info(f"Loading URL: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DocumentLoadError(f"Failed to fetch URL '{url}': {exc}") from exc

    # Parse HTML and extract main text
    soup = BeautifulSoup(response.text, "lxml")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "advertisement", "noscript"]):
        tag.decompose()

    # Prefer article/main body; fallback to full body
    main_content = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", {"id": "content"})
        or soup.find("div", {"class": "content"})
        or soup.body
    )

    raw_text = main_content.get_text(separator="\n") if main_content else soup.get_text()
    text = _clean_text(raw_text)

    if not text.strip():
        raise DocumentLoadError(f"No text content found at URL: {url}")

    parsed = urlparse(url)
    document = Document(
        page_content=text,
        metadata={
            "source": url,
            "file_name": parsed.netloc + parsed.path,
            "page": 1,
            "total_pages": 1,
            "doc_type": "url",
            "loaded_at": datetime.now(timezone.utc).isoformat(),
            "status_code": response.status_code,
            "content_length": len(text),
        },
    )

    logger.info(f"Loaded URL: {url} ({len(text)} characters)")
    return [document]


def load_documents(source: Union[str, Path]) -> list[Document]:
    """
    Unified entry point — auto-detects PDF vs URL.

    Args:
        source: Either a file path (str/Path) to a PDF or an HTTP(S) URL.

    Returns:
        List of Document objects ready for chunking.

    Raises:
        DocumentLoadError: If source type can't be determined or loading fails.
    """
    source_str = str(source)

    if source_str.startswith(("http://", "https://")):
        return load_url(source_str)

    path = Path(source_str)
    if path.suffix.lower() == ".pdf":
        return load_pdf(path)

    raise DocumentLoadError(
        f"Unsupported source type: '{source}'. "
        "Provide a .pdf file path or an http(s):// URL."
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """
    Normalise whitespace in extracted text.

    pypdf sometimes produces text with excessive newlines and spaces
    from PDF column layouts. This normalises them without losing structure.
    """
    import re
    # Collapse multiple blank lines into a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces (but not newlines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def _validate_url(url: str) -> None:
    """Validate URL scheme to prevent SSRF-style issues."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise DocumentLoadError(
            f"Invalid URL scheme '{parsed.scheme}'. Only http/https are supported."
        )
    if not parsed.netloc:
        raise DocumentLoadError(f"Invalid URL (no domain): '{url}'")
