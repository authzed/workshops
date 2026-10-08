"""Test fixtures for secure RAG tests."""

import os
import pytest
from agentic_rag.grpc_helpers import create_insecure_spicedb_client


@pytest.fixture
def qdrant_client():
    """Create a QdrantClient for tests (imported lazily so collection never needs the driver)."""
    from qdrant_client import QdrantClient

    return QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


@pytest.fixture
def spicedb_client():
    """Create SpiceDB client for tests."""
    return create_insecure_spicedb_client("localhost:50051", "devtoken")


@pytest.fixture
def sample_state():
    """Create sample state for testing."""
    return {
        "query": "Test query",
        "subject_id": "alice",
        "filter_mode": "post",
        "allowed_doc_ids": None,
        "max_attempts": 3,
        "retrieval_attempt": 0,
        "messages": [],
        "reasoning": [],
        "retrieved_documents": [],
        "authorized_documents": [],
        "denied_count": 0,
        "authorization_passed": False,
        "answer": "",
    }
