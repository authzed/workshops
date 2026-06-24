# Setup

Get the stubbed agentic RAG running locally — broken by design — so we can trigger the vulnerability in Checkpoint 1 and fix it properly in Checkpoint 2. This is best done before the workshop starts.

## What you need

- **Docker Desktop** (Option A) or a **GitHub account** (Option B — Codespaces)
- An **OpenAI API key** — used for embeddings and answer generation

## Get the code

```bash
git clone https://github.com/authzed/workshops.git
cd workshops/agentic-rag-authorization/starter
```

## Option A — Run locally with Docker

Copy the example env file and drop in your OpenAI key:

```bash
cp .env.example .env
```

Open `.env` and set `OPENAI_API_KEY` to your actual key. Everything else — Milvus URI, SpiceDB endpoint, preshared token — is already wired up to match `docker-compose.yml`.

Start the infrastructure:

```bash
docker compose up -d
```

This brings up five containers: four for Milvus (`milvus-etcd`, `milvus-minio`, `milvus-standalone`, and its dependencies) and one for SpiceDB. SpiceDB runs in-memory with a preshared key of `devtoken` — no persistence, no TLS, exactly what you want for a workshop.

Create a virtual environment and install dependencies:

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Option B — Run in GitHub Codespaces

For anyone who can't run Docker locally, Codespaces is the path. The repo ships with a `.devcontainer/` config that handles everything automatically.

1. On the repo page, click **Code ▸ Codespaces ▸ Create codespace on main**
2. The devcontainer will run `docker compose up -d` and install dependencies on startup
3. Once the Codespace is ready, open `.env` and add your `OPENAI_API_KEY`

## Load the data

```bash
python examples/setup_environment.py
```

Two things happen here:

- **SpiceDB setup** — loads the authorization schema and writes all relationships: department memberships, document viewers, cross-department access, and individual exceptions
- **Milvus setup** — embeds all 50 sample documents using `text-embedding-3-small` and inserts them into a vector collection

Expected tail output:

```
============================================================
✅ Setup complete!
============================================================

You can now run: python examples/basic_example.py
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

This confirms SpiceDB has the right relationships in place — department-based access, cross-department collaboration, individual exceptions, and public documents. We'll rely on all of this in Checkpoint 2 when we wire authorization into the RAG pipeline. Note that the RAG itself isn't secured yet. That's not a bug — it's the whole point of Checkpoint 1.

---

## Completion Milestone: Setup

- [ ] Cloned the repo
- [ ] Infrastructure is up — Docker or Codespaces
- [ ] `.env` has a valid OpenAI API key
- [ ] 50 documents embedded into Milvus
- [ ] 18/18 permission checks pass

Next: [Checkpoint 1 — Run the Agentic RAG](1-agentic-rag.md).
