"""Pre-filter node.

WORKSHOP STUB
-------------
Right now this node returns no allow-list, so retrieval is never restricted and
pre-filter mode leaks exactly like the unsecured pipeline. You implement the real
LookupResources call in Part 3.
"""

from ..state import AgenticRAGState
from ..logging_config import get_logger

logger = get_logger("nodes.prefilter")


async def prefilter_node(state: AgenticRAGState) -> dict:
    """Resolve the subject's viewable document ids BEFORE retrieval.

    This node ALWAYS runs. In the stub it returns None (no restriction).
    """
    # TODO(Part 3): In pre mode, call SpiceDB LookupResources(view, document) and
    # return the list of allowed document ids here.
    return {"allowed_doc_ids": None}
