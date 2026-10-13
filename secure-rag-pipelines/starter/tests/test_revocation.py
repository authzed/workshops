"""Integration test for on-demand revocation (DeleteRelationships). Part 4c.

Requires live SpiceDB + setup_environment. No LLM needed. Uses a throwaway grant
on a document outside dana's canonical set, so it leaves the seed data unchanged.
"""
import pytest
from authzed.api.v1 import (
    WriteRelationshipsRequest, RelationshipUpdate, Relationship,
    CheckPermissionRequest, ObjectReference, SubjectReference, Consistency,
)
from agentic_rag.grpc_helpers import create_insecure_spicedb_client
from examples.revoke_grant import revoke_view

HAS_PERMISSION = 2
DOC = "engineering-architecture-002"  # not one of dana's normal grants


@pytest.mark.integration
def test_revocation_is_immediate():
    c = create_insecure_spicedb_client("localhost:50051", "devtoken")

    def can_view():
        return c.CheckPermission(CheckPermissionRequest(
            resource=ObjectReference(object_type="document", object_id=DOC),
            permission="view",
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dana")),
            consistency=Consistency(fully_consistent=True),
        )).permissionship == HAS_PERMISSION

    # Grant a throwaway viewer so dana's canonical 7-doc set is untouched.
    c.WriteRelationships(WriteRelationshipsRequest(updates=[RelationshipUpdate(
        operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
        relationship=Relationship(
            resource=ObjectReference(object_type="document", object_id=DOC),
            relation="viewer",
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dana"))))]))
    assert can_view() is True

    revoke_view("dana", DOC)
    # Immediate: the delete is a write, so the revision advances and the check
    # reflects it at once (no clock tick needed, unlike relationship expiration).
    assert can_view() is False
