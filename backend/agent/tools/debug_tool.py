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
        "Du bist ein Python-Debugger. Analysiere den Code auf Syntaxfehler und Logikfehler. "
        "Antworte NUR mit einem JSON-Objekt, kein Text davor oder danach:\n"
        '{"error_found": true/false, "suggestion": "Beschreibung auf Deutsch"}'
    ))
    human = HumanMessage(content=f"Code:\n```python\n{code}\n```")
    response = llm.invoke([system, human])
    return _parse_debug_response(response.content)


def _parse_debug_response(content: str) -> dict:
    """Robustly parse JSON response from LLM, handling markdown fences and malformed output."""
    # Versuche JSON direkt zu parsen
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # JSON aus Markdown-Blöcken extrahieren
    match = re.search(r'\{[^}]+\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: aus Text ableiten
    error_found = any(word in content.lower() for word in ["fehler", "error", "syntaxfehler", "problem"])
    return {"error_found": error_found, "suggestion": content.strip()}
