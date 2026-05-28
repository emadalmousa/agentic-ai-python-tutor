# agent/tutor_agent.py

**Pfad:** `backend/agent/tutor_agent.py`
**Zweck:** Orchestriert die Code-Analyse über einen ReAct-Agenten. Der Agent entscheidet selbst welche Tools er aufruft und in welcher Reihenfolge.

## Kernkonzept: ReAct-Agent

Statt Tools fest nacheinander aufzurufen, bekommt der Agent alle Tools und einen System-Prompt. Er durchläuft einen **Reason → Act → Observe**-Loop:

1. Agent liest den Code und den System-Prompt
2. Agent entscheidet: "Ich brauche eine Erklärung" → ruft `explain_code_tool` auf
3. Agent sieht das Ergebnis (Observation) und entscheidet was als nächstes nötig ist
4. Wiederholt bis alle nötigen Tools aufgerufen wurden
5. Gibt eine Final Answer aus

Das ist der Unterschied zu einem normalen Chat-Bot: der Agent *überlegt* bevor er handelt.

## Öffentliche Schnittstelle

### `run_analysis(code: str) -> dict`

```python
def run_analysis(code: str) -> dict
```

Einzige öffentlich genutzte Funktion. Gibt immer ein Dict mit diesen Schlüsseln zurück:

```python
{
    "explanation": str,        # Erklärung auf Deutsch
    "error_found": bool,       # True wenn Fehler gefunden
    "error_type": str,         # "Syntaxfehler" | "Logikfehler" | "Kein Fehler"
    "suggestion": str,         # Verbesserungshinweis
    "next_exercise": str|None, # Übungsaufgabe
}
```

Wirft `ServiceUnavailableError` wenn das LLM nicht erreichbar ist → HTTP 503.

---

### `ServiceUnavailableError`

```python
class ServiceUnavailableError(Exception): pass
```

Wird in `main.py` als HTTP 503 zurückgegeben. Wird ausgelöst wenn das LLM einen Verbindungsfehler oder Timeout meldet.

## Private Funktionen

### `_build_tools() -> list`

Gibt die feste Tool-Liste zurück: `[explain_code_tool, debug_code_tool, exercise_tool]`.

### `_parse_agent_output(text: str) -> dict`

Extrahiert die 5 Pflichtfelder aus dem Free-Text der Agent-Antwort via Regex. Der System-Prompt verlangt ein bestimmtes Format (z.B. `Erklärung: ...`). Wenn ein Feld fehlt, wird ein sicherer Default zurückgegeben:

| Feld | Default wenn nicht gefunden |
|------|-----------------------------|
| `explanation` | Der gesamte Text |
| `error_found` | `False` |
| `error_type` | `"Kein Fehler"` |
| `suggestion` | `"Keine Angabe"` |
| `next_exercise` | `None` |

### `_is_connection_error(e: Exception) -> bool`

Prüft ob eine Exception ein Verbindungsproblem ist (ConnectionError, Timeout etc.). Entscheidet ob `ServiceUnavailableError` ausgelöst werden soll.

## Ablauf von `run_analysis`

```
run_analysis(code)
    │
    ├── get_llm()              → LLM-Instanz holen (OpenAI oder Ollama)
    ├── _build_tools()         → [explain_code_tool, debug_code_tool, exercise_tool]
    ├── create_agent(llm, tools, system_prompt)   → LangGraph CompiledStateGraph
    ├── agent.invoke({"messages": [...]})          → ReAct-Loop läuft
    └── _parse_agent_output(final_text)            → dict mit 5 Feldern
```

## System-Prompt

Der Agent bekommt einen deutschen System-Prompt der erklärt:
- Welche Tools vorhanden sind und wann sie genutzt werden sollen
- In welchem Format die Final Answer ausgegeben werden muss (Erklärung / Fehler gefunden / Fehlertyp / Verbesserungsvorschlag / Nächste Übung)
