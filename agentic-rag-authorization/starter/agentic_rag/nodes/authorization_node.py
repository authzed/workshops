"""Authorization node — the deterministic security boundary.

WORKSHOP STUB
-------------
Right now this node lets EVERYTHING through. It does no real permission
check, so every document semantic search returns is passed straight to the
LLM — including documents the user is not allowed to see. That is the data
leak you will observe in Checkpoint 1.

Your job in Checkpoint 2 (see 2-secure-it.md) is to replace the pass-through
below with a real SpiceDB permission check, so only authorized documents
reach the model. This node ALWAYS runs in the graph — the agent cannot
route around it.
"""

from langchain_core.messages import SystemMessage

from ..state import AgenticRAGState
from ..logging_config import get_logger

logger = get_logger("nodes.authorization")


async def authorization_node(state: AgenticRAGState) -> dict:
    """Filter retrieved documents by permission before generation.

    STUB: pass-through. Replace the two marked lines in Checkpoint 2.
    """
    retrieved = state["retrieved_documents"]

    # TODO(Checkpoint 2): Replace this pass-through with a real SpiceDB check.
    # As written, every retrieved document is treated as authorized — the bug.
    authorized = retrieved
    denied_count = 0

    logger.info(
        "Authorization (STUB — pass-through, no real check)",
        extra={
            "subject_id": state["subject_id"],
            "authorized": len(authorized),
            "denied": denied_count,
        },
    )

    return {
        "authorized_documents": authorized,
        "denied_count": denied_count,
        "authorization_passed": len(authorized) > 0,
        "messages": [
            SystemMessage(
                content=f"Authorization (stub): {len(authorized)}/{len(retrieved)} documents authorized"
            )
        ],
    }
