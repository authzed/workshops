## AuthZed Workshops

Here's the hub for all self-guided AuthZed workshops.  

#### 1. Building Authorization for Agentic RAG Systems
This workshop teaches you to add a deterministic authorization boundary to an agentic RAG system. You'll run a LangGraph-based agentic RAG, watch semantic search leak documents across departments, then implement a SpiceDB permission check the agent can't bypass. Uses SpiceDB, Milvus, LangGraph, OpenAI, and Docker Compose. [Link](https://github.com/authzed/workshops/tree/main/agentic-rag-authorization)

#### 2. Delegated Authorization for AI Agents
This workshop teaches you to give AI agents fine-grained, delegated permissions instead of broad ambient credentials. You'll build a DevOps deploy agent on goose and model delegation with SpiceDB using Relationship-Based Access Control (ReBAC) — scoped delegation, time-bound grants that expire on their own, instant revocation, and hierarchical permissions. Uses SpiceDB, goose, Python, and Docker. [Link](https://github.com/authzed/workshops/tree/main/delegated-agent-authorization)

#### 3. Secure Your RAG Pipelines With Fine Grained Authorization
This workshop gives you hands-on knowledge on using SpiceDB to safeguard sensitive data in your RAG pipelines. There are different branches for this workshop:

- (recommended) Using the OpenAI API, Pinecone, a local Jupyter Notebook instance and SpiceDB. [Link](https://github.com/authzed/workshops/tree/main/secure-rag-pipelines)
- Using the Deepseek R1 LLM (via OpenRouter), Pinecone, OpenAI Embeddings, a local Jupyter Notebook instance and SpiceDB. [Link](https://github.com/authzed/workshops/tree/deepseek/secure-rag-pipelines)

#### 4. Update A Web View Based on Permissions
This workshop will illustrate how you can update a view based on what permissions the user has. The workshop uses a NextJS template by Vercel for an admin dashboard, written in TypeScript. [Link](https://github.com/authzed/workshops/tree/main/update-views-authorization)

#### 5. From Zero to Permissions System in 10 Minutes using AuthZed MCP Servers
This workshop teaches you how to build and reason about authorization systems using **AuthZed** and **SpiceDB**, powered by **Model Context Protocol (MCP)** servers.  [Link](https://github.com/authzed/workshops/tree/main/mcp-assisted-authorization)

## Contributing

1. To update or contribute to a workshop, make a [pull request](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) with a detailed description of all changes made.