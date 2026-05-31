import json
import re
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm


def _parse_json(text: str) -> dict:
    text = re.sub(r"```json\s*|\s*```", "", text).strip()
    return json.loads(text)


@tool
def generate_exercise(
    skill_key: str,
    skill_label: str,
    level: str,
    completed_exercise_titles: str,
) -> str:
    """Generiert dynamisch eine neue Übungsaufgabe für Intermediate- oder Advanced-Skills.

    Gibt ein JSON-Objekt mit title, description, expected_output und hint zurück.
    completed_exercise_titles ist eine kommagetrennte Liste bereits abgeschlossener Aufgabentitel.
    """
    llm = get_llm()

    difficulty_guidance = {
        "intermediate": (
            "Das Schwierigkeitsniveau ist 'Fortgeschritten' (Intermediate). "
            "Der Schüler kennt Python-Grundlagen und arbeitet jetzt mit objektorientierter Programmierung, "
            "Fehlerbehandlung, Dateioperationen oder funktionalen Konzepten."
        ),
        "advanced": (
            "Das Schwierigkeitsniveau ist 'Profi' (Advanced). "
            "Der Schüler beherrscht Python gut und arbeitet jetzt mit fortgeschrittenen Konzepten wie "
            "Vererbung, Dekoratoren, Generatoren, Rekursion oder Design Patterns."
        ),
    }.get(level, "Das Schwierigkeitsniveau ist Fortgeschritten.")

    already_done = ""
    if completed_exercise_titles.strip():
        already_done = (
            f"\nBereits abgeschlossene Aufgaben (diese Titel NICHT wiederverwenden):\n"
            f"{completed_exercise_titles}\n"
        )

    system = SystemMessage(content=(
        "Du bist ein kreativer Python-Tutor. Erstelle eine Übungsaufgabe auf Deutsch.\n\n"
        "Anforderungen:\n"
        "- Keine externen Bibliotheken (nur Python-Standardbibliothek)\n"
        "- Kein input() verwenden\n"
        "- Klare, deterministische expected_output (exakte Ausgabe des korrekten Codes)\n"
        "- Aufgabenbeschreibung vollständig auf Deutsch\n"
        "- Keine Wiederholung bereits abgeschlossener Aufgaben\n\n"
        "Antworte NUR mit diesem JSON-Format, ohne Markdown oder Text davor/danach:\n"
        '{"title": "...", "description": "...", "expected_output": "...", "hint": "..."}\n\n'
        "Feldregeln:\n"
        "- title: kurzer deutscher Titel (max. 60 Zeichen)\n"
        "- description: vollständige deutsche Aufgabenbeschreibung inkl. was ausgegeben werden soll\n"
        "- expected_output: exakte stdout-Ausgabe des korrekten Programms (Zeilenumbrüche als \\n)\n"
        "- hint: ein hilfreicher Tipp ohne die Lösung zu verraten"
    ))
    human = HumanMessage(content=(
        f"Skill: {skill_label} ({skill_key})\n"
        f"{difficulty_guidance}\n"
        f"{already_done}\n"
        "Erstelle eine passende Übungsaufgabe."
    ))
    response = llm.invoke([system, human])
    try:
        result = _parse_json(response.content)
        # Ensure all required fields are present
        for field in ("title", "description", "expected_output", "hint"):
            if not result.get(field):
                result[field] = f"[{field} nicht verfügbar]"
        return json.dumps(result, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        return json.dumps({
            "title": f"Aufgabe zu {skill_label}",
            "description": "Schreibe ein Python-Programm, das das aktuelle Konzept demonstriert.",
            "expected_output": "Hallo Welt",
            "hint": "Nutze das in dieser Lektion gelernte Konzept.",
        }, ensure_ascii=False)
