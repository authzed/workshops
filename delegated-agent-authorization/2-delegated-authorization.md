# Checkpoint 2 — Delegated Authorization

Checkpoint 1 ended with a working exploit: `authz.decide()` returned `ALLOWED` for everything, so
the agent could destroy production on request. Here you replace the stub with the real thing — a
SpiceDB schema that models *who an agent acts for*, and a `decide()` that turns a permission
question into one of three honest answers: the agent can do this itself, a human needs to say yes
first, or nobody involved is allowed to do this at all.

---

## ReBAC, in one paragraph

Most authorization systems people reach for first are **RBAC** — role-based access control. You
assign `alice` the role `deploy-engineer`, and a table somewhere says that role can deploy. It
works until you need "the person `alice` is deploying *for*" or "whoever approved this specific
change" — relationships between subjects and resources that a flat role list can't express without
exploding into a role per case.

**ReBAC** — relationship-based access control — models permissions as a graph instead: subjects,
resources, and the relations between them, with permissions defined as graph traversals over those
relations. This is the model Google published in 2019 as
[**Zanzibar**](https://research.google/pubs/pub48190/), the system that authorizes Google Drive,
Docs, and Calendar. SpiceDB is an open-source implementation of the same ideas. A permission check
in SpiceDB isn't a table lookup — it's "is there a path through the relationship graph from this
subject to this resource with this permission." That graph-walk is exactly what lets you model
delegation directly: an `agent` node with a `delegator` edge to the `user` it acts for, and
permissions that consider both.

---

## Write the schema

Open `schema.zed`. Right now it's the Checkpoint 1 stub — `environment` has no relations or
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

Walking it:

- **`user`** — an empty definition. Humans don't need relations of their own here; they're
  subjects that other things point to.
- **`agent { relation delegator: user }`** — this is the delegation edge. An agent doesn't hold
  authority on its own; it has exactly one relation, `delegator`, pointing at the human it acts
  for. Everything about "the agent may do only what its human could" flows from this one edge.
- **`environment`** — the resource being deployed to, approved for, or destroyed. It has four
  relations (`direct_deployer`, `agent_deployer`, `approver`, `destroyer`) and three permissions
  computed from them:
  - `permission deploy = direct_deployer + agent_deployer` — a **union**. A human wired up as
    `direct_deployer` can deploy, and separately, an agent wired up as `agent_deployer` can
    deploy. Same permission, two independent ways to earn it — that's the delegation: granting
    `agent_deployer` on an environment is what lets an *agent* deploy there without a human doing
    it directly.
  - `permission approve = approver` — a human-only relation. Nothing gives an agent `approve`,
    so agents can never approve their own grants.
  - `permission destroy = destroyer` — deliberately its own relation, not folded into `deploy`.
    Deploying a service and tearing down an entire environment are different levels of
    consequence, so they get different permissions with different holders.

Notice what's *not* here: nothing grants `agent_deployer` or `destroyer` to anyone yet. The schema
defines what delegation and destruction *mean*; the relationships you write next decide who
actually has them.

---

## Seed the delegation graph

```bash
python bootstrap.py
```

`bootstrap.py` writes this `schema.zed` to SpiceDB, then writes the relationships that make the
graph mean something for this workshop:

- `alice` is `direct_deployer` on **both** `staging` and `production` — she can deploy either
  herself, right now, no agent involved.
- `alice` is `approver` on `production` — she's the one who can sign off on the agent's production
  requests.
- `sre_admin` is `destroyer` on **both** environments, and is the *only* one. Not even Alice can
  destroy — tearing down an environment is scoped to a separate role entirely.
- `goose_alice` (the agent) has `delegator: alice` — it acts for Alice specifically. `decide()`
  will read this edge to find out whose authority to fall back on.
- `goose_alice` is `agent_deployer` on `staging` only. That's the one delegated grant this
  checkpoint hands the agent directly — staging autonomy, nothing more.

Nobody made the agent `agent_deployer` on `production`, and nobody made it (or Alice) a
`destroyer` anywhere. Those gaps are intentional — they're what `decide()` is about to expose as
`NEEDS_APPROVAL` and `BLOCKED` instead of silently failing.

---

## Implement `decide()`

Open `authz.py`. The Checkpoint 1 stub ignored every argument and returned `ALLOWED`. Replace it
with the real three-way decision:

```python
async def decide(client, agent_id, permission, environment_id) -> AuthzResult:
    if await check(client, "agent", agent_id, permission, "environment", environment_id):
        return AuthzResult(Decision.ALLOWED,
            f"agent:{agent_id} holds delegated '{permission}' on environment:{environment_id}")
    delegator = await read_delegator(client, agent_id)
    if delegator and await check(client, "user", delegator, permission, "environment", environment_id):
        return AuthzResult(Decision.NEEDS_APPROVAL,
            f"agent:{agent_id} lacks '{permission}'; delegator user:{delegator} holds it — human approval required")
    return AuthzResult(Decision.BLOCKED,
        f"neither agent:{agent_id} nor its delegator may '{permission}' environment:{environment_id}")
```

`check()` and `read_delegator()` are already provided at the top of `authz.py` — one wraps
`CheckPermission`, the other reads the `agent#delegator` relationship straight off the graph. The
logic is a strict fallthrough, evaluated in this order:

1. **Does the agent itself hold the permission?** — `check(client, "agent", agent_id, permission,
   "environment", environment_id)` asks SpiceDB the same question `deploy = direct_deployer +
   agent_deployer` was built to answer: is there a path from `agent:goose_alice` to `deploy` on
   `environment:staging`? For staging, yes — `ALLOWED`, and the agent never has to ask anyone.
2. **If not, could the human it acts for do this?** — `read_delegator()` walks the `delegator`
   edge to find `alice`, then runs the identical check as `user:alice`. For production, Alice
   holds `deploy` directly (`direct_deployer`) but the agent doesn't — so this branch fires:
   `NEEDS_APPROVAL`. The agent isn't blocked outright, because its human unambiguously *could* do
   this; it's paused until that human says so explicitly.
3. **If neither holds it, `BLOCKED`.** — for `destroy` on any environment, the agent has no
   `agent_deployer`-style grant (there's no such relation for destroy in this schema, so `check`
   on the agent fails), and Alice isn't a `destroyer` either — only `sre_admin` is. Neither side
   of the delegation chain has the permission, so there's nothing to escalate to. `BLOCKED` is
   final for this call; no amount of retrying changes the answer without someone writing a new
   relationship.

Three inputs, one `CheckPermission`-shaped question asked at most twice, and every branch returns
a reason string that names exactly which relationship justified the answer.

---

## See the three-way decision

### The web UI

```bash
python web.py
```

Open `http://127.0.0.1:8000`. This is a small FastAPI front end — its own docstring says it plainly:
*"The front end holds no authorization logic of its own — what you see is exactly what SpiceDB
decides."* It turns your text into a tool call (`deploy(service, environment)` or
`destroy(environment)`) and hands off to the exact same `deploybot_server.do_deploy` /
`do_destroy` functions goose calls, which call your new `decide()` before touching anything. The
version numbers you see at first paint (`staging: checkout v3, payments v5`, `production: checkout
v2, payments v4`) come from `infra_state.json`, checked into the starter repo as the baseline the
UI resets to.

