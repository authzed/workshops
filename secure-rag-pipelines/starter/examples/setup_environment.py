"""Initialize Qdrant and SpiceDB with sample data."""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from authzed.api.v1 import (
    WriteSchemaRequest,
    WriteRelationshipsRequest,
    Relationship,
    RelationshipUpdate,
    ObjectReference,
    SubjectReference,
)
from agentic_rag.grpc_helpers import create_insecure_spicedb_client

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from parse_documents import load_all_documents


def setup_spicedb():
    """Setup SpiceDB schema and relationships."""
    print("Setting up SpiceDB...")

    client = create_insecure_spicedb_client("localhost:50051", "devtoken")

    schema_path = os.path.join(os.path.dirname(__file__), "..", "data", "schema.zed")
    with open(schema_path) as f:
        schema = f.read()

    client.WriteSchema(WriteSchemaRequest(schema=schema))
    print("  ✅ Schema loaded")

    documents = load_all_documents()

    updates = [
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="engineering"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="alice")
                ),
            ),
        ),
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="sales"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="bob")
                ),
            ),
        ),
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="hr"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="hr_manager")
                ),
            ),
        ),
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="finance"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="finance_manager")
                ),
            ),
        ),
    ]

    for doc in documents:
        doc_id = doc['doc_id']
        dept = doc['department']

        if dept == "public":
            for user in ["alice", "bob", "hr_manager", "finance_manager", "dana"]:
                updates.append(
                    RelationshipUpdate(
                        operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                        relationship=Relationship(
                            resource=ObjectReference(object_type="document", object_id=doc_id),
                            relation="viewer",
                            subject=SubjectReference(
                                object=ObjectReference(object_type="user", object_id=user)
                            ),
                        ),
                    )
                )
        else:
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="document", object_id=doc_id),
                        relation="viewer",
                        subject=SubjectReference(
                            object=ObjectReference(object_type="department", object_id=dept),
                            optional_relation="member",
                        ),
                    ),
                )
            )

    cross_dept_docs = [
        ("engineering-architecture-001", "sales"),
        ("sales-guide-005", "engineering"),
        ("hr-policy-001", "finance"),
    ]

    for doc_id, additional_dept in cross_dept_docs:
        updates.append(
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="document", object_id=doc_id),
                    relation="viewer",
                    subject=SubjectReference(
                        object=ObjectReference(object_type="department", object_id=additional_dept),
                        optional_relation="member",
                    ),
                ),
            )
        )

    individual_exceptions = [
        ("alice", "sales-proposal-001"),
        ("finance_manager", "hr-policy-002"),
        ("bob", "engineering-guide-006"),
    ]

    for user, doc_id in individual_exceptions:
        updates.append(
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="document", object_id=doc_id),
                    relation="viewer",
                    subject=SubjectReference(
                        object=ObjectReference(object_type="user", object_id=user)
                    ),
                ),
            )
        )

    # Contractor: dana is in no department and gets a tiny, explicit slice of the
    # corpus. This makes the pre-filter "small slice of a large corpus" story vivid.
    contractor_docs = ["engineering-guide-006", "engineering-guide-007"]
    for doc_id in contractor_docs:
        updates.append(
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="document", object_id=doc_id),
                    relation="viewer",
                    subject=SubjectReference(
                        object=ObjectReference(object_type="user", object_id="dana")
                    ),
                ),
            )
        )

    client.WriteRelationships(WriteRelationshipsRequest(updates=updates))
    print(f"  ✅ {len(updates)} relationships configured")
    print("  Users and Departments:")
    print("    - alice: engineering department")
    print("    - bob: sales department")
    print("    - hr_manager: hr department")
    print("    - finance_manager: finance department")
    print("  Permission Patterns:")
    print(f"    - Department-based: All dept members access their dept docs")
    print(f"    - Cross-department: 3 collaboration documents")
    print(f"    - Individual exceptions: 3 special access grants")
    print(f"    - Public access: 5 documents accessible to all users")
    print("    - dana: contractor, 2 engineering guides + public only")


def setup_qdrant():
    """Setup Qdrant with sample documents using local fastembed embeddings."""
    print("\nSetting up Qdrant...")

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)

    if client.collection_exists("Documents"):
        client.delete_collection("Documents")
        print("  ✅ Dropped existing Documents collection")

    client.create_collection(
        collection_name="Documents",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print("  ✅ Documents collection created")

    documents = load_all_documents()
    print(f"  ✅ Loaded {len(documents)} documents from data/documents/")

    # Embed locally with fastembed (first run downloads the model, ~50MB).
    from agentic_rag.node_helpers import get_embedder

    print("  Embedding documents locally (first run downloads the model)...")
    embedder = get_embedder()
    embeddings = list(embedder.embed([doc["content"] for doc in documents]))

    points = [
        PointStruct(
            id=i,
            vector=embedding.tolist(),
            payload={
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "content": doc["content"],
                "department": doc["department"],
                "classification": doc["classification"],
            },
        )
        for i, (doc, embedding) in enumerate(zip(documents, embeddings))
    ]

    client.upsert(collection_name="Documents", points=points)
    print(f"  ✅ Inserted {len(points)} documents with embeddings")

    dept_counts = {}
    for doc in documents:
        dept = doc['department']
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    print("  Document Distribution:")
    for dept, count in sorted(dept_counts.items()):
        print(f"    - {dept}: {count} documents")


def main():
    """Run setup."""
    print("=" * 60)
    print("Agentic RAG with Authorization - Environment Setup")
    print("=" * 60)

    setup_spicedb()
    setup_qdrant()

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
