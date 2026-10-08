"""Integration test validating relationship expiration (Part 4b).

Requires live SpiceDB (docker infra). No LLM needed. Writes an expiration-enabled
schema; the suite's final step / setup_environment restores the seed schema.

Note on the in-memory datastore: it advances its revision only on writes, and
SpiceDB evaluates expiration at the snapshot revision. So to *observe* an expiry
we (a) use fully_consistent reads and (b) perform a write to advance the clock
past the expiry before the final check. Persistent datastores (Postgres/CRDB/
Spanner) advance the revision with wall-clock, so no nudge is needed there.
"""
import os
import time
import pytest
from authzed.api.v1 import (
    WriteSchemaRequest, WriteRelationshipsRequest, RelationshipUpdate, Relationship,
    CheckPermissionRequest, ObjectReference, SubjectReference, Consistency,
)
from agentic_rag.grpc_helpers import create_insecure_spicedb_client
from examples.expiring_grant import grant_temp_view

HAS_PERMISSION = 2
DOC = "engineering-architecture-001"

SCHEMA_WITH_EXPIRATION = """use expiration

definition user {}

definition department {
    relation member: user
}

definition document {
    relation owner: user
    relation viewer: user | department#member
    relation temp_viewer: user with expiration
    relation department_doc: department

    permission view = viewer + owner + temp_viewer
    permission edit = owner
}"""


@pytest.mark.integration
def test_temp_grant_is_honored_then_expires():
    client = create_insecure_spicedb_client(
        os.getenv("SPICEDB_ENDPOINT", "localhost:50051"),
        os.getenv("SPICEDB_TOKEN", "devtoken"),
    )
    # NEW relation (temp_viewer), so WriteSchema succeeds without a datastore reset.
    client.WriteSchema(WriteSchemaRequest(schema=SCHEMA_WITH_EXPIRATION))

    def advance_clock():
        # Any write bumps the in-memory datastore revision (advances its clock).
        client.WriteRelationships(WriteRelationshipsRequest(updates=[RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="document", object_id="public-handbook-001"),
                relation="viewer",
                subject=SubjectReference(object=ObjectReference(object_type="user", object_id="alice")),
            ),
        )]))

    def can_view():
        r = client.CheckPermission(CheckPermissionRequest(
            resource=ObjectReference(object_type="document", object_id=DOC),
            permission="view",
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dana")),
            consistency=Consistency(fully_consistent=True),
        ))
        return r.permissionship == HAS_PERMISSION

    # A live grant (long expiry) is honored.
    grant_temp_view("dana", DOC, 300)
    advance_clock()
    assert can_view() is True

    # An expired grant is excluded from the check (TOUCH overwrites the expiry).
    grant_temp_view("dana", DOC, 1)
    time.sleep(2)
    advance_clock()  # advance the revision past the expiry
    assert can_view() is False
