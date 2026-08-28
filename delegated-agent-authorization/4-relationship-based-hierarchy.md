# Checkpoint 4 — Relationship-Based Hierarchy

Checkpoint 3 made every grant time-bound and revocable, but it left each environment answering
for itself. Staging autonomy and production autonomy live as two unrelated facts in the graph —
revoking one has no opinion about the other. That's not how a real deploy pipeline works. If the
whole point of staging is to catch a bad build before it reaches production, then an agent that's
lost its staging privileges has lost the thing that made its production privileges trustworthy in
the first place. Here you make that dependency real: production's autonomy is *contingent* on
staging's, enforced by the graph, not by anyone remembering to check.

---

## Contingent authority — why RBAC can't express this

The policy you want is: "the agent may deploy production on its own only while it can also deploy
staging on its own." RBAC can only ever hear the first half of that sentence: "the agent has role
X." What you actually need is "the agent has role X *and* a second, independent fact about a
different resource currently holds." RBAC assigns roles to subjects and stops there — a role is a
static label, not a live query against another resource. To fake this
dependency in a role system you'd need a role that means "agent-with-current-staging-autonomy," and
you'd need to *maintain* it — write code somewhere that watches for staging revocation and
downgrades the production role in lockstep, by hand, every time. Miss one code path and the two
facts drift out of sync: production autonomy silently outlives the staging autonomy it was supposed
to depend on.

ReBAC doesn't need a synchronization job, because the dependency isn't a copy of a fact — it's a
graph traversal that reads the live fact every time. You add one relation that says "this
environment is gated by that one," and a permission that walks it. There's nothing to keep in sync,
because there's nothing duplicated to begin with.

---

## Schema edit: a relation and an intersection

Open `schema.zed`. Inside `definition environment`, add one relation and one permission —
`gated_by` and `agent_deploy` — then rewire `deploy` to go through it:

```zed
definition environment {
    relation direct_deployer: user
    relation agent_deployer: agent with expiration
    relation approver: user
    relation destroyer: user
    relation gated_by: environment
    permission agent_deploy = agent_deployer & gated_by->agent_deployer
    permission deploy = direct_deployer + agent_deploy
    permission approve = approver
    permission destroy = destroyer
}
```

Two new pieces, and one rewrite of a permission you already wrote in Checkpoint 2:

- **`relation gated_by: environment`** — an edge from one environment to another. This is new: every
  other relation on `environment` so far has pointed at a `user` or `agent`. `gated_by` points at
  another `environment` entirely — it's how one resource says "my autonomy answers to that resource
  over there."
- **`permission agent_deploy = agent_deployer & gated_by->agent_deployer`** — the payoff line. Read
  the right-hand side as two separate questions joined by `&`, an **intersection**: both must hold.
  - `agent_deployer` — does the agent hold *this* environment's own delegated grant? Same relation
    as before, checked the same way.
  - `gated_by->agent_deployer` — the **arrow**. `gated_by` is a relation, not a permission, so the
    arrow means: follow every `gated_by` edge from this environment to whatever environment it
    points at, and re-ask `agent_deployer` — the *relation*, not `deploy` — over there, for the same
    subject. It's a one-hop traversal to a different resource, evaluated fresh on every check.
  - Put together: the agent may `agent_deploy` here only if it holds *this* environment's own grant
    **and** it holds `agent_deployer` on whatever environment gates this one. `&` is what makes
    it contingent instead of additive — either side going empty collapses the whole permission to
    empty, immediately, without anyone deleting the other side.
- **`permission deploy = direct_deployer + agent_deploy`** — the Checkpoint 2 line was
  `direct_deployer + agent_deployer`; the agent's whole way in now runs through `agent_deploy`
  instead of the bare relation. A human's `direct_deployer` grant is untouched — Alice can still
  deploy either environment herself, gate or no gate. The gate only ever constrains the *agent's*
  path.

Now look at what the seed is about to wire up: staging's `gated_by` will point at *itself*, and
production's `gated_by` will point at *staging*. For staging, `agent_deploy` becomes
`agent_deployer & agent_deployer` on the same environment — redundant with itself, which is exactly
right, because staging is the base of the hierarchy; nothing gates it but its own grant. For
production, `agent_deploy` becomes `agent_deployer(production) & agent_deployer(staging)` — two
independent relationships, on two different resources, both required.

---

## Seed the hierarchy

Add two relationships to `bootstrap.seed()`, alongside the ones already there:

```python
rel("environment", "staging", "gated_by", "environment", "staging"),
rel("environment", "production", "gated_by", "environment", "staging"),
```

Re-run it:

```bash
python bootstrap.py
```

The graph now has an edge from `production` to `staging` and a self-edge on `staging`. Nothing
about `direct_deployer`, `approver`, or `destroyer` changes — the gate is scoped entirely to the
agent's delegated path, `agent_deploy`, which is exactly the piece `deploy` now includes instead of
the bare `agent_deployer` relation.

---

## See the cascade

Grant the agent both environments the way Checkpoint 2 and 3 taught you:

