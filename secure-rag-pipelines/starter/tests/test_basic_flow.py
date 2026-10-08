"""Full-graph integration tests for secure RAG.

These drive the whole graph through to generation, so they need live infra
(docker compose up + setup_environment) AND a working chat model (LLM_API_KEY).
Marked `integration`; they are skipped by default runs without infra/LLM.
"""

import pytest
from agentic_rag.graph import build_agentic_rag_graph

# Shipped starter leaks (stubs) and these drive the whole graph (needs an LLM).
# Unskip after you implement Part 2 (post-filter) and Part 3 (pre-filter).
pytestmark = pytest.mark.skip(reason="Full-graph enforcement implemented by the attendee in Parts 2-3 and needs an LLM — unskip after filling the stubs")


def _state(query, subject_id, max_attempts, filter_mode="post"):
    return {
        "query": query,
        "subject_id": subject_id,
        "filter_mode": filter_mode,
        "allowed_doc_ids": None,
        "max_attempts": max_attempts,
        "retrieval_attempt": 0,
        "messages": [],
        "reasoning": [],
        "retrieved_documents": [],
        "authorized_documents": [],
        "denied_count": 0,
        "authorization_passed": False,
        "answer": "",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_authorized_access():
    """An authorized user can access documents (post mode)."""
    graph = build_agentic_rag_graph()
    result = await graph.ainvoke(
        _state("What are our engineering best practices?", "alice", 3)
    )
    assert len(result["authorized_documents"]) > 0
    assert result["authorization_passed"] is True
    assert result["answer"] != ""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_denied_access():
    """An unauthorized user is denied cross-department documents (post mode)."""
    graph = build_agentic_rag_graph()
    result = await graph.ainvoke(
        _state("What are the HR policies and employee guidelines?", "bob", 3)
    )
    assert len(result["authorized_documents"]) == 0
    assert result["denied_count"] > 0
    assert result["answer"] != ""
    assert "access" in result["answer"].lower() or "permission" in result["answer"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prefilter_small_slice_for_contractor():
    """Pre mode: the contractor only ever retrieves documents she may view."""
    from agentic_rag.graph import run_agentic_rag_async
    result = await run_agentic_rag_async(
        query="engineering onboarding guide", subject_id="dana",
        max_attempts=1, filter_mode="pre",
    )
    ids = {d.metadata["doc_id"] for d in result["retrieved_documents"]}
    assert ids.issubset({
        "engineering-guide-006", "engineering-guide-007",
        "public-handbook-001", "public-handbook-002", "public-handbook-003",
        "public-policy-004", "public-policy-005",
    })
    assert result["denied_count"] == 0
