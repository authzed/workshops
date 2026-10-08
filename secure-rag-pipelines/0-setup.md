# Setup

This workshop is in several parts. First we build an agentic RAG pipeline over a mock corpus of documents. That pipeline leaks data across users, so we then add fine-grained authorization with SpiceDB — first **post-filter** (check each retrieved document), then **pre-filter** (ask SpiceDB which documents are allowed *before* you retrieve), and finally a couple of smaller SpiceDB features. The `starter/` folder is a stub of the working code, meant only for this workshop.

The vector store is **Qdrant** (open source); authorization is **SpiceDB**; embeddings run locally with **fastembed** (no key); the chat model is provider-agnostic.

## Get the code

Get a shell in the `starter/` folder one of two ways, then follow the shared install steps.

**Locally** (needs Docker Desktop):

```bash
git clone https://github.com/authzed/workshops.git
cd workshops/secure-rag-pipelines/starter
```

**GitHub Codespaces** (no local Docker needed): on the repo page, click **Code ▸ Codespaces ▸ Create codespace on main**. The devcontainer provisions Docker + Python; when the terminal is ready:

```bash
cd secure-rag-pipelines/starter
```

> **Codespace didn't pick up the devcontainer?** Open the Command Palette → **Dev Containers: Reopen in Container** and point it at `secure-rag-pipelines/starter`.

## Installation

From `starter/`, the steps are identical for both paths — **only the `docker compose` command in step 2 differs.**

### 1. Configure your chat-model key

```bash
cp .env.example .env
```

Open `.env` and set `LLM_API_KEY`. The chat model is provider-agnostic — leave `LLM_BASE_URL` blank for OpenAI, or point it at any OpenAI-compatible provider (Anthropic/Claude, Groq, a local Ollama, or your company's endpoint) and set `LLM_MODEL` to match; see the comments in `.env.example`. Embeddings run **locally** via fastembed, so they need no key. The Qdrant URL and SpiceDB endpoint/token already match the compose files.

### 2. Start the infrastructure

**Local Docker Desktop:**

```bash
docker compose up -d --wait
```

**Codespaces** — Docker-in-Docker's bridge network is unreliable, so layer on the host-networking override:

```bash
docker compose -f docker-compose.yml -f docker-compose.codespaces.yml up -d --wait
```

Either command brings up two containers: **Qdrant** (vector store, ports 6333/6334) and **SpiceDB** (in-memory, preshared key `devtoken` — not for prod). That's the whole stack — one vector-store container, not Milvus's three.

### 3. Create a virtual environment and install dependencies

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Load the data

```bash
python examples/setup_environment.py
```

Two things happen here:

- **Qdrant setup** — embeds all 50 sample documents locally with fastembed (`bge-small-en-v1.5`, 384-dim; the model downloads once on first run) and upserts them into a vector collection. Each document's `doc_id` lives in the point **payload** (Qdrant point ids are integers), which is what the pre-filter matches on later.
- **SpiceDB setup** — loads the authorization schema and writes all relationships: department memberships, document viewers, cross-department access, individual exceptions, and the contractor `dana`.

Expected tail output:

```
============================================================
✅ Setup complete!
============================================================
```

With a document distribution of:
- engineering: 15 documents
- finance: 10 documents
- hr: 10 documents
- public: 5 documents
- sales: 10 documents

## Verify

```bash
python scripts/verify_permissions.py
```

Expected result:

```
Results: 23 passed, 0 failed
```

This confirms SpiceDB has the right relationships in place:

- department-based access
- cross-department collaboration
- individual exceptions
- public documents, and
- the contractor `dana`, who can see only two engineering guides plus the public docs

We'll rely on all of this when we wire authorization into the RAG pipeline. Note that the RAG itself isn't secured yet.

---

## Completion Milestone: Setup

- [ ] Cloned the repo
- [ ] Infrastructure is up — Docker or Codespaces (Qdrant + SpiceDB)
- [ ] `.env` has a valid `LLM_API_KEY` (plus `LLM_BASE_URL`/`LLM_MODEL` if you're not using OpenAI)
- [ ] 50 documents embedded into Qdrant
- [ ] 23/23 permission checks pass

Next: [Part 1 — Run the RAG (and watch it leak)](1-run-the-rag.md).
