## Secure Your RAG Pipelines With Fine Grained Authorization

This workshop gives you hands-on knowledge on using SpiceDB to safeguard sensitive data in RAG pipelines. You will learn how to pre-filter and post-filter vector database queries with a list of authorized object IDs to improve security and efficiency. This workshop uses OpenAI, Pinecone, Langchain, Jupyter Notebook and SpiceDB

### Why is this important? 

Building enterprise-ready AI poses challenges around data security, accuracy, scalability, and integration, especially in compliance-regulated industries like healthcare and finance. Firms are increasing efforts to mitigate risks associated with LLMs, particularly regarding sensitive data exfiltration of personally identifiable information and/or sensitive company data. The primary mitigation strategy is to build guardrails around Retrieval-Augmented Generation (RAG) to safeguard data while also optimizing query response quality and efficiency. 

To enable precise guardrails, one must implement permissions systems with advanced fine grained authorization capabilities such as returning lists of authorized subjects and accessible resources. Such systems ensure timely access to authorized data while preventing exfiltration of sensitive information, making RAGs more efficient and improving performance at scale

## Architecture Diagram

Here is a high-level architecture diagram of this demo
![architecture diagram](/secure-rag-pipelines/secure-rag.png)

**Last Updated**: Jun 12, 2025

### Workshop Modules

0. [Setup](https://github.com/authzed/workshops/blob/main/secure-rag-pipelines/00-setup.md)
1. [Secure Your RAG Pipelines With Fine Grained Authorization](https://github.com/authzed/workshops/blob/main/secure-rag-pipelines/01-rag.ipynb)
