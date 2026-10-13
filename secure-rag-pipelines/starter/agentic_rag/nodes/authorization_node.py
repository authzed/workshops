"""Authorization node: the deterministic security boundary.

WORKSHOP STUB
-------------
Right now this node lets EVERYTHING through. It does no real permission
check, so every document retrieval returns is passed straight to the LLM,
including documents the user is not allowed to see. That is the data leak you
will observe in Part 1, and fix in Part 2.
"""

from langchain_core.messages import SystemMessage

from ..state import AgenticRAGState
from ..logging_config import get_logger

logger = get_logger("nodes.authorization")


async def authorization_node(state: AgenticRAGState) -> dict:
    """Keep only the documents the subject is allowed to view.

    This node ALWAYS runs and the agent cannot route around it.
    """
    retrieved = state["retrieved_documents"]

    # TODO(Part 2): Replace this pass-through with a real SpiceDB check.
    # As written, every retrieved document is treated as authorized. That's the bug.
    authorized = retrieved
    denied_count = 0

    return {
        "authorized_documents": authorized,
        "denied_count": denied_count,
        "authorization_passed": len(authorized) > 0,
        "messages": [
            SystemMessage(
                content=f"Authorization: {len(authorized)}/{len(retrieved)} documents authorized (STUB, no checks)"
            )
        ],
    }
