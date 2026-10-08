"""Configuration management for agentic RAG system."""

from dataclasses import dataclass
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration for agentic RAG system."""

    # Qdrant (vector store)
    qdrant_url: str

    # SpiceDB
    spicedb_endpoint: str
    spicedb_token: str

    # Chat LLM (provider-agnostic). Embeddings run locally and need no key.
    # Works with OpenAI, Anthropic, Azure, Groq, Together, vLLM/Ollama, or any
    # OpenAI-compatible corporate endpoint. Leave llm_base_url blank for OpenAI.
    llm_api_key: str
    llm_model: str = "gpt-4"
    llm_base_url: str = ""

    # Agent behavior
    max_retrieval_attempts: int = 1

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            spicedb_endpoint=os.getenv("SPICEDB_ENDPOINT", "localhost:50051"),
            spicedb_token=os.getenv("SPICEDB_TOKEN", "devtoken"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "gpt-4"),
            llm_base_url=os.getenv("LLM_BASE_URL", ""),
            max_retrieval_attempts=int(os.getenv("MAX_RETRIEVAL_ATTEMPTS", "1")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@lru_cache
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config.from_env()
