import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)


def get_classifier_llm():
    """Gibt ein billiges/schnelles Modell für Klassifikation zurück."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-..."):
        try:
            from langchain_openai import ChatOpenAI
            import openai
            client = openai.OpenAI(api_key=api_key)
            client.models.list()
            return ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0)
        except Exception as e:
            logger.warning("OpenAI nicht verfügbar für Klassifikation (%s) — Fallback auf Ollama", e)
    from langchain_ollama import ChatOllama
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        temperature=0,
    )


def get_llm():
    api_key = os.getenv("OPENAI_API_KEY", "")

    if api_key and not api_key.startswith("sk-..."):
        try:
            from langchain_openai import ChatOpenAI
            import openai
            client = openai.OpenAI(api_key=api_key)
            client.models.list()
            logger.info("OpenAI API aktiv — verwende gpt-4o")
            return ChatOpenAI(
                api_key=api_key,
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                temperature=0,
            )
        except Exception as e:
            logger.warning("OpenAI nicht verfügbar (%s) — Fallback auf Ollama", e)

    from langchain_ollama import ChatOllama
    logger.info("Verwende Ollama — Modell: %s", os.getenv("OLLAMA_MODEL", "llama3.2"))
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        temperature=0,
    )
