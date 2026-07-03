"""Shared helper functions for nodes."""

import time
from contextlib import contextmanager
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from fastembed import TextEmbedding

from .config import get_config

# Local embedding model: runs on CPU, no API key, downloads weights once (~50MB)
# and caches them. 384-dim output — keep the Milvus collection's `dim` in sync.
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
_embedder: TextEmbedding | None = None


def get_llm() -> ChatOpenAI:
    """Get the configured chat model (provider-agnostic).

    Uses the OpenAI-compatible interface, so it works with OpenAI, Anthropic,
    Azure, Groq, Together, local vLLM/Ollama, or any corporate endpoint — set
    LLM_MODEL, LLM_API_KEY, and (for anything but OpenAI) LLM_BASE_URL in .env.

    Returns:
        ChatOpenAI: Configured chat model with temperature=0.
    """
    config = get_config()
    return ChatOpenAI(
        model=config.llm_model,
        temperature=0,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url or None,
    )


def get_embedder() -> TextEmbedding:
    """Get the cached local embedding model, loading it on first use."""
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(EMBEDDING_MODEL)
    return _embedder


def embed(text: str) -> list[float]:
    """Embed a single string locally with fastembed (384-dim, no API key)."""
    vector = next(iter(get_embedder().embed([text])))
    return vector.tolist() if hasattr(vector, "tolist") else list(vector)


@contextmanager
def log_node_execution(logger, node_name: str, extra: Dict[str, Any]):
    """Context manager for timing and logging node execution.

    Args:
        logger: Logger instance to use
        node_name: Name of the node being executed
        extra: Extra fields to include in log messages

    Yields:
        None

    Example:
        with log_node_execution(logger, "retrieval", {"query": query}):
            # ... node logic ...
            pass
    """
    start_time = time.time()
    logger.info(f"Starting {node_name}", extra=extra)

    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"{node_name} complete",
            extra={**extra, "duration_ms": duration_ms}
        )
