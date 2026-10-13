"""List every user who can view a document (LookupSubjects). Part 4.

The reverse of the pre-filter's LookupResources. Pre-filter asks "which documents
can this user see?"; this asks "who can see this document?", the question an
access review, or an audit after a leak, actually needs.
"""
import os
import sys

from dotenv import load_dotenv
from authzed.api.v1 import LookupSubjectsRequest, ObjectReference

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agentic_rag.grpc_helpers import create_insecure_spicedb_client


def who_can_view(doc_id: str) -> list[str]:
    """Return the sorted list of user ids that can view ``doc_id``."""
    client = create_insecure_spicedb_client(
        os.getenv("SPICEDB_ENDPOINT", "localhost:50051"),
        os.getenv("SPICEDB_TOKEN", "devtoken"),
    )
    users = []
    for resp in client.LookupSubjects(
        LookupSubjectsRequest(
            resource=ObjectReference(object_type="document", object_id=doc_id),
            permission="view",
            subject_object_type="user",
        )
    ):
        users.append(resp.subject.subject_object_id)
    return sorted(users)


if __name__ == "__main__":
    doc = sys.argv[1] if len(sys.argv) > 1 else "hr-policy-001"
    print(f"Users who can view {doc}:")
    for u in who_can_view(doc):
        print(f"  - {u}")
