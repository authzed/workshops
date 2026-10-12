"""Retrieval node - retrieve documents from Qdrant using semantic vector search."""

from langchain_core.messages import SystemMessage
from langchain_core.documents import Document
from qdrant_client.models import Filter, FieldCondition, MatchAny

from ..state import AgenticRAGState
from ..config import get_config
from ..logging_config import get_logger
from ..qdrant_client import get_qdrant_client
from ..node_helpers import embed, log_node_execution

logger = get_logger("nodes.retrieval")


def retrieval_node(state: AgenticRAGState) -> dict:
    """Retrieve documents from Qdrant based on semantic similarity to the query.

    In pre-filter mode, ``state['allowed_doc_ids']`` restricts the search to the
    documents the subject may view (a Qdrant payload filter on ``doc_id``); an
    empty allow-list means the subject can see nothing, so we retrieve nothing.
    """
    config = get_config()

    with log_node_execution(
        logger,
        "retrieval",
        {"query": state["query"], "subject_id": state["subject_id"]},
    ):
        try:
            allowed = state.get("allowed_doc_ids")
            if allowed is not None and len(allowed) == 0:
                # Pre-filter resolved to zero viewable docs, so retrieve nothing.
                return {
                    "retrieved_documents": [],
                    "retrieval_attempt": state["retrieval_attempt"] + 1,
                    "messages": [
                        SystemMessage(content="Retrieved 0 documents (no accessible docs)")
                    ],
                }

            client = get_qdrant_client(config.qdrant_url)
            query_embedding = embed(state["query"])

            query_filter = None
            if allowed:
                query_filter = Filter(
                    must=[FieldCondition(key="doc_id", match=MatchAny(any=allowed))]
                )

            response = client.query_points(
                collection_name="Documents",
                query=query_embedding,
                limit=5,
                with_payload=True,
                query_filter=query_filter,
                score_threshold=config.score_threshold,
            )

            documents = [
                Document(
                    page_content=p.payload["content"],
                    metadata={
                        "doc_id": p.payload["doc_id"],
                        "title": p.payload["title"],
                        "department": p.payload["department"],
                        "classification": p.payload["classification"],
                    },
                )
                for p in response.points
            ]

            logger.info(
                "Retrieved documents",
                extra={
                    "document_count": len(documents),
                    "doc_ids": [doc.metadata.get("doc_id") for doc in documents],
                },
            )

            return {
                "retrieved_documents": documents,
                "retrieval_attempt": state["retrieval_attempt"] + 1,
                "messages": [
                    SystemMessage(content=f"Retrieved {len(documents)} documents from Qdrant")
                ],
            }

        except Exception as e:
            logger.error(
                "Retrieval failed",
                extra={
                    "query": state["query"],
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            return {
                "retrieved_documents": [],
                "retrieval_attempt": state["retrieval_attempt"] + 1,
                "messages": [
                    SystemMessage(
                        content=f"Retrieval failed: {str(e)}. Unable to retrieve documents."
                    )
                ],
            }
