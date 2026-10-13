# secure-rag-pipelines starter

This is the starter code for the **Secure RAG Pipelines** workshop. It's a stub: two security nodes ship deliberately broken so you can fix them as you work through the parts. Don't read it as a finished reference.

Follow the workshop, not this file, for the walkthrough:

- [Setup](../0-setup.md)
- [Part 1: Run the RAG (and watch it leak)](../1-run-the-rag.md)
- [Part 2: Secure it with post-filter](../2-post-filter.md)
- [Part 3: Pre-filter with LookupResources](../3-pre-filter.md)
- [Part 4: Smaller features](../4-smaller-features.md)
- [Next steps](../5-nextsteps.md)

## Quick start

```bash
cp .env.example .env            # set LLM_API_KEY
docker compose up -d --wait     # Qdrant + SpiceDB
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python examples/setup_environment.py   # embed 50 docs into Qdrant, seed SpiceDB
python scripts/verify_permissions.py   # expect: 23 passed, 0 failed
python run_ui.py                # http://localhost:8000
```

## The stack

- **Qdrant** (vector store) and **SpiceDB** (authorization), both local via `docker-compose.yml`
- **fastembed** for local 384-dim embeddings (no API key)
- A provider-agnostic chat model (`LLM_API_KEY`, `LLM_MODEL`, optional `LLM_BASE_URL`)

Only two environment variables touch infra, and both default correctly for local Docker:

```
QDRANT_URL=http://localhost:6333
SPICEDB_ENDPOINT=localhost:50051
```

## Layout

```
agentic_rag/
  graph.py              LangGraph state machine: prefilter -> retrieve -> authorize -> generate
  state.py              AgenticRAGState (incl. filter_mode, allowed_doc_ids)
  qdrant_client.py      Qdrant client singleton
  grpc_helpers.py       SpiceDB client singleton
  node_helpers.py       local fastembed embedding + logging helpers
  nodes/
    prefilter_node.py   STUB: you implement LookupResources in Part 3
    retrieval_node.py   Qdrant vector search + optional payload filter
    authorization_node.py  STUB: you implement CheckPermission in Part 2
    reasoning_node.py   retry strategy (used when max_attempts > 1)
    generation_node.py  grounded answer generation
api/                    FastAPI app (/api/query, /api/users, /api/health) behind run_ui.py
ui/index.html           single-page UI with the pre/post authorization toggle
data/                   schema.zed, 50 sample documents, PERMISSIONS.md
examples/               setup_environment.py (data load), expiring_grant.py (Part 4b)
scripts/                verify_permissions.py, parse_documents.py
tests/                  pytest; solution tests are skipped until you fill the stubs
```

The two stubbed nodes (`prefilter_node.py`, `authorization_node.py`) leak on purpose. The worked solutions live in the workshop parts, and the tests that cover them are skipped with a note telling you which part implements them. The full reference implementation is linked from [Next steps](../5-nextsteps.md).
