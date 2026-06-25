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

## Start the web UI

The clearest way to watch the agent work is the bundled web UI. From the `starter/` directory, with your environment ready from setup (virtual environment active if you're running locally) and the services still up:

```bash
python run_ui.py
```

It runs a few pre-flight checks — Milvus, SpiceDB, your OpenAI key, and whether the documents are loaded — then starts a server on `http://localhost:8000` and opens your browser for you.

The page has three parts:

- **User Selection** — a dropdown of the four demo users (Alice/Engineering, Bob/Sales, HR Manager, Finance Manager). This is who the agent runs *as*.
- **Query** — the question you want to ask.
- **Results** — what comes back, split into **Authorized Documents**, **Denied Documents**, and the final **Answer**, with retrieved/authorized/denied counts above them.

That split between Authorized and Denied is the whole story of this workshop. Keep your eye on it.

---

## Watch it leak

`bob` is in sales. He has no business knowing about engineering's internal microservices architecture. Let's ask anyway.

In the UI:

1. Pick **Bob (Sales)** from the user dropdown.
2. Ask: **What are our microservices architecture patterns?** (it's already filled in as the suggested query).
3. Submit.

Look at the results. Engineering documents — things like `engineering-architecture-002` — land under **Authorized Documents**. **Denied Documents** shows **0**. And the **Answer** is a confident, detailed summary of your microservices architecture, written for a sales rep who should never have seen any of it.

The exact doc_ids depend on your live Milvus data, but the pattern holds: engineering architecture documents rank highly against that query, retrieval surfaces them, and the authorization node waves every one of them straight through.

Nothing was denied. Bob got the lot.

---

## Your turn — reproduce the leak as someone else

Switching users in the UI is a single dropdown change, so try a few. Open `starter/data/PERMISSIONS.md` and pick a user/query pair that *should* be restricted:

- **HR Manager** asking "What are our quarterly financial reports?" (finance is off-limits to HR)
- **Finance Manager** asking "What are the sales playbooks?" (sales isn't in their access pattern)
- **Alice (Engineering)** asking "What HR policies do we have?" (engineering has no HR access)

Run one and watch the same thing happen: documents from the wrong department sitting under **Authorized**, **Denied Documents** stuck at 0.

This is the permission matrix you'll enforce in Checkpoint 2. Reading it now — who *should* see what — sets you up for the SpiceDB schema ahead.

---

## Retrieval has no idea what permissions are

Semantic search ranks documents by *similarity to your query*, not by *who's allowed to read them*. A query about microservices architecture will reliably surface engineering architecture documents regardless of whether the person asking is an engineer, a sales rep, or anyone else. The vector index doesn't know about departments or clearance levels — it only knows about meaning.

The authorization node is the one and only place in this pipeline where access control can actually happen. Right now it does nothing. That's why every query leaks.

---

## Completion Milestone: Checkpoint 1

- [ ] Started the web UI and ran a query end-to-end through the agent
- [ ] Reproduced a cross-department leak with the `bob` / microservices scenario — engineering docs under Authorized, Denied at 0
- [ ] Reproduced the leak as at least one other user
- [ ] Can explain why retrieval alone can't enforce authorization

Next: [Checkpoint 2 — Secure it with SpiceDB](2-secure-it.md).
