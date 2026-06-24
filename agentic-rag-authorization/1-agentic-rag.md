# Checkpoint 1 — Run the Agentic RAG (and watch it leak)

The goal here is simple: get the agent running, then catch it in the act of handing back documents the user has no business seeing.

---

## The flow — three nodes, one critical gap

The agent is a LangGraph state machine defined in `agentic_rag/graph.py`. With `max_attempts=1` (the default), it runs a clean three-node pipeline:

**`retrieve`** (`agentic_rag/nodes/retrieval_node.py`) — Embeds your query with OpenAI's `text-embedding-3-small` and fires a vector search against Milvus, returning the top 5 semantically similar documents.

**`authorize`** (`agentic_rag/nodes/authorization_node.py`) — The security boundary. Every document that came out of retrieval passes through here before the LLM ever sees it. This is the only node with the power to deny access.

**`generate`** (`agentic_rag/nodes/generation_node.py`) — Takes whatever the authorization node passed through and asks OpenAI to produce an answer grounded strictly in those documents. It knows how many documents were authorized versus denied and factors that into its response.

It's "agentic" because the graph has a conditional reason/retry path: when `max_attempts > 1`, the graph can loop — reasoning about why authorization failed and retrying retrieval with a refined strategy. For this checkpoint, we're using the straightforward 3-node path.

---

## The authorization node is a deliberate stub

Open `agentic_rag/nodes/authorization_node.py`. The module docstring tells you exactly what you're looking at:

```
WORKSHOP STUB
-------------
Right now this node lets EVERYTHING through. It does no real permission
check, so every document semantic search returns is passed straight to the
LLM — including documents the user is not allowed to see. That is the data
leak you will observe in Checkpoint 1.
```

And the implementation makes good on that warning:

```python
# TODO(Checkpoint 2): Replace this pass-through with a real SpiceDB check.
# As written, every retrieved document is treated as authorized — the bug.
authorized = retrieved
denied_count = 0
```

Every single retrieved document becomes an authorized document. `denied_count` is always zero. This is deliberate — it's the bug you're here to fix.

---

## Run the demo scenarios

From the `starter/` directory, run the bundled example script:

```bash
python examples/basic_example.py
```

This runs 8 scenarios across all four users: `alice` (engineering), `bob` (sales), `hr_manager`, and `finance_manager`. Each scenario prints the retrieved document count, the authorized document count, and the agent's final answer.

Notice that no matter who asks, the authorized count always matches the retrieved count. `DENIED: 0` every time. The stub doesn't discriminate.

You'll also see an empty "Agent Reasoning" section in the output — that's expected. Reasoning only runs when `max_attempts > 1` triggers the retry path; at the default of `max_attempts=1`, the reason node is never reached. The Next Steps module covers adaptive retry and shows what that section actually contains.

---

## Watch it leak

Here's the scenario: `bob` is in sales. He has no business knowing about engineering's internal microservices architecture. Let's ask anyway.

Run this from the `starter/` directory:

```bash
python -c "import asyncio; from agentic_rag.graph import run_agentic_rag_async; \
r=asyncio.run(run_agentic_rag_async('What are our microservices architecture patterns?', 'bob')); \
print('AUTHORIZED:', [d.metadata['doc_id'] for d in r['authorized_documents']]); \
print('DENIED:', r['denied_count'])"
```

You'll see engineering documents — things like `engineering-architecture-002` — show up in the `AUTHORIZED` list. And `DENIED: 0`.

The exact doc_ids depend on your live Milvus data, but the pattern is consistent: engineering architecture documents rank highly against that query, the retrieval node surfaces them, and the authorization node waves them straight through to the LLM.

`bob` gets a detailed answer about your microservices architecture. He was never supposed to.

---

## Your turn — reproduce the leak with a different pair

Open `starter/data/PERMISSIONS.md` and pick a different user/query combination that *should* be restricted. The permission matrix gives you plenty of options. For example:

- `hr_manager` asking "What are our quarterly financial reports?" (finance is off-limits to HR)
- `finance_manager` asking "What are the sales playbooks?" (sales documents aren't in their access pattern)
- `alice` asking "What HR policies do we have?" (engineering has no HR access)

Take the one-liner from the previous section, swap in your chosen user and query, and run it. You should see the same result: relevant documents from the wrong department, `DENIED: 0`.

This is the permission matrix you'll be enforcing in Checkpoint 2. Reading it now — understanding who *should* have access to what — primes you for the SpiceDB schema design ahead.

---

## Retrieval has no idea what permissions are

Semantic search ranks documents by *similarity to your query*, not by *who's allowed to read them*. A query about microservices architecture will reliably surface engineering architecture documents regardless of whether the person asking is an engineer, a sales rep, or anyone else. The vector index doesn't know about departments or clearance levels — it only knows about meaning.

The authorization node is the one and only place in this pipeline where access control can actually happen. Right now it does nothing. That's why every query leaks.

---

## Completion Milestone: Checkpoint 1

- [ ] Ran the agentic RAG pipeline end-to-end with `python examples/basic_example.py`
- [ ] Reproduced a cross-department leak with the `bob` / microservices scenario
- [ ] Reproduced the leak with at least one additional user/query pair of your choice
- [ ] Can explain why retrieval alone can't enforce authorization

Next: [Checkpoint 2 — Secure it with SpiceDB](2-secure-it.md).
