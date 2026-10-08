# Part 1 — Run the RAG (and watch it leak)

The goal here is simple: get the agent running, then catch it handing back documents the user has no business seeing.

---

## The flow — four nodes

The agent is a LangGraph state machine defined in `agentic_rag/graph.py`. It runs a four-node pipeline:

1. **`prefilter`** (`agentic_rag/nodes/prefilter_node.py`): In **pre-filter** mode, asks SpiceDB which documents the user may view *before* retrieval. In **post-filter** mode it does nothing. **Intentionally a stub in Part 1** — it returns no allow-list, so nothing is restricted.

2. **`retrieve`** (`agentic_rag/nodes/retrieval_node.py`): Embeds your query locally with fastembed (`bge-small-en-v1.5`) and runs a vector search against Qdrant, returning the top 5 semantically similar documents. If the prefilter produced an allow-list, retrieval applies it as a Qdrant payload filter.

3. **`authorize`** (`agentic_rag/nodes/authorization_node.py`): The post-filter security boundary. Every retrieved document passes through here before the LLM sees it. **Intentionally a stub in Part 1** — it lets everything through.

4. **`generate`** (`agentic_rag/nodes/generation_node.py`): Asks the chat model for an answer grounded strictly in the authorized documents.

It's "agentic" because the graph has a conditional reason/retry path: with `max_attempts > 1` it can reason about why authorization failed and retry retrieval with a refined strategy. For this part we use the straightforward path with `max_attempts=1`.

---

## Two deliberate stubs

Open `agentic_rag/nodes/authorization_node.py`. Its docstring says exactly what you're looking at:

```
WORKSHOP STUB
-------------
Right now this node lets EVERYTHING through. It does no real permission
check, so every document retrieval returns is passed straight to the LLM —
including documents the user is not allowed to see.
```

The implementation makes good on that warning:

```python
# TODO(Part 2): Replace this pass-through with a real SpiceDB check.
# As written, every retrieved document is treated as authorized — the bug.
authorized = retrieved
denied_count = 0
```

`agentic_rag/nodes/prefilter_node.py` is the same story: its stub returns `{"allowed_doc_ids": None}`, so retrieval is never restricted. We fix `authorize` in Part 2 and `prefilter` in Part 3.

---

## Start the web UI

The clearest way to watch the agent work is the bundled web UI. From the `starter/` directory, with your environment ready from setup (virtual environment active if you're running locally) and the services still up:

```bash
python run_ui.py
```

This starts a server on `http://localhost:8000` and opens your browser for you.

There's an **Authorization mode** toggle — **Post-filter** and **Pre-filter**. Leave it on **Post-filter** for now; we'll use Pre-filter in Part 3.

---

## Watch it leak

`bob` is in sales. He has no business knowing about engineering's internal microservices architecture. Let's ask anyway.

In the UI:

1. Pick **Bob (Sales)** from the user dropdown.
2. Leave the mode on **Post-filter**.
3. Ask: **What are our microservices architecture patterns?** (it's the suggested query).
4. Submit.

Look at the results. Engineering documents — things like `engineering-architecture-002` — land under **Authorized Documents**. **Denied** shows **0**. And the **Answer** is a confident summary of your microservices architecture, written for a sales rep who should not have seen any of it.

The exact `doc_ids` depend on your live Qdrant data, but the pattern holds: engineering architecture documents rank highly against that query, retrieval surfaces them, and the authorization node waves every one straight through.

This is a security breach.

---

## Retrieval has no idea what permissions are

Semantic search ranks documents by *similarity to your query*, not by *who's allowed to read them*. A query about microservices architecture will reliably surface engineering architecture documents regardless of who's asking.

The authorization node is the one place in this pipeline where access control can happen in post-filter mode. Right now it does nothing, and that's why every query leaks data.

---

## Completion Milestone: Part 1

- [ ] Started the web UI and ran a query end-to-end through the agent
- [ ] Reproduced a cross-department leak with the `bob` / microservices scenario — engineering docs under Authorized, Denied at 0
- [ ] Reproduced the leak as at least one other user
- [ ] Can explain why retrieval alone can't enforce authorization

Next: [Part 2 — Secure it with post-filter](2-post-filter.md).
