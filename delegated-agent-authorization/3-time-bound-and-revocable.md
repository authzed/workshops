# Checkpoint 3 — Time-Bound and Revocable

Checkpoint 2 gave the agent a real grant: `goose_alice` is `agent_deployer` on `staging`, forever,
until someone edits the graph by hand. That's already better than ambient authority, but "forever"
is still a bigger blast radius than most delegation actually needs. An incident responder pulled in
at 2am should get staging access for the duration of the incident, not a standing grant nobody
remembers to revoke. Here you make that grant expire on its own, and give an operator a way to kill
it early.

---

## Temporary access for incident windows

The shape you want is: "this agent may deploy staging, but only for the next 60 minutes." Two ways
to build that:

- **A caveat**: SpiceDB lets you attach a boolean expression to a relationship (`agent_deployer:
  agent with expiry_check`) and pass in context like `now < grant_expiry` at check time. It works,
  but it's you re-deriving "is this timestamp in the past" by hand, on every check, forever.
- **Relationship expiration**: SpiceDB has a built-in `optional_expires_at` field on a
  relationship. You write the expiry once, at grant time, and `CheckPermission` treats an expired
  relationship as if it were never written. No caveat context to thread through, no expression to
  get subtly wrong.

Expiration wins here for a reason that matters beyond convenience: it's evaluated **server-side,
inside the same consistent snapshot as the rest of the check**. There's no window where a
just-expired grant still reads as valid because a caveat context object was stale, and no separate
process has to notice the expiry and act on it. SpiceDB's own datastore garbage-collects expired
relationships in the background. The grant simply stops existing, on schedule, without anything
external polling for it.

---

## Schema edit: opt in, then mark the relation

Two changes to `schema.zed`. First, expiration is an opt-in schema feature. Declare it at the top
of the file:

```zed
use expiration
```

Second, mark `agent_deployer` as a relation that can carry an expiration:

```zed
definition environment {
    relation direct_deployer: user
    relation agent_deployer: agent with expiration
    relation approver: user
    relation destroyer: user
    permission deploy  = direct_deployer + agent_deployer
    permission approve = approver
    permission destroy = destroyer
}
```

The diff is one line at the top of the file and one word — `with expiration` — on the
`agent_deployer` relation. `direct_deployer`, `approver`, and `destroyer` stay exactly as they
were: those grants are still meant to be standing, not temporary, so nothing about them changes.
`permission deploy = direct_deployer + agent_deployer` doesn't change either. The union doesn't
know or care that one side of it can expire. That's the point: expiration is a property of the
*relationship*, not a new code path `decide()` has to special-case.

---

## Update the seed

`bootstrap.py` already takes a `--window-minutes` flag and threads it into `seed()`. Checkpoint 2
left the actual staging grant unexpiring; this is where that gets fixed. Import
`expiry_from_now` from `authz` (it builds the protobuf `Timestamp` that `optional_expires_at`
expects) and pass it into the staging `agent_deployer` write:

```python
from authz import expiry_from_now
# ...
rel("environment", "staging", "agent_deployer", "agent", AGENT_ID,
    expires_at=expiry_from_now(window_minutes)),
```

`rel()` (in `relationships.py`) already accepts an `expires_at` keyword and threads it into
`optional_expires_at`. That plumbing was there from the start, waiting for the schema to allow it.
Now every `bootstrap.py` run grants staging autonomy for exactly `window_minutes` from *now*, not
forever.

---

## Update `approve.py`

The human-in-the-loop path needs the same fix. `approve.py` already takes `--minutes`
(default 10) and ignored it. Checkpoint 2's version wrote the grant with no expiry at all. Import
`expiry_from_now` alongside the checks it already runs, and carry it into the write:

```python
from authz import check, read_delegator, expiry_from_now
# ...
update = rel("environment", environment, "agent_deployer", "agent", agent_id,
             expires_at=expiry_from_now(minutes))
```

Now clicking **Approve prod · 10m** in the web UI writes a grant that expires 10 minutes later on
its own. No follow-up step, nothing to remember to undo. An approval that never expires was really
a standing grant with extra steps; this makes "approved for now" mean what it says.

---

## See expiry without waiting

