"""LangChain-Tool: analysiert Python-Code auf Fehler und gibt strukturiertes JSON zurück."""
import json
import re
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm


@tool
def debug_code_tool(code: str) -> dict:
    """Analysiert Python-Code auf Fehler und gibt strukturiertes Ergebnis zurück.

    Gibt ein Dict mit error_found (bool), error_type (str) und suggestion (str) zurück.
    Wird vom ReAct-Agenten aufgerufen wenn der Student einen Fehler vermutet.
    """
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
    """Parst die LLM-Antwort tolerant gegenüber Markdown-Wrapping und fehlenden Feldern.

    Drei Versuche in aufsteigender Toleranz:
    1. Direktes JSON-Parsing (bestes Szenario)
    2. Markdown-Marker entfernen und nochmal versuchen
    3. Sicheres Fallback-Dict zurückgeben
    """
    # Versuch 1: direkt als JSON parsen
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # Versuch 2: ``` und ```json Marker entfernen
    stripped = re.sub(r'^```(?:json)?\s*', '', content.strip(), flags=re.MULTILINE)
    stripped = re.sub(r'```\s*$', '', stripped.strip(), flags=re.MULTILINE)
    try:
        result = json.loads(stripped.strip())
        # error_type ableiten wenn nicht im JSON vorhanden (ältere LLM-Versionen)
        if "error_type" not in result:
            result["error_type"] = "Syntaxfehler" if result.get("error_found") else "Kein Fehler"
        return result
    except json.JSONDecodeError:
        pass

    # Versuch 3: sicheres Default zurückgeben — lieber "kein Fehler" als Crash
    return {"error_found": False, "error_type": "Kein Fehler", "suggestion": "Analyse nicht möglich."}
