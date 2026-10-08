# Secure Your RAG Pipelines with Fine-Grained Authorization (Pre-Filter & Post-Filter)

This workshop gives you hands-on experience securing a RAG pipeline with SpiceDB. You build an agentic RAG system over a corpus of documents owned by many different users, watch it leak data across departments, then lock it down two ways and learn when to use each:

1. **Post-filter** — retrieve documents, then check permissions on each with `CheckPermission`
2. **Pre-filter** — ask SpiceDB which documents a user may see with `LookupResources` *before* you retrieve, and pass that set as a filter into the vector search

You'll also pick up two smaller SpiceDB features: bulk permission checks and self-expiring grants.

The stack: **SpiceDB** for authorization, **Qdrant** (open-source) for the vector store, local **fastembed** embeddings (no key), and an OpenAI-compatible chat model for generation — all running locally via Docker, with a web UI.

### Why this matters

TL;DR: **AI can't secure AI.**

Enterprise AI has one non-negotiable: a user can only ever augment a prompt with data they're allowed to see. You can't delegate that to the model, because probabilistic systems hallucinate, misinterpret, and guess. Authorization has to be deterministic, and it has to live *outside* the model — in code that runs whether or not the model "remembers" the rule.

Fine-grained authorization in RAG is best achieved with **Relationship-Based Access Control (ReBAC)**: decisions based on relationships between objects (who owns what, who belongs to which team, what role grants what access). This is more precise and composable than RBAC or ABAC.

### What you'll build

![post-filter](/secure-rag-pipelines/images/post-filter.png)

![pre-filter](/secure-rag-pipelines/images/pre-filter.png)

- Run a LangGraph agentic RAG pipeline — `prefilter → retrieve → authorize → generate` — over a 50-document, multi-department corpus, with a web UI
- Watch the naive version leak documents across departments
- Implement **post-filter** authorization (`CheckPermission`) so the agent can only ever answer from documents the user may see
- Implement **pre-filter** authorization (`LookupResources` → Qdrant payload filter), compare it against post-filter live with a UI toggle, and learn which to reach for
- Collapse the per-document loop into one `CheckBulkPermissions` call, and grant a contractor time-boxed access that expires on its own

It builds on an agentic RAG core (the retry loop is retained), taught here with a pre-filter focus. The sibling [agentic-rag-authorization](https://github.com/authzed/workshops/tree/main/agentic-rag-authorization) workshop is a post-filter deep-dive on Milvus.

### Prerequisites

- **Docker** (or a GitHub account for Codespaces)
- **Python 3.11+**
- An **API key for a chat model** — OpenAI, or any OpenAI-compatible provider

Embeddings run locally via fastembed, so there's no key needed there. The chat model is provider-agnostic — set `LLM_API_KEY`, `LLM_MODEL`, and (for anything but OpenAI) `LLM_BASE_URL` in `.env`. SpiceDB and Qdrant both run locally via Docker Compose — no additional accounts or cloud services.

### Watch the talk

This conference talk walks through the concepts behind the workshop:

[![DevConf talk](/secure-rag-pipelines/images/youtube.png)](https://youtu.be/aeace8MDlhk "Secure RAG Pipelines")

---

**Last Updated**: Oct 8, 2026

### Workshop Modules

0. [Setup](0-setup.md)
1. [Part 1 — Run the RAG (and watch it leak)](1-run-the-rag.md)
2. [Part 2 — Secure it with post-filter](2-post-filter.md)
3. [Part 3 — Pre-filter with LookupResources](3-pre-filter.md)
4. [Part 4 — Smaller features (bulk checks + expiring grants)](4-smaller-features.md)
5. [Next steps](5-nextsteps.md)

Let's get started with [Setup](0-setup.md).
