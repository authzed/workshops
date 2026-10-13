"""Tests for config loading."""

import os
from unittest.mock import patch
from agentic_rag.config import Config


def test_config_loads_qdrant_url():
    env = {
        "QDRANT_URL": "http://qdrant-host:6333",
        "LLM_API_KEY": "sk-test",
        "SPICEDB_TOKEN": "tok",
        "SPICEDB_ENDPOINT": "localhost:50051",
    }
    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()
    assert config.qdrant_url == "http://qdrant-host:6333"


def test_config_qdrant_default():
    env = {
        "LLM_API_KEY": "sk-test",
        "SPICEDB_TOKEN": "tok",
        "SPICEDB_ENDPOINT": "localhost:50051",
    }
    with patch.dict(os.environ, env, clear=True):
        config = Config.from_env()
    assert config.qdrant_url == "http://localhost:6333"


def test_config_has_qdrant_url():
    env = {"QDRANT_URL": "http://example:6333", "LLM_API_KEY": "sk-test"}
    with patch.dict(os.environ, env, clear=True):
        cfg = Config.from_env()
    assert cfg.qdrant_url == "http://example:6333"
    assert not hasattr(cfg, "milvus_uri")


def test_config_has_no_weaviate_fields():
    config = Config.from_env()
    assert not hasattr(config, "weaviate_url")
    assert not hasattr(config, "weaviate_api_key")
