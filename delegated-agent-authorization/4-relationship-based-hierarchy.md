# Part 4 — Relationship-Based Hierarchy

Part 3 made every grant time-bound and revocable, but it left each environment answering
for itself. Staging autonomy and production autonomy live as two unrelated facts in the graph —
revoking one has no opinion about the other. That's not how a real deploy pipeline works. 

If the whole point of staging is to catch a bad build before it reaches production, then an agent that's
lost its staging privileges has lost the thing that made its production privileges trustworthy in
the first place. Here you make that dependency real: production's autonomy is *contingent* on
staging's, enforced by the graph. ReBAC makes this pattern very straightforward.

---

## Contingent authority — why RBAC can't express this

The idea you want is: "the agent may deploy production on its own only while it can also deploy
staging on its own." RBAC can only ever hear the first half of that sentence: "the agent has role
X." What you actually need is "the agent has role X *and* a second, independent fact about a
different resource currently holds." 

ReBAC handles this natively: express the dependency as one relation plus a permission that walks it,
and every check falls into place. Hierarchies and nested permissions are cheap to compute.

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

Two new pieces, and one rewrite of a permission you already wrote in Part 2:

- **`relation gated_by: environment`** — an edge from one environment to another. This is new: every
  other relation on `environment` so far has pointed at a `user` or `agent`. `gated_by` points at
  another `environment` entirely — it's how one resource says "my autonomy answers to that resource
  over there."
- **`permission agent_deploy = agent_deployer & gated_by->agent_deployer`** — Read
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
- **`permission deploy = direct_deployer + agent_deploy`** — the Part 2 line was
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
# Add this to the seed() method in bootstrap.py
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

Start the web UI (`python web.py`) and grant the agent both environments the way Parts 2 and 3
taught you. Staging is already autonomous from the seed; click **Approve prod · 10m** to give
production its own `agent_deployer` write. 

Confirm both are live, in the web UI or by asking goose to deploy each
environment: staging ✅ **ALLOWED** from its standing grant, production ✅ **ALLOWED** from the
approval you just ran. Two independent relationships, both satisfying `agent_deploy` on their
respective environments.

Now pull the base out from under it by clicking **Revoke staging**.

That deletes exactly one relationship,
`environment:staging#agent_deployer@agent:goose_alice`, and nothing else. It does not touch
production. And yet: ask for "deploy checkout to production" again, and it comes back
⏸️ **NEEDS APPROVAL** — the same verdict as if someone had revoked production directly, except
nobody did. `agent_deploy` on production still needs `gated_by->agent_deployer`, that arrow still
points at staging, and staging's `agent_deployer` relationship is gone, so the intersection goes
empty, and `deploy` falls back to the delegator check, same as any other lost grant. One delete,
two environments affected, because the second one was never independent to begin with.

The web UI shows this precisely: production's grant card stays on screen but turns dashed, tagged
**"suspended · gated by staging"** — the relationship itself is untouched, only what it computes to
has changed. 

---

## Drive it with goose (optional)

With both grants live, ask goose to "deploy checkout to production" — ✅ **ALLOWED**. Click
**Revoke staging**, then ask again: ⏸️ **NEEDS APPROVAL**, even though you never touched production.

---

## Suspend, not erase

This isn't a cascading delete. Production's own grant
(`environment:production#agent_deployer@agent:goose_alice`, written by **Approve prod · 10m**) never
moved — `agent_deploy` just recomputed from `true` to `false` because one of the two facts it
depends on is gone. Re-grant staging and production comes straight back, with no writes to
production. That's the difference between evaluating a permission and deleting a grant.

---

## Completion Milestone: Part 4

- [ ] Added `relation gated_by: environment`, `permission agent_deploy = agent_deployer &
      gated_by->agent_deployer`, and rewired `permission deploy = direct_deployer + agent_deploy`
      in `schema.zed`
- [ ] Seeded the hierarchy in `bootstrap.py` — staging gated by itself, production gated by staging
- [ ] Clicked **Approve prod · 10m**, confirmed both environments `ALLOWED`, then clicked
      **Revoke staging** and watched production fall back to `NEEDS_APPROVAL` with no second delete
- [ ] Saw production's grant go dashed/"suspended" in the web UI while the underlying relationship
      stayed in the graph
- [ ] Can explain why this is contingent evaluation rather than a cascading delete, and why RBAC
      can't express "this role's authority depends on that other role currently holding" without a
      role explosion and a synchronization job to keep it honest

Next: [Next steps](5-nextsteps.md)
