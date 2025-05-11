# AI Agent Authorization Demo using SpiceDB, Pinecone, and OpenAI

This demo shows how to build a secure Retrieval-Augmented Generation (RAG) pipeline where AI Agents can only access documents they are authorized for. Authorization decisions are enforced by SpiceDB.

## Features

* Define agents and documents in SpiceDB
* Assign document read permissions to specific agents
* Store documents and embeddings in Pinecone
* Secure RAG pipeline: filter document retrievals based on real-time SpiceDB checks
* Prevent unauthorized data from ever reaching the AI model

## Stack

* **SpiceDB** for permissions and relationship management
* **Pinecone** as vector database for document embeddings
* **OpenAI GPT-4** for language generation
* **Python + Jupyter Notebook** for orchestration

## Prerequisites

* Python 3.8+
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

3. Open the Jupyter notebook and run all cells

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
await query_rag_with_authz("agent-007", "What is the content of project doc-2?")
```

## Demo scenario

* `agent-007` can view `doc-1`, `doc-2`
* `agent-042` can view `doc-3`
* Unauthorized document mentions are blocked with clear feedback

## Notes

* This demo is built for educational and prototype purposes
* In production, always secure your keys and consider rate limits & latency

## TO DO

This snippet does a substring match and not an exact document ID match. 

```
for doc_id in unauthorized_docs:
    if doc_id in user_query:
        return f"You are not authorized to view the contents of document '{doc_id}'."
```


