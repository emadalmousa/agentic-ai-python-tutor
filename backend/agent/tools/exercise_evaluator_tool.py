import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm
from agent.tools._utils import _parse_json


@tool
def evaluate_exercise(
    code: str,
    exercise_description: str,
    expected_output: str,
    stdout: str,
) -> str:
    """Bewertet eine Schüler-Lösung für eine Python-Übungsaufgabe.

    Gibt ein JSON-Objekt mit result (richtig/teilweise/falsch),
    what_was_good, what_went_wrong und hint zurück.
    """
    llm = get_llm()

    # Priority 1: stdout is empty — must be falsch before calling LLM
    if not stdout.strip():
        system = SystemMessage(content=(
            "Du bist ein ermutigender Python-Tutor für Anfänger.\n"
            "Der Code des Schülers hat keine Ausgabe produziert (wahrscheinlich ein Laufzeitfehler "
            "oder der Code ist unvollständig).\n\n"
            "Antworte NUR mit diesem JSON-Format, ohne Markdown oder Text davor/danach:\n"
            '{"result": "falsch", "what_was_good": "...", "what_went_wrong": "...", "hint": "..."}\n\n'
            "Regeln:\n"
            "- result muss 'falsch' sein\n"
            "- what_was_good: finde etwas Positives im Code (z.B. Struktur, Ansatz)\n"
            "- what_went_wrong: erkläre auf Deutsch einfach, warum keine Ausgabe entstand\n"
            "- hint: gib einen konkreten ersten Schritt zum Beheben des Problems\n"
            "- Alle Texte auf Deutsch, anfängerfreundlich und ermutigend\n"
            "- Code-Beispiele in den Texten immer als Markdown-Code-Block formatieren: ```python ... ```"
        ))
        human = HumanMessage(content=(
            f"Aufgabenbeschreibung:\n{exercise_description}\n\n"
            f"Erwartete Ausgabe:\n{expected_output}\n\n"
            f"Code des Schülers:\n```python\n{code}\n```\n\n"
            "Der Code hat keine Ausgabe produziert."
        ))
        response = llm.invoke([system, human])
        try:
            return json.dumps(_parse_json(response.content), ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            return json.dumps({
                "result": "falsch",
                "what_was_good": "Der Ansatz ist erkennbar.",
                "what_went_wrong": "Der Code hat keine Ausgabe produziert.",
                "hint": "Prüfe ob dein Code eine print()-Anweisung enthält.",
            }, ensure_ascii=False)

    # Priority 2: exact stdout match — verify concept correctness via LLM
    if stdout.strip() == expected_output.strip():
        system = SystemMessage(content=(
            "Du bist ein ermutigender Python-Tutor für Anfänger.\n"
            "Die Ausgabe des Schüler-Codes stimmt exakt mit der erwarteten Ausgabe überein.\n\n"
            "Prüfe NUR: Löst der Code die Aufgabe wirklich mit dem richtigen Konzept, "
            "oder hat der Schüler die Ausgabe einfach mit print() hardcodiert (z.B. print('5') "
            "statt eine Schleife zu schreiben)?\n\n"
            "Antworte NUR mit diesem JSON-Format, ohne Markdown oder Text davor/danach:\n"
            '{"result": "richtig_oder_teilweise", "what_was_good": "...", "what_went_wrong": "...", "hint": "..."}\n\n'
            "Regeln für result:\n"
            "- 'richtig': Ausgabe korrekt UND Code verwendet das richtige Konzept\n"
            "- 'teilweise': Ausgabe korrekt ABER Code ist trivial hardcodiert oder umgeht das Konzept\n"
            "Regeln:\n"
            "- what_was_good: immer einen positiven Aspekt nennen (nie leer lassen)\n"
            "- what_went_wrong: leer lassen wenn result='richtig', sonst erklären was suboptimal ist\n"
            "- hint: bei 'richtig' einen Bonustipp geben; bei 'teilweise' zeigen wie man es richtig macht\n"
            "- Alle Texte auf Deutsch, anfängerfreundlich und ermutigend\n"
            "- Code-Beispiele in den Texten immer als Markdown-Code-Block formatieren: ```python ... ```"
        ))
        human = HumanMessage(content=(
            f"Aufgabenbeschreibung:\n{exercise_description}\n\n"
            f"Erwartete Ausgabe:\n{expected_output}\n\n"
            f"Code des Schülers:\n```python\n{code}\n```\n\n"
            f"Tatsächliche Ausgabe:\n{stdout}"
        ))
        response = llm.invoke([system, human])
        try:
            result = _parse_json(response.content)
            # Normalise the result field — LLM may return the literal placeholder
            if result.get("result") == "richtig_oder_teilweise":
                result["result"] = "richtig"
            if result.get("result") not in ("richtig", "teilweise", "falsch"):
                result["result"] = "richtig"
            # Ensure required fields are never empty
            if not result.get("what_was_good"):
                result["what_was_good"] = "Gute Arbeit — die Ausgabe ist korrekt!"
            if not result.get("hint"):
                result["hint"] = "Weiter so! Probiere die nächste Aufgabe."
            return json.dumps(result, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            return json.dumps({
                "result": "richtig",
                "what_was_good": "Die Ausgabe stimmt exakt mit der erwarteten Ausgabe überein.",
                "what_went_wrong": "",
                "hint": "Weiter so! Probiere die nächste Aufgabe.",
            }, ensure_ascii=False)

    # Priority 3: stdout does not match but is non-empty — LLM determines teilweise vs falsch
    system = SystemMessage(content=(
        "Du bist ein ermutigender Python-Tutor für Anfänger.\n"
        "Der Code des Schülers hat eine Ausgabe produziert, die NICHT mit der erwarteten übereinstimmt.\n\n"
        "Beurteile:\n"
        "- 'teilweise': wenn der Code das richtige Konzept verwendet, aber einen kleinen Fehler hat "
        "(z.B. falscher Startwert, falsche Berechnung, aber Schleife/Struktur korrekt)\n"
        "- 'falsch': wenn der Code das falsche Konzept verwendet oder grundlegend falsch ist\n\n"
        "Antworte NUR mit diesem JSON-Format, ohne Markdown oder Text davor/danach:\n"
        '{"result": "teilweise_oder_falsch", "what_was_good": "...", "what_went_wrong": "...", "hint": "..."}\n\n'
        "Regeln für result: entweder 'teilweise' oder 'falsch'\n"
        "- what_was_good: immer einen positiven Aspekt nennen (nie leer lassen)\n"
        "- what_went_wrong: erkläre konkret was falsch ist\n"
        "- hint: gib einen hilfreichen Hinweis ohne die vollständige Lösung zu verraten\n"
        "- Alle Texte auf Deutsch, anfängerfreundlich und ermutigend\n"
        "- Code-Beispiele in den Texten immer als Markdown-Code-Block formatieren: ```python ... ```"
    ))
    human = HumanMessage(content=(
        f"Aufgabenbeschreibung:\n{exercise_description}\n\n"
        f"Erwartete Ausgabe:\n{expected_output}\n\n"
        f"Code des Schülers:\n```python\n{code}\n```\n\n"
        f"Tatsächliche Ausgabe:\n{stdout}"
    ))
    response = llm.invoke([system, human])
    try:
        result = _parse_json(response.content)
        if result.get("result") not in ("richtig", "teilweise", "falsch"):
            result["result"] = "falsch"
        if not result.get("what_was_good"):
            result["what_was_good"] = "Du hast Code geschrieben — das ist der erste Schritt!"
        if not result.get("hint"):
            result["hint"] = "Schau dir die Aufgabenbeschreibung nochmal genau an."
        return json.dumps(result, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        return json.dumps({
            "result": "falsch",
            "what_was_good": "Du hast Code geschrieben — das ist der erste Schritt!",
            "what_went_wrong": "Die Ausgabe stimmt nicht mit der erwarteten Ausgabe überein.",
            "hint": "Vergleiche deine Ausgabe mit der erwarteten und finde den Unterschied.",
        }, ensure_ascii=False)
