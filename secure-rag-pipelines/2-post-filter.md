# Part 2 — Secure it with post-filter

We'll make one code change to turn the leaking pipeline from Part 1 into one that enforces real access control. This is a check the agent can't skip, and no prompt-engineering trick gets past it.

**You need deterministic security checks in a probabilistic world.**

---

## The model is already loaded

When you ran `setup_environment.py` in setup, it wrote a SpiceDB schema into your local instance (`data/schema.zed`):

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

In plain terms: a user can `view` a document if they're a direct `viewer` or its `owner`. The interesting part is that `viewer` can be satisfied two ways — a specific user, or every `member` of a department (`department#member`). This is the power of **ReBAC**: Relationship-Based Access Control. Bob is a member of the sales department, so he inherits viewer access to every document that grants `viewer` to `department:sales#member`.

The access patterns this creates: department-based (every member sees their department's docs), cross-department (three docs shared for collaboration), individual exceptions (one-off grants), public (five docs granted to everyone), and the contractor `dana` (two engineering guides + public). The full set of writes is in `examples/setup_environment.py`.

---

## How a permission check works

SpiceDB answers one question at a time: *does this subject have this permission on this resource?*

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

`permissionship == 2` means `LOOKUP_PERMISSIONSHIP_HAS_PERMISSION` — SpiceDB traversed the relationship graph and found a path from the subject to the permission. Anything else is a denial. To see this against all 23 cases in the workshop's permission matrix, run `python scripts/verify_permissions.py`.

---

## Implement the authorization node

Open `agentic_rag/nodes/authorization_node.py`. Right now it has the two TODO lines that make `authorized = retrieved` and `denied_count = 0` — the bug from Part 1. Replace the **entire file** with this:

```python
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
```

The `pre` branch is a pass-through we'll rely on in Part 3 (there the prefilter already restricted retrieval, so re-checking here would be redundant work). The `post` path is the one that matters now: it calls `CheckPermission` once per retrieved document — at most 5 calls.

---

## Re-run the same query

The UI server runs with auto-reload, so the moment you save `authorization_node.py` it picks up your change. (If you'd stopped it, start it again from `starter/` with `python run_ui.py`.)

Back in the browser, with the mode still on **Post-filter**, run the exact same query — **Bob (Sales)**, *What are our microservices architecture patterns?* — and submit.

Watch what moves. Before, `engineering-architecture-002` sat under **Authorized** with Denied at 0. Now that same document drops into **Denied Documents**, tagged *"User 'bob' does not have permission to access this document"*, and the denied count climbs above zero. The **Answer** shifts too: the LLM is working only with what bob is allowed to read.

`engineering-architecture-001`, by contrast, will typically stay under **Authorized** for bob — that's the cross-department document explicitly shared with sales.

---

## The node is the right place, not the prompt

The authorization node is deterministic. It doesn't interpret or reason, and it doesn't get confused by a clever query. It runs a binary check against SpiceDB for every document, and SpiceDB either finds the permission path or it doesn't. It's a node in a graph the agent always executes — there's no branch that skips it, so the LLM only ever receives documents that already cleared the check. It *cannot* leak what it *never saw*.

Try to trick it: tell the pipeline that Bob joined Engineering. The checks are still enforced deterministically and your data is safe. Putting access control in a system prompt is an anti-pattern — a prompt can be bypassed by prompt injection.

One cost worth noting: this node calls `CheckPermission` once per document. Five docs, five round trips. We collapse that into a single call in Part 4.

---

## Completion Milestone: Part 2

- [ ] Replaced the pass-through stub with the real SpiceDB `CheckPermission` loop
- [ ] The `bob` / microservices query now moves `engineering-architecture-002` into Denied Documents
- [ ] Confirmed legitimate access (department, cross-department, exceptions, public) still works
- [ ] Can explain why enforcing access in the node — not the prompt — is the correct design

Next: [Part 3 — Pre-filter with LookupResources](3-pre-filter.md).
