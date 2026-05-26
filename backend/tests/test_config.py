"""
Tests: agent package structure and LLM factory.

Validates that:
- The agent and agent.tools packages are importable
- get_llm() returns ChatOpenAI when OPENAI_API_KEY is valid
- get_llm() falls back to ChatOllama when OPENAI_API_KEY is absent/invalid
- get_llm() picks up OLLAMA_MODEL and OLLAMA_BASE_URL from env when using Ollama fallback
- get_classifier_llm() follows the same provider logic

No running LLM instance is required — instances are only created, never invoked.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Package structure
# ---------------------------------------------------------------------------


class TestPackageImports:
    def test_agent_package_importable(self):
        """import agent must succeed without errors."""
        import agent  # noqa: F401

        assert True

    def test_agent_tools_package_importable(self):
        """import agent.tools must succeed without errors."""
        import agent.tools  # noqa: F401

        assert True

    def test_agent_config_importable(self):
        """from agent.config import get_llm must succeed."""
        from agent.config import get_llm  # noqa: F401

        assert callable(get_llm)


# ---------------------------------------------------------------------------
# get_llm() — OpenAI primary
# ---------------------------------------------------------------------------


class TestGetLlmOpenAI:
    def test_get_llm_returns_openai_when_key_valid(self, monkeypatch):
        """get_llm() returns ChatOpenAI when OPENAI_API_KEY is set and API is reachable."""
        from langchain_openai import ChatOpenAI

        monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-key")

        mock_client = MagicMock()
        mock_client.models.list.return_value = []

        with patch("openai.OpenAI", return_value=mock_client):
            from agent.config import get_llm
            llm = get_llm()

        assert isinstance(llm, ChatOpenAI)

    def test_get_llm_uses_llm_model_env(self, monkeypatch):
        """When LLM_MODEL is set, get_llm() uses that model for OpenAI."""
        from langchain_openai import ChatOpenAI

        monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-key")
        monkeypatch.setenv("LLM_MODEL", "gpt-4-turbo")

        mock_client = MagicMock()
        mock_client.models.list.return_value = []

        with patch("openai.OpenAI", return_value=mock_client):
            from agent.config import get_llm
            llm = get_llm()

        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4-turbo"


# ---------------------------------------------------------------------------
# get_llm() — Ollama fallback
# ---------------------------------------------------------------------------


class TestGetLlmOllamaFallback:
    def test_get_llm_falls_back_to_ollama_when_no_key(self, monkeypatch):
        """get_llm() returns ChatOllama when OPENAI_API_KEY is absent."""
        from langchain_ollama import ChatOllama

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from agent.config import get_llm
        llm = get_llm()

        assert isinstance(llm, ChatOllama)

    def test_get_llm_falls_back_to_ollama_when_key_is_placeholder(self, monkeypatch):
        """get_llm() returns ChatOllama when OPENAI_API_KEY is the placeholder value."""
        from langchain_ollama import ChatOllama

        monkeypatch.setenv("OPENAI_API_KEY", "sk-...")

        from agent.config import get_llm
        llm = get_llm()

        assert isinstance(llm, ChatOllama)

    def test_get_llm_uses_ollama_model_env(self, monkeypatch):
        """When using Ollama fallback, OLLAMA_MODEL is respected."""
        from langchain_ollama import ChatOllama

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")

        from agent.config import get_llm
        llm = get_llm()

        assert isinstance(llm, ChatOllama)
        assert llm.model == "llama3.1"

    def test_get_llm_uses_ollama_base_url_env(self, monkeypatch):
        """When using Ollama fallback, OLLAMA_BASE_URL is respected."""
        from langchain_ollama import ChatOllama

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://remote-ollama:11434")

        from agent.config import get_llm
        llm = get_llm()

        assert isinstance(llm, ChatOllama)
        assert llm.base_url == "http://remote-ollama:11434"

    def test_get_llm_default_ollama_model(self, monkeypatch):
        """When OLLAMA_MODEL is absent and no OpenAI key, default model is llama3.2."""
        from langchain_ollama import ChatOllama

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)

        from agent.config import get_llm
        llm = get_llm()

        assert isinstance(llm, ChatOllama)
        assert llm.model == "llama3.2"
