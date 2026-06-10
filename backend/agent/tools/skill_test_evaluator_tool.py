"""LangChain-Tool: bewertet die Antworten eines Skill-Tests.

Scoring-Übersicht:
- MC (3 Fragen): je 10 Punkte per Python-Stringvergleich — kein LLM nötig
- Code-Lesen:    30 Punkte per LLM (semantischer Vergleich, toleriert Formulierungsunterschiede)
- Mini-Task:     40 Punkte per LLM (prüft ob Code die erwartete Ausgabe produziert)
- Gesamt:        0-100, bestanden wenn >= 60

Für Code-Lesen und Mini-Task gibt es Conservative Fallbacks auf exakten Stringvergleich
falls das LLM nicht erreichbar ist oder kein gültiges JSON zurückgibt.
"""
import json
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm
from agent.tools._utils import _parse_json


@tool
def evaluate_skill_test(
    skill_key: str,
    mc_answers: str,
    mc_correct: str,
    mini_task_description: str,
    mini_task_expected: str,
    mini_task_code: str,
    code_reading_answer: str,
    code_reading_correct: str,
    mini_task_actual_output: str = "",
) -> str:
    """Bewertet die Antworten eines Skill-Tests.

    mc_answers und mc_correct sind kommagetrennte Strings (z.B. 'A,B,C').
    Gibt ein JSON-Objekt mit total_score, passed und per_question_feedback zurück.

    Scoring:
    - Jede MC-Frage: 10 Punkte × 3 = 30 Punkte gesamt (exakter String-Vergleich, kein LLM)
    - Code-Lesen: 30 Punkte (LLM bewertet semantisch)
    - Mini-Aufgabe: 40 Punkte (LLM bewertet ob Code die erwartete Ausgabe produziert)
    - Gesamt: 0-100, bestanden wenn >= 60
    """
    llm = get_llm()

    # --- MC-Bewertung (reines Python, kein LLM) ---
    answers = [a.strip().upper() for a in mc_answers.split(",") if a.strip()]
    corrects = [c.strip().upper() for c in mc_correct.split(",") if c.strip()]

    # Auf genau 3 Einträge auffüllen falls Eingabe fehlerhaft ist
    while len(answers) < 3:
        answers.append("")
    while len(corrects) < 3:
        corrects.append("")

    mc_feedback = []
    mc_score = 0
    for i in range(3):
        is_correct = answers[i] == corrects[i]  # exakter Vergleich: "A" == "A"
        if is_correct:
            mc_score += 10
        mc_feedback.append({
            "question_type": f"mc_{i + 1}",
            "correct": is_correct,
            "explanation": (
                f"Richtig! Die korrekte Antwort ist {corrects[i]}."
                if is_correct
                else f"Leider falsch. Du hast {answers[i] or '(keine Antwort)'} gewählt, "
                     f"die richtige Antwort wäre {corrects[i]} gewesen."
            ),
        })

    # --- Code-Lesen-Bewertung (LLM, semantisch) ---
    code_reading_score = 0
    code_reading_correct_flag = False
    code_reading_explanation = ""

    cr_system = SystemMessage(content=(
        "Du bist ein Python-Tutor. Bewerte ob die Antwort des Schülers auf die Code-Lese-Frage "
        "semantisch korrekt ist.\n\n"
        "Antworte NUR mit diesem JSON-Format, ohne Markdown oder Text davor/danach:\n"
        '{"correct": true, "explanation": "..."}\n\n'
        "Regeln:\n"
        "- correct: true wenn die Antwort semantisch mit der richtigen Antwort übereinstimmt "
        "(kleine Unterschiede in Formulierung sind ok — z.B. 'gibt 8 aus' = '8')\n"
        "- explanation: kurze deutsche Erklärung ob und warum die Antwort korrekt/falsch ist"
    ))
    cr_human = HumanMessage(content=(
        f"Richtige Antwort: {code_reading_correct}\n"
        f"Antwort des Schülers: {code_reading_answer}\n\n"
        "Ist die Antwort semantisch korrekt?"
    ))
    try:
        cr_response = llm.invoke([cr_system, cr_human])
        cr_result = _parse_json(str(cr_response.content))
        code_reading_correct_flag = bool(cr_result.get("correct", False))
        code_reading_explanation = cr_result.get("explanation", "")
        if code_reading_correct_flag:
            code_reading_score = 30
    except (json.JSONDecodeError, ValueError):
        # Konservativer Fallback: exakter Stringvergleich (case-insensitive)
        code_reading_correct_flag = (
            code_reading_answer.strip().lower() == code_reading_correct.strip().lower()
        )
        code_reading_score = 30 if code_reading_correct_flag else 0
        code_reading_explanation = (
            "Richtig!" if code_reading_correct_flag
            else f"Die richtige Antwort wäre: {code_reading_correct}"
        )

    code_reading_feedback = {
        "question_type": "code_reading",
        "correct": code_reading_correct_flag,
        "explanation": code_reading_explanation,
    }

    # --- Mini-Task-Bewertung (LLM) ---
    mini_task_score = 0
    mini_task_correct = False
    mini_task_explanation = ""

    mt_system = SystemMessage(content=(
        "Du bist ein Python-Tutor. Bewerte ob der Code des Schülers die erwartete Ausgabe produzieren würde.\n\n"
        "Antworte NUR mit diesem JSON-Format, ohne Markdown oder Text davor/danach:\n"
        '{"correct": true, "explanation": "..."}\n\n'
        "Regeln:\n"
        "- correct: true wenn der Code (wenn fehlerfrei ausgeführt) die erwartete Ausgabe produziert\n"
        "- Kleine Formatierungsunterschiede (z.B. zusätzlicher Zeilenumbruch) sind tolerierbar\n"
        "- explanation: kurze deutsche Erklärung"
    ))
    # Wenn subprocess-Ausgabe verfügbar → LLM bekommt die echte Ausgabe als zusätzlichen Kontext
    actual_output_section = (
        f"Tatsächliche Ausgabe (ausgeführt): {mini_task_actual_output}\n\n"
        if mini_task_actual_output
        else ""
    )
    mt_human = HumanMessage(content=(
        f"Aufgabe: {mini_task_description}\n"
        f"Erwartete Ausgabe: {mini_task_expected}\n\n"
        f"Code des Schülers:\n```python\n{mini_task_code}\n```\n\n"
        f"{actual_output_section}"
        "Würde dieser Code die erwartete Ausgabe produzieren?"
    ))
    try:
        mt_response = llm.invoke([mt_system, mt_human])
        mt_result = _parse_json(str(mt_response.content))
        mini_task_correct = bool(mt_result.get("correct", False))
        mini_task_explanation = mt_result.get("explanation", "")
        if mini_task_correct:
            mini_task_score = 40
    except (json.JSONDecodeError, ValueError):
        # LLM-Fehler → als falsch werten (kein Guess bei 40-Punkte-Aufgabe)
        mini_task_correct = False
        mini_task_explanation = "Die Bewertung konnte nicht durchgeführt werden."

    mini_task_feedback = {
        "question_type": "mini_task",
        "correct": mini_task_correct,
        "explanation": mini_task_explanation,
    }

    # --- Gesamt-Score berechnen ---
    total_score = mc_score + code_reading_score + mini_task_score
    passed = total_score >= 60  # Bestehensgrenze: 60 von 100 Punkten

    # Feedback-Liste: 3 MC + code_reading + mini_task (in dieser Reihenfolge)
    per_question_feedback = mc_feedback + [code_reading_feedback, mini_task_feedback]

    result = {
        "total_score": total_score,
        "passed": passed,
        "mc_score": mc_score,
        "code_reading_score": code_reading_score,
        "mini_task_score": mini_task_score,
        "per_question_feedback": per_question_feedback,
    }
    return json.dumps(result, ensure_ascii=False)
