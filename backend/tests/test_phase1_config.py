"""
Phase 1 tests: agent package structure and LLM factory.

Validates that:
- The agent and agent.tools packages are importable
- get_llm() returns a ChatOllama instance without contacting Ollama
- get_llm() picks up OLLAMA_MODEL and OLLAMA_BASE_URL from environment variables
- Default values are used when env vars are absent

No running Ollama instance is required — ChatOllama is only instantiated,
never invoked.
"""

import importlib
import os

import pytest
from langchain_ollama import ChatOllama


# ---------------------------------------------------------------------------
# Package structure
# ---------------------------------------------------------------------------


class TestPackageImports:
    def test_agent_package_importable(self):
        """import agent must succeed without errors."""
        import agent  # noqa: F401 (import-only test)

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
# get_llm() return type
# ---------------------------------------------------------------------------


class TestGetLlmReturnType:
    def test_get_llm_returns_chat_ollama(self):
        """get_llm() must return a ChatOllama instance (no LLM call made)."""
        from agent.config import get_llm

        llm = get_llm()

        assert isinstance(llm, ChatOllama)


# ---------------------------------------------------------------------------
# get_llm() reads environment variables
# ---------------------------------------------------------------------------


class TestGetLlmEnvVars:
    def test_get_llm_uses_env_model(self, monkeypatch):
        """When OLLAMA_MODEL is set, get_llm() uses that model name."""
        monkeypatch.setenv("OLLAMA_MODEL", "test-model")

        from agent.config import get_llm

        llm = get_llm()

        assert llm.model == "test-model"

    def test_get_llm_uses_env_base_url(self, monkeypatch):
        """When OLLAMA_BASE_URL is set, get_llm() uses that URL."""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://test:11434")

        from agent.config import get_llm

        llm = get_llm()

        assert llm.base_url == "http://test:11434"

    def test_get_llm_default_model_when_env_absent(self, monkeypatch):
        """When OLLAMA_MODEL is not set, get_llm() falls back to 'llama3.2'."""
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)

        from agent.config import get_llm

        llm = get_llm()

        assert llm.model == "llama3.2"

    def test_get_llm_default_base_url_when_env_absent(self, monkeypatch):
        """When OLLAMA_BASE_URL is not set, get_llm() falls back to localhost."""
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

        from agent.config import get_llm

        llm = get_llm()

        assert llm.base_url == "http://localhost:11434"

    def test_get_llm_each_call_reflects_current_env(self, monkeypatch):
        """get_llm() reads env at call time, so two calls with different env
        values must each return an instance configured for that call's env."""
        from agent.config import get_llm

        monkeypatch.setenv("OLLAMA_MODEL", "model-alpha")
        llm_alpha = get_llm()

        monkeypatch.setenv("OLLAMA_MODEL", "model-beta")
        llm_beta = get_llm()

        assert llm_alpha.model == "model-alpha"
        assert llm_beta.model == "model-beta"
