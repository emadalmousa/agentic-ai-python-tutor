"""Skill-Tests router — generates and evaluates skill tests."""
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

# Build quick skill lookups
_SKILL_META: dict[str, dict] = {s["key"]: s for s in SKILL_TREE}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    skill_key: str


class GenerateResponse(BaseModel):
    test_session_id: int
    test_data: dict


class SubmitTestRequest(BaseModel):
    test_session_id: int              # server-side session; replaces client-supplied test_data
    skill_key: str
    mc_answers: dict[str, str]        # {"0": "A", "1": "B", "2": "C"}
    code_reading_answer: str
    mini_task_code: str


class SubmitTestResponse(BaseModel):
    total_score: int
    passed: bool
    mc_score: int
    code_reading_score: int
    mini_task_score: int
    per_question_feedback: list
    attempt_number: int


# ---------------------------------------------------------------------------
# POST /skill-tests/generate
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=GenerateResponse)
def generate_test(
    data: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates a skill test, stores it server-side, and returns a session id."""
    skill = _SKILL_META.get(data.skill_key)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    raw_result = generate_skill_test.invoke({
        "skill_key": data.skill_key,
        "skill_label": skill["label"],
        "user_level": current_user.level,
    })
    test_data = json.loads(raw_result)

    # Count prior attempts to set attempt_number for this session row
    prior_attempts = (
        db.query(SkillTestResult)
        .filter_by(user_id=current_user.id, skill_key=data.skill_key)
        .count()
    )
    attempt_number = prior_attempts + 1

    session_row = SkillTestResult(
        user_id=current_user.id,
        skill_key=data.skill_key,
        score=0,
        passed=False,
        attempt_number=attempt_number,
        generated_test=test_data,
    )
    db.add(session_row)
    db.commit()
    db.refresh(session_row)

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
    """Evaluates a submitted skill test using the server-stored test data."""
    skill = _SKILL_META.get(data.skill_key)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    # Fetch the session row — validate ownership to prevent cross-user access
    session_row = (
        db.query(SkillTestResult)
        .filter_by(id=data.test_session_id, user_id=current_user.id)
        .first()
    )
    if not session_row:
        raise HTTPException(status_code=404, detail="Test-Session nicht gefunden.")

    test_data = session_row.generated_test or {}

    # 1. Run mini_task_code via subprocess
    mini_stdout, _mini_stderr = run_user_code(data.mini_task_code)

    # 2. Extract correct answers from authoritative server-side test_data
    mc_questions = test_data.get("multiple_choice", [])
    mc_correct_list = [q.get("correct", "") for q in mc_questions]
    mc_correct_str = ",".join(mc_correct_list)

    mc_answers_list = [
        data.mc_answers.get(str(i), "")
        for i in range(len(mc_questions))
    ]
    mc_answers_str = ",".join(mc_answers_list)

    code_reading = test_data.get("code_reading", {})
    mini_task = test_data.get("mini_task", {})

    # 3. Call evaluate_skill_test tool — pass actual stdout so evaluator can use it
    raw_result = evaluate_skill_test.invoke({
        "skill_key": data.skill_key,
        "mc_answers": mc_answers_str,
        "mc_correct": mc_correct_str,
        "mini_task_description": mini_task.get("description", ""),
        "mini_task_expected": mini_task.get("expected_output", ""),
        "mini_task_code": data.mini_task_code,
        "mini_task_actual_output": mini_stdout,
        "code_reading_answer": data.code_reading_answer,
        "code_reading_correct": code_reading.get("correct_answer", ""),
    })
    eval_result = json.loads(raw_result)

    # 4. Update the existing session row with the real score and pass status
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
