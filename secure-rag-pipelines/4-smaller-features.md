# Part 4: Smaller features

Two short, standalone features to round things out. First, collapse that per-document loop into a single call. Then, grants that clean up after themselves.

## (a) One call for many documents: CheckBulkPermissions

The post-filter node you wrote in Part 2 calls `CheckPermission` once per retrieved document. Five documents, five round trips. Fifty, fifty. SpiceDB has a better way: send all the ids in one `CheckBulkPermissions` request and get a result back per item.

In `agentic_rag/nodes/authorization_node.py`, swap the imports and replace the per-document loop (the `for doc in retrieved:` block) with one bulk call. The imports become:

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

Each entry in `resp.pairs` carries both the original request (`pair.request.resource.object_id`) and the result (`pair.item.permissionship`). Same decision, same Authorized/Denied split on the Bob query, one round trip instead of N. This is the production default, and it's what the upstream reference implementation uses throughout.

## (b) Grants that expire on their own: relationship expiration

Access is often temporary. A contractor for a week. An auditor who needs one document for a day. You could grant it and set a reminder to revoke it later with a cron job, but now you've got a second system that has to agree with SpiceDB about when "later" is, plus a window where the grant is still live after it should be gone. Someone always deploys at 59:58.

SpiceDB has a cleaner answer: pin an expiry to the relationship itself. An expired relationship is treated as if it were never written, evaluated server-side inside the same permission check. Nothing external has to poll for it, and there's no window.

### Schema edit

Expiration is opt-in. Edit `data/schema.zed`: add `use expiration` at the top, and add a `temp_viewer` relation that carries an expiration, unioned into `view`:

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

Notice we add a *new* relation (`temp_viewer`) instead of marking the existing `viewer` with expiration. That's deliberate. Narrowing an existing relation's allowed subject types while old-shaped relationships still exist forces a full datastore reset. Adding a brand-new relation doesn't; `WriteSchema` takes it cleanly. Re-apply the schema and relationships:

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

Give Dana a 30-second view of an engineering architecture doc she normally can't touch:

```bash
python -c "from examples.expiring_grant import grant_temp_view; grant_temp_view('dana', 'engineering-architecture-001', 30)"
```

There's no revoke step to remember and nothing to undo. The grant stops existing on schedule. That's the flexibility ReBAC gives you.

### One honest caveat about the in-memory datastore

SpiceDB evaluates expiration at the revision your check reads. Persistent datastores (Postgres, CockroachDB, Spanner) move that revision forward with wall-clock time, so an expired grant vanishes on its own the moment you re-check. The in-memory datastore this workshop runs only moves its revision forward when something is *written*. So a read-only "poll until it expires" loop can keep seeing a grant past its expiry until the next write nudges the clock.

You can watch the real behavior deterministically with a fully-consistent check and a tiny write to tick the clock:

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

def tick():  # any write moves the in-memory datastore's clock forward
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
tick(); print("after expiry:", can_view())         # False, expired and excluded
```

In production you'd drop the `tick()`; the datastore's clock moves on its own. The lesson lands the same either way: expiry is evaluated inside the permission check, so an expired grant was never a valid answer to begin with. No cron job can say that.

## Completion Milestone: Part 4

- [ ] Replaced the post-filter loop with a single `CheckBulkPermissions` call and confirmed identical results
- [ ] Added `use expiration` and a `temp_viewer: user with expiration` relation, then re-applied the schema
- [ ] Granted Dana a temporary view and watched it lapse (ticking the clock on the in-memory datastore)
- [ ] Can explain why expiry evaluated inside `CheckPermission` beats a cron job that deletes old relationships

Next: [Next steps](5-nextsteps.md).
