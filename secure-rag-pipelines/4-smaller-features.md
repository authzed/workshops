# Part 4: Smaller features

A few short, standalone features to round things out: collapse that per-document loop into a single call, grants that clean up after themselves, pulling a grant on demand, and answering "who can see this?" for an audit.

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

## (c) Pull a grant right now: on-demand revocation

Expiration is revocation you schedule in advance. Sometimes you need it *now*: a contractor is offboarded, a document gets reclassified, someone fat-fingered a share. That's a `DeleteRelationships` call. `examples/revoke_grant.py` deletes a direct viewer grant:

```python
from authzed.api.v1 import (
    WriteRelationshipsRequest, RelationshipUpdate, Relationship,
    ObjectReference, SubjectReference,
)

# ... inside revoke_view(user, doc_id):
RelationshipUpdate(
    operation=RelationshipUpdate.Operation.OPERATION_DELETE,
    relationship=Relationship(
        resource=ObjectReference(object_type="document", object_id=doc_id),
        relation="viewer",
        subject=SubjectReference(object=ObjectReference(object_type="user", object_id=user)),
    ),
)
```

Try it on Dana. In the UI (Pre-filter mode) she has a Pre-allowed count of 7, and `engineering-guide-006` is one of them. Revoke it:

```bash
python -c "from examples.revoke_grant import revoke_view; revoke_view('dana', 'engineering-guide-006')"
```

Re-run her query. Pre-allowed drops to 6 and `engineering-guide-006` is gone from her results. Note what you *didn't* have to do: there's no tick here, unlike the expiry demo. The delete is itself a write, so it moves the datastore's revision forward and the very next check sees it. On-demand revocation is instant on any datastore. (Re-run `python examples/setup_environment.py` to give Dana her grant back.)

To revoke department-based access instead of a one-off grant, you'd delete the membership relationship (`department:engineering#member@user:...`) rather than a document viewer. Same call, different relationship.

## (d) Who can see this document? LookupSubjects

The pre-filter answered "which documents can this user see?" with `LookupResources`. Flip it: "who can see *this* document?" That's `LookupSubjects`, and it's the question an access review, or an audit after a leak, actually asks. `examples/who_can_view.py`:

```python
from authzed.api.v1 import LookupSubjectsRequest, ObjectReference

for resp in client.LookupSubjects(
    LookupSubjectsRequest(
        resource=ObjectReference(object_type="document", object_id=doc_id),
        permission="view",
        subject_object_type="user",
    )
):
    print(resp.subject.subject_object_id)
```

Run it against a cross-department document:

```bash
python examples/who_can_view.py hr-policy-001
```

You'll get `finance_manager` and `hr_manager`: the HR department plus finance, which has `hr-policy-001` shared with it for budget planning. SpiceDB walked every relationship path that lands on `view`, including the ones through department membership, so you don't have to reason about the graph by hand. In a RAG system this is how you answer the uncomfortable post-incident question, "exactly who could the assistant have served this document to?", and how you sanity-check a sensitive document's audience before you ever embed it.

## Completion Milestone: Part 4

- [ ] Replaced the post-filter loop with a single `CheckBulkPermissions` call and confirmed identical results
- [ ] Added `use expiration` and a `temp_viewer: user with expiration` relation, then re-applied the schema
- [ ] Granted Dana a temporary view and watched it lapse (ticking the clock on the in-memory datastore)
- [ ] Can explain why expiry evaluated inside `CheckPermission` beats a cron job that deletes old relationships
- [ ] Revoked a grant on demand with `DeleteRelationships` and saw Dana's pre-filter set shrink immediately
- [ ] Listed every user who can view a document with `LookupSubjects`

Next: [Next steps](5-nextsteps.md).
