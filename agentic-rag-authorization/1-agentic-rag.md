# Checkpoint 1 — Run the Agentic RAG (and watch it leak)

The goal here is simple: get the agent running, then catch it in the act of handing back documents the user has no business seeing.

---

## The flow — Three nodes

![workflow](/agentic-rag-authorization/images/simple-agentic-rag.png)

The agent is a LangGraph state machine defined in `agentic_rag/graph.py`. With `max_attempts=1` (the default), it runs a clean three-node pipeline:

1. **`retrieve`** (`agentic_rag/nodes/retrieval_node.py`): Embeds your query locally with fastembed (`bge-small-en-v1.5`) and fires a vector search against Milvus, returning the top 5 semantically similar documents.

2. **`authorize`** (`agentic_rag/nodes/authorization_node.py`): The security boundary. Every document that came out of retrieval passes through here before the LLM ever sees it. This is the only node with the power to deny access. Intentionally incomplete in Part 1.

3. **`generate`** (`agentic_rag/nodes/generation_node.py`): Takes whatever the authorization node passed through and asks OpenAI to produce an answer grounded strictly in those documents. It knows how many documents were authorized versus denied and factors that into its response.

It's "agentic" because the graph has a conditional reason/retry path: when `max_attempts > 1`, the graph can loop - reasoning about why authorization failed and retrying retrieval with a refined strategy. For this checkpoint, we're using the straightforward 3-node path.

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

Every single retrieved document becomes an authorized document. `denied_count` is always zero. This is what we need to fix.

---

## Start the web UI

The clearest way to watch the agent work is the bundled web UI. From the `starter/` directory, with your environment ready from setup (virtual environment active if you're running locally) and the services still up:

```bash
python run_ui.py
```

This starts a server on `http://localhost:8000` and opens your browser for you.

Play around with different users, questions and results. 

---

## Watch it leak

`bob` is in sales. He has no business knowing about engineering's internal microservices architecture. Let's ask anyway.

In the UI:

1. Pick **Bob (Sales)** from the user dropdown.
2. Ask: **What are our microservices architecture patterns?** (it's already filled in as the suggested query).
3. Submit.

Look at the results. Engineering documents — things like `engineering-architecture-002` — land under **Authorized Documents**. **Denied Documents** shows **0**. And the **Answer** is a confident, detailed summary of your microservices architecture, written for a sales rep who should not have seen any of it.

The exact `doc_ids` depend on your live Milvus data, but the pattern holds: engineering architecture documents rank highly against that query, retrieval surfaces them, and the authorization node waves every one of them straight through.

This is a security breach.

---

## Retrieval has no idea what permissions are

Semantic search ranks documents by *similarity to your query*, not by *who's allowed to read them*. A query about microservices architecture will reliably surface engineering architecture documents regardless of whether the person asking is an engineer, a sales rep, or anyone else.

The authorization node is the one and only place in this pipeline where access control can actually happen. Right now it does nothing and that's why every query leaks data.

---

## Completion Milestone: Checkpoint 1

- [ ] Started the web UI and ran a query end-to-end through the agent
- [ ] Reproduced a cross-department leak with the `bob` / microservices scenario — engineering docs under Authorized, Denied at 0
- [ ] Reproduced the leak as at least one other user
- [ ] Can explain why retrieval alone can't enforce authorization

Next: [Checkpoint 2 — Secure it with SpiceDB](2-secure-it.md).
