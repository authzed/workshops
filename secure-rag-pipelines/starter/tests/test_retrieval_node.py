"""Unit tests for retrieval node (Qdrant)."""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


@pytest.fixture
def sample_state():
    return {
        "query": "engineering best practices",
        "subject_id": "alice",
        "filter_mode": "post",
        "allowed_doc_ids": None,
        "max_attempts": 1,
        "retrieval_attempt": 0,
        "messages": [], "reasoning": [],
        "retrieved_documents": [], "authorized_documents": [],
        "denied_count": 0, "authorization_passed": False, "answer": "",
    }


def _point(doc_id="doc-001"):
    return SimpleNamespace(
        payload={"doc_id": doc_id, "title": "T", "content": "C",
                 "department": "engineering", "classification": "internal"},
        score=0.9,
    )


def test_retrieval_returns_documents(sample_state):
    from agentic_rag.nodes.retrieval_node import retrieval_node
    with patch("agentic_rag.nodes.retrieval_node.get_qdrant_client") as gc, \
         patch("agentic_rag.nodes.retrieval_node.embed") as emb:
        emb.return_value = [0.1] * 384
        client = MagicMock()
        client.query_points.return_value = SimpleNamespace(points=[_point()])
        gc.return_value = client
        result = retrieval_node(sample_state)
    doc = result["retrieved_documents"][0]
    assert isinstance(doc, Document)
    assert doc.metadata["doc_id"] == "doc-001"
    assert result["retrieval_attempt"] == 1
    # No filter passed when allowed_doc_ids is None
    assert client.query_points.call_args.kwargs.get("query_filter") is None


def test_retrieval_applies_payload_filter(sample_state):
    from agentic_rag.nodes.retrieval_node import retrieval_node
    sample_state["allowed_doc_ids"] = ["engineering-guide-006", "engineering-guide-007"]
    with patch("agentic_rag.nodes.retrieval_node.get_qdrant_client") as gc, \
         patch("agentic_rag.nodes.retrieval_node.embed") as emb:
        emb.return_value = [0.1] * 384
        client = MagicMock()
        client.query_points.return_value = SimpleNamespace(points=[_point("engineering-guide-006")])
        gc.return_value = client
        retrieval_node(sample_state)
    qfilter = client.query_points.call_args.kwargs["query_filter"]
    # The filter targets the payload doc_id field
    assert qfilter.must[0].key == "doc_id"
    assert set(qfilter.must[0].match.any) == {"engineering-guide-006", "engineering-guide-007"}


def test_retrieval_empty_allowed_list_returns_nothing(sample_state):
    from agentic_rag.nodes.retrieval_node import retrieval_node
    sample_state["allowed_doc_ids"] = []
    with patch("agentic_rag.nodes.retrieval_node.get_qdrant_client") as gc, \
         patch("agentic_rag.nodes.retrieval_node.embed") as emb:
        emb.return_value = [0.1] * 384
        client = MagicMock()
        gc.return_value = client
        result = retrieval_node(sample_state)
    assert result["retrieved_documents"] == []
    client.query_points.assert_not_called()
