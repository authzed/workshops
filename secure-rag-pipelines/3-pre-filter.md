# Part 3 — Pre-filter with LookupResources

Post-filter works, but it has a shape problem. Consider **Dana**, a contractor. Dana can see exactly two engineering guides plus the public docs — about 7 of 50 documents. In post-filter mode, a query from Dana retrieves the top 5 semantically similar documents and *then* discards the ones she can't see. If her query is about something she has no access to, we retrieve 5 documents and throw all 5 away — a wasted round trip, and the LLM gets nothing useful.

**Pre-filter** flips the order: ask SpiceDB *which documents Dana may view* first, then search only within that set. The vector store never even considers a document she can't see.

---

## LookupResources: "what can this subject see?"

Post-filter asks SpiceDB one question per document ("can Dana see *this*?"). Pre-filter asks a single, different question: *which documents of this type can this subject view?* That's the `LookupResources` API:

```python
from authzed.api.v1 import LookupResourcesRequest, ObjectReference, SubjectReference

for resp in client.LookupResources(
    LookupResourcesRequest(
        subject=SubjectReference(
            object=ObjectReference(object_type="user", object_id="dana")
        ),
        permission="view",
        resource_object_type="document",
    )
):
    print(resp.resource_object_id)  # one allowed document id per response
```

For Dana this streams back her ~7 ids. We pass that set to Qdrant as a payload filter so the search only ranks those documents.

---

## First, watch pre-filter leak too

Flip the UI's **Authorization mode** toggle to **Pre-filter**, pick **Dana (Contractor)**, and run a query. It leaks — Dana gets documents she shouldn't. That's because `prefilter_node.py` is still a stub returning `{"allowed_doc_ids": None}` (no restriction), exactly like the authorize node was in Part 1. Let's fill it in.

---

## Implement the pre-filter node

Open `agentic_rag/nodes/prefilter_node.py` and replace the **entire file** with this:

```python
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
```

The retrieval node already knows what to do with that list — it's wired to turn a non-empty `allowed_doc_ids` into a Qdrant payload filter:

```python
from qdrant_client.models import Filter, FieldCondition, MatchAny

query_filter = Filter(
    must=[FieldCondition(key="doc_id", match=MatchAny(any=allowed))]
)
```

Note the filter keys off the **payload** field `doc_id`, not the Qdrant point id (point ids are integers). That structured, typed filter is a little cleaner than a raw query-string expression. One edge case is handled for you: if `allowed_doc_ids` is an *empty* list (the subject can see nothing), retrieval returns zero documents rather than running an unfiltered search.

---

## Re-run as Dana and compare

Save the file (auto-reload picks it up). With the mode on **Pre-filter**, run a query as **Dana**. Now:

- Only Dana's documents are retrieved — the search never surfaces anything outside her slice.
- **Denied** is **0** by construction. There's nothing to retrieve-then-discard.
- A new stat appears: **Pre-allowed** — the number of ids `LookupResources` returned.

Now toggle between **Post-filter** and **Pre-filter** on the same Dana query and watch the difference. Post-filter retrieves 5, authorizes a couple, denies the rest. Pre-filter retrieves only what's allowed, denies nothing. Same answer, different path to it.

---

## Which one should you use?

Both are correct — they differ in *where* the load lands.

- **Pre-filter** pushes work onto SpiceDB up front (one `LookupResources` call whose cost grows with how many documents the subject can see) and needs a vector store that supports filtered queries (Qdrant does). It wins when a subject can see only a small slice of a large corpus — a contractor with 3 documents out of 10,000, say. You never retrieve-then-discard.
- **Post-filter** is simpler and pushes the check to the tail end (one `CheckPermission` per retrieved document). It wins when most users can see most of the corpus with a few exceptions carved out.

If in doubt: small-slice-of-large-corpus → pre-filter; most-users-see-most-docs → post-filter.

---

## Completion Milestone: Part 3

- [ ] Flipped to Pre-filter and reproduced the leak with the prefilter stub
- [ ] Implemented `prefilter_node.py` with `LookupResources`
- [ ] Re-ran as Dana: only her documents retrieved, Denied 0, a Pre-allowed count shown
- [ ] A/B'd pre vs post on the same query and can explain the trade-off

Next: [Part 4 — Smaller features](4-smaller-features.md).
