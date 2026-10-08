"""Unit tests for the authorization node (enforcing + mode-aware)."""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


def _docs():
    return [
        Document(page_content="a", metadata={"doc_id": "d1", "title": "t1"}),
        Document(page_content="b", metadata={"doc_id": "d2", "title": "t2"}),
    ]


@pytest.mark.asyncio
async def test_pre_mode_is_passthrough():
    from agentic_rag.nodes.authorization_node import authorization_node
    out = await authorization_node(
        {"subject_id": "dana", "filter_mode": "pre", "retrieved_documents": _docs()}
    )
    assert len(out["authorized_documents"]) == 2
    assert out["denied_count"] == 0


@pytest.mark.asyncio
async def test_post_mode_denies_unpermitted():
    from agentic_rag.nodes.authorization_node import authorization_node
    fake = MagicMock()
    fake.CheckPermission.side_effect = [
        SimpleNamespace(permissionship=2),  # d1 allowed
        SimpleNamespace(permissionship=1),  # d2 denied
    ]
    with patch("agentic_rag.nodes.authorization_node.get_spicedb_client", return_value=fake):
        out = await authorization_node(
            {"subject_id": "bob", "filter_mode": "post", "retrieved_documents": _docs()}
        )
    assert [d.metadata["doc_id"] for d in out["authorized_documents"]] == ["d1"]
    assert out["denied_count"] == 1
