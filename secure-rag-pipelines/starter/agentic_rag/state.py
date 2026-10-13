"""State schema for agentic RAG with authorization."""

from typing import TypedDict, Annotated, List, Optional
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
import operator


class AgenticRAGState(TypedDict):
    """State for agentic RAG with authorization.

    This state flows through the LangGraph state machine, tracking:
    - User query and subject identity
    - Agent reasoning and messages
    - Retrieved and authorized documents
    - Authorization results and decisions
    """

    # Input
    query: str
    subject_id: str

    # Authorization mode: "post" (CheckPermission after retrieval) or "pre"
    # (LookupResources -> filter before retrieval)
    filter_mode: str
    # Pre-filter: document ids the subject may view (None in post mode)
    allowed_doc_ids: Optional[List[str]]

    # Configuration
    max_attempts: int

    # Agent messages (accumulated)
    messages: Annotated[List[BaseMessage], operator.add]

    # Retrieval
    retrieval_attempt: int
    retrieved_documents: List[Document]

    # Authorization (deterministic)
    authorized_documents: List[Document]
    denied_count: int
    authorization_passed: bool

    # Final output
    answer: str
    reasoning: List[str]
