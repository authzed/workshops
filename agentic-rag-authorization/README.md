# Building Authorization for Agentic RAG Systems

Semantic search doesn't know what a user is allowed to read. It retrieves by similarity — and similarity doesn't care about department boundaries, classification levels, or access policies. So when your AI agent runs a vector search to augment a prompt, it will cheerfully surface documents the user has no business seeing. The agent doesn't know any better. That's not a bug in the model — it's a gap in the architecture.

The fix is a deterministic SpiceDB permission check wired directly into the agent's retrieval step. Not a prompt instruction. Not a system message asking the LLM to "only use authorized content." A hard authorization node the agent can't reason its way around.

### Why is this important?

Enterprise AI has one non-negotiable: a user can only ever augment a prompt with data they're allowed to see. And you can't delegate that to the model — probabilistic systems hallucinate, misinterpret, and guess. **AI can't secure AI.** Authorization has to be deterministic.

Fine-grained authorization in agentic RAG is best achieved with **Relationship-based Access Control (ReBAC)**. ReBAC makes decisions based on relationships between objects (who owns what, who belongs to which team, what role grants what access) — which is more precise and composable than traditional RBAC or ABAC. SpiceDB implements ReBAC, and it's what we'll use here.

### What you'll build

- Run a LangGraph agentic RAG pipeline — retrieve → authorize → generate — backed by **Milvus** (vector DB) and **OpenAI** (embeddings + generation)
- Watch the naive version leak documents across departments: semantic similarity returns everything relevant, regardless of who's asking
- Implement the SpiceDB authorization node using the raw `authzed` Python SDK — a permission check the agent calls explicitly, before any document reaches the prompt
- Run the same query again and see it return only what the user is actually allowed to see

Two checkpoints. By the end, you have a working agentic RAG where authorization isn't advisory — it's structural.

### Workshop format

90 minutes total: roughly 25–30 minutes of talk, followed by 60 minutes of hands-on. There are two checkpoints to validate your progress along the way.

Setup involves pulling Docker images and seeding the vector DB — best done as pre-work before the session starts. The [Setup module](0-setup.md) walks you through it.

### Prerequisites

- **Docker** (or a GitHub account if you'd prefer to use Codespaces)
- **Python 3.10+**
- An **OpenAI API key**

SpiceDB and Milvus both run locally via Docker Compose — no additional accounts or cloud services needed.

### Stack

- **SpiceDB** — ReBAC authorization engine
- **Milvus** — vector database for semantic search
- **LangGraph** — agent orchestration (retrieve → authorize → generate)
- **OpenAI** — embeddings and response generation
- **Python** — everything is in Python; the `authzed` SDK handles SpiceDB calls directly

---

**Last Updated**: Jun 24, 2026

### Workshop Modules

0. [Setup](0-setup.md)
1. [Checkpoint 1 — Run the Agentic RAG (and watch it leak)](1-agentic-rag.md)
2. [Checkpoint 2 — Secure it with SpiceDB](2-secure-it.md)
3. [Next Steps](3-nextsteps.md)

Let's get started with [Setup](0-setup.md).
