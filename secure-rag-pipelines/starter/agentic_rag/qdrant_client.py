"""Qdrant client connection pooling."""

from threading import Lock
from typing import Optional

from qdrant_client import QdrantClient

_qdrant_client: Optional[QdrantClient] = None
_qdrant_lock = Lock()


def get_qdrant_client(url: str) -> QdrantClient:
    """Get or create a reusable QdrantClient (singleton, thread-safe)."""
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
    with _qdrant_lock:
        if _qdrant_client is None:
            _qdrant_client = QdrantClient(url=url)
    return _qdrant_client


def reset_qdrant_client() -> None:
    """Reset singleton (useful for testing)."""
    global _qdrant_client
    with _qdrant_lock:
        _qdrant_client = None
