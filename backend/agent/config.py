"""LLM-Konfiguration: Wählt OpenAI oder Ollama basierend auf verfügbaren Credentials.

Alle get_*-Funktionen verwenden das gleiche Muster:
  1. OPENAI_API_KEY gesetzt und nicht Platzhalter → OpenAI versuchen
  2. OpenAI nicht erreichbar → Fallback auf lokales Ollama
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)


def get_classifier_llm():
    """Gibt ein billiges/schnelles Modell für Klassifikationsaufgaben zurück.

    Verwendet gpt-4o-mini statt gpt-4o — Klassifikation (ja/nein) braucht kein starkes Modell.
    temperature=0 für deterministische Antworten.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-..."):
        # sk-... ist der Platzhalter in .env.example — echte Keys haben andere Präfixe
        try:
            from langchain_openai import ChatOpenAI
            import openai
            client = openai.OpenAI(api_key=api_key)
            client.models.list()  # Verbindungstest: schlägt fehl wenn Key ungültig
            return ChatOpenAI(api_key=SecretStr(api_key), model="gpt-4o-mini", temperature=0)
        except Exception as e:
            logger.warning("OpenAI nicht verfügbar für Klassifikation (%s) — Fallback auf Ollama", e)
    from langchain_ollama import ChatOllama
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        temperature=0,
    )


def get_llm():
    """Gibt das Haupt-LLM für alle Tutor-Aufgaben zurück (OpenAI bevorzugt, Ollama als Fallback).

    Modell ist per LLM_MODEL-Env konfigurierbar, Standard ist gpt-4o.
    temperature=0 sorgt für konsistente, reproduzierbare Antworten.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    if api_key and not api_key.startswith("sk-..."):
        try:
            from langchain_openai import ChatOpenAI
            import openai
            client = openai.OpenAI(api_key=api_key)
            client.models.list()  # Verbindungstest vor dem Erstellen des LLM-Objekts
            logger.info("OpenAI API aktiv — verwende gpt-4o")
            return ChatOpenAI(
                api_key=SecretStr(api_key),
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


def get_embeddings():
    """Gibt ein Embedding-Modell zurück (OpenAI bevorzugt, Ollama als Fallback).

    Embeddings werden für den RAG-Vektorstore benötigt.
    OpenAI text-embedding-ada-002 ist Standard, Ollama nutzt das konfigurierte Modell.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    if api_key and not api_key.startswith("sk-..."):
        try:
            from langchain_openai import OpenAIEmbeddings
            import openai
            client = openai.OpenAI(api_key=api_key)
            client.models.list()  # Verbindungstest
            logger.info("OpenAI API aktiv — verwende OpenAIEmbeddings")
            return OpenAIEmbeddings(api_key=SecretStr(api_key))
        except Exception as e:
            logger.warning("OpenAI nicht verfügbar für Embeddings (%s) — Fallback auf Ollama", e)

    from langchain_ollama import OllamaEmbeddings
    logger.info("Verwende OllamaEmbeddings — Modell: %s", os.getenv("OLLAMA_MODEL", "llama3.2"))
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
    )
