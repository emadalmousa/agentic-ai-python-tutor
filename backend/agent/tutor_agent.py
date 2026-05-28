import re

from langchain.agents import create_agent

from agent.config import get_llm
from agent.tools.explain_tool import explain_code_tool
from agent.tools.debug_tool import debug_code_tool
from agent.tools.exercise_tool import exercise_tool


class ServiceUnavailableError(Exception):
    pass


_SYSTEM_PROMPT = """\
Du bist ein Python-Tutor für Anfänger. Halte alle Antworten kurz und einfach.

Du hast Zugriff auf folgende Werkzeuge:
- explain_code_tool: Erklärt Python-Code kurz auf Deutsch.
- debug_code_tool: Findet Fehler im Code.
- exercise_tool: Generiert eine kurze Übungsaufgabe.
Analysiere den Code:
1. Rufe explain_code_tool auf.
2. Rufe debug_code_tool auf.
3. Rufe exercise_tool auf.

Gib deine Antwort GENAU in diesem Format aus — KURZ und EINFACH:

Erklärung: <2-3 Sätze, einfache Sprache>
Fehler gefunden: <ja oder nein>
Fehlertyp: <kurz oder "Kein Fehler">
Verbesserungsvorschlag: <1 Satz oder "Kein Fehler gefunden.">
Nächste Übung: <kurze Aufgabe, max. 3 Sätze>
"""


def _parse_agent_output(text: str) -> dict:
    """Extrahiert die 5 Pflichtfelder aus der Agenten-Antwort. Gibt Defaults zurück wenn Felder fehlen."""
    def extract(label: str) -> str | None:
        pattern = rf"(?i){re.escape(label)}[:\s]+(.+?)(?=\n[A-ZÄÖÜa-zäöü][^\n]*:|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    explanation = extract("Erklärung") or text
    error_found_raw = (extract("Fehler gefunden") or "nein").lower()
    error_type = extract("Fehlertyp") or "Kein Fehler"
    suggestion = extract("Verbesserungsvorschlag") or "Keine Angabe"
    next_exercise = extract("Nächste Übung")

    return {
        "explanation": explanation,
        "error_found": "ja" in error_found_raw,
        "error_type": error_type,
        "suggestion": suggestion,
        "next_exercise": next_exercise,
    }


def _build_tools() -> list:
    return [explain_code_tool, debug_code_tool, exercise_tool]


def run_analysis(code: str) -> dict:
    """ReAct-Agent analysiert den Code mit allen verfügbaren Tools und gibt ein strukturiertes Ergebnis zurück."""
    try:
        llm = get_llm()
        tools = _build_tools()
        agent = create_agent(llm, tools, system_prompt=_SYSTEM_PROMPT)
        result = agent.invoke({
            "messages": [("human", f"Analysiere diesen Python-Code:\n```python\n{code}\n```")]
        })
        messages = result.get("messages", [])
        final_text = messages[-1].content if messages else ""
        return _parse_agent_output(final_text)
    except Exception as e:
        if _is_connection_error(e):
            raise ServiceUnavailableError(
                "LLM ist nicht erreichbar. Bitte prüfe die KI-Engine-Konfiguration."
            ) from e
        raise


def _is_connection_error(e: Exception) -> bool:
    msg = str(e).lower()
    class_name = type(e).__name__.lower()
    keywords = ["connection", "connect", "refused", "unreachable", "timeout"]
    return any(kw in msg or kw in class_name for kw in keywords)
