import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


def get_llm() -> ChatOllama:
    """
    Create and return a configured ChatOllama instance.

    Reads OLLAMA_BASE_URL and OLLAMA_MODEL from environment variables.
    Defaults to http://localhost:11434 and llama3.2 if not set.

    Returns:
        ChatOllama: Configured LLM client instance
    """
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        temperature=0,
    )
