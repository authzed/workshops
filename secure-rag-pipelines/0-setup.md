# Setup

Here's what we'll build in the workshop. First you build an agentic RAG pipeline over a mock knowledge base. It leaks data across users, which is the point. Then you lock it down two ways, post-filter and pre-filter, and finish with a couple of smaller features. The `starter/` folder holds a stub of the working code, meant only for this workshop.

We'll only use open source tools for this: **Qdrant** (open source) for the vector store, **SpiceDB** for authorization, local **fastembed** for embeddings (no key), and a provider-agnostic chat model for the answer. 

## Get the code

Get a shell in `starter/` one of two ways, then follow the shared install steps.

**Locally** (needs Docker Desktop):

```bash
git clone https://github.com/authzed/workshops.git
cd workshops/secure-rag-pipelines/starter
```

**GitHub Codespaces** (no local Docker needed): on the repo page, click **Code ▸ Codespaces ▸ Create codespace on main**. The devcontainer provisions Docker and Python. When the terminal is ready:

```bash
cd secure-rag-pipelines/starter
```

> **Codespace didn't pick up the devcontainer?** Open the Command Palette, run **Dev Containers: Reopen in Container**, and point it at `secure-rag-pipelines/starter`.

## Installation

From `starter/`, the steps are the same for both paths. Only the `docker compose` command in step 2 differs.

### 1. Configure your chat-model key

```bash
cp .env.example .env
```

Open `.env` and set `LLM_API_KEY`. The chat model is provider-agnostic: leave `LLM_BASE_URL` blank for OpenAI, or point it at any OpenAI-compatible provider (Anthropic/Claude, Mistral, a local Ollama, your company's gateway) and set `LLM_MODEL` to match. See the comments in `.env.example`. Embeddings run locally through fastembed, so they need no key. The Qdrant URL and SpiceDB endpoint and token already match the compose files.

### 2. Start the infrastructure

**Local Docker Desktop:**

```bash
docker compose up -d --wait
```

**Codespaces**:

```bash
docker compose -f docker-compose.yml -f docker-compose.codespaces.yml up -d --wait
```

Either command brings up two containers: **Qdrant** (the vector store, ports 6333 and 6334) and **SpiceDB** (in-memory, preshared key `devtoken`, not for prod).

### 3. Create a virtual environment and install dependencies

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Load the data

```bash
python examples/setup_environment.py
```

Two things happen here:

- **Qdrant setup** embeds all 50 sample documents locally with fastembed (`bge-small-en-v1.5`, 384-dim; the model downloads once on first run) and upserts them into a vector collection. Each document's `doc_id` lives in the point *payload* (Qdrant point ids are integers), which is what the pre-filter matches on later.
- **SpiceDB setup** loads the authorization schema and writes the relationships: department memberships, document viewers, cross-department access, individual exceptions, and the contractor `dana`. The complicated permission model we're building [is here](https://github.com/authzed/workshops/blob/workshop/secure-rag-pipelines-refactor/secure-rag-pipelines/starter/data/PERMISSIONS.md) 

The tail of the output should read:

```
============================================================
✅ Setup complete!
============================================================
```

with this document distribution:
- engineering: 15 documents
- finance: 10 documents
- hr: 10 documents
- public: 5 documents
- sales: 10 documents

## Verify

```bash
python scripts/verify_permissions.py
```

You want:

```
Results: 23 passed, 0 failed
```

That confirms SpiceDB has the relationships in place: department-based access, cross-department collaboration, individual exceptions, public documents, and the contractor `dana`, who can see only two engineering guides plus the public docs. We lean on all of it once authorization goes into the pipeline. The RAG itself isn't secured yet.

---

## Completion Milestone: Setup

- [ ] Cloned the repo
- [ ] Infrastructure is up, Docker or Codespaces (Qdrant + SpiceDB)
- [ ] `.env` has a valid `LLM_API_KEY` (plus `LLM_BASE_URL`/`LLM_MODEL` if you're not on OpenAI)
- [ ] 50 documents embedded into Qdrant
- [ ] 23/23 permission checks pass

Next: [Part 1: Run the RAG (and watch it leak)](1-run-the-rag.md).
