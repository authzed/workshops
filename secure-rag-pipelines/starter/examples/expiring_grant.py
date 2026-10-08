"""Grant `dana` a short-lived viewer grant on a document, to watch it expire.

Part 4b reference. Requires a schema that includes `use expiration` and a
`temp_viewer: user with expiration` relation on `document` (see 4-smaller-features.md).
"""
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.protobuf.timestamp_pb2 import Timestamp
from authzed.api.v1 import (
    WriteRelationshipsRequest, RelationshipUpdate, Relationship,
    ObjectReference, SubjectReference,
)

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agentic_rag.grpc_helpers import create_insecure_spicedb_client


def expiry_from_now(seconds: int) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(datetime.now(timezone.utc) + timedelta(seconds=seconds))
    return ts


def grant_temp_view(user: str, doc_id: str, seconds: int):
    client = create_insecure_spicedb_client(
        os.getenv("SPICEDB_ENDPOINT", "localhost:50051"),
        os.getenv("SPICEDB_TOKEN", "devtoken"),
    )
    client.WriteRelationships(WriteRelationshipsRequest(updates=[
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="document", object_id=doc_id),
                relation="temp_viewer",
                subject=SubjectReference(object=ObjectReference(object_type="user", object_id=user)),
                optional_expires_at=expiry_from_now(seconds),
            ),
        )
    ]))
    print(f"Granted {user} temp view on {doc_id} for {seconds}s")


if __name__ == "__main__":
    grant_temp_view("dana", "engineering-architecture-001", 30)
