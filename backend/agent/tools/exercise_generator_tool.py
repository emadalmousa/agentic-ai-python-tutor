"""LangChain-Tool: generiert dynamisch neue Übungsaufgaben für Intermediate/Advanced-Skills.

Wird vom Chat-Agenten über suggest_personalized_exercise aufgerufen wenn der Student
eine neue Übung für einen bestimmten Skill möchte.
Anders als die statische exercises.py-Bibliothek generiert dieses Tool jedes Mal neue,
abwechslungsreiche Aufgaben und vermeidet bereits abgeschlossene Aufgabentitel.
"""
import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm
from agent.tools._utils import _parse_json


@tool
def generate_exercise(
    skill_key: str,
    skill_label: str,
    level: str,
    completed_exercise_titles: str,
) -> str:
    """Generiert dynamisch eine neue Übungsaufgabe für Intermediate- oder Advanced-Skills.

    Gibt ein JSON-Objekt mit title, description, expected_output und hint zurück.
    completed_exercise_titles ist eine kommagetrennte Liste bereits abgeschlossener Aufgabentitel —
    das LLM soll diese nicht wiederholen um Abwechslung zu gewährleisten.
    """
    llm = get_llm()

    # Level-spezifische Schwierigkeitsbeschreibung für den LLM-Prompt
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

    # Bereits abgeschlossene Aufgaben in den Prompt einbauen damit keine Wiederholungen entstehen
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
        result = _parse_json(str(response.content))
        # Alle Pflichtfelder auf Vorhandensein prüfen
        for field in ("title", "description", "expected_output", "hint"):
            if not result.get(field):
                result[field] = f"[{field} nicht verfügbar]"
        return json.dumps(result, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        # Fallback damit der Student immer eine Aufgabe bekommt
        return json.dumps({
            "title": f"Aufgabe zu {skill_label}",
            "description": "Schreibe ein Python-Programm, das das aktuelle Konzept demonstriert.",
            "expected_output": "Hallo Welt",
            "hint": "Nutze das in dieser Lektion gelernte Konzept.",
        }, ensure_ascii=False)
