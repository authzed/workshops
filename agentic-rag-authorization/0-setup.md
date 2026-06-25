# Setup

This workshop is in two parts. First, we build an Agentic RAG pipeline with a mock corpus of documents. This pipeline will leak data so in Part 2, we'll add fine-grained authorization to the system. The `starter` folder in this repo is a stub of the working code and is meant only for this workshop. The corpus of documents and the working code for this example [can be found here](https://github.com/authzed/examples/tree/main/agentic-rag-authorization)

## Get the code

```bash
git clone https://github.com/authzed/workshops.git
cd workshops/agentic-rag-authorization/starter
```

## Option A - Run locally with Docker

Copy the example `.env` file and drop in your OpenAI key:

```bash
cp .env.example .env
```

Open `.env` and set `OPENAI_API_KEY` to your actual key. Everything else such as the Milvus URI, SpiceDB endpoint, and preshared-token is already wired up to match `docker-compose.yml`.

Start the infrastructure:

```bash
docker compose up -d
```

This brings up four containers: three for the Milvus stack (`milvus-etcd`, `milvus-minio`, `milvus-standalone`) and one for SpiceDB. SpiceDB runs in-memory with a preshared key of `devtoken`, not recommended for prod ofc.

Create a virtual environment and install dependencies:

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Option B - Run in GitHub Codespaces

For anyone who can't run Docker locally, Codespaces is the path. The repo ships with a `.devcontainer/` config that handles everything automatically.

1. On the repo page, click **Code ▸ Codespaces ▸ Create codespace on main**
2. The devcontainer will run `docker compose up -d` and install dependencies on startup
3. Once the Codespace is ready, open `.env` and add your `OPENAI_API_KEY`

## Load the data

```bash
python examples/setup_environment.py
```

Two things happen here:

- **Milvus setup** — embeds all 50 sample documents using `text-embedding-3-small` and inserts them into a vector collection
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
- [ ] `.env` has a valid OpenAI API key
- [ ] 50 documents embedded into Milvus
- [ ] 18/18 permission checks pass

Next: [Checkpoint 1 — Run the Agentic RAG](1-agentic-rag.md).
