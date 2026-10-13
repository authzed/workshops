"""Unit tests for Qdrant client singleton."""

from unittest.mock import patch, MagicMock


def test_get_qdrant_client_returns_singleton():
    from agentic_rag.qdrant_client import get_qdrant_client, reset_qdrant_client
    reset_qdrant_client()
    with patch("agentic_rag.qdrant_client.QdrantClient") as mock_cls:
        mock_cls.return_value = MagicMock()
        c1 = get_qdrant_client("http://localhost:6333")
        c2 = get_qdrant_client("http://localhost:6333")
    assert c1 is c2
    mock_cls.assert_called_once_with(url="http://localhost:6333")


def test_reset_clears_singleton():
    from agentic_rag.qdrant_client import get_qdrant_client, reset_qdrant_client
    reset_qdrant_client()
    with patch("agentic_rag.qdrant_client.QdrantClient") as mock_cls:
        mock_cls.return_value = MagicMock()
        get_qdrant_client("http://localhost:6333")
        reset_qdrant_client()
        get_qdrant_client("http://localhost:6333")
    assert mock_cls.call_count == 2
