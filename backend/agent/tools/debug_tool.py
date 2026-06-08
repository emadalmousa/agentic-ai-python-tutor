import json
import re
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm


@tool
def debug_code_tool(code: str) -> dict:
    """Analysiert Python-Code auf Fehler und gibt strukturiertes Ergebnis zurück."""
    llm = get_llm()
    system = SystemMessage(content=(
        "Du bist ein Python-Debugger und Code-Reviewer für Anfänger.\n"
        "Analysiere den Code auf:\n"
        "- Syntaxfehler (fehlende Doppelpunkte, falsche Einrückung, etc.)\n"
        "- Logikfehler (Code läuft, macht aber das Falsche)\n"
        "- Typische Anfängerfehler\n"
        "- Verbesserungsvorschläge (auch wenn kein Fehler)\n\n"
        "Antworte NUR mit diesem JSON-Format, kein Text davor oder danach:\n"
        '{"error_found": true/false, "error_type": "Syntaxfehler"|"Logikfehler"|"Kein Fehler", '
        '"suggestion": "Konkrete Beschreibung auf Deutsch was falsch ist oder wie man es verbessern kann"}'
    ))
    human = HumanMessage(content=f"Code:\n```python\n{code}\n```")
    response = llm.invoke([system, human])
    return _parse_debug_response(str(response.content))


def _parse_debug_response(content: str) -> dict:
    """Parst die LLM-Antwort tolerant gegenüber Markdown-Wrapping und fehlenden Feldern."""
    # Versuch 1: direkt als JSON parsen (bestes Szenario)
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # Versuch 2: Markdown-Code-Block-Marker entfernen und nochmal versuchen
    stripped = re.sub(r'^```(?:json)?\s*', '', content.strip(), flags=re.MULTILINE)
    stripped = re.sub(r'```\s*$', '', stripped.strip(), flags=re.MULTILINE)
    try:
        result = json.loads(stripped.strip())
        # error_type ableiten wenn nicht im JSON — ältere LLM-Versionen geben es nicht zurück
        if "error_type" not in result:
            result["error_type"] = "Syntaxfehler" if result.get("error_found") else "Kein Fehler"
        return result
    except json.JSONDecodeError:
        pass

    # Versuch 3 (Fallback): sicheres Default-Ergebnis zurückgeben
    return {"error_found": False, "error_type": "Kein Fehler", "suggestion": "Analyse nicht möglich."}
