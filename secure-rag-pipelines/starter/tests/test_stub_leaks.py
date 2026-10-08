"""The shipped starter must leak: the authorization stub authorizes everything.

This is the Part 1 bug, pinned as a test so a well-meaning edit can't silently
"fix" the starter (which would remove the whole point of Parts 1-2). No infra or
LLM needed; it calls the node directly.
"""

import pytest
from langchain_core.documents import Document


@pytest.mark.asyncio
async def test_authorization_stub_authorizes_everything():
    from agentic_rag.nodes.authorization_node import authorization_node
    docs = [
        Document(page_content="x", metadata={"doc_id": "engineering-architecture-002", "title": "T"}),
        Document(page_content="y", metadata={"doc_id": "hr-policy-001", "title": "T2"}),
    ]
    # bob is in sales and may see neither doc, but the stub does no check.
    out = await authorization_node(
        {"subject_id": "bob", "filter_mode": "post", "retrieved_documents": docs}
    )
    assert len(out["authorized_documents"]) == 2  # the leak
    assert out["denied_count"] == 0


@pytest.mark.asyncio
async def test_prefilter_stub_returns_no_allow_list():
    from agentic_rag.nodes.prefilter_node import prefilter_node
    out = await prefilter_node({"subject_id": "dana", "filter_mode": "pre"})
    assert out["allowed_doc_ids"] is None  # no restriction -> pre mode also leaks
