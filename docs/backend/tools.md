# agent/tools/

**Pfad:** `backend/agent/tools/`
**Zweck:** Drei LangChain-Tools die vom ReAct-Agenten aufgerufen werden können. Jedes Tool ist eine mit `@tool` dekorierte Funktion — der Agent sieht die Docstring-Beschreibung und entscheidet selbst ob und wann er das Tool aufruft.

## Gemeinsames Muster

Alle Tools folgen demselben Muster:

```python
@tool
def tool_name(parameter: type) -> return_type:
    """Beschreibung für den Agenten."""
    llm = get_llm()           # Provider-agnostisch
    # ... Prompt bauen ...
    response = llm.invoke([system, human])
    return response.content
```

`get_llm()` aus `agent/config.py` entscheidet welcher Provider genutzt wird. Die Tools selbst wissen das nicht.

---

## explain_code_tool

**Datei:** `agent/tools/explain_tool.py`

```python
@tool
def explain_code_tool(code: str) -> str
```

**Aufgabe:** Erklärt Python-Code Schritt für Schritt auf Deutsch für Anfänger.

**System-Prompt Inhalt:**
- Beginne mit einem Satz: was der Code insgesamt macht
- Erkläre jede wichtige Zeile oder jeden Block nummeriert
- Erkläre verwendete Python-Konzepte kurz
- Bei Fehler im Code: erkläre auch was der Fehler bewirkt

**Eingabe:** `{"code": "for i in range(5):\n    print(i)"}`

**Ausgabe:** Langer Markdown-Text auf Deutsch

---

## debug_code_tool

**Datei:** `agent/tools/debug_tool.py`

```python
@tool
def debug_code_tool(code: str) -> dict
```

**Aufgabe:** Analysiert Python-Code auf Fehler und gibt ein strukturiertes JSON-Dict zurück.

**System-Prompt Inhalt:**
- Prüfe auf Syntaxfehler, Logikfehler und typische Anfängerfehler
- Antworte NUR mit JSON — kein Text davor oder danach

**Eingabe:** `{"code": "..."}`

**Ausgabe:**
```python
{
    "error_found": True,
    "error_type": "Syntaxfehler",
    "suggestion": "Fehlender Doppelpunkt nach der for-Schleife."
}
```

**`_parse_debug_response(content: str) -> dict`** (private Hilfsfunktion):

Parst die LLM-Antwort in drei Schritten:
1. Direktes JSON-Parsing (`json.loads`)
2. Code-Fence entfernen (`` ```json ... ``` ``) und erneut parsen
3. Fallback: `{"error_found": False, "error_type": "Kein Fehler", "suggestion": "Analyse nicht möglich."}`

---

## exercise_tool

**Datei:** `agent/tools/exercise_tool.py`

```python
@tool
def exercise_tool(code: str, error_found: bool, suggestion: str) -> str
```

**Aufgabe:** Generiert eine passende Übungsaufgabe basierend auf dem Code und dem gefundenen Fehler.

**System-Prompt Inhalt:**
- Wenn Fehler vorhanden: Übung die genau das fehlerhafte Konzept übt
- Wenn kein Fehler: leicht fortgeschrittenere Aufgabe die auf dem Code aufbaut

**Ausgabeformat** (vom System-Prompt verlangt):
```
🎯 Aufgabe: [Was der Schüler programmieren soll]
💡 Tipp: [Hilfreicher Hinweis]
✅ Ziel: [Was der fertige Code ausgeben soll]
```

**Eingabe:** `{"code": "...", "error_found": true, "suggestion": "..."}`

**Ausgabe:** Formatierter Aufgabentext auf Deutsch
