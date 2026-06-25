# Next Steps

You've wired a SpiceDB authorization node into a LangGraph RAG pipeline — a deterministic security boundary that checks every retrieved document against real permissions before the LLM ever sees it. That's the core of it. But there's more worth exploring.

---

## Adaptive mode — let the agent retry

Right now you're probably running with `max_attempts=1`, which gives you the clean three-node path: retrieve → authorize → generate. That's the right default for most queries.

Set `max_attempts > 1` and the graph changes shape. After authorization fails — no documents passed, all denied — instead of immediately generating an "access denied" explanation, the `authorize` node routes to the `reason` node (`agentic_rag/nodes/reasoning_node.py`). That node gets the full picture: how many docs were retrieved, how many passed, how many were denied, and how many attempts remain. It reasons about what to try differently and loops back to retrieve.

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

---

## Post-filter is correct; pre-filter scales better

What you built is **post-filter** authorization: retrieve documents from Milvus first, then call SpiceDB on each one. It's simple, always correct, and works well when a user has access to a reasonable fraction of the corpus.

The alternative is **pre-filter**: before touching Milvus, call SpiceDB's `LookupResources` API to ask "which document IDs is this user allowed to view?" then pass that set as an ID filter into the vector search. The LLM only ever sees documents that are definitely allowed — you never retrieve-then-discard.

The trade-off is real. Pre-filter pushes load onto SpiceDB upfront (the `LookupResources` call grows with the corpus), and you need your vector store to support filtered queries. Post-filter pushes the check to the tail end and can waste a retrieval round-trip when most results are denied. Neither is universally better.

If your users can see only a small slice of a large corpus — say, a contractor who has access to three documents out of ten thousand — pre-filter is the right call. If most users can see most documents with a few exceptions carved out, post-filter is simpler and plenty fast.

The sibling workshop [**secure-rag-pipelines**](https://github.com/authzed/workshops/tree/main/secure-rag-pipelines) covers both patterns in depth, with working implementations for each.

---

## One SpiceDB call for many documents

The authorization node you wrote calls `CheckPermission` once per document. For five retrieved documents, that's five round trips. For fifty, it's fifty.

SpiceDB has `CheckBulkPermissions` — a single call that sends all your document IDs in one request and gets back a permission result for each. The latency profile is entirely different.

The full reference implementation at [authzed/examples/agentic-rag-authorization](https://github.com/authzed/examples/tree/main/agentic-rag-authorization) uses `CheckBulkPermissions` via the `langchain-spicedb` integration. That's the right place to look if you want to see how bulk checking fits into the node.

---

## Go to production with AuthZed Cloud

The SpiceDB you've been running is in-memory via Docker Compose. It resets when the container stops. It's fine for a workshop; it's not fine for production.

**AuthZed Cloud** gives you a managed, durable SpiceDB with a persistent datastore (CockroachDB), replicated deployments, and least-privilege access control via Service Accounts, Tokens, Roles, and Policies.

The schema you've been testing locally maps directly. Once you have an AuthZed Cloud Permissions System provisioned:

1. Point `zed` at your cloud endpoint: `zed context set <name> <endpoint> <api-token>`
2. Write your schema: `zed schema write permissions/schema.zed`
3. Update your `.env` file: set `SPICEDB_ENDPOINT` to your cloud permissions-system endpoint and `SPICEDB_TOKEN` to your API token. No code changes needed — `agentic_rag/config.py` already reads both from the environment, and `agentic_rag/grpc_helpers.py` uses them to create the client.

Everything else in the code stays the same. The authorization node doesn't know or care whether SpiceDB is local or managed — it's just a gRPC call.

Get started at [authzed.com](https://authzed.com/products/authzed-cloud).

---

## Keep exploring in the web UI

The UI you used across both checkpoints (`python run_ui.py`, backed by `api/` and `ui/`) is worth more of your time. Now that the node enforces real permissions, switch between users and throw queries at it — watch documents move between **Authorized** and **Denied** as you change who's asking. It's the fastest way to build intuition for the access patterns.

---

## The full reference implementation

The workshop starter is intentionally simplified — one stub to fill in, one straightforward pattern to learn.

The upstream repo at [authzed/examples/agentic-rag-authorization](https://github.com/authzed/examples/tree/main/agentic-rag-authorization) is the production-shaped version. It uses `CheckBulkPermissions` via `langchain-spicedb`, handles errors differently, and has more complete observability. Once you're comfortable with the concepts here, that's where to go next.

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
- **ai-agent-authorization workshop**: [github.com/authzed/workshops/tree/main/ai-agent-authorization](https://github.com/authzed/workshops/tree/main/ai-agent-authorization)
- **Full reference implementation**: [github.com/authzed/examples/tree/main/agentic-rag-authorization](https://github.com/authzed/examples/tree/main/agentic-rag-authorization)

---

The industry spent the last decade learning to pull authorization out of application code and into a system built for it — for human users. Agents don't get a pass. If anything, they need it more: they move faster, ask more, and never get tired of trying. You've secured one pipeline. Go do the rest.
