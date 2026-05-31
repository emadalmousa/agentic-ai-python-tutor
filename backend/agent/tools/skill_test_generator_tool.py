import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm
from agent.tools._utils import _parse_json


@tool
def generate_skill_test(skill_key: str, skill_label: str, user_level: str) -> str:
    """Generiert einen vollständigen Skill-Test mit 3 Multiple-Choice-Fragen,
    einer Code-Lese-Aufgabe und einer Mini-Aufgabe.

    Gibt ein JSON-Objekt zurück das dem Skill Test Question Shape entspricht.
    """
    llm = get_llm()

    system = SystemMessage(content=(
        "Du bist ein Python-Prüfer. Erstelle einen Skill-Test auf Deutsch.\n\n"
        "Der Test muss GENAU dieses JSON-Format haben, ohne Markdown oder Text davor/danach:\n"
        "{\n"
        '  "multiple_choice": [\n'
        '    {"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, '
        '"correct": "A", "explanation": "..."},\n'
        '    {"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, '
        '"correct": "B", "explanation": "..."},\n'
        '    {"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, '
        '"correct": "C", "explanation": "..."}\n'
        "  ],\n"
        '  "code_reading": {\n'
        '    "code": "...",\n'
        '    "question": "...",\n'
        '    "correct_answer": "..."\n'
        "  },\n"
        '  "mini_task": {\n'
        '    "description": "...",\n'
        '    "expected_output": "..."\n'
        "  }\n"
        "}\n\n"
        "Anforderungen:\n"
        "- Genau 3 Multiple-Choice-Fragen (nicht mehr, nicht weniger)\n"
        "- correct-Feld muss exakt 'A', 'B', 'C' oder 'D' sein (Großbuchstabe)\n"
        "- code_reading.code muss ein kurzes, lesbares Python-Snippet sein (max. 10 Zeilen)\n"
        "- mini_task.expected_output muss die exakte stdout-Ausgabe sein\n"
        "- Alle Texte auf Deutsch\n"
        "- Fragen dem Skill und Niveau angemessen\n"
        "- explanation erklärt warum die Antwort korrekt ist"
    ))
    human = HumanMessage(content=(
        f"Skill: {skill_label} ({skill_key})\n"
        f"Niveau des Schülers: {user_level}\n\n"
        "Erstelle den Skill-Test."
    ))
    response = llm.invoke([system, human])
    try:
        result = _parse_json(response.content)
        # Validate structure minimally
        if "multiple_choice" not in result or len(result["multiple_choice"]) != 3:
            raise ValueError("multiple_choice must have exactly 3 questions")
        if "code_reading" not in result:
            raise ValueError("code_reading section missing")
        if "mini_task" not in result:
            raise ValueError("mini_task section missing")
        return json.dumps(result, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        # Return a minimal valid fallback test
        fallback = {
            "multiple_choice": [
                {
                    "question": f"Was ist das Hauptmerkmal von '{skill_label}'?",
                    "options": {
                        "A": "Es ist ein Python-Schlüsselwort",
                        "B": "Es ermöglicht strukturierten Code",
                        "C": "Es wird nur in Klassen verwendet",
                        "D": "Es ist nur für Experten",
                    },
                    "correct": "B",
                    "explanation": f"'{skill_label}' ermöglicht strukturierten und lesbaren Python-Code.",
                },
                {
                    "question": "Welche Aussage ist korrekt?",
                    "options": {
                        "A": "Python ist eine kompilierte Sprache",
                        "B": "Python ist eine interpretierte Sprache",
                        "C": "Python hat keine Standardbibliothek",
                        "D": "Python unterstützt keine Funktionen",
                    },
                    "correct": "B",
                    "explanation": "Python wird interpretiert, nicht kompiliert.",
                },
                {
                    "question": "Was gibt print('Hallo') aus?",
                    "options": {
                        "A": "hallo",
                        "B": "'Hallo'",
                        "C": "Hallo",
                        "D": "print(Hallo)",
                    },
                    "correct": "C",
                    "explanation": "print() gibt den Text ohne Anführungszeichen aus.",
                },
            ],
            "code_reading": {
                "code": "x = 5\ny = 3\nprint(x + y)",
                "question": "Was gibt dieser Code aus?",
                "correct_answer": "8",
            },
            "mini_task": {
                "description": f"Schreibe ein kurzes Python-Programm das das Konzept '{skill_label}' demonstriert und 'Fertig' ausgibt.",
                "expected_output": "Fertig",
            },
        }
        return json.dumps(fallback, ensure_ascii=False)
