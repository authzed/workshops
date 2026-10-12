## AuthZed Workshops

Here's the hub for all self-guided AuthZed workshops.  

#### 1. Building Authorization for Agentic RAG Systems
This workshop teaches you to add a deterministic authorization boundary to an agentic RAG system. You'll run a LangGraph-based agentic RAG, watch semantic search leak documents across departments, then implement a SpiceDB permission check the agent can't bypass. Uses SpiceDB, Milvus, LangGraph, OpenAI, and Docker Compose. [Link](https://github.com/authzed/workshops/tree/main/agentic-rag-authorization)

#### 2. Delegated Authorization for AI Agents
This workshop teaches you to give AI agents fine-grained, delegated permissions instead of broad ambient credentials. You'll build a DevOps deploy agent on goose and model delegation with SpiceDB using Relationship-Based Access Control (ReBAC): scoped delegation, time-bound grants that expire on their own, instant revocation, and hierarchical permissions. Uses SpiceDB, goose, Python, and Docker. [Link](https://github.com/authzed/workshops/tree/main/delegated-agent-authorization)

#### 3. Secure Your RAG Pipelines With Fine-Grained Authorization (Pre-Filter & Post-Filter)
This hands-on workshop teaches two ways to stop a RAG pipeline from leaking documents across users. You'll run an agentic RAG over a multi-department corpus, watch it leak, then lock it down with post-filter (CheckPermission after retrieval) and pre-filter (LookupResources before retrieval), comparing the two live with a UI toggle. It closes with bulk permission checks and self-expiring grants. Uses SpiceDB, Qdrant, local fastembed embeddings, a provider-agnostic chat model, LangGraph, and Docker. [Link](https://github.com/authzed/workshops/tree/main/secure-rag-pipelines)

An older notebook-based variant using DeepSeek R1 (via OpenRouter), Pinecone, and OpenAI embeddings lives on a separate branch. [Link](https://github.com/authzed/workshops/tree/deepseek/secure-rag-pipelines)

#### 4. Update A Web View Based on Permissions
This workshop will illustrate how you can update a view based on what permissions the user has. The workshop uses a NextJS template by Vercel for an admin dashboard, written in TypeScript. [Link](https://github.com/authzed/workshops/tree/main/update-views-authorization)

#### 5. From Zero to Permissions System in 10 Minutes using AuthZed MCP Servers
This workshop teaches you how to build and reason about authorization systems using **AuthZed** and **SpiceDB**, powered by **Model Context Protocol (MCP)** servers.  [Link](https://github.com/authzed/workshops/tree/main/mcp-assisted-authorization)

## Contributing

1. To update or contribute to a workshop, make a [pull request](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) with a detailed description of all changes made.