Try the three cases:

- **"Deploy checkout to staging"** → ✅ **ALLOWED**. The agent's own `agent_deployer` grant
  covers it; the version bumps immediately.
- **"Deploy checkout to production"** → ⏸️ **NEEDS APPROVAL**. The agent doesn't hold `deploy` on
  production, but Alice does — nothing is applied, and the reason names her as the delegator who'd
  have to sign off.
- **"Tear down production"** → 🚫 **BLOCKED**. Neither the agent nor Alice is a `destroyer` —
  only `sre_admin` is. Nothing to escalate to; production stays up.

Click **Approve prod · 10m** (or run the CLI directly, see below), then retry the production
deploy — it flips to ✅ **ALLOWED**. Nothing about `decide()` changed; the relationship graph did.

### `approve.py` — the human in the loop

```bash
python approve.py --approver alice --env production
```

Before writing anything, `approve.py` runs two checks of its own: is `alice` actually an
`approver` on `production`, and does her `delegator` relationship to the agent still hold
`deploy` there? Only if both pass does it write one relationship —
`environment:production#agent_deployer@agent:goose_alice` — the same relation your schema's
`deploy` permission already unions over. That single write is the entire "approval": no new code
path, no special-cased branch in `decide()`. The next `decide()` call for
`("goose_alice", "deploy", "production")` hits branch 1 straight away and returns `ALLOWED`,
because the graph now has a direct path.

