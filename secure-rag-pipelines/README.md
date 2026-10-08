# Secure Your RAG Pipelines with Fine-Grained Authorization (Pre-Filter & Post-Filter)

Say you build a RAG assistant for your company. Everyone asks it questions, and it answers from the same pile of internal documents. Then someone in sales asks about the engineering roadmap, and the bot happily summarizes it. Oops.

That's the whole problem in one sentence: semantic search ranks documents by what they're *about*, not by *who's allowed to read them*. This workshop fixes that with SpiceDB, and it teaches you the two ways to do it.

1. **Post-filter.** Retrieve first, then check each document with `CheckPermission` and drop the ones the user can't see.
2. **Pre-filter.** Ask SpiceDB which documents the user may see with `LookupResources` *before* you retrieve, and search only inside that set.

You'll build both, flip between them live with a toggle, and learn when to reach for which. Then you'll pick up two smaller SpiceDB features: bulk permission checks, and grants that expire on their own.

The stack runs entirely on your machine: **SpiceDB** for authorization, **Qdrant** (open source) for the vector store, local **fastembed** embeddings (no key), and any OpenAI-compatible chat model for the answer.

### Why this matters

AI can't secure AI.

Enterprise AI has one rule you don't get to break: a user can only ever augment a prompt with data they're allowed to see. You can't hand that job to the model, because models guess. They hallucinate, they get prompt-injected, they misread the room. Authorization has to be deterministic, and it has to live outside the model, in code that runs whether or not the model "remembers" the rule.

The right tool for this is **Relationship-Based Access Control (ReBAC)**: decisions based on the relationships between things (who owns what, who's on which team, what a role grants). It's more precise and more composable than RBAC or ABAC, and it's what SpiceDB was built for.

### What you'll build

![post-filter](/secure-rag-pipelines/images/post-filter.png)

![pre-filter](/secure-rag-pipelines/images/pre-filter.png)

- A LangGraph agentic RAG pipeline (`prefilter → retrieve → authorize → generate`) over a 50-document corpus owned by five different departments, with a web UI
- The naive version leaking documents across departments, so you can see the bug before you fix it
- Post-filter authorization with `CheckPermission`, so the agent can only ever answer from documents the user may see
- Pre-filter authorization with `LookupResources` feeding a Qdrant payload filter, side by side with post-filter so the trade-off is something you watch, not something you take on faith
- The per-document loop collapsed into one `CheckBulkPermissions` call, plus a contractor handed time-boxed access that expires on its own

It's built on an agentic RAG core (the reason-and-retry loop is still in there), taught with a pre-filter focus. The sibling [agentic-rag-authorization](https://github.com/authzed/workshops/tree/main/agentic-rag-authorization) workshop is the post-filter deep-dive, on Milvus.

### Prerequisites

- **Docker** (or a GitHub account, for Codespaces)
- **Python 3.11+**
- An **API key for a chat model**: OpenAI, or any OpenAI-compatible provider

Embeddings run locally through fastembed, so there's no key for those. The chat model is provider-agnostic: set `LLM_API_KEY`, `LLM_MODEL`, and (for anything but OpenAI) `LLM_BASE_URL` in `.env`. SpiceDB and Qdrant both run locally via Docker Compose, so there are no other accounts to create.

### Watch the talk

This conference talk walks through the ideas behind the workshop:

[![DevConf talk](/secure-rag-pipelines/images/youtube.png)](https://youtu.be/aeace8MDlhk "Secure RAG Pipelines")

---

**Last Updated**: Oct 8, 2026

### Workshop Modules

0. [Setup](0-setup.md)
1. [Part 1: Run the RAG (and watch it leak)](1-run-the-rag.md)
2. [Part 2: Secure it with post-filter](2-post-filter.md)
3. [Part 3: Pre-filter with LookupResources](3-pre-filter.md)
4. [Part 4: Smaller features (bulk checks and expiring grants)](4-smaller-features.md)
5. [Next steps](5-nextsteps.md)

Start with [Setup](0-setup.md).
