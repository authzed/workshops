# Building Authorization for Agentic RAG Systems

This workshop shows how to add fine-grained authorization to a production-like Agentic RAG system using SpiceDB. Standard RAG pipelines follow a fixed `query -> retrieve -> generate` flow. This workshops teaches you how  to add a deterministic authorization step in your RAG, that agents cannot bypass. 

The workshop uses SpiceDB for authorization, Milvus as the vector database, local fastembed embeddings, and an OpenAI-compatible chat model for generation.

### Why is this important?

TL;DR: **AI can't secure AI.**

Enterprise AI has one non-negotiable: a user can only ever augment a prompt with data they're allowed to see. And you can't delegate that to the model because probabilistic systems hallucinate, misinterpret, and guess. Authorization has to be deterministic.

Fine-grained authorization in Agentic RAG is best achieved with **Relationship-based Access Control (ReBAC)**. ReBAC makes decisions based on relationships between objects (who owns what, who belongs to which team, what role grants what access). This is more precise and composable than traditional RBAC or ABAC.

### What you'll build

![agentic-rag](/agentic-rag-authorization/images/full-agentic-rag.png)

- Run a LangGraph agentic RAG pipeline — retrieve → authorize → generate — backed by **Milvus** (vector DB), local **fastembed** embeddings, and an **OpenAI-compatible chat model** for generation, with a frontend.
- Watch the naive version leak documents across departments: semantic similarity returns everything relevant, regardless of who's asking
- Implement the SpiceDB authorization node using the raw `authzed` Python SDK — a permission check the agent calls explicitly, before any document reaches the prompt
- Run the same query again and see it return only what the user is actually allowed to see

### Prerequisites

- **Docker** (or a GitHub account if you'd prefer to use Codespaces)
- **Python 3.10+**
- An **API key for a chat model** — OpenAI, or any OpenAI-compatible provider

Embeddings run locally via fastembed, so there's no key needed there. The chat model that writes the final answer is provider-agnostic — set `LLM_API_KEY`, `LLM_MODEL`, and (for anything but OpenAI) `LLM_BASE_URL` in `.env` to use OpenAI, Anthropic, Groq, a local Ollama, or your company's endpoint. See `.env.example` for examples.

SpiceDB and Milvus both run locally via Docker Compose — no additional accounts or cloud services needed.

---

**Last Updated**: Jun 25, 2026

### Workshop Modules

0. [Setup](0-setup.md)
1. [Checkpoint 1 — Run the Agentic RAG (and watch it leak)](1-agentic-rag.md)
2. [Checkpoint 2 — Secure it with SpiceDB](2-secure-it.md)
3. [Next Steps](3-nextsteps.md)

Let's get started with [Setup](0-setup.md).
