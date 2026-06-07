"""Level-Tests router — generates and evaluates end-of-level tests covering all skills of a level."""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.code_runner import run_user_code
from models.skill_progress import SKILL_TREE
from models.level_test import LevelTestResult
from models.user import User
from routers.auth import get_current_user
from agent.tools.skill_test_generator_tool import generate_skill_test
from agent.tools.skill_test_evaluator_tool import evaluate_skill_test

router = APIRouter(prefix="/level-tests", tags=["level-tests"])

LEVEL_LABELS = {
    "beginner":     "Anfänger",
    "intermediate": "Fortgeschritten",
    "advanced":     "Profi",
}

def _skills_for_level(level: str) -> list[dict]:
    return [s for s in SKILL_TREE if s["level"] == level]


class GenerateRequest(BaseModel):
    level: str  # "beginner" | "intermediate" | "advanced"


class GenerateResponse(BaseModel):
    test_session_id: int
    level: str
    test_data: dict


class SubmitRequest(BaseModel):
    test_session_id: int
    level: str
    mc_answers: dict[str, str]
    code_reading_answer: str
    mini_task_code: str


class SubmitResponse(BaseModel):
    total_score: int
    passed: bool
    mc_score: int
    code_reading_score: int
    mini_task_score: int
    per_question_feedback: list
    attempt_number: int


@router.post("/generate", response_model=GenerateResponse)
def generate_level_test(
    data: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.level not in LEVEL_LABELS:
        raise HTTPException(status_code=400, detail=f"Unbekanntes Level: {data.level}")

    skills = _skills_for_level(data.level)
    if not skills:
        raise HTTPException(status_code=404, detail="Keine Skills für dieses Level gefunden.")

    # Build a combined label covering all skills of the level
    skill_labels = ", ".join(s["label"] for s in skills)
    level_label = LEVEL_LABELS[data.level]

    raw = generate_skill_test.invoke({
        "skill_key": f"level_{data.level}",
        "skill_label": f"{level_label} — {skill_labels}",
        "user_level": current_user.level,
    })
    test_data = json.loads(raw)

    prior = db.query(LevelTestResult).filter_by(user_id=current_user.id, level=data.level).count()
    row = LevelTestResult(
        user_id=current_user.id,
        level=data.level,
        score=0,
        passed=False,
        attempt_number=prior + 1,
        generated_test=test_data,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return GenerateResponse(test_session_id=row.id, level=data.level, test_data=test_data)


@router.post("/submit", response_model=SubmitResponse)
def submit_level_test(
    data: SubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(LevelTestResult).filter_by(id=data.test_session_id, user_id=current_user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Test-Session nicht gefunden.")

    test_data = row.generated_test or {}
    mini_stdout, _ = run_user_code(data.mini_task_code)

    mc_questions = test_data.get("multiple_choice", [])
    mc_correct_str = ",".join(q.get("correct", "") for q in mc_questions)
    mc_answers_str = ",".join(data.mc_answers.get(str(i), "") for i in range(len(mc_questions)))
    code_reading = test_data.get("code_reading", {})
    mini_task = test_data.get("mini_task", {})

    raw = evaluate_skill_test.invoke({
        "skill_key": f"level_{data.level}",
        "mc_answers": mc_answers_str,
        "mc_correct": mc_correct_str,
        "mini_task_description": mini_task.get("description", ""),
        "mini_task_expected": mini_task.get("expected_output", ""),
        "mini_task_code": data.mini_task_code,
        "mini_task_actual_output": mini_stdout,
        "code_reading_answer": data.code_reading_answer,
        "code_reading_correct": code_reading.get("correct_answer", ""),
    })
    result = json.loads(raw)

    row.score = result["total_score"]
    row.passed = result["passed"]
    db.commit()

    return SubmitResponse(
        total_score=result["total_score"],
        passed=result["passed"],
        mc_score=result["mc_score"],
        code_reading_score=result["code_reading_score"],
        mini_task_score=result["mini_task_score"],
        per_question_feedback=result["per_question_feedback"],
        attempt_number=row.attempt_number,
    )


@router.get("/status/{level}")
def get_level_test_status(
    level: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns whether the user has passed the level test."""
    best = (
        db.query(LevelTestResult)
        .filter_by(user_id=current_user.id, level=level)
        .order_by(LevelTestResult.score.desc())
        .first()
    )
    return {
        "level": level,
        "attempted": best is not None,
        "passed": best.passed if best else False,
        "best_score": best.score if best else 0,
        "attempts": db.query(LevelTestResult).filter_by(user_id=current_user.id, level=level).count(),
    }