Waiting out a 60-minute window to prove this works isn't worth your time, so the web UI gives you a
faster lever: **Grant staging · 30s**, a button that hands the agent a 30-second staging window you
can watch expire live.

> **Reset the datastore first, once.** You just changed `agent_deployer`'s allowed subject type
> from `agent` to `agent with expiration`. SpiceDB won't narrow a relation's allowed types while
> relationships in the old shape — the plain `agent` grants Checkpoint 2 seeded — still exist, so
> the first `bootstrap.py` run this checkpoint fails on `WriteSchema` before it ever gets to
> reseed. Reset the datastore once, then re-seed against the new schema:
>
> ```bash
> docker compose down -v && docker compose up -d --wait
> python bootstrap.py
> ```

Start the web UI (`python web.py`) and open `http://127.0.0.1:8000`. Click **Grant staging · 30s**.
The **grants** panel shows staging's card with a live countdown and a shrinking bar. Watch it hit
zero, then ask the agent to "deploy checkout to staging" — the one request that was unconditionally
✅ **ALLOWED** in Checkpoint 2 — and it now comes back ⏸️ **NEEDS APPROVAL** instead, with Alice
named as the delegator who'd have to approve it. Nothing about `decide()` changed. The agent's own
`agent_deployer` check on staging fails because the relationship it was reading simply isn't there
anymore, as far as SpiceDB is concerned: it expired on schedule, server-side, with nothing external
polling for it.

Now the other lever, instant revocation, for when you don't want to wait for even a 30-second window
to run out. Click **Revoke staging**. The `agent_deployer` relationship on `staging` is deleted
outright, and the staging card disappears from the panel on the next 5-second poll, because
`/api/state`'s `ReadRelationships` no longer returns the grant. Ask the agent to deploy staging
again and you get the identical ⏸️ **NEEDS APPROVAL**, the same outcome as letting the window lapse,
just on your schedule instead of the clock's. An operator who sees something wrong mid-incident
doesn't wait for a TTL; they click one button and the grant is gone on the very next check.

---

## Drive it with goose (optional)

If you're running the goose path, the same lever works in natural language. Click **Grant staging ·
30s** (or **Revoke staging**), then in a `goose session` ask it to "deploy checkout to staging."
Before the window runs out, ✅ **ALLOWED**; after it expires — or once you've revoked —
⏸️ **NEEDS APPROVAL**. goose is calling the same gated `deploy` tool, so it sees exactly what the
web UI sees.

---

## Why contingent evaluation beats a cron job

The obvious fix looks like this: keep the grant unexpiring, and run a cron job that deletes
`agent_deployer` relationships older than an hour. Don't. A cron-based cleanup means the
grant is *actually* valid — checkable, usable, real — for however long it takes the cron job to
notice and catch up, which is never zero. Someone deploys at minute 59:58 using a grant that's
"supposed to" be gone; whether that succeeds depends on scheduler jitter, not policy. You've also
now got a second system that has to run, has to not fail silently, and has to agree with SpiceDB
about what "expired" means. Two sources of truth for one fact.

Relationship expiration collapses that back to one. There's no janitor process to keep alive: the
expiry is evaluated *at check time*, inside the same call that's already asking "does this
relationship exist and hold." An expired grant isn't cleaned up later. It was never a valid answer
to begin with, the moment the clock passed `expires_at`. Garbage collection still runs in the
background to reclaim storage, but it's a housekeeping detail, not part of the authorization
decision. The boundary is exactly as tight as `CheckPermission` itself.

---

## Completion Milestone: Checkpoint 3

- [ ] Added `use expiration` to `schema.zed` and marked `agent_deployer: agent with expiration`
- [ ] Updated `bootstrap.py`'s staging seed to carry `expires_at=expiry_from_now(window_minutes)`
- [ ] Updated `approve.py`'s grant write to carry `expires_at=expiry_from_now(minutes)`
- [ ] Clicked **Grant staging · 30s**, watched the countdown hit zero, and saw the agent's staging
      autonomy drop to `NEEDS_APPROVAL` on its own — then **Revoke staging** do the same instantly
- [ ] Can explain why expiration evaluated inside `CheckPermission` beats a cron job that deletes
      old relationships

Next: [Checkpoint 4 — Relationship-based hierarchy](4-relationship-based-hierarchy.md)
