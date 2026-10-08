"""Integration test for the pre-filter path against live SpiceDB + Qdrant.

No LLM required — this drives prefilter_node + retrieval_node directly, which is
where the deterministic authorization behaviour lives. Requires docker infra up
and setup_environment to have run.
"""

import pytest

DANA_ALLOWED = {
    "engineering-guide-006", "engineering-guide-007",
    "public-handbook-001", "public-handbook-002", "public-handbook-003",
    "public-policy-004", "public-policy-005",
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prefilter_resolves_contractor_slice():
    from agentic_rag.nodes.prefilter_node import prefilter_node
    out = await prefilter_node({"subject_id": "dana", "filter_mode": "pre"})
    assert set(out["allowed_doc_ids"]) == DANA_ALLOWED


@pytest.mark.integration
def test_retrieval_respects_prefilter_slice():
    from agentic_rag.nodes.retrieval_node import retrieval_node
    state = {
        "query": "engineering onboarding guide and architecture",
        "subject_id": "dana",
        "filter_mode": "pre",
        "allowed_doc_ids": sorted(DANA_ALLOWED),
        "retrieval_attempt": 0,
    }
    result = retrieval_node(state)
    ids = {d.metadata["doc_id"] for d in result["retrieved_documents"]}
    assert ids  # retrieved something
    assert ids.issubset(DANA_ALLOWED)  # and only allowed docs


@pytest.mark.integration
def test_post_mode_retrieval_is_unfiltered():
    """Post mode (allowed_doc_ids=None) can surface docs dana may NOT see — that is
    exactly why post mode needs the authorize check afterwards."""
    from agentic_rag.nodes.retrieval_node import retrieval_node
    state = {
        "query": "microservices architecture patterns",
        "subject_id": "dana",
        "filter_mode": "post",
        "allowed_doc_ids": None,
        "retrieval_attempt": 0,
    }
    result = retrieval_node(state)
    ids = {d.metadata["doc_id"] for d in result["retrieved_documents"]}
    assert ids  # retrieved the top-k unfiltered
    assert not ids.issubset(DANA_ALLOWED)  # includes docs outside dana's slice
