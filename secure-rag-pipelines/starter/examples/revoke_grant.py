"""Revoke a direct viewer grant on a document (on-demand revocation). Part 4.

Deleting the relationship is itself a write, so the next permission check reflects
it immediately, because the datastore's revision advances on the delete. That's
the contrast with expiring grants, which are revocation scheduled in advance.
"""
import os
import sys

from dotenv import load_dotenv
from authzed.api.v1 import (
    WriteRelationshipsRequest,
    RelationshipUpdate,
    Relationship,
    ObjectReference,
    SubjectReference,
)

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agentic_rag.grpc_helpers import create_insecure_spicedb_client


def revoke_view(user: str, doc_id: str):
    """Delete the direct ``viewer`` grant from ``user`` on ``doc_id``."""
    client = create_insecure_spicedb_client(
        os.getenv("SPICEDB_ENDPOINT", "localhost:50051"),
        os.getenv("SPICEDB_TOKEN", "devtoken"),
    )
    client.WriteRelationships(WriteRelationshipsRequest(updates=[
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_DELETE,
            relationship=Relationship(
                resource=ObjectReference(object_type="document", object_id=doc_id),
                relation="viewer",
                subject=SubjectReference(object=ObjectReference(object_type="user", object_id=user)),
            ),
        )
    ]))
    print(f"Revoked {user}'s viewer grant on {doc_id}")


if __name__ == "__main__":
    revoke_view("dana", "engineering-guide-006")
