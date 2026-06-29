# Next Steps

You've wired a SpiceDB authorization node into a LangGraph RAG pipeline - a deterministic security boundary that checks every retrieved document against real permissions before the LLM ever sees it. But there's more worth exploring.

---

## Adaptive mode — let the agent retry

Right now you're probably running with `max_attempts=1`, which gives you the clean three-node path: `retrieve → authorize → generate`.

The agentic part comes in when you set `max_attempts > 1` . After authorization fails, instead of immediately generating an "access denied" explanation, the `authorize` node routes to the `reason` node (`agentic_rag/nodes/reasoning_node.py`). That node gets the full picture: how many docs were retrieved, how many passed, how many were denied, and how many attempts remain. It reasons about what to try differently and loops back to retrieve.

The authorization check still runs on every attempt. The `reason` node can't instruct the graph to skip it, and there's no code path that gets around it. The agent adapts its *search strategy*, not its *permissions*.

Try it on a query that gets fully denied:

```python
result = await run_agentic_rag_async(
    query="Show me the Q3 engineering roadmap",
    subject_id="bob",
    max_attempts=3,
)
```

Watch the `reasoning` field in the returned state — it's a list of the agent's decisions across attempts. Useful for understanding why the agent gave up, or why it eventually found something.

![agentic-rag](/agentic-rag-authorization/images/full-agentic-rag.png)

---

## Post-filter and pre-filter 

What you built is **post-filter** authorization: retrieve documents from Milvus first, then call SpiceDB on each one. It works well when a user has access to a reasonable fraction of the corpus.

![post-filter](/agentic-rag-authorization/images/post-filter.png)

The alternative is **pre-filter**: before touching Milvus, call SpiceDB's `LookupResources` API to ask "which document IDs is this user allowed to view?" then pass that set as an ID filter into the vector search. The LLM only ever sees documents that are definitely allowed — you never retrieve-then-discard.

![pre-filter](/agentic-rag-authorization/images/pre-filter.png)

Which one you choose depends on your usecase. Pre-filter pushes load onto SpiceDB upfront (the `LookupResources` call grows with the corpus), and you need your vector store to support filtered queries. Post-filter pushes the check to the tail end and can waste a retrieval round-trip when most results are denied.

If your users can see only a small slice of a large corpus — say, a contractor who has access to three documents out of ten thousand — pre-filter is the right call. If most users can see most documents with a few exceptions carved out, post-filter is simpler and plenty fast.

The sibling workshop [**secure-rag-pipelines**](https://github.com/authzed/workshops/tree/main/secure-rag-pipelines) covers both patterns in depth, with working implementations for each.

---

## One SpiceDB call for many documents

The authorization node you wrote calls `CheckPermission` once per document. For five retrieved documents, that's five round trips. For fifty, it's fifty.

SpiceDB has `CheckBulkPermissions` — a single call that sends all your document IDs in one request and gets back a permission result for each. The latency is significantly reduced with this call.

The full reference implementation at [authzed/examples/agentic-rag-authorization](https://github.com/authzed/examples/tree/main/agentic-rag-authorization) uses `CheckBulkPermissions` via the `langchain-spicedb` integration. That's the right place to look if you want to see how bulk checking fits into the node.

---

## Go to production

The SpiceDB you've been running is in-memory via Docker Compose. This works for a workshop or a proof of concept, but not for production, where you want a durable datastore and a deployment you can lean on. You've got three ways to get there:

- **SpiceDB, self-hosted (open source)** — run it yourself. You have full control, and it runs on your infrastructure and ops. The right call if you're happy managing the database and have specific deployment requirements.
- **[AuthZed Cloud](https://authzed.com/products/authzed-cloud)** — managed, self-service, pay-as-you-go SpiceDB. Provision a permissions system on demand and get enterprise features like audit logging without running anything yourself. The easy on-ramp for startups and growing teams.
- **[AuthZed Dedicated](https://authzed.com/products/authzed-dedicated)** — a fully private, single-tenant deployment in the cloud provider and regions you choose, sold annually. For enterprises that need dedicated infrastructure and geographic or compliance guarantees while offloading the ops.

Not sure which fits? The [Picking a product](https://authzed.com/docs/authzed/guides/picking-a-product) guide walks through the trade-offs.

Whichever you pick, your code doesn't change. The schema you tested locally maps directly, and the authorization node doesn't know or care whether SpiceDB is local or managed — point `SPICEDB_ENDPOINT` and `SPICEDB_TOKEN` in your `.env` at the new instance and you're done. The permission check is just a gRPC/API call.

One more swap for production: this workshop embeds locally with **fastembed** so there's nothing to sign up for and no key to manage. In production you'd more likely reach for a hosted embedding model — OpenAI's `text-embedding-3-small`, a Cohere or Voyage model, or whatever your LLM provider offers — for higher retrieval quality without running the model yourself. Embeddings are decoupled from both the vector store and the chat model, so it's a one-function change in `embed()` — just keep the index and queries on the same model, and match the Milvus collection's `dim` to its output.

---

## The full reference implementation

The upstream repo at [authzed/examples/agentic-rag-authorization](https://github.com/authzed/examples/tree/main/agentic-rag-authorization) is the production-shaped version. It uses `CheckBulkPermissions` via `langchain-spicedb`, handles errors differently, and has more complete observability. Once you're comfortable with the concepts here, that's where to go next. You can swap out Milvus for any vector database such as Pinecone, PGVector, Weaviate (there's a branch with this implementation), etc

---

## Homework

A few things worth trying on your own:

1. **Add a new department and prove isolation.** Create a `legal` department with a new user, write the relationships into SpiceDB, and add some documents tagged to `legal`. Then confirm that `alice` (engineering) can't see them, and that your new user can't see engineering documents. The schema needs no changes — that's the point.

2. **Add an `editor` permission and check it.** The current schema has `view` and `edit`, but the agent only checks `view`. Add a node that calls `CheckPermission` for `edit` before allowing a write operation, and wire it into the graph. Start from `agentic_rag/nodes/authorization_node.py` as a template.

3. **Switch to pre-filter with `LookupResources`.** Replace the post-filter authorization node with a pre-filter approach: call `LookupResources` at the start of the retrieval step, get back the list of allowed document IDs, and pass them as a filter to the Milvus query. Compare the two approaches — latency, correctness, what happens at the edges.

---

## Resources

- **SpiceDB documentation**: [authzed.com/docs](https://authzed.com/docs)
- **AuthZed Cloud**: [authzed.com/products/authzed-cloud](https://authzed.com/products/authzed-cloud)
- **secure-rag-pipelines workshop** (pre-filter and post-filter, both): [github.com/authzed/workshops/tree/main/secure-rag-pipelines](https://github.com/authzed/workshops/tree/main/secure-rag-pipelines)
- **Full reference implementation**: [github.com/authzed/examples/tree/main/agentic-rag-authorization](https://github.com/authzed/examples/tree/main/agentic-rag-authorization)

---
