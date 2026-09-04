# Part 3 — Time-Bound and Revocable

Part 2 gave the agent a real grant: `goose_alice` is `agent_deployer` on `staging`, forever,
until someone edits the graph by hand. That's already better than ambient authority, but typically you need 
time-bound delegation. An incident responder pulled in at 2am should get staging access for the duration of the incident, not a permanent grant nobody
remembers to revoke. Here you make that grant expire on its own, and give an operator a way to kill
it early.

---

## Temporary access for incident windows

The shape you want is: "this agent may deploy staging, but only for the next 60 minutes." There are two ways
to build that:

- **A caveat**: SpiceDB lets you attach a boolean expression to a relationship (`agent_deployer:
  agent with expiry_check`) and pass in context like `now < grant_expiry` at check time. It works,
  but it's you re-deriving "is this timestamp in the past" by hand, on every check.

- **Relationship expiration**: SpiceDB has a built-in `optional_expires_at` field on a
  relationship. You write the expiry once, at grant time, and `CheckPermission` treats an expired
  relationship as if it were never written. 

Expiration is the preferred method as it's evaluated **server-side,
inside the same consistent snapshot as the rest of the check**. There's no window where a
just-expired grant still reads as valid because a caveat context object was stale, and no separate
process has to notice the expiry and act on it. SpiceDB's own datastore garbage-collects expired
relationships in the background. The grant simply stops existing, on schedule, without anything
external polling for it.

---

## Schema edit: opt in, then mark the relation

To add time-bound delegation, first make two changes to `schema.zed`. First, expiration is an opt-in schema feature. Declare it at the top
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

## Update the relationships

`bootstrap.py` already takes a `--window-minutes` flag and threads it into `seed()`. Part 2
left the actual staging grant unexpiring; this is where that gets fixed. Import
`expiry_from_now` from `authz` (it builds the protobuf `Timestamp` that `optional_expires_at`
expects) and pass it into the staging `agent_deployer` write:

```python
# Add this import at the top of bootstrap.py
from authz import expiry_from_now

# Add this line in seed() method
rel("environment", "staging", "agent_deployer", "agent", AGENT_ID,
    expires_at=expiry_from_now(window_minutes)),
```

`rel()` (in `relationships.py`) already accepts an `expires_at` keyword and threads it into
`optional_expires_at`. Now every `bootstrap.py` run grants staging autonomy for exactly `window_minutes` from *now*, not
forever.

---

## Update `approve.py`

The human-in-the-loop path needs the same fix. In `approve.py` import `expiry_from_now` alongside the checks it already runs, and carry it into the write:

```python
# Add this import at the top of approve.py
from authz import check, read_delegator, expiry_from_now

# Add this line in the approve() method
update = rel("environment", environment, "agent_deployer", "agent", agent_id,
             expires_at=expiry_from_now(minutes))
```

Now clicking **Approve prod · 10m** in the web UI writes a grant that expires 10 minutes later on
its own. There's no follow-up step or a step to undo.

---

## See expiry without waiting

The web UI has a **Grant staging · 30s** button that hands the agent a 30-second staging window you
can watch expire live.

> **Reset the datastore first, once.** You just changed `agent_deployer`'s allowed subject type
> from `agent` to `agent with expiration`. SpiceDB won't narrow a relation's allowed types while
> relationships in the old shape — the plain `agent` grants Part 2 seeded — still exist, so
> the first `bootstrap.py` run this part fails on `WriteSchema` before it ever gets to
> reseed. Reset the datastore once, then re-seed against the new schema:
>
> ```bash
> docker compose down -v && docker compose up -d --wait
> python bootstrap.py
> ```

Start the web UI (`python web.py`) and open `http://127.0.0.1:8000`. Click **Grant staging · 30s**.
The **grants** panel shows staging's card with a live countdown and a shrinking bar. Watch it hit
zero, then ask the agent to "deploy checkout to staging" — the one request that was unconditionally
✅ **ALLOWED** in Part 2 — and it now comes back ⏸️ **NEEDS APPROVAL**, with Alice named as the
delegator who'd have to approve it. `decide()` didn't change; the grant it was reading simply
expired, on schedule.

Now the other lever, instant revocation, for when you don't want to wait for even a 30-second window
to run out. Click **Revoke staging**. The `agent_deployer` relationship on `staging` is deleted
outright, and the staging card disappears from the panel on the next 5-second poll, because
`/api/state`'s `ReadRelationships` no longer returns the grant. Ask the agent to deploy staging
again and you get the identical ⏸️ **NEEDS APPROVAL**, the same outcome as letting the window lapse,
just on your schedule instead of the clock's. An operator who sees something wrong mid-incident
doesn't wait for a TTL; they click one button and the grant is gone on the very next check.

---

## Drive it with goose (optional)

Click **Grant staging · 30s** (or **Revoke staging**), then ask goose to "deploy checkout to
staging" in a `goose session` — ✅ before the window lapses, ⏸️ **NEEDS APPROVAL** after.

---

## Why not a cron job?

The obvious alternative — keep the grant forever and delete it later with a cron job — is an
anti-pattern. The grant stays *actually* valid until the job catches up (never zero: someone deploys
at 59:58 on a grant that's "supposed to" be gone), and you've added a second system that has to
agree with SpiceDB about what "expired" means. Relationship expiration collapses that to one: the
expiry is evaluated at check time, so an expired grant was never a valid answer to begin with.

---

## Completion Milestone: Part 3

- [ ] Added `use expiration` to `schema.zed` and marked `agent_deployer: agent with expiration`
- [ ] Updated `bootstrap.py`'s staging seed to carry `expires_at=expiry_from_now(window_minutes)`
- [ ] Updated `approve.py`'s grant write to carry `expires_at=expiry_from_now(minutes)`
- [ ] Clicked **Grant staging · 30s**, watched the countdown hit zero, and saw the agent's staging
      autonomy drop to `NEEDS_APPROVAL` on its own — then **Revoke staging** do the same instantly
- [ ] Can explain why expiration evaluated inside `CheckPermission` beats a cron job that deletes
      old relationships

Next: [Part 4 — Relationship-based hierarchy](4-relationship-based-hierarchy.md)
