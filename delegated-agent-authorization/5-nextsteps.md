# Next Steps

We started the project with an agent that could destroy production on a whim. Now every call it
makes resolves through a relationship graph: delegated authority, a three-way decision, expiring
grants, and a hierarchy that suspends dependents automatically. This is what Authorization in the world of AI looks like.
What's left is scaling this — how the same shape holds up once you scale to many
agents across many resources.

---

## One schema, not one authorization system per resource

Nothing about `schema.zed` is specific to deploy agents. `agent { relation delegator: user }` is
the entire idea of delegation, expressed once, as a graph edge: not a column on a `deploys` table or a separate microservice
that re-derives on its own. If you add a new resource type to the platform such as a database or a CI pipeline, you can reuse `direct_deployer` / `agent_deployer` / `gated_by` directly or extend the same pattern by a line or two. 

If you add a new agent it's just one `delegator` edge. You don't have to create a new permission system because the platform added new
resource types. The graph just gains one more kind of node.

That's the payoff of modeling authority as relationships instead of scattering `if user.role ==
"admin"` checks through the codebase: the schema is the single place authority is defined, and
every service that needs an answer asks the same graph the same kind of question.

## `CheckBulkPermissions` — asking about many resources at once

The `decide()` method in this workshop asks one question at a time: can this agent do *this* thing to *this*
environment. That's the right shape for a mutating call: `deploy` and `destroy` each act on one
resource. But an agent with a bigger surface area often needs a different question, one worth
asking before it decides what to do next or before a UI renders a list of options: *which of
these N resources may I touch at all?*

Looping a `CheckPermission` call per resource works, but it's N round trips to answer one
question, and nothing guarantees they're all evaluated against the same snapshot of the graph.
SpiceDB's `CheckBulkPermissions` RPC takes a batch of `(resource, permission, subject)` tuples and
answers all of them in a single call, against one consistent read. `deploybot`'s
`list_environments` (deliberately left ungated in this workshop) is exactly the tool that would
reach for this at scale: instead of "list every environment" as an unchecked read, it becomes "of
these N environments, which does this agent hold `view` on," answered in one round trip instead of
N. 

Note: If you don't already have the candidate list, and want *every* resource a subject can reach
rather than a filter over a known set, `LookupResources` is the streaming counterpart to reach for
instead.

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
