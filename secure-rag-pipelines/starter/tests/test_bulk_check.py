"""Integration test validating the CheckBulkPermissions shape used in Part 4a.

Requires live SpiceDB (docker infra) + setup_environment. No LLM needed.
"""
import pytest
from authzed.api.v1 import (
    CheckBulkPermissionsRequest,
    CheckBulkPermissionsRequestItem,
    ObjectReference,
    SubjectReference,
)
from agentic_rag.grpc_helpers import create_insecure_spicedb_client

HAS_PERMISSION = 2


@pytest.mark.integration
def test_bulk_check_returns_per_item_results():
    client = create_insecure_spicedb_client("localhost:50051", "devtoken")
    subject = SubjectReference(object=ObjectReference(object_type="user", object_id="dana"))
    doc_ids = ["engineering-guide-006", "engineering-architecture-001"]
    items = [
        CheckBulkPermissionsRequestItem(
            resource=ObjectReference(object_type="document", object_id=d),
            permission="view",
            subject=subject,
        )
        for d in doc_ids
    ]
    resp = client.CheckBulkPermissions(CheckBulkPermissionsRequest(items=items))
    results = {pair.request.resource.object_id: pair.item.permissionship for pair in resp.pairs}
    assert results["engineering-guide-006"] == HAS_PERMISSION
    assert results["engineering-architecture-001"] != HAS_PERMISSION
