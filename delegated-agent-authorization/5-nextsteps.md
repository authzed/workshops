# Next Steps

We started the project with an agent that could destroy production on a whim. Now every call it
makes resolves through a relationship graph: delegated authority, a three-way decision, expiring
grants, and a hierarchy that suspends dependents automatically. This is what Authorization in the world of AI looks like.
What's left is scaling this — how the same shape holds up once you scale to many
agents across many resources.

---

## One schema, not one authorization system per resource

Nothing about `schema.zed` is specific to deploy agents. `agent { relation delegator: user }` is the
entire idea of delegation, expressed once as a graph edge — not a column on a table or logic a
second service re-derives. A new resource type (a database, a CI pipeline) reuses
`direct_deployer` / `agent_deployer` / `gated_by` or extends the pattern by a line or two; a new
agent is one `delegator` edge. The schema stays the single place authority is defined, instead of
`if user.role == "admin"` checks scattered across services.

## `CheckBulkPermissions` — asking about many resources at once

`decide()` asks one question at a time — right for a mutating call, where `deploy` and `destroy`
each act on one resource. But an agent with a bigger surface often needs *which of these N resources
may I touch?* — before it acts, or before a UI renders a list. Looping `CheckPermission` per
resource is N round trips with no shared snapshot; SpiceDB's `CheckBulkPermissions` answers a batch
of `(resource, permission, subject)` tuples in one consistent call. `deploybot`'s `list_environments`
(ungated here) is exactly that at scale: "of these N environments, which does this agent hold `view`
on." (Want *every* resource a subject can reach, with no candidate list? That's `LookupResources`.)

## Scaling ReBAC with SpiceDB

The SpiceDB you've been running is in-memory via Docker Compose. This works for a workshop or a proof of concept, but not for production, where you want a durable datastore and a deployment you can lean on. You've got three ways to get there:

- **SpiceDB, self-hosted (open source)** — run it yourself. You have full control, and it runs on your infrastructure and ops. Works if you're happy managing the database and have specific deployment requirements.
- **[AuthZed Cloud](https://authzed.com/products/authzed-cloud)** — managed, self-service, pay-as-you-go SpiceDB. Provision a permissions system on demand and get enterprise features like audit logging without running anything yourself. The easy on-ramp for startups and growing teams.
- **[AuthZed Dedicated](https://authzed.com/products/authzed-dedicated)** — a fully private, single-tenant deployment in the cloud provider and regions you choose, sold annually. For enterprises that need dedicated infrastructure and geographic or compliance guarantees while offloading the ops.

---

## Resources

- **SpiceDB documentation**: [authzed.com/docs](https://authzed.com/docs)
- **AuthZed Cloud**: [authzed.com/products/authzed-cloud](https://authzed.com/products/authzed-cloud)
- **Full reference implementation**: [Source Code here](https://github.com/sohanmaheshwar/goose-spicedb-delegation)
