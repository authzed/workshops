# Next steps

You've got an agentic RAG pipeline with a deterministic SpiceDB boundary, in two shapes (post-filter and pre-filter), plus bulk checks and self-expiring grants. Here's where it goes next.

## Let the agent retry

You've been running with `max_attempts=1`, the clean path: `prefilter → retrieve → authorize → generate`.

Set `max_attempts > 1` and the agent gets a reason-and-retry loop. When authorization comes up empty, instead of giving up it routes to the `reason` node (`agentic_rag/nodes/reasoning_node.py`), which sees how many docs were retrieved, authorized, and denied, decides what to try differently, and loops back to retrieve. The authorization check still runs on every attempt. The agent gets to adapt its search strategy, never its permissions. There's no code path that skips the check, which is the whole point of putting it in a node.

## Pre-filter vs post-filter, for real

The two patterns you built aren't just a teaching exercise. The choice shows up in production.

Reach for pre-filter when a subject sees a sliver of a large corpus (the contractor with 3 of 10,000 docs). One `LookupResources` call, no retrieve-then-discard, though the call's cost grows with how much the subject can see, and your vector store has to support filtered queries.

Reach for post-filter when most users see most of the corpus. It's simpler, and `CheckBulkPermissions` keeps it to one round trip.

Nothing stops you from doing both, or switching per subject based on how much they can see.

## Go to production

The SpiceDB here runs in-memory via Docker Compose. Fine for a workshop, wrong for production, where you want a durable datastore (and, as Part 4 showed, one whose revision tracks wall-clock so expiration just works without a nudge). Three ways to get there:

- **SpiceDB, self-hosted (open source).** Run it yourself, on your own infrastructure.
- **[AuthZed Cloud](https://authzed.com/products/authzed-cloud).** Managed, self-service, pay-as-you-go SpiceDB, with enterprise features like audit logging.
- **[AuthZed Dedicated](https://authzed.com/products/authzed-dedicated).** A private, single-tenant deployment in the cloud provider and regions you choose.

The [Picking a product](https://authzed.com/docs/authzed/guides/picking-a-product) guide walks the trade-offs. Whichever you pick, your code doesn't change: point `SPICEDB_ENDPOINT` and `SPICEDB_TOKEN` at the new instance and the schema and checks come along as-is.

One more production swap. This workshop embeds locally with fastembed so there's nothing to sign up for. In production you'd often reach for a hosted embedding model (OpenAI `text-embedding-3-small`, Cohere, Voyage). Embeddings are decoupled from both the vector store and the chat model, so it's a one-function change in `embed()`. Keep the index and the queries on the same model, and match the Qdrant collection's vector size to its output dimension. Qdrant itself scales from this single container to a managed cluster ([Qdrant Cloud](https://qdrant.tech/)) with the same client code, or swap it for pgvector or Weaviate; the pre-filter only needs an "id in set" filter.

## Homework

1. **Add a department and prove isolation.** Create a `legal` department with a user and some documents, write the relationships, and confirm `alice` (engineering) can't see them and your new user can't see engineering docs. The schema needs no changes, which is the point.
2. **Combine pre-filter with a caveat.** Add a SpiceDB caveat (say, access only during business hours) to a grant and thread the context through `LookupResources`. Watch the allowed set grow and shrink with the context. Heads up: with a caveat, `LookupResources` can return `CONDITIONAL` results, so the prefilter node would need to inspect `permissionship`, not just collect every id.
3. **Measure the trade-off.** Give one user 3 of the 50 docs and another 45, then time the same query in pre- and post-filter mode for each. The crossover point is the lesson.

## Resources

- SpiceDB docs: [authzed.com/docs](https://authzed.com/docs)
- AuthZed Cloud: [authzed.com/products/authzed-cloud](https://authzed.com/products/authzed-cloud)
- Sibling workshop, the post-filter deep-dive on Milvus: [agentic-rag-authorization](https://github.com/authzed/workshops/tree/main/agentic-rag-authorization)
- Conference talk, Secure RAG Pipelines: [youtu.be/aeace8MDlhk](https://youtu.be/aeace8MDlhk)

The industry spent the last decade learning to scope access for human users. We're doing it again for AI pipelines, and the answer is the same: keep the decision in a system that was built to make it, not in the model.
