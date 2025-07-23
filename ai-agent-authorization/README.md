# AI Agent Authorization Workshop using SpiceDB, Pinecone, and OpenAI

This demo shows how to build a secure Retrieval-Augmented Generation (RAG) pipeline where AI Agents can only access documents they are authorized for. Authorization decisions are enforced by SpiceDB.

**Last updated**: Jun 16, 2025

## Features

* Define agents and documents in SpiceDB
* Assign document read permissions to specific agents
* Store documents and embeddings in Pinecone
* Secure RAG pipeline: filter document retrievals based on real-time SpiceDB checks
* Get a summary of only authorized documents
* Prevent unauthorized data from ever reaching the AI model

## Stack

* **SpiceDB** for permissions and relationship management
* **Pinecone** as vector database for document embeddings
* **OpenAI GPT-4** for language generation
* **Python + Jupyter Notebook** for orchestration

## Prerequisites

* Python 3.x
* SpiceDB instance
* API keys and accounts for:
  * Pinecone
  * OpenAI

## Setup

1. Clone this repo
2. Create a `.env` file with your keys:

```
SPICEDB_ADDR=<your-spicedb-endpoint>
SPICEDB_API_KEY=<your-spicedb-api-key>
PINECONE_API_KEY=<your-pinecone-api-key>
OPENAI_API_KEY=<your-openai-api-key>
```

3. Start SpiceDB locally by running the command

`spicedb serve --grpc-preshared-key "<SPICEDB_API_KEY>"`

4. Open the Jupyter notebook and run all cells

## How it works

1. **Schema setup:**

   * Define `agent` and `document` objects in SpiceDB.
2. **Permission setup:**

   * Assign `reader` relationships between agents and documents.
3. **Document storage:**

   * Upsert documents and OpenAI embeddings into Pinecone.
4. **Secure query:**

   * Retrieve candidate documents from Pinecone
   * Filter documents by SpiceDB permission checks
   * Send only authorized document content to OpenAI for response generation

## Example usage

```python
await query_rag_with_authz("sales-agent", "What is the content of project doc-2?")
summary = await summarize_accessible_docs("hr-agent")
```

## Demo scenario

* `sales-agent` can view `doc-1`, `doc-2`
* `hr-agent` can view `doc-3`
* Unauthorized document mentions are blocked with clear feedback

## Architecture Diagram

Here is a high-level architecture diagram of this demo
![architecture diagram](/ai-agent-authorization/pre-filter-authz.png)

Check out this YouTube video that explains the concepts in this workshop

[![AI Agent Authorization](ai-agent-authorization/yt-screen.png)](https://youtu.be/UjKa5T1dIVw "AI Agent Authorization")

## Notes

* This demo is built for educational and prototype purposes
* In production, always secure your keys and consider rate limits & latency




