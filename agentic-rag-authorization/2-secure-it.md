# Checkpoint 2 — Secure it with SpiceDB

One code change. That's all it takes to turn the leaking pipeline from Checkpoint 1 into one that enforces real access control — a check the agent can't route around, and no prompt-engineering trick gets past it.

---

## The model is already loaded

When you ran `setup_environment.py` in the setup module, it wrote a SpiceDB schema into your local instance. Here's what that schema actually says:

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

In plain terms: a user can `view` a document if they're a direct `viewer` on it, or if they're its `owner`. The interesting part is that `viewer` can be satisfied two ways — a specific user, or every `member` of a department (`department#member`). That second form is **ReBAC**: Relationship-Based Access Control. Access isn't just a flat list; it follows graph edges. Bob is a member of the sales department, so Bob inherits viewer access to every document that grants `viewer` to `department:sales#member`.

The four access patterns this creates:

- **Department-based**: Every department member can see their department's documents — the default pattern for all 45 non-public docs.
- **Cross-department**: Three documents are intentionally shared across departments for collaboration (`engineering-architecture-001` to sales, `sales-guide-005` to engineering, `hr-policy-001` to finance).
- **Individual exceptions**: Three specific users get one-off grants outside their department (`alice` gets `sales-proposal-001`, `bob` gets `engineering-guide-006`, `finance_manager` gets `hr-policy-002`).
- **Public**: Five documents (`public-handbook-*`, `public-policy-*`) are individually granted to all four users.

---

## The relationships are already written

`setup_environment.py` also wrote all the relationships into SpiceDB — you don't need to run it again. But it's worth seeing what that write side of the API looks like. Here's the snippet that makes alice a member of the engineering department:

```python
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
```

`OPERATION_TOUCH` is idempotent — write it once, write it a hundred times, the result is the same relationship. The full set of writes (all four department memberships, document viewers, cross-department grants, individual exceptions, and public access) is in `examples/setup_environment.py` if you want to walk through it.

---

## How a permission check works

SpiceDB answers one question at a time: *does this subject have this permission on this resource?* The API call is straightforward:

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

`permissionship == 2` means `LOOKUP_PERMISSIONSHIP_HAS_PERMISSION` — SpiceDB traversed the relationship graph and found a path from the subject to the permission. Anything else is a denial.

To see this against all 18 test cases in the workshop's permission matrix, run:

```bash
python scripts/verify_permissions.py
```

Every scenario — department access, cross-department, individual exceptions, and deliberate denials — is covered there. All 18 should pass before you proceed.

---

## Implement the authorization node

Open `agentic_rag/nodes/authorization_node.py` (from the `starter/` directory). Right now it has two TODO lines that make `authorized = retrieved` and `denied_count = 0` — the bug from Checkpoint 1. Replace the entire file with this:

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

HAS_PERMISSION = 2  # authzed permissionship: LOOKUP_PERMISSIONSHIP_HAS_PERMISSION


async def authorization_node(state: AgenticRAGState) -> dict:
    """Keep only the documents the subject is allowed to view.

    This node ALWAYS runs and the agent cannot route around it.
    """
    config = get_config()
    client = get_spicedb_client(config.spicedb_endpoint, config.spicedb_token)

    retrieved = state["retrieved_documents"]
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

The loop calls `CheckPermission` once per retrieved document — at most 5 calls, which is plenty for the workshop. If you're curious about the production optimization that collapses this into a single `CheckBulkPermissions` call, that's in Next Steps.

---

## Re-run the same query

Same one-liner from Checkpoint 1, from the `starter/` directory:

```bash
python -c "import asyncio; from agentic_rag.graph import run_agentic_rag_async; \
r=asyncio.run(run_agentic_rag_async('What are our microservices architecture patterns?', 'bob')); \
print('AUTHORIZED:', [d.metadata['doc_id'] for d in r['authorized_documents']]); \
print('DENIED:', r['denied_count'])"
```

Before (Checkpoint 1): `engineering-architecture-002` — a pure engineering document bob has no business seeing — showed up in `AUTHORIZED`. `DENIED: 0`.

After (this checkpoint): `engineering-architecture-002` is gone from `AUTHORIZED`. `DENIED` is greater than zero. The generated answer will note that some relevant information wasn't accessible, because the LLM is now working only with what bob is actually permitted to read.

`engineering-architecture-001`, by contrast, will still appear authorized for bob — that's a cross-department document explicitly shared with sales. That's not a leak; that's the permission matrix working correctly.

---

## Prove it across users

```bash
python examples/basic_example.py
```

The denial scenarios — alice being denied sales playbooks, hr_manager being denied finance reports, finance_manager being denied engineering architecture — now behave correctly. The legitimate access patterns (department-based, cross-department, individual exceptions, public) still work exactly as before.

`DENIED: 0` should never appear again for a cross-department query. If it does, something's wrong with the SpiceDB connection or the relationships weren't written correctly.

---

## The node is the right place — not the prompt

Here's the thing: the authorization node is deterministic. It doesn't interpret, it doesn't reason, it doesn't get confused by a clever query. It runs a binary check against SpiceDB for every document, and SpiceDB either finds the permission path or it doesn't.

More importantly, it's a node in a graph the agent always executes. There's no branch that skips it. The LLM only ever receives documents that have already cleared the permission check — which means it *cannot* leak what it *never saw*.

Putting access control in a system prompt is the alternative, and it doesn't hold up. An LLM can be convinced to ignore, reinterpret, or work around instructions. SpiceDB can't. AI can't secure AI.

---

## Completion Milestone: Checkpoint 2

- [ ] Replaced the pass-through stub with the real SpiceDB `CheckPermission` loop
- [ ] The `bob` / microservices query now returns `DENIED` > 0 and excludes `engineering-architecture-002`
- [ ] Legitimate access (department, cross-department, exceptions, public) still works correctly via `python examples/basic_example.py`
- [ ] Can explain why enforcing access in the node — not the prompt — is the correct design

Next: [Next Steps](3-nextsteps.md).
