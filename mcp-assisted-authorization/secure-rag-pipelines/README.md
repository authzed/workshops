## Secure Your RAG Pipelines With Fine Grained Authorization (Pre-Filter & Post-Filter)

This workshop gives you hands-on knowledge on using SpiceDB to safeguard sensitive data in RAG pipelines. You will learn two techniques

1. How to pre-filter a vector database queries with a list of authorized object IDs
2. How to retrieve relevant documents and then check for permissions using post-filter

Using fine-grained authorization in RAG improves security and efficiency. This workshop uses OpenAI, Pinecone, Langchain, Jupyter Notebook and SpiceDB.

### Why is this important? 

Building enterprise-ready AI requires ensuring users can only augment prompts with data they're authorized to access. Fine-grained authorization in Retrieval-Augmented Generation (RAG) can be achieved with Relationship-based Access Control (ReBAC). ReBAC enables decisions based on relationships between objects, offering more precise control compared to traditional models like RBAC and ABAC.

The pre-requisites for the workshop: 


- Access to a SpiceDB instance and API key
- A Pinecone account and API key
- An OpenAI account and API key
- Jupyter Notebook and Python installed


## Architecture Diagram

Here is a high-level architecture diagram of a typical RAG pipeline. Notice the lack of authorization
![architecture diagram](/secure-rag-pipelines/images/RAG_pipelines.png)

Check out this conference talk that explains all of the concepts in this workshop

[![DevConf talk](/secure-rag-pipelines/images/youtube.png)](https://youtu.be/aeace8MDlhk "Secure RAG Pipelines")

**Last Updated**: Oct 15, 2025

### Workshop Modules

0. [Setup](https://github.com/authzed/workshops/blob/main/secure-rag-pipelines/00-setup.md)
1. [Secure Your RAG Pipelines With Fine Grained Authorization](https://github.com/authzed/workshops/blob/main/secure-rag-pipelines/01-rag.ipynb)
