"""Unit tests for the pre-filter node."""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock


def _state(subject_id="dana", filter_mode="pre"):
    return {"subject_id": subject_id, "filter_mode": filter_mode}


@pytest.mark.asyncio
async def test_prefilter_post_mode_returns_none():
    from agentic_rag.nodes.prefilter_node import prefilter_node
    out = await prefilter_node(_state(filter_mode="post"))
    assert out["allowed_doc_ids"] is None


@pytest.mark.skip(reason="LookupResources implemented by the attendee in Part 3; unskip to verify your solution")
@pytest.mark.asyncio
async def test_prefilter_pre_mode_collects_resource_ids():
    from agentic_rag.nodes.prefilter_node import prefilter_node
    fake = MagicMock()
    fake.LookupResources.return_value = [
        SimpleNamespace(resource_object_id="engineering-guide-006"),
        SimpleNamespace(resource_object_id="engineering-guide-007"),
    ]
    with patch("agentic_rag.nodes.prefilter_node.get_spicedb_client", return_value=fake):
        out = await prefilter_node(_state())
    assert sorted(out["allowed_doc_ids"]) == ["engineering-guide-006", "engineering-guide-007"]


@pytest.mark.asyncio
async def test_prefilter_defaults_to_post_when_mode_absent():
    """A state missing filter_mode entirely must default to post (no restriction), not KeyError."""
    from agentic_rag.nodes.prefilter_node import prefilter_node
    out = await prefilter_node({"subject_id": "dana"})
    assert out["allowed_doc_ids"] is None
