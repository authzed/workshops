"""Unit tests for the /query API (filter_mode + allowed_ids_count)."""

from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


def _fake_result(filter_mode):
    from langchain_core.documents import Document
    doc = Document(page_content="c", metadata={"doc_id": "engineering-guide-006", "title": "T"})
    return {
        "query": "q", "subject_id": "dana", "answer": "a",
        "retrieved_documents": [doc],
        "authorized_documents": [doc],
        "denied_count": 0, "retrieval_attempt": 1,
        "allowed_doc_ids": ["engineering-guide-006", "engineering-guide-007"] if filter_mode == "pre" else None,
    }


def test_query_accepts_filter_mode_and_reports_allowed_count():
    from api.main import app
    with patch("api.routes.run_agentic_rag_async", new=AsyncMock(side_effect=lambda **kw: _fake_result(kw["filter_mode"]))):
        client = TestClient(app)
        r = client.post("/api/query", json={"query": "q", "subject_id": "dana", "filter_mode": "pre"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["stats"]["allowed_ids_count"] == 2
