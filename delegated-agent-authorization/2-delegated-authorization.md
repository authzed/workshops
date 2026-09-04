# Part 2 — Delegated Authorization

Part 1 ended with `authz.decide()` returning `ALLOWED` for everything, so
the agent could destroy production on request. In this section, we replace the stub with the real thing — a
SpiceDB schema that models *who an agent acts for*, and a `decide()` that turns a permission
question into one of three answers: 

- the agent can do this
- a human needs to say yes first 
- nobody involved is allowed to do this at all.

---

## Permissions are a graph, not a table

Authorization has traditionally been solved with **Role-Based Access Control** (permissions via
roles like "admin"/"editor") or **Attribute-Based Access Control** (decisions from attributes like
department or geography). Both are too coarse for the delegation modern AI agents need. That's where
ReBAC comes in.

**ReBAC** — relationship-based access control — models permissions as a graph: subjects, resources,
and the relations between them, with permissions defined as traversals over those relations. It's
the model Google published as [**Zanzibar**](https://research.google/pubs/pub48190/) (the system
behind Drive, Docs, and Calendar); SpiceDB is an open-source implementation. Every check reduces to
one question:

> Is this **actor** allowed to perform this **action** on this **resource**?

Here's the graph you'll build in this part — objects joined by the relations you'll write, with the agent's delegated grant on `staging` highlighted:

![Relationship graph](/delegated-agent-authorization/images/fig2-relationship-graph.svg)
---

## Write the schema

In SpiceDB parlance, this actor and this resource are both Objects and this action is a Permission or Relation. Any usecase can be represented by using a schema that defines the different objects and the relations between them. 

Open `schema.zed`. Right now it's the Part 1 stub — `environment` has no relations or
permissions at all, so there's nothing for `decide()` to consult even if it wanted to. Replace the
whole file with:

```zed
definition user {}
definition agent {
    relation delegator: user
}
definition environment {
    relation direct_deployer: user
    relation agent_deployer: agent
    relation approver: user
    relation destroyer: user
    permission deploy  = direct_deployer + agent_deployer
    permission approve = approver
    permission destroy = destroyer
}
```

Before walking through it, two bits of SpiceDB syntax. A `relation name: type` line declares a
relation whose *subjects* are of that type — `agent_deployer: agent` reads as "an `agent` may be
wired up as an `agent_deployer` here," not "`agent_deployer` is an agent." And a **relation** differs
from a **permission**: a relation is a stored fact you write into the graph (an edge), while a
permission is computed from relations on every check (with `+`, and later `&` and `->`).

Let's go through each line:

- `user` is an empty definition. Humans don't need relations of their own here; they're
  subjects that other things point to.
- `agent { relation delegator: user }` is the delegation edge. An agent doesn't hold
  authority on its own; it has exactly one relation, `delegator`, pointing at the human it acts
  for. Everything about "the agent may do only what its human could" flows from this one edge.
- `environment` is the resource being deployed to, approved for, or destroyed. It has four
  relations (`direct_deployer`, `agent_deployer`, `approver`, `destroyer`) and three permissions
  computed from them:
  - `permission deploy = direct_deployer + agent_deployer` is a **union**. A human wired up as
    `direct_deployer` can deploy, and separately, an agent wired up as `agent_deployer` can
    deploy. Same permission, two independent ways to earn it — that's the delegation: granting
    `agent_deployer` on an environment is what lets an *agent* deploy there without a human doing
    it directly.
  - `permission approve = approver` is human-only — nothing gives an agent `approve`, so it can
    never approve its own grants.
  - `permission destroy = destroyer` is deliberately its own relation, not folded into `deploy`:
    tearing down an environment is a different level of consequence than deploying to one.

Notice what's *not* here: nothing grants `agent_deployer` or `destroyer` to anyone yet. The schema
defines what delegation and destruction *mean*; the relationships you write next decide who
actually has them.

---

## Seed the delegation graph

Every state change in a ReBAC system is a relationship write. Seed the ones this workshop needs:

```bash
python bootstrap.py
```

`bootstrap.py` writes this `schema.zed` to SpiceDB, then writes the relationships that make the
graph mean something for this workshop:

- `alice` is `direct_deployer` on **both** `staging` and `production` — she can deploy either
  herself, right now, no agent involved.
- `alice` is `approver` on `production`. She's the one who can sign off on the agent's production
  requests.
- `sre_admin` is `destroyer` on **both** environments, and is the *only* one. Not even Alice can
  destroy — tearing down an environment is scoped to a separate role entirely.
- `goose_alice` (the agent) has `delegator: alice`. It acts for Alice specifically. `decide()`
  will read this edge to find out whose authority to fall back on.
- `goose_alice` is `agent_deployer` on `staging` only. That's the one delegated grant this
  part hands the agent directly. Staging autonomy, nothing more.

