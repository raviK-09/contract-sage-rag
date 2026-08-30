"""
Thin wrapper around Ollama via LangChain's ChatOllama interface.
Returns a BaseChatModel — swapping to OpenAI or Anthropic is a one-line change.
"""


import logging
from functools import lru_cache
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseChatModel:
    """
    Return a cached LLM instance for the given model + temperature combo.

    lru_cache with maxsize=4 means we can hold up to 4 different
    (model, temperature) configurations in memory simultaneously.
    E.g.: primary model + fallback model, each at two temperatures.

    Args:
        model      : Model name override (default from settings).
        temperature: Temperature override (default from settings).

    Returns:
        A LangChain BaseChatModel — works identically for all providers.
    """
    target_model = model or settings.LLM_MODEL
    target_temp  = temperature if temperature is not None else settings.LLM_TEMPERATURE

    logger.info(
        f"Initialising LLM: model='{target_model}' "
        f"temperature={target_temp} "
        f"base_url='{settings.OLLAMA_BASE_URL}'"
    )

    # Trade-off: Why ChatOllama over raw requests to Ollama's API?
    # ChatOllama gives us: streaming, LangChain message format, retries,
    # and most importantly — the SAME interface as ChatOpenAI/ChatAnthropic.
    return ChatOllama(
        model=target_model,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=target_temp,
        num_predict=settings.LLM_MAX_TOKENS,
        # keep_alive ensures the model stays loaded between requests
        # Trade-off: uses GPU/CPU memory but eliminates ~5s model load time per request
        keep_alive="10m",
    )


def get_primary_llm() -> BaseChatModel:
    """Convenience: return the primary (highest quality) LLM."""
    return get_llm(model=settings.LLM_MODEL)


def get_fallback_llm() -> BaseChatModel:
    """
    Convenience: return the lightweight fallback LLM.

    Used when:
    - Confidence score is borderline and we want a faster second opinion
    - Primary model is unavailable / times out
    - Running evaluation where speed matters more than quality
    """
    return get_llm(model=settings.LLM_MODEL_FALLBACK)


def check_ollama_connection() -> dict:
    """
    Verify Ollama is running and the required models are available.

    Returns a status dict used by the FastAPI /health endpoint.
    """
    import httpx

    status = {
        "ollama_running": False,
        "primary_model_available": False,
        "fallback_model_available": False,
        "available_models": [],
        "error": None,
    }

    try:
        response = httpx.get(
            f"{settings.OLLAMA_BASE_URL}/api/tags",
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
        status["ollama_running"] = True

        available = [m["name"] for m in data.get("models", [])]
        status["available_models"] = available

        # Check if our models are pulled (name may include :latest tag)
        def _model_available(name: str) -> bool:
            return any(name in m or m.startswith(name) for m in available)

        status["primary_model_available"]  = _model_available(settings.LLM_MODEL)
        status["fallback_model_available"] = _model_available(settings.LLM_MODEL_FALLBACK)

    except Exception as exc:
        status["error"] = str(exc)
        logger.warning(f"Ollama connection check failed: {exc}")

    return status
