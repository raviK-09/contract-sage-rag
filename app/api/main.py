"""
FastAPI application factory with CORS middleware, request timing, health check,
and routers for /ingest, /query, and /documents.
"""


import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependencies import get_vector_store
from app.api.routes import documents, ingest, query
from app.api.schemas import HealthResponse
from app.config import settings
from app.generation.llm_client import check_ollama_connection

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered legal contract Q&A system. "
        "Upload contracts, ask questions in plain English, "
        "get answers with exact clause citations."
    ),
    version="0.1.0",
    docs_url="/docs",           # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",         # ReDoc at http://localhost:8000/redoc
    openapi_url="/openapi.json",
)

# ── CORS Middleware ────────────────────────────────────────────────────────────
# Trade-off: Allow all origins in development for easy Streamlit ↔ API comms.
# In production, restrict to specific frontend domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to every response for performance monitoring."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response

# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return consistent JSON errors rather than crashing with HTML 500 pages."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs for details."},
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(query.router)

# ── Health endpoint ───────────────────────────────────────────────────────────
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check service and dependency health",
)
def health_check() -> HealthResponse:
    """
    Returns the health status of all dependencies:
    - Ollama connectivity and model availability
    - Vector store chunk count

    Used by monitoring tools and the Streamlit sidebar status indicator.
    """
    ollama_status = check_ollama_connection()
    store = get_vector_store()

    overall = "healthy" if ollama_status["ollama_running"] else "degraded"

    return HealthResponse(
        status=overall,
        ollama_running=ollama_status["ollama_running"],
        primary_model_available=ollama_status["primary_model_available"],
        fallback_model_available=ollama_status["fallback_model_available"],
        vector_store_chunks=store.count(),
        available_models=ollama_status["available_models"],
        app_name=settings.APP_NAME,
        version="0.1.0",
    )

# ── Root redirect ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
    }


# ── Dev server entrypoint ─────────────────────────────────────────────────────
def start():
    """Called by the `serve-api` CLI script defined in pyproject.toml."""
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.API_LOG_LEVEL,
    )


if __name__ == "__main__":
    start()
