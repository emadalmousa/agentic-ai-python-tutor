from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm

_HINT_LEVEL_INSTRUCTIONS = {
    1: (
        "Stufe 1 — Konzepthinweis:\n"
        "Erkläre welches Python-Konzept oder welchen Ansatz der Schüler verwenden soll. "
        "Nenne KEINE konkreten Funktionen, Methoden oder Syntax. "
        "Nur die Idee und den Denkansatz beschreiben."
    ),
    2: (
        "Stufe 2 — Syntaxhinweis:\n"
        "Nenne die konkrete Python-Funktion, Methode, das Schlüsselwort oder die Struktur, "
        "die für diese Aufgabe benötigt wird. "
        "Zeige KEIN vollständiges Codebeispiel, aber erkläre kurz wie sie verwendet wird."
    ),
    3: (
        "Stufe 3 — Lösungsnaher Hinweis:\n"
        "Zeige die Code-Struktur oder einen partiellen Code-Schnipsel, "
        "der dem Schüler zeigt wie er anfangen soll. "
        "Lasse aber das Kernstück der Lösung offen — verrate NICHT die vollständige Lösung. "
        "Verwende Platzhalter wie '...' für die Teile, die der Schüler selbst ausfüllen soll."
    ),
}


@tool
def get_hint(code: str, exercise_description: str, hint_level: int) -> str:
    """Gibt einen gestuften Tipp für eine Python-Übungsaufgabe zurück.

    hint_level 1 = konzeptueller Tipp, 2 = Syntaxtipp, 3 = lösungsnaher Tipp.
    Gibt einen deutschen Klartext-String zurück (kein JSON).
    """
    llm = get_llm()
    level = max(1, min(3, int(hint_level)))
    level_instruction = _HINT_LEVEL_INSTRUCTIONS[level]

    system = SystemMessage(content=(
        "Du bist ein geduldiger und ermutigender Python-Tutor für Anfänger.\n"
        "Deine Aufgabe ist es, einen hilfreichen Tipp zu geben — aber NICHT die vollständige Lösung.\n\n"
        f"{level_instruction}\n\n"
        "Wichtig:\n"
        "- Antworte auf Deutsch\n"
        "- Sei ermutigend und positiv\n"
        "- Halte den Tipp kurz (2-4 Sätze)\n"
        "- Verrate niemals die vollständige Lösung\n"
        "- Wenn du Code-Beispiele zeigst, verwende immer Markdown-Code-Blöcke: ```python ... ```"
    ))
    human = HumanMessage(content=(
        f"Aufgabe:\n{exercise_description}\n\n"
        f"Bisheriger Code des Schülers:\n```python\n{code}\n```\n\n"
        f"Bitte gib einen Tipp der Stufe {level}."
    ))
    try:
        response = llm.invoke([system, human])
        return str(response.content)
    except Exception:
        return "Ein Tipp ist gerade nicht verfügbar. Bitte versuche es erneut."