### goose (optional, live-LLM path)

If you registered the `deploybot` extension in setup:

```bash
goose session
```

Drive the same three requests in natural language — "Deploy checkout to staging", "Deploy checkout
to production", "Tear down the production environment" — and watch the identical
✅ / ⏸️ / 🚫 verdicts come back, because goose is calling the same `deploybot_server.py` tools the
web UI calls, gated by the same `decide()`.

### Deterministic path

```bash
python scripts/verify.py --checkpoint 2
```

```
Verifying Checkpoint 2...
  ✅ agent deploy staging: got Decision.ALLOWED, want Decision.ALLOWED
  ✅ agent deploy production: got Decision.NEEDS_APPROVAL, want Decision.NEEDS_APPROVAL
  ✅ agent destroy production: got Decision.BLOCKED, want Decision.BLOCKED
  ✅ after approve: deploy production: got Decision.ALLOWED, want Decision.ALLOWED
PASS ✅
```

No LLM, no goose — this calls your `decide()` directly against a live SpiceDB, runs `approve.py`
in the middle, and checks the exact same four outcomes you just watched in the UI or goose.

---

## Why the check — not the prompt — is the boundary

Nothing in this checkpoint told the agent, in English, "you may deploy staging but not
production, and never destroy anything." There's no system-prompt instruction to argue with, talk
around, or forget three turns into a conversation. The agent's tool call runs through
`deploybot_server._decide_and_mutate`, which calls `decide()` before it ever touches
`infra_state.json` — and `decide()`'s answer is fully determined by `CheckPermission` calls
against a relationship graph the agent has no way to write to. Ask the same question a thousand
different ways, through goose or the web UI or a hand-written script, and you get the same
`ALLOWED` / `NEEDS_APPROVAL` / `BLOCKED` back every time, because the agent never gets to
*compute* the answer — it only ever receives one that SpiceDB already computed. That's the
difference between a guardrail that's a suggestion and one that's a boundary: the boundary doesn't
care what the model believes, only what the graph says.

---

## Completion Milestone: Checkpoint 2

- [ ] Wrote `schema.zed` — `agent`, `environment`, and the `deploy` / `approve` / `destroy`
      permissions
- [ ] Seeded the graph with `python bootstrap.py`
- [ ] Implemented the three-way `decide()` in `authz.py`
- [ ] `python scripts/verify.py --checkpoint 2` prints `PASS ✅`
- [ ] Saw all three decisions — `ALLOWED`, `NEEDS_APPROVAL`, `BLOCKED` — in the web UI and/or
      goose, and watched `approve.py` flip production to `ALLOWED`
- [ ] Can explain ReBAC in your own words, and why `agent { relation delegator: user }` is what
      makes delegation a graph edge instead of a special case in code

Next: [Checkpoint 3 — Time-bound and revocable](3-time-bound-and-revocable.md)
