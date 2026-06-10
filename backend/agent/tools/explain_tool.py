"""LangChain-Tool: erklärt Python-Code in einfacher deutscher Sprache."""
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm


@tool
def explain_code_tool(code: str) -> str:
    """Erklärt Python-Code Schritt für Schritt auf Deutsch.

    Wird vom ReAct-Agenten bei Verständnisfragen aufgerufen.
    Antwort ist bewusst kurz (3-4 Sätze) — Anfänger überfordert zu viel Text.
    """
    llm = get_llm()
    system = SystemMessage(content=(
        "Du bist ein Python-Tutor für Anfänger. Antworte KURZ und EINFACH.\n\n"
        "Maximal 3-4 Sätze:\n"
        "1. Was macht der Code? (1 Satz)\n"
        "2. Wie funktioniert er? (1-2 Sätze, einfache Sprache)\n"
        "3. Hat er einen Fehler? Falls ja: was und wie beheben? (1 Satz)\n\n"
        "Kein Fachjargon. Keine langen Listen. Auf Deutsch."
    ))
    human = HumanMessage(content=f"Code:\n```python\n{code}\n```")
    response = llm.invoke([system, human])
    return str(response.content)
