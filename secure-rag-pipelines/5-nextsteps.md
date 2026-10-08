# Next steps

You've built an agentic RAG pipeline with a deterministic SpiceDB authorization boundary, in two shapes — **post-filter** (`CheckPermission` after retrieval) and **pre-filter** (`LookupResources` before retrieval) — plus bulk checks and self-expiring grants. Here's where to go from here.

---

## Adaptive mode — let the agent retry

You've been running with `max_attempts=1`, the clean path: `prefilter → retrieve → authorize → generate`.

Set `max_attempts > 1` and the agent gets a reason/retry loop. When authorization denies everything, instead of giving up it routes to the `reason` node (`agentic_rag/nodes/reasoning_node.py`), which sees how many docs were retrieved, authorized, and denied, decides what to try differently, and loops back to retrieve. The authorization check still runs on every attempt — the agent adapts its *search strategy*, not its *permissions*. There's no code path that skips the check.

---

## Pre-filter vs post-filter, in production

The two patterns you built aren't just a teaching exercise — the choice is real:

- **Pre-filter** when a subject sees a small slice of a large corpus (the contractor with 3 of 10,000 docs). One `LookupResources` call, no retrieve-then-discard, but the call's cost grows with how much the subject can see, and your vector store must support filtered queries.
- **Post-filter** when most users see most of the corpus. Simpler, and `CheckBulkPermissions` keeps it to a single round trip.

Nothing stops you from combining them, or switching per subject based on how much they can see.

---

## Go to production

The SpiceDB here is in-memory via Docker Compose — fine for a workshop, not for production, where you want a durable datastore (and, as you saw in Part 4, one whose revision tracks wall-clock so expiration just works). Three ways to get there:

- **SpiceDB, self-hosted (open source)** — run it yourself on your own infrastructure.
- **[AuthZed Cloud](https://authzed.com/products/authzed-cloud)** — managed, self-service, pay-as-you-go SpiceDB with enterprise features like audit logging.
- **[AuthZed Dedicated](https://authzed.com/products/authzed-dedicated)** — a fully private, single-tenant deployment in the cloud provider and regions you choose.

The [Picking a product](https://authzed.com/docs/authzed/guides/picking-a-product) guide walks through the trade-offs. Whichever you pick, your code doesn't change: point `SPICEDB_ENDPOINT` and `SPICEDB_TOKEN` at the new instance and the schema and checks map over directly.

One more production swap: this workshop embeds locally with **fastembed** so there's nothing to sign up for. In production you'd often reach for a hosted embedding model (OpenAI `text-embedding-3-small`, Cohere, Voyage). Embeddings are decoupled from both the vector store and the chat model, so it's a one-function change in `embed()` — keep the index and queries on the same model, and match the Qdrant collection's vector size to its output dimension.

Qdrant itself scales from this single container to a managed cluster ([Qdrant Cloud](https://qdrant.tech/)) with the same client code. Or swap it for pgvector, Weaviate, or any store with filtered search — the pre-filter only needs an "id in set" filter.

---

## Homework

1. **Add a new department and prove isolation.** Create a `legal` department with a user and some documents, write the relationships, and confirm `alice` (engineering) can't see them and your new user can't see engineering docs. The schema needs no changes — that's the point.
2. **Combine pre-filter with a caveat.** Add a SpiceDB caveat (e.g. access only during business hours) to a grant and thread the context through `LookupResources`. Watch the allowed set shrink and grow with the context.
3. **Measure the trade-off.** Give one user access to 3 of the 50 docs and another access to 45. Time the same query in pre- vs post-filter mode for each. The crossover point is the lesson.

---

## Resources

- **SpiceDB documentation**: [authzed.com/docs](https://authzed.com/docs)
- **AuthZed Cloud**: [authzed.com/products/authzed-cloud](https://authzed.com/products/authzed-cloud)
- **Sibling workshop — agentic RAG (post-filter deep-dive, Milvus)**: [github.com/authzed/workshops/tree/main/agentic-rag-authorization](https://github.com/authzed/workshops/tree/main/agentic-rag-authorization)
- **Conference talk — Secure RAG Pipelines**: [youtu.be/aeace8MDlhk](https://youtu.be/aeace8MDlhk)

---
