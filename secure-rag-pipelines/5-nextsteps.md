# Next steps

You've got an agentic RAG pipeline with a deterministic SpiceDB boundary, in two shapes (post-filter and pre-filter), plus bulk checks and self-expiring grants. Here's where it goes next.

## Let the agent retry

You've been running with `max_attempts=1`, the clean path: `prefilter → retrieve → authorize → generate`.

Set `max_attempts > 1` and the agent gets a reason-and-retry loop. When authorization comes up empty, instead of giving up it routes to the `reason` node (`agentic_rag/nodes/reasoning_node.py`), which sees how many docs were retrieved, authorized, and denied, decides what to try differently, and loops back to retrieve. The authorization check still runs on every attempt. The agent gets to adapt its search strategy, never its permissions. There's no code path that skips the check, which is the whole point of putting it in a node.

## Three RAG-authorization patterns worth exploring

The workshop keeps retrieval deliberately simple. Three patterns show up the moment you take this to a real corpus.

**1. Over-fetch to recover post-filter recall.** You saw post-filter under-retrieve: ask Bob for microservices patterns and four of his five slots go to documents he can't see, leaving the LLM one document to work with. The fix is to over-fetch, retrieve `k x N` candidates, run the permission check, then keep the first `k` that survive. You trade a bigger retrieval and more permission checks for a full context window. `CheckBulkPermissions` keeps the extra checks to one round trip, so it's cheaper than it sounds. Pre-filter sidesteps the problem entirely, which is part of why it exists.

**2. Compose the permission filter with metadata filters.** Authorization isn't the only thing you filter on. You'll also want "only this department," "only the last 90 days," "only `confidential` and below." Because the pre-filter is already a Qdrant `Filter`, you just add more `FieldCondition`s next to the `doc_id` allow-list, and the vector search honors all of them at once. 

**3. Authorize at the chunk, not the document.** Real documents get split into chunks before embedding, and a single document often mixes a public summary with a confidential appendix. Carry a resource id onto each chunk (its own object, or the parent document's id) and run the permission check per chunk. The pipeline you built doesn't change shape; only the granularity of the `doc_id` you check does. This is where ReBAC earns its keep, because a chunk can inherit its document's grants through one relationship instead of being re-shared by hand.

## Go to production

The SpiceDB here runs in-memory via Docker Compose but in any 'live' system you would have an underlying datastore such as Postgres or Cockroach that stores all the relationships.

 It's also where you'd handle read-your-writes properly: capture the `ZedToken` returned by a write and pass it as `at_least_as_fresh` on the next check, so a just-granted document is immediately retrievable without reaching for `fully_consistent` on the hot path. 
 
 To run a live instance of SpiceDB, there are three ways:

- **SpiceDB, self-hosted (open source).** Run it yourself, on your own infrastructure.
- **[AuthZed Cloud](https://authzed.com/products/authzed-cloud).** Managed, self-service, pay-as-you-go SpiceDB, with enterprise features like audit logging.
- **[AuthZed Dedicated](https://authzed.com/products/authzed-dedicated).** A private, single-tenant deployment in the cloud provider and regions you choose.

One more production note. This workshop embeds locally with fastembed so there's nothing to sign up for. In production you'd often reach for a hosted embedding model (OpenAI `text-embedding-3-small`, Mistral, etc). Embeddings are decoupled from both the vector store and the chat model, so it's a one-function change in `embed()`. Keep the index and the queries on the same model, and match the Qdrant collection's vector size to its output dimension. Qdrant itself scales from this single container to a managed cluster ([Qdrant Cloud](https://qdrant.tech/)) with the same client code, or swap it for pgvector or Weaviate; the pre-filter only needs an "id in set" filter.

## Homework

1. **Add a department and prove isolation.** Create a `legal` department with a user and some documents, write the relationships, and confirm `alice` (engineering) can't see them and your new user can't see engineering docs. The schema needs no changes, which is the point.
2. **Combine pre-filter with a caveat.** Add a SpiceDB caveat (say, access only during business hours) to a grant and thread the context through `LookupResources`. Watch the allowed set grow and shrink with the context. Heads up: with a caveat, `LookupResources` can return `CONDITIONAL` results, so the prefilter node would need to inspect `permissionship`, not just collect every id.

## Resources

- SpiceDB docs: [authzed.com/docs](https://authzed.com/docs)
- AuthZed Cloud: [authzed.com/products/authzed-cloud](https://authzed.com/products/authzed-cloud)
- Qdrant docs: [qdrant.tech/documentation/](https://qdrant.tech/documentation/)

The industry spent the last decade learning to scope access for human users. We're doing it again for AI pipelines and Agents, and the answer is the same: keep the decision in a system that was built to make it, not in the model.
