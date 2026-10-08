"""Authorization node — the deterministic security boundary."""

from langchain_core.messages import SystemMessage
from authzed.api.v1 import (
    CheckPermissionRequest,
    ObjectReference,
    SubjectReference,
)

from ..state import AgenticRAGState
from ..config import get_config
from ..logging_config import get_logger
from ..grpc_helpers import get_spicedb_client

logger = get_logger("nodes.authorization")

HAS_PERMISSION = 2  # LOOKUP_PERMISSIONSHIP_HAS_PERMISSION


async def authorization_node(state: AgenticRAGState) -> dict:
    """Keep only the documents the subject is allowed to view.

    This node ALWAYS runs and the agent cannot route around it. In pre-filter
    mode the retrieval step already restricted results to allowed documents, so
    this node is a pass-through; in post-filter mode it does the enforcing.
    """
    retrieved = state["retrieved_documents"]

    if state.get("filter_mode", "post") == "pre":
        return {
            "authorized_documents": retrieved,
            "denied_count": 0,
            "authorization_passed": len(retrieved) > 0,
            "messages": [
                SystemMessage(
                    content=f"Authorization (pre-filter): {len(retrieved)} documents already restricted"
                )
            ],
        }

    config = get_config()
    client = get_spicedb_client(config.spicedb_endpoint, config.spicedb_token)
    subject = SubjectReference(
        object=ObjectReference(object_type="user", object_id=state["subject_id"])
    )

    authorized = []
    denied_ids = []
    for doc in retrieved:
        request = CheckPermissionRequest(
            resource=ObjectReference(
                object_type="document", object_id=doc.metadata["doc_id"]
            ),
            permission="view",
            subject=subject,
        )
        response = client.CheckPermission(request)
        if response.permissionship == HAS_PERMISSION:
            authorized.append(doc)
        else:
            denied_ids.append(doc.metadata["doc_id"])

    logger.info(
        "Authorization results",
        extra={
            "subject_id": state["subject_id"],
            "authorized": len(authorized),
            "denied": len(denied_ids),
            "denied_doc_ids": denied_ids,
        },
    )
    return {
        "authorized_documents": authorized,
        "denied_count": len(denied_ids),
        "authorization_passed": len(authorized) > 0,
        "messages": [
            SystemMessage(
                content=f"Authorization: {len(authorized)}/{len(retrieved)} documents authorized"
            )
        ],
    }
