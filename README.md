# AuthZed Workshops

Self-guided, hands-on workshops for fine-grained authorization with [SpiceDB](https://authzed.com/spicedb). Each one runs locally, builds something real, and ends with working code. Pick one and start.

| Workshop | What you build | Stack |
| --- | --- | --- |
| **[Building Authorization for Agentic RAG Systems](https://github.com/authzed/workshops/tree/main/agentic-rag-authorization)** | Watch an agentic RAG leak documents across departments, then add a SpiceDB permission check the agent can't bypass. | SpiceDB, Milvus, LangGraph, OpenAI, Docker |
| **[Delegated Authorization for AI Agents](https://github.com/authzed/workshops/tree/main/delegated-agent-authorization)** | Give a DevOps deploy agent scoped, delegated permissions: time-bound grants that expire on their own, instant revocation, and a permission hierarchy. | SpiceDB, goose, Python, Docker |
| **[Secure Your RAG Pipelines (Pre-Filter & Post-Filter)](https://github.com/authzed/workshops/tree/main/secure-rag-pipelines)** | Stop a RAG pipeline leaking two ways, post-filter and pre-filter, compared live with a toggle, then add bulk checks and self-expiring grants. | SpiceDB, Qdrant, fastembed, LangGraph, Docker |
| **[Update a Web View Based on Permissions](https://github.com/authzed/workshops/tree/main/update-views-authorization)** | Render an admin dashboard whose UI changes with the viewer's permissions. | SpiceDB, Next.js, TypeScript |
| **[Zero to Permissions System in 10 Minutes with MCP](https://github.com/authzed/workshops/tree/main/mcp-assisted-authorization)** | Build and reason about an authorization model using AuthZed's Model Context Protocol (MCP) servers. | SpiceDB, AuthZed, MCP |

> **Secure Your RAG Pipelines** also has an older notebook-based variant (DeepSeek R1 via OpenRouter, Pinecone, OpenAI embeddings) on a [separate branch](https://github.com/authzed/workshops/tree/deepseek/secure-rag-pipelines).

## New to SpiceDB?

Start with **Secure Your RAG Pipelines** or **Building Authorization for Agentic RAG Systems**. Both open with a working app that leaks data, so you see the problem before you fix it. No prior authorization background is assumed; comfort with a terminal, Python, and Docker is enough.

## Contributing

To update or contribute to a workshop, open a [pull request](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) with a clear description of your changes.
