"""Skill-Tests-Router: generiert und bewertet skill-spezifische Tests."""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.code_runner import run_user_code
from models.skill_progress import SKILL_TREE
from models.skill_test import SkillTestResult
from models.user import User
from routers.auth import get_current_user
from agent.tools.skill_test_generator_tool import generate_skill_test
from agent.tools.skill_test_evaluator_tool import evaluate_skill_test

router = APIRouter(prefix="/skill-tests", tags=["skill-tests"])

# Schneller Lookup: skill_key → skill-Metadaten
_SKILL_META: dict[str, dict] = {s["key"]: s for s in SKILL_TREE}


# ---------------------------------------------------------------------------
# Pydantic-Schemas
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Anfrage zur Test-Generierung für einen bestimmten Skill."""
    skill_key: str


class GenerateResponse(BaseModel):
    """Antwort mit Session-ID und den Testfragen (ohne richtige Antworten für MC)."""
    test_session_id: int  # wird beim Submit mitgeschickt um server-seitige Daten zu laden
    test_data: dict       # multiple_choice, code_reading, mini_task


class SubmitTestRequest(BaseModel):
    """Abgabe der Test-Antworten mit Referenz auf die server-seitige Session."""
    test_session_id: int              # verknüpft mit SkillTestResult.id in der DB
    skill_key: str
    mc_answers: dict[str, str]        # {"0": "A", "1": "B", "2": "C"}
    code_reading_answer: str
    mini_task_code: str               # Code des Studenten für die Mini-Aufgabe


class SubmitTestResponse(BaseModel):
    """Ergebnis der Test-Bewertung mit Score-Aufschlüsselung."""
    total_score: int         # 0-100
    passed: bool             # True wenn total_score >= 60
    mc_score: int            # 0-30 (3 × 10 Punkte)
    code_reading_score: int  # 0-30
    mini_task_score: int     # 0-40
    per_question_feedback: list  # Feedback pro Teilaufgabe
    attempt_number: int      # Versuchs-Nummer (erster Versuch = 1)


# ---------------------------------------------------------------------------
# POST /skill-tests/generate
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=GenerateResponse)
def generate_test(
    data: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generiert einen Skill-Test per LLM und speichert ihn server-seitig.

    Ablauf:
    1. Skill-Metadaten laden (Label für LLM-Prompt benötigt)
    2. LLM generiert Test: 3 MC-Fragen + Code-Lesen + Mini-Task
    3. Test inkl. richtiger Antworten in DB speichern
    4. Test-Daten an Client zurückgeben (ohne richtige MC-Antworten — die bleiben server-seitig)

    Warum server-seitig speichern? Der Client bekommt die generierten Fragen, aber die richtigen
    Antworten bleiben in generated_test in der DB — so kann der Student nicht schummeln.
    """
    skill = _SKILL_META.get(data.skill_key)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    # LangChain-Tool direkt aufrufen — generiert vollständigen Test in einem LLM-Aufruf
    raw_result = generate_skill_test.invoke({
        "skill_key": data.skill_key,
        "skill_label": skill["label"],
        "user_level": current_user.level,
    })
    test_data = json.loads(raw_result)

    # Versuchs-Nummer berechnen: wieviele Tests hat der Student für diesen Skill schon gemacht?
    prior_attempts = (
        db.query(SkillTestResult)
        .filter_by(user_id=current_user.id, skill_key=data.skill_key)
        .count()
    )
    attempt_number = prior_attempts + 1

    # Neuen DB-Eintrag anlegen mit score=0 — wird nach Submit aktualisiert
    session_row = SkillTestResult(
        user_id=current_user.id,
        skill_key=data.skill_key,
        score=0,
        passed=False,
        attempt_number=attempt_number,
        generated_test=test_data,  # speichert auch die richtigen Antworten
    )
    db.add(session_row)
    db.commit()
    db.refresh(session_row)  # lädt die server-generierte ID

    return GenerateResponse(test_session_id=session_row.id, test_data=test_data)


# ---------------------------------------------------------------------------
# POST /skill-tests/submit
# ---------------------------------------------------------------------------

@router.post("/submit", response_model=SubmitTestResponse)
def submit_test(
    data: SubmitTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bewertet die eingereichten Test-Antworten anhand der server-seitig gespeicherten Daten.

    Ablauf:
    1. Session-Zeile aus DB laden (enthält richtige Antworten)
    2. Mini-Task-Code via subprocess ausführen → stdout für LLM-Bewertung
    3. Richtige MC-Antworten aus DB-Daten extrahieren (nicht vom Client übernehmen)
    4. evaluate_skill_test-Tool aufrufen: MC (Python), Code-Lesen (LLM), Mini-Task (LLM)
    5. Score in DB aktualisieren
    """
    skill = _SKILL_META.get(data.skill_key)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    # Session laden und Eigentümerschaft prüfen — kein Cross-User-Zugriff erlaubt
    session_row = (
        db.query(SkillTestResult)
        .filter_by(id=data.test_session_id, user_id=current_user.id)
        .first()
    )
    if not session_row:
        raise HTTPException(status_code=404, detail="Test-Session nicht gefunden.")

    test_data = session_row.generated_test or {}

    # 1. Mini-Task-Code ausführen — stdout wird dem LLM als "tatsächliche Ausgabe" übergeben
    mini_stdout, _mini_stderr = run_user_code(data.mini_task_code)

    # 2. Richtige Antworten aus server-seitigen DB-Daten extrahieren
    mc_questions = test_data.get("multiple_choice", [])
    mc_correct_list = [q.get("correct", "") for q in mc_questions]
    mc_correct_str = ",".join(mc_correct_list)  # z.B. "A,C,B"

    # Student-Antworten in gleicher Reihenfolge aufbereiten
    mc_answers_list = [
        data.mc_answers.get(str(i), "")  # fehlende Antwort → leerer String
        for i in range(len(mc_questions))
    ]
    mc_answers_str = ",".join(mc_answers_list)

    code_reading = test_data.get("code_reading", {})
    mini_task = test_data.get("mini_task", {})

    # 3. Bewertung: MC per Python-Vergleich, Code-Lesen und Mini-Task per LLM
    raw_result = evaluate_skill_test.invoke({
        "skill_key": data.skill_key,
        "mc_answers": mc_answers_str,
        "mc_correct": mc_correct_str,
        "mini_task_description": mini_task.get("description", ""),
        "mini_task_expected": mini_task.get("expected_output", ""),
        "mini_task_code": data.mini_task_code,
        "mini_task_actual_output": mini_stdout,  # subprocess-Ausgabe für bessere LLM-Bewertung
        "code_reading_answer": data.code_reading_answer,
        "code_reading_correct": code_reading.get("correct_answer", ""),
    })
    eval_result = json.loads(raw_result)

    # 4. Session-Zeile mit echtem Score aktualisieren
    session_row.score = eval_result["total_score"]
    session_row.passed = eval_result["passed"]
    db.commit()

    return SubmitTestResponse(
        total_score=eval_result["total_score"],
        passed=eval_result["passed"],
        mc_score=eval_result["mc_score"],
        code_reading_score=eval_result["code_reading_score"],
        mini_task_score=eval_result["mini_task_score"],
        per_question_feedback=eval_result["per_question_feedback"],
        attempt_number=session_row.attempt_number,
    )
