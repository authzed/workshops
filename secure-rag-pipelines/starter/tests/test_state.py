"""Tests for AgenticRAGState schema."""


def test_state_has_filter_fields():
    from agentic_rag.state import AgenticRAGState
    ann = AgenticRAGState.__annotations__
    assert "filter_mode" in ann
    assert "allowed_doc_ids" in ann
