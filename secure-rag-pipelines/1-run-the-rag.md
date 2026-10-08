# Part 1: Run the RAG (and watch it leak)

The goal for this part is small and a little mischievous: get the agent running, then catch it handing back documents the user has no business seeing.

## Four nodes

The agent is a LangGraph state machine in `agentic_rag/graph.py`. It runs four nodes in order:

1. **`prefilter`** (`agentic_rag/nodes/prefilter_node.py`). In pre-filter mode, it asks SpiceDB which documents the user may see before anything is retrieved. In post-filter mode it does nothing. It's a stub in Part 1, so right now it does nothing either way.
2. **`retrieve`** (`agentic_rag/nodes/retrieval_node.py`). Embeds your query locally with fastembed and runs a vector search against Qdrant, returning the top 5 matches. If the prefilter handed it an allow-list, it applies that as a Qdrant payload filter.
3. **`authorize`** (`agentic_rag/nodes/authorization_node.py`). The post-filter security boundary. Every retrieved document passes through here before the LLM sees it. Also a stub in Part 1: it waves everything through.
4. **`generate`** (`agentic_rag/nodes/generation_node.py`). Asks the chat model for an answer grounded strictly in the authorized documents.

It's "agentic" because the graph can loop. With `max_attempts > 1` it reasons about why authorization came up empty and retries retrieval with a different strategy. We'll leave that off for now and run the straight path with `max_attempts=1`.

## Two deliberate stubs

Open `agentic_rag/nodes/authorization_node.py`. The docstring tells you exactly what you're looking at:

```
WORKSHOP STUB
-------------
Right now this node lets EVERYTHING through. It does no real permission
check, so every document retrieval returns is passed straight to the LLM,
including documents the user is not allowed to see.
```

And the body makes good on the threat:

```python
# TODO(Part 2): Replace this pass-through with a real SpiceDB check.
# As written, every retrieved document is treated as authorized. That's the bug.
authorized = retrieved
denied_count = 0
```

`agentic_rag/nodes/prefilter_node.py` is the same deal: its stub returns `{"allowed_doc_ids": None}`, so retrieval is never restricted. You fix `authorize` in Part 2 and `prefilter` in Part 3.

## Start the web UI

The clearest way to watch the agent work is the bundled UI. From `starter/`, with your environment ready from setup (virtual environment active if you're local) and the services up:

```bash
python run_ui.py
```

That starts a server on `http://localhost:8000` and opens your browser.

You'll see an **Authorization mode** toggle, Post-filter and Pre-filter. Leave it on Post-filter for now. Pre-filter comes in Part 3.

## Watch it leak

`bob` is in sales. He has no reason to know anything about engineering's internal microservices architecture. So let's have him ask.

In the UI:

1. Pick **Bob (Sales)** from the user dropdown.
2. Leave the mode on **Post-filter**.
3. Ask: **What are our microservices architecture patterns?** (it's the suggested query).
4. Submit.

Look at the results. Engineering documents, things like `engineering-architecture-002`, show up under **Authorized Documents**. **Denied** reads **0**. And the **Answer** is a confident write-up of your microservices architecture, served to a sales rep who should never have seen it.

The exact `doc_id`s depend on your live Qdrant data, but the shape holds: engineering architecture documents rank high against that query, retrieval surfaces them, and the authorization node waves every one through.

This is a breach.

## Retrieval doesn't know what a permission is

Here's the thing: semantic search ranks documents by how close they are to your query, not by who's allowed to read them. Ask about microservices architecture and you'll pull engineering architecture docs every time, whether you're an engineer, a sales rep, or a stranger off the street.

In post-filter mode, the authorization node is the one place access control can actually happen. Right now it does nothing, and that's why every query leaks.

## Completion Milestone: Part 1

- [ ] Started the web UI and ran a query end-to-end through the agent
- [ ] Reproduced a cross-department leak with the `bob` / microservices scenario: engineering docs under Authorized, Denied at 0
- [ ] Reproduced the leak as at least one other user
- [ ] Can explain why retrieval alone can't enforce authorization

Next: [Part 2: Secure it with post-filter](2-post-filter.md).
