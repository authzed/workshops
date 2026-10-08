# Part 4 — Smaller features

Two short, independent features that round out the authorization story: collapsing the post-filter loop into a single call, and grants that expire on their own.

---

## (a) One call for many documents — `CheckBulkPermissions`

The post-filter node you wrote in Part 2 calls `CheckPermission` once per retrieved document. Five documents, five round trips. Fifty, fifty. SpiceDB has `CheckBulkPermissions`: send all the document ids in one request, get back a result per item.

In `agentic_rag/nodes/authorization_node.py`, swap the imports and replace the per-document loop (the `for doc in retrieved:` block) with a single bulk call. The imports become:

```python
from authzed.api.v1 import (
    CheckBulkPermissionsRequest,
    CheckBulkPermissionsRequestItem,
    ObjectReference,
    SubjectReference,
)
```

And the loop becomes:

```python
items = [
    CheckBulkPermissionsRequestItem(
        resource=ObjectReference(object_type="document", object_id=doc.metadata["doc_id"]),
        permission="view",
        subject=subject,
    )
    for doc in retrieved
]
resp = client.CheckBulkPermissions(CheckBulkPermissionsRequest(items=items))

allowed_ids = {
    pair.request.resource.object_id
    for pair in resp.pairs
    if pair.item.permissionship == HAS_PERMISSION
}
authorized = [d for d in retrieved if d.metadata["doc_id"] in allowed_ids]
denied_ids = [d.metadata["doc_id"] for d in retrieved if d.metadata["doc_id"] not in allowed_ids]
```

Each entry in `resp.pairs` carries the original request (`pair.request.resource.object_id`) and the result (`pair.item.permissionship`). Same decision, same results as the loop — one round trip instead of N. Re-run the Bob / microservices query; the Denied/Authorized split is identical, the latency is lower.

> This is the production default. The upstream reference implementation uses `CheckBulkPermissions` throughout.

---

## (b) Grants that expire on their own — relationship expiration

Sometimes access should be temporary: a contractor pulled in for a week, an auditor granted a document for a day. You *could* grant it and remember to revoke it later with a cron job — but that's a second system that has to agree with SpiceDB about when "later" is, and there's always a window where the grant is still live after it should be gone. SpiceDB has a better answer: attach an expiry to the relationship itself. An expired relationship is treated as if it were never written, evaluated server-side inside the same permission check — nothing external has to poll for it.

### Schema edit

Expiration is an opt-in schema feature. Edit `data/schema.zed`: add `use expiration` at the top, and add a `temp_viewer` relation that carries an expiration, unioned into `view`:

```zed
use expiration

definition user {}

definition department {
    relation member: user
}

definition document {
    relation owner: user
    relation viewer: user | department#member
    relation temp_viewer: user with expiration
    relation department_doc: department

    permission view = viewer + owner + temp_viewer
    permission edit = owner
}
```

We add a **new** relation (`temp_viewer`) rather than marking the existing `viewer` with expiration. That matters: narrowing an existing relation's allowed subject types while relationships of the old shape still exist forces a datastore reset. Adding a brand-new relation doesn't — `WriteSchema` accepts it cleanly. Re-apply the schema and relationships:

```bash
python examples/setup_environment.py
```

### Grant a temporary view

`examples/expiring_grant.py` writes a `temp_viewer` grant with an `optional_expires_at` timestamp:

```python
from datetime import datetime, timedelta, timezone
from google.protobuf.timestamp_pb2 import Timestamp

def expiry_from_now(seconds: int) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(datetime.now(timezone.utc) + timedelta(seconds=seconds))
    return ts

# ... inside grant_temp_view(user, doc_id, seconds):
RelationshipUpdate(
    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
    relationship=Relationship(
        resource=ObjectReference(object_type="document", object_id=doc_id),
        relation="temp_viewer",
        subject=SubjectReference(object=ObjectReference(object_type="user", object_id=user)),
        optional_expires_at=expiry_from_now(seconds),
    ),
)
```

Grant Dana a 30-second view of an engineering architecture doc she normally can't see:

```bash
python -c "from examples.expiring_grant import grant_temp_view; grant_temp_view('dana', 'engineering-architecture-001', 30)"
```

Now query as **Dana** in the UI (Pre-filter mode) — `engineering-architecture-001` is in her allowed set. Wait for the window to lapse and it drops out, with no revoke step and no cron job. The grant simply stops existing, on schedule.

### A note on the in-memory datastore

SpiceDB evaluates expiration at the **revision** your check reads. Persistent datastores (Postgres, CockroachDB, Spanner) advance that revision with wall-clock time, so an expired grant disappears on its own the moment you re-check. The **in-memory** datastore this workshop runs advances its revision only when something is *written* — so a purely read-only "watch it expire" loop can keep seeing a grant past its expiry until the next write ticks the clock forward.

You can see the real behavior deterministically with a fully-consistent check and a tiny write to advance the clock:

```python
import time
from authzed.api.v1 import (
    CheckPermissionRequest, WriteRelationshipsRequest, RelationshipUpdate,
    Relationship, ObjectReference, SubjectReference, Consistency,
)
from agentic_rag.grpc_helpers import get_spicedb_client
from examples.expiring_grant import grant_temp_view

c = get_spicedb_client("localhost:50051", "devtoken")

def can_view():
    r = c.CheckPermission(CheckPermissionRequest(
        resource=ObjectReference(object_type="document", object_id="engineering-architecture-001"),
        permission="view",
        subject=SubjectReference(object=ObjectReference(object_type="user", object_id="dana")),
        consistency=Consistency(fully_consistent=True),
    ))
    return r.permissionship == 2

def tick():  # any write advances the in-memory datastore's clock
    c.WriteRelationships(WriteRelationshipsRequest(updates=[RelationshipUpdate(
        operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
        relationship=Relationship(
            resource=ObjectReference(object_type="document", object_id="public-handbook-001"),
            relation="viewer",
            subject=SubjectReference(object=ObjectReference(object_type="user", object_id="alice")),
        ),
    )]))

grant_temp_view("dana", "engineering-architecture-001", 3)
tick(); print("right after grant:", can_view())   # True
time.sleep(4)
tick(); print("after expiry:", can_view())         # False — expired, excluded
```

In production you wouldn't write the `tick()` — the datastore's clock moves on its own. The lesson is the same either way: expiry is evaluated *inside* the permission check, so an expired grant was never a valid answer to begin with.

---

## Completion Milestone: Part 4

- [ ] Replaced the post-filter loop with a single `CheckBulkPermissions` call and confirmed identical results
- [ ] Added `use expiration` + a `temp_viewer: user with expiration` relation and re-applied the schema
- [ ] Granted Dana a temporary view and watched it lapse (using a tick on the in-memory datastore)
- [ ] Can explain why expiration evaluated inside `CheckPermission` beats a cron job that deletes old relationships

Next: [Next steps](5-nextsteps.md).
