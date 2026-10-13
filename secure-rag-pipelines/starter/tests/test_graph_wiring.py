"""Unit tests for graph wiring (prefilter entry + filter_mode plumbing)."""

import inspect


def test_run_async_has_filter_mode_default():
    from agentic_rag import graph as g
    sig = inspect.signature(g.run_agentic_rag_async)
    assert sig.parameters["filter_mode"].default == "post"


def test_run_sync_has_filter_mode_default():
    from agentic_rag import graph as g
    sig = inspect.signature(g.run_agentic_rag)
    assert sig.parameters["filter_mode"].default == "post"


def test_graph_has_prefilter_node():
    from agentic_rag.graph import build_agentic_rag_graph
    compiled = build_agentic_rag_graph()
    assert "prefilter" in compiled.get_graph().nodes