Nobody made the agent `agent_deployer` on `production`, and nobody made it (or Alice) a
`destroyer` anywhere. Those gaps are intentional — they're what `decide()` is about to expose as
`NEEDS_APPROVAL` and `BLOCKED` instead of silently failing.

---

## Implement `decide()`

Open `authz.py`. The Part 1 stub ignored every argument and returned `ALLOWED`. Replace it
with the real three-way decision:

```python
async def decide(client, agent_id, permission, environment_id) -> AuthzResult:
    # 1. Agent holds the permission directly → autonomous action allowed
    if await check(client, "agent", agent_id, permission, "environment", environment_id):
        return AuthzResult(
            Decision.ALLOWED,
            f"agent:{agent_id} holds delegated '{permission}' on environment:{environment_id}"
        )

    # 2. Agent lacks permission — check if the delegator (human) could do it
    delegator = await read_delegator(client, agent_id)
    if delegator and await check(client, "user", delegator, permission, "environment", environment_id):
        return AuthzResult(
            Decision.NEEDS_APPROVAL,
            f"agent:{agent_id} lacks '{permission}'; "
            f"delegator user:{delegator} holds it — human approval required"
        )

    # 3. Neither agent nor delegator may perform this action
    return AuthzResult(
        Decision.BLOCKED,
        f"neither agent:{agent_id} nor its delegator may '{permission}' environment:{environment_id}"
    )
```

`check()` and `read_delegator()` are provided at the top of `authz.py`: one wraps `CheckPermission`,
the other reads the `agent#delegator` edge. It's a strict fallthrough — the agent's own grant
(branch 1), else its delegator's authority (branch 2 → `NEEDS_APPROVAL`), else `BLOCKED`. So staging
is `ALLOWED` (the agent holds it), production is `NEEDS_APPROVAL` (only Alice does), and any
`destroy` is `BLOCKED` (nobody in the chain is a `destroyer`). Every branch returns a reason string
naming the relationship that justified it.

---

## See the three-way decision in action

### The web UI

```bash
python web.py
```

Open `http://127.0.0.1:8000` and try the three cases — the front end holds no authorization logic of
its own; what you see is exactly what SpiceDB decides:

- **"Deploy checkout to staging"** → ✅ **ALLOWED**. The agent's own `agent_deployer` grant
  covers it; the version bumps immediately.
- **"Deploy checkout to production"** → ⏸️ **NEEDS APPROVAL**. The agent doesn't hold `deploy` on
  production, but Alice does — nothing is applied, and the reason names her as the delegator who'd
  have to sign off.
- **"Tear down production"** → 🚫 **BLOCKED**. Neither the agent nor Alice is a `destroyer` —
  only `sre_admin` is. Nothing to escalate to; production stays up.

Click **Approve prod · 10m**, then retry the production deploy — it flips to ✅ **ALLOWED**. 
Let's see how that works:

### Approve — the human in the loop

**Approve prod · 10m** is the approval path. Before writing anything, it runs two checks of its own: is `alice` actually an `approver` on
`production`, and does her `delegator` relationship to the agent still hold `deploy` there? Only if
both pass does it write one relationship:
`environment:production#agent_deployer@agent:goose_alice`. That's SpiceDB's notation for a
relationship — `resource#relation@subject` — and it reads: on `environment:production`, the subject
`agent:goose_alice` holds the `agent_deployer` relation. It's the same relation your schema's
`deploy` permission already unions over. 

That single write is the entire "approval": no new code path, no special-cased branch in `decide()`. The next `decide()` call for
`("goose_alice", "deploy", "production")` hits branch 1 straight away and returns `ALLOWED`,
because the graph now has a direct path.

### goose (optional)

```bash
goose session
```

Drive the same three requests in natural language — identical ✅ / ⏸️ / 🚫 verdicts, because goose
calls the same tools gated by the same `decide()`.

---

## Why the check — not the prompt — is the boundary

There's no system-prompt rule to argue with here. `decide()`'s answer is fully determined by
`CheckPermission` against a graph the agent can't write to — ask the same question a thousand ways,
through goose or the web UI or a script, and you get the same verdict, because the agent never
*computes* it, it only receives it.

---

## Completion Milestone: Part 2

- [ ] Wrote `schema.zed` — `agent`, `environment`, and the `deploy` / `approve` / `destroy`
      permissions
- [ ] Seeded the graph with `python bootstrap.py`
- [ ] Implemented the three-way `decide()` in `authz.py`
- [ ] Saw all three decisions — `ALLOWED`, `NEEDS_APPROVAL`, `BLOCKED` — in the web UI (and/or
      goose), and watched **Approve prod · 10m** flip production to `ALLOWED`
- [ ] Can explain ReBAC in your own words, and why `agent { relation delegator: user }` is what
      makes delegation a graph edge instead of a special case in code

Next: [Part 3 — Time-bound and revocable](3-time-bound-and-revocable.md)
