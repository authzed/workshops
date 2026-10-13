"""Integration test: Qdrant collection is populated. Requires docker infra + setup_environment."""
import os
import pytest
from qdrant_client import QdrantClient


@pytest.mark.integration
def test_documents_collection_populated():
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    assert client.collection_exists("Documents")
    count = client.count("Documents").count
    assert count == 50
    pts, _ = client.scroll("Documents", limit=1, with_payload=True)
    assert "doc_id" in pts[0].payload
