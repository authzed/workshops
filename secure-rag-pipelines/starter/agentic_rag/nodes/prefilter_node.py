"""Pre-filter node — ask SpiceDB which documents the subject may view, BEFORE retrieval."""

from langchain_core.messages import SystemMessage
from authzed.api.v1 import (
    LookupResourcesRequest,
    ObjectReference,
    SubjectReference,
)

from ..state import AgenticRAGState
from ..config import get_config
from ..logging_config import get_logger
from ..grpc_helpers import get_spicedb_client

logger = get_logger("nodes.prefilter")


async def prefilter_node(state: AgenticRAGState) -> dict:
    """In pre mode, resolve the subject's viewable document ids via LookupResources.

    Returns allowed_doc_ids=None in post mode (no-op); the authorize node enforces there.
    """
    if state.get("filter_mode", "post") != "pre":
        return {"allowed_doc_ids": None}

    config = get_config()
    client = get_spicedb_client(config.spicedb_endpoint, config.spicedb_token)
    subject = SubjectReference(
        object=ObjectReference(object_type="user", object_id=state["subject_id"])
    )

    allowed = []
    for resp in client.LookupResources(
        LookupResourcesRequest(
            subject=subject,
            permission="view",
            resource_object_type="document",
        )
    ):
        allowed.append(resp.resource_object_id)

    logger.info(
        "Pre-filter resolved allowed documents",
        extra={"subject_id": state["subject_id"], "allowed_count": len(allowed)},
    )
    return {
        "allowed_doc_ids": allowed,
        "messages": [
            SystemMessage(content=f"Pre-filter: {len(allowed)} documents allowed for subject")
        ],
    }
