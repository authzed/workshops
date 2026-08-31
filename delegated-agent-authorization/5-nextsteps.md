# Next Steps

Four parts ago the agent could destroy production on a whim. Now every mutating call it
makes resolves through a relationship graph: delegated authority, a three-way decision, expiring
grants, and a hierarchy that suspends dependents automatically. That's the whole mechanism. What's
left is zooming out — how the same shape holds up once "one agent, two environments" becomes "many
agents, many resources, a real platform team on the other end of the pager."

---

## One schema, not one authorization system per resource

Nothing about `schema.zed` is specific to deploy agents. `agent { relation delegator: user }` is
the entire idea of delegation, expressed once, as a graph edge: not a column on a `deploys` table,
not a special case in a `DeployService.deploy()` method, not something a second microservice
re-derives on its own. Add a new resource type to the platform — a database, a feature-flag
service, a CI pipeline — and it either reuses `direct_deployer` / `agent_deployer` / `gated_by`
directly or extends the same pattern by a line or two. Add a new agent and it's one `delegator`
edge. Nobody stands up a tenth bespoke permission system because the platform grew a tenth
resource type; the graph just gains one more kind of node.

That's the payoff of modeling authority as relationships instead of scattering `if user.role ==
"admin"` checks through the codebase: the schema is the single place authority is defined, and
every service that needs an answer asks the same graph the same kind of question.

## `CheckBulkPermissions` — asking about many resources at once

`decide()` in this workshop asks one question at a time: can this agent do *this* thing to *this*
environment. That's the right shape for a mutating call: `deploy` and `destroy` each act on one
resource. But an agent with a bigger surface area often needs a different question, one worth
asking before it decides what to do next or before a UI renders a list of options: *which of
these N resources may I touch at all?*

Looping a `CheckPermission` call per resource works, but it's N round trips to answer one
question, and nothing guarantees they're all evaluated against the same snapshot of the graph.
SpiceDB's `CheckBulkPermissions` RPC takes a batch of `(resource, permission, subject)` tuples and
answers all of them in a single call, against one consistent read. `deploybot`'s
`list_environments` — deliberately left ungated in this workshop — is exactly the tool that would
reach for this at scale: instead of "list every environment" as an unchecked read, it becomes "of
these N environments, which does this agent hold `view` on," answered in one round trip instead of
N. (If you don't already have the candidate list, and want *every* resource a subject can reach
rather than a filter over a known set, `LookupResources` is the streaming counterpart to reach for
instead.)

## On-behalf-of vs. advisory enforcement

Every check in this workshop is **on-behalf-of, blocking enforcement**. `decide()`'s answer isn't
a suggestion; it's the gate itself: `deploybot_server.py` calls it *before* touching
`infra_state.json`, and an `ALLOWED`/`NEEDS_APPROVAL`/`BLOCKED` verdict is the only way anything
happens. The agent never gets to act first and ask forgiveness later.

That's the right default for anything that mutates state, but it's not the only mode worth
knowing. **Advisory enforcement** is when a check informs a decision without being the gate on
it — logged for audit, surfaced to a human reviewer, used to rank or filter results — while the
actual authority to act sits somewhere else. This workshop's own `list_environments` is an
advisory-shaped tool by design (its code comment says so directly: *"UNGATED in this workshop"*):
reads are lower stakes than a destroy, so it was left open to keep the parts focused on the
mutating path. A real platform team draws that line deliberately, tool by tool, action class by
action class — not by defaulting everything to advisory because blocking enforcement takes more
wiring.

## Where this workshop deliberately stopped short

Two things were left ungated on purpose, to keep every part's diff small and centered on one
new idea at a time:

- `list_environments` has no permission check. Every environment in `infra_state.json` is
  visible to every agent, always. A production version gates it behind a `view` permission and
  filters the listing to what the caller can actually see — exactly the `CheckBulkPermissions`
  shape described above.
- Revocation has no permission check. `revoke.py` — the helper behind the web UI's **Revoke**
  buttons — deletes a delegation without checking who's asking, so anyone who can reach the UI can
  pull any agent's access on any environment. A production version gates revocation behind a
  `manage` permission, so only an environment's own operators can pull an agent's access.

The [full reference solution](https://github.com/sohanmaheshwar/goose-spicedb-delegation) does
both. Its schema adds two permissions this workshop never defines:

```zed
permission view   = direct_deployer + approver + destroyer + agent_deploy
permission manage = direct_deployer
```

`view` includes `agent_deploy` deliberately — an agent that's lost its deploy autonomy (staging
revoked, cascade in effect) also loses visibility into the environment it can no longer touch, so
the same `gated_by` cascade from Part 4 hides a suspended environment from `list_environments`
as a side effect, with no extra code. `revoke.py` in the solution checks `manage` before it deletes
anything:

```python
if not await check(client, "user", revoker, "manage", "environment", environment):
    print(f"❌ Refused: user:{revoker} may not manage environment:{environment} (revocation requires an env operator)")
    return 1
```

Same pattern as everything you built in this workshop — one more permission, one more `check()`
call, no new architecture.

## Scaling ReBAC with SpiceDB

SpiceDB is an open-source implementation of the model Google described in its 2019
[Zanzibar paper](https://research.google/pubs/pub48190/) — the system that has authorized Google
Drive, Docs, and Calendar at global scale for years. The graph-walk you used for `gated_by` and
`delegator` in this workshop is the same primitive Zanzibar uses for Drive's folder-sharing
inheritance; deploy agents and shared documents turn out to be the same authorization problem
wearing different resource names.

Everything here ran against a single local `spicedb serve` container with a Postgres datastore.
That's fine for a workshop, not how you'd run this for a real platform. In production, SpiceDB is
typically deployed via the
[SpiceDB Operator](https://authzed.com/docs/spicedb/ops/operator) on Kubernetes, which manages
the cluster, datastore migrations, and rolling upgrades as a `SpiceDBCluster` resource instead of
a docker-compose file you manage by hand. If you want to go from "SpiceDB on my laptop" to "SpiceDB
as a platform dependency," that's the next thing worth spending 90 minutes on — and more self-guided
workshops, including this one, live at
[`github.com/authzed/workshops`](https://github.com/authzed/workshops).

---

That's the whole arc: one schema, one `decide()`, and a graph that scales by adding relationships
instead of adding code.
