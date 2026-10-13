# Part 3: Pre-filter with LookupResources

Post-filter works. It also has a shape problem, and Dana is where you see it.

Dana's a contractor. She can read exactly two engineering guides plus the public docs, roughly 7 of the 50. In post-filter mode, when Dana asks a question we retrieve the top 5 matches and *then* throw away the ones she can't see. If her question lands near documents she has no access to, we fetch 5 and bin all 5. A wasted round trip, and the LLM gets nothing to work with.

Pre-filter flips the order. Ask SpiceDB which documents Dana may see first, then search only inside that set. The vector store never even considers a document she can't read.

## LookupResources asks the other question

Post-filter asks SpiceDB the same question once per document: can Dana see this one? Pre-filter asks a single, different question: which documents of this type can Dana see at all? That's `LookupResources`:

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

For Dana that streams back her ~7 ids. We hand that set to Qdrant as a filter so the search only ranks those documents.

## First, watch pre-filter leak too

Flip the UI's **Authorization mode** toggle to **Pre-filter**, pick **Dana (Contractor)**, and run a query. It leaks. Dana gets documents she shouldn't, because `prefilter_node.py` is still a stub returning `{"allowed_doc_ids": None}`, which means "no restriction," exactly like the authorize node back in Part 1. Let's fill it in.

## Implement the pre-filter node

Open `agentic_rag/nodes/prefilter_node.py` and replace the whole file with this:

```python
"""Pre-filter node: ask SpiceDB which documents the subject may view, BEFORE retrieval."""

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

    Returns allowed_doc_ids=None in post mode (a no-op); the authorize node enforces there.
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

The retrieval node already knows what to do with that list. It turns a non-empty `allowed_doc_ids` into a Qdrant payload filter:

```python
from qdrant_client.models import Filter, FieldCondition, MatchAny

query_filter = Filter(
    must=[FieldCondition(key="doc_id", match=MatchAny(any=allowed))]
)
```

Notice the filter keys off the payload field `doc_id`, not the Qdrant point id (point ids are integers; the human-readable id rides along in the payload). A structured, typed filter like this reads better than a stringly-typed query expression, and it's harder to get subtly wrong. One edge case is handled for you: if `allowed_doc_ids` comes back empty (the subject can see nothing), retrieval returns zero documents instead of quietly running an unfiltered search.

One thing to watch with pre-filter: it fills its k retrieval slots from the allowed set, so when a user has only one or two genuinely relevant documents, the leftover slots get padded with low-relevance docs they happen to be allowed to see, and that noise dilutes the answer. Retrieval guards against it with a relevance floor (`SCORE_THRESHOLD`, default 0.6): documents scoring below it aren't retrieved at all. Ask alice to "show me sales proposals" and you'll see why it matters, she has exactly one, so pre-filter returns that proposal plus one closely-related guide rather than padding the context with unrelated engineering memos. Tune the floor to your own corpus and embedding model.

## Re-run as Dana, then compare

Save the file (auto-reload picks it up). Mode on **Pre-filter**, run a query as **Dana**. Now only her documents are retrieved, the search never surfaces anything outside her slice, **Denied** is **0** because there was nothing to throw away, and a new stat appears: **Pre-allowed**, the number of ids `LookupResources` returned.

Now flip between **Post-filter** and **Pre-filter** on the same Dana query and watch the difference. Post-filter fetches 5, keeps a couple, denies the rest. Pre-filter fetches only what's allowed and denies nothing. Same answer, two different roads to it.

## Which one should you use?

Both are correct. They differ in where the work lands, so steel-man each before you pick.

Pre-filter puts the work up front: one `LookupResources` call (whose cost grows with how many documents the subject can see), and it needs a vector store that supports filtered queries, which Qdrant does. It wins when a subject can see only a sliver of a big corpus, the contractor with 3 documents out of 10,000. You never retrieve-then-discard.

Post-filter is simpler and puts the check at the tail: one `CheckPermission` per retrieved document. It wins when most users can see most of the corpus, with a few exceptions carved out.

If you're unsure: small slice of a large corpus, pre-filter; most users see most docs, post-filter.

## Completion Milestone: Part 3

- [ ] Flipped to Pre-filter and reproduced the leak with the prefilter stub
- [ ] Implemented `prefilter_node.py` with `LookupResources`
- [ ] Re-ran as Dana: only her documents retrieved, Denied 0, a Pre-allowed count shown
- [ ] Compared pre vs post on the same query and can explain the trade-off

Next: [Part 4: Smaller features](4-smaller-features.md).