```bash
python approve.py --approver alice --env production
```

Staging is already autonomous from the seed; production just got its own `agent_deployer` write
from `approve.py`, same as always — nothing about `approve.py` changed. Confirm both are live, in
the web UI (`python web.py`) or by asking goose to deploy each environment: staging ✅ **ALLOWED**
from its standing grant, production ✅ **ALLOWED** from the approval you just ran. Two independent
relationships, both satisfying `agent_deploy` on their respective environments.

Now pull the base out from under it:

```bash
python revoke.py --env staging
```

`revoke.py` hasn't changed since Checkpoint 3 — it deletes exactly one relationship,
`environment:staging#agent_deployer@agent:goose_alice`, and nothing else. It does not touch
production. And yet: ask for "deploy checkout to production" again, and it comes back
⏸️ **NEEDS APPROVAL** — the same verdict as if someone had revoked production directly, except
nobody did. `agent_deploy` on production still needs `gated_by->agent_deployer`, that arrow still
points at staging, and staging's `agent_deployer` relationship is gone, so the intersection goes
empty, and `deploy` falls back to the delegator check, same as any other lost grant. One delete,
two environments affected, because the second one was never independent to begin with.

The web UI shows this precisely: production's grant card stays on screen but turns dashed, tagged
**"suspended · gated by staging"** — the relationship itself is untouched, only what it computes to
has changed. A system message spells out why: *"alice revoked the staging delegation — production
autonomy is gated by it, so it suspends too."*

Confirm it deterministically:

```bash
python scripts/verify.py --checkpoint 4
```

```
Verifying Checkpoint 4...
✅ Approved: agent:goose_alice may deploy environment:production
  ✅ with both grants: deploy production: got Decision.ALLOWED, want Decision.ALLOWED
✅ Revoked: agent:goose_alice agent_deployer on environment:staging
  ✅ cascade: deploy staging: got Decision.NEEDS_APPROVAL, want Decision.NEEDS_APPROVAL
  ✅ cascade: deploy production: got Decision.NEEDS_APPROVAL, want Decision.NEEDS_APPROVAL
PASS ✅
```

The first check approves production and confirms both environments are live. The second revokes
only staging and confirms *both* fall back to `NEEDS_APPROVAL` — the cascade, asserted the same way
every other checkpoint's behavior was: by calling `decide()` directly against a live SpiceDB, no UI
or LLM required.

---

## Suspend, not erase — why this is contingent evaluation

Look again at what `revoke.py --env staging` actually deleted:
`environment:staging#agent_deployer@agent:goose_alice`. That's one tuple. The relationship
`environment:production#agent_deployer@agent:goose_alice` — the one `approve.py` wrote — is still
sitting in the graph, completely untouched. `agent_deploy` on production went from `ALLOWED` to
`NEEDS_APPROVAL` without a single write touching production's own relationships. Nothing was
deleted there; a permission that used to evaluate `true` now evaluates `false`, because one of the
two facts it depends on changed underneath it.

That's the distinction worth sitting with: this is **evaluation**, not **deletion**. A cascading
delete — the RBAC-shaped fix, where revoking a base role fires code that goes and deletes every
dependent grant — would have to walk every environment gated by staging and remove their
`agent_deployer` relationships one by one, and it would have to get that walk exactly right or leave
orphaned grants behind. `gated_by->agent_deployer` doesn't walk anything at write time. It's read at
*check* time, against whatever the graph currently says, every single time — the same way expiration
in Checkpoint 3 didn't need a cron job to notice a grant had gone stale.

The proof is the revive. Re-grant staging — run `bootstrap.py` again, or write the relationship
directly — and, without touching production at all, `agent_deploy` on production goes straight back
to `ALLOWED`, for whatever's left of the window `approve.py` originally gave it. The production
relationship was never wrong; it was only ever asking a question whose answer depends on staging.
Suspend, not erase, is what lets a fact come back to life just by the thing it depends on coming
back — no re-approval, no re-run of `approve.py`, because the grant itself never went anywhere.

---

## Completion Milestone: Checkpoint 4

- [ ] Added `relation gated_by: environment`, `permission agent_deploy = agent_deployer &
      gated_by->agent_deployer`, and rewired `permission deploy = direct_deployer + agent_deploy`
      in `schema.zed`
- [ ] Seeded the hierarchy in `bootstrap.py` — staging gated by itself, production gated by staging
- [ ] Approved production, confirmed both environments `ALLOWED`, then revoked staging and watched
      production fall back to `NEEDS_APPROVAL` with no second delete
- [ ] Saw production's grant go dashed/"suspended" in the web UI while the underlying relationship
      stayed in the graph
- [ ] `python scripts/verify.py --checkpoint 4` prints `PASS ✅`
- [ ] Can explain why this is contingent evaluation rather than a cascading delete, and why RBAC
      can't express "this role's authority depends on that other role currently holding" without a
      role explosion and a synchronization job to keep it honest

Next: [Next steps](5-nextsteps.md)
