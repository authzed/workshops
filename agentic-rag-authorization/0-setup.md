# Setup

This workshop is in two parts. First, we build an Agentic RAG pipeline with a mock corpus of documents. This pipeline will leak data so in Part 2, we'll add fine-grained authorization to the system. The `starter` folder in this repo is a stub of the working code and is meant only for this workshop. The corpus of documents and the working code for this example [can be found here](https://github.com/authzed/examples/tree/main/agentic-rag-authorization)

## Get the code

Get a shell in the `starter/` folder one of two ways, then follow the shared install steps.

**Locally** (needs Docker Desktop):

```bash
git clone https://github.com/authzed/workshops.git
cd workshops/agentic-rag-authorization/starter
```

**GitHub Codespaces** (no local Docker needed): on the repo page, click **Code ▸ Codespaces ▸ Create codespace on main**. The devcontainer provisions Docker + Python; when the terminal is ready:

```bash
cd agentic-rag-authorization/starter
```

> **Codespace didn't pick up the devcontainer?** (no `docker`, missing tools) — open the Command Palette → **Dev Containers: Reopen in Container** and point it at `agentic-rag-authorization/starter`.

## Installation

From `starter/`, the steps are identical for both paths — **only the `docker compose` command in step 2 differs.**

### 1. Configure your chat-model key

```bash
cp .env.example .env
```

Open `.env` and set `LLM_API_KEY`. The chat model is provider-agnostic — leave `LLM_BASE_URL` blank for OpenAI, or point it at any OpenAI-compatible provider (Anthropic/Claude, Groq, a local Ollama, or your company's endpoint) and set `LLM_MODEL` to match; see the comments in `.env.example`. Embeddings run **locally** via fastembed, so they need no key. The Milvus URI, SpiceDB endpoint, and preshared token already match the compose files.

### 2. Start the infrastructure

**Local Docker Desktop:**

```bash
docker compose up -d --wait
```

**Codespaces** — Docker-in-Docker's bridge network is unreliable, so layer on the host-networking override:

```bash
docker compose -f docker-compose.yml -f docker-compose.codespaces.yml up -d --wait
```

Either command brings up four containers: the Milvus stack (`milvus-etcd`, `milvus-minio`, `milvus-standalone`) and SpiceDB (in-memory, preshared key `devtoken` — not for prod).

### 3. Create a virtual environment and install dependencies

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Load the data

```bash
python examples/setup_environment.py
```

Two things happen here:

- **Milvus setup** — embeds all 50 sample documents locally with fastembed (`bge-small-en-v1.5`, 384-dim; the model downloads once on first run) and inserts them into a vector collection
- **SpiceDB setup** — loads the authorization schema and writes all relationships: department memberships, document viewers, cross-department access, and individual exceptions

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
Results: 18 passed, 0 failed
```

This confirms SpiceDB has the right relationships in place: 

- department-based access 
- cross-department collaboration
- individual exceptions, and 
- public documents. 

We'll rely on all of this in Checkpoint 2 when we wire authorization into the RAG pipeline. Note that the RAG itself isn't secured yet.

---

## Completion Milestone: Setup

- [ ] Cloned the repo
- [ ] Infrastructure is up — Docker or Codespaces
- [ ] `.env` has a valid `LLM_API_KEY` (plus `LLM_BASE_URL`/`LLM_MODEL` if you're not using OpenAI)
- [ ] 50 documents embedded into Milvus
- [ ] 18/18 permission checks pass

Next: [Checkpoint 1 — Run the Agentic RAG](1-agentic-rag.md).
