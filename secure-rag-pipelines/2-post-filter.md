# Part 2: Secure it with post-filter

One code change turns the leaking pipeline from Part 1 into one that enforces real access control. It's a check the agent can't skip, and no clever prompt gets around it. That's the point: in a probabilistic world, you still need a deterministic security check.

![Post-filter flow: the application embeds the query and retrieves from the vector DB, then checks each retrieved document against SpiceDB with CheckPermission before generating the answer](/secure-rag-pipelines/images/post-filter-flow.png)

## The model is already loaded

When you ran `setup_environment.py`, it wrote a SpiceDB schema into your local instance. Here's `data/schema.zed`:

```zed
definition user {}

definition department {
    relation member: user
}

definition document {
    relation owner: user
    relation viewer: user | department#member
    relation department_doc: department

    permission view = viewer + owner
    permission edit = owner
}
```

In plain terms: you can `view` a document if you're a direct `viewer` or the `owner`. The interesting bit is that `viewer` is satisfied two ways, a specific user *or* every `member` of a department (`department#member`). That's what ReBAC buys you. Bob is a member of the sales department, so he inherits viewer access to every document that grants `viewer` to `department:sales#member`, and nothing else.

That one line buys you a handful of access patterns: department members see their department's docs, three documents are shared across departments for collaboration, a few users get one-off exceptions, five public docs go to everyone, and the contractor `dana` gets exactly two engineering guides plus the public set. The full list of writes is in `examples/setup_environment.py`.

## How a permission check works

SpiceDB answers one question at a time: can this subject do this thing to this resource?

```python
from authzed.api.v1 import CheckPermissionRequest, ObjectReference, SubjectReference

request = CheckPermissionRequest(
    resource=ObjectReference(object_type="document", object_id=doc_id),
    permission="view",
    subject=SubjectReference(
        object=ObjectReference(object_type="user", object_id=user)
    ),
)
response = client.CheckPermission(request)
allowed = response.permissionship == 2  # HAS_PERMISSION
```

`permissionship == 2` is `LOOKUP_PERMISSIONSHIP_HAS_PERMISSION`: SpiceDB walked the relationship graph and found a path from the subject to the permission. Anything else is a no. Run `python scripts/verify_permissions.py` to see it answer all 23 cases in the workshop's permission matrix.

## Implement the authorization node

Open `agentic_rag/nodes/authorization_node.py`. Right now it has those two TODO lines that set `authorized = retrieved` and `denied_count = 0`, the bug from Part 1. Replace the whole file with this:

```python
"""Authorization node: the deterministic security boundary."""

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
```

The `pre` branch is a pass-through we'll lean on in Part 3, where the prefilter already narrowed retrieval and re-checking here would be wasted work. The `post` path is the one that matters today: one `CheckPermission` per retrieved document, at most 5 calls.

## Re-run the same query

The UI server auto-reloads, so the moment you save `authorization_node.py` your change is live. (Stopped it? Start it again from `starter/` with `python run_ui.py`.)

Back in the browser, mode still on **Post-filter**, run the same query: **Bob (Sales)**, *What are our microservices architecture patterns?* Submit.

Watch what moves. Before, `engineering-architecture-002` sat under Authorized with Denied at 0. Now it drops into **Denied Documents**, tagged *"User 'bob' does not have permission to access this document"*, and the denied count climbs. The **Answer** changes too, because the LLM only ever gets what bob is allowed to read. `engineering-architecture-001` usually stays under Authorized for bob, by the way, that's the cross-department doc shared with sales. The system isn't being stingy. It's being exact.

## Put the check in the node, not the prompt

The authorization node doesn't interpret anything. It doesn't reason, and it doesn't fall for a clever query. It runs a binary check against SpiceDB for every document, and SpiceDB either finds a path or it doesn't. It's a node the graph always runs, with no branch that skips it, so the LLM only ever receives documents that already cleared the check. It can't leak what it never saw.

Go ahead and try to trick it. Tell the pipeline Bob just joined engineering. The checks still hold, because they're reading relationships in SpiceDB, not sentences in a prompt. Access control in a system prompt is an anti-pattern: a prompt is a suggestion, and prompt injection is a thing.

One cost to flag: this node makes one call per document. Five docs, five round trips. Fifty docs, fifty. We fix that in Part 4.

## Completion Milestone: Part 2

- [ ] Replaced the pass-through stub with the real SpiceDB `CheckPermission` loop
- [ ] The `bob` / microservices query now moves `engineering-architecture-002` into Denied Documents
- [ ] Confirmed legitimate access still works (department, cross-department, exceptions, public)
- [ ] Can explain why enforcing in the node, not the prompt, is the correct design

Next: [Part 3: Pre-filter with LookupResources](3-pre-filter.md).
