"""Skill-Tests router — generates and evaluates skill tests."""
import json
import subprocess
import sys

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
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


class SubmitTestRequest(BaseModel):
    skill_key: str
    mc_answers: dict[str, str]          # {"0": "A", "1": "B", "2": "C"}
    code_reading_answer: str
    mini_task_code: str
    test_data: dict                      # full test data returned from generate endpoint


class SubmitTestResponse(BaseModel):
    total_score: int
    passed: bool
    mc_score: int
    code_reading_score: int
    mini_task_score: int
    per_question_feedback: list
    attempt_number: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_code(code: str) -> tuple[str, str]:
    """Runs user code in a subprocess and returns (stdout, stderr)."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "TimeoutError: Code lief zu lange (>10s)."


# ---------------------------------------------------------------------------
# POST /skill-tests/generate
# ---------------------------------------------------------------------------

@router.post("/generate")
def generate_test(
    data: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates a skill test for the given skill_key."""
    skill = _SKILL_META.get(data.skill_key)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    raw_result = generate_skill_test.invoke({
        "skill_key": data.skill_key,
        "skill_label": skill["label"],
        "user_level": current_user.level,
    })

    return json.loads(raw_result)


# ---------------------------------------------------------------------------
# POST /skill-tests/submit
# ---------------------------------------------------------------------------

@router.post("/submit", response_model=SubmitTestResponse)
def submit_test(
    data: SubmitTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluates a submitted skill test and persists the result."""
    skill = _SKILL_META.get(data.skill_key)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    # 1. Run mini_task_code via subprocess
    _mini_stdout, _mini_stderr = _run_code(data.mini_task_code)

    # 2. Extract correct answers from test_data
    mc_questions = data.test_data.get("multiple_choice", [])
    mc_correct_list = [q.get("correct", "") for q in mc_questions]
    mc_correct_str = ",".join(mc_correct_list)

    # Build mc_answers string in order (keys "0", "1", "2")
    mc_answers_list = [
        data.mc_answers.get(str(i), "")
        for i in range(len(mc_questions))
    ]
    mc_answers_str = ",".join(mc_answers_list)

    code_reading = data.test_data.get("code_reading", {})
    mini_task = data.test_data.get("mini_task", {})

    # 3. Call evaluate_skill_test tool
    raw_result = evaluate_skill_test.invoke({
        "skill_key": data.skill_key,
        "mc_answers": mc_answers_str,
        "mc_correct": mc_correct_str,
        "mini_task_description": mini_task.get("description", ""),
        "mini_task_expected": mini_task.get("expected_output", ""),
        "mini_task_code": data.mini_task_code,
        "code_reading_answer": data.code_reading_answer,
        "code_reading_correct": code_reading.get("correct_answer", ""),
    })
    eval_result = json.loads(raw_result)

    # 4. Save SkillTestResult — increment attempt_number if this user has prior attempts
    prior_attempts = (
        db.query(SkillTestResult)
        .filter_by(user_id=current_user.id, skill_key=data.skill_key)
        .count()
    )
    attempt_number = prior_attempts + 1

    test_record = SkillTestResult(
        user_id=current_user.id,
        skill_key=data.skill_key,
        score=eval_result["total_score"],
        passed=eval_result["passed"],
        attempt_number=attempt_number,
    )
    db.add(test_record)
    db.commit()

    return SubmitTestResponse(
        total_score=eval_result["total_score"],
        passed=eval_result["passed"],
        mc_score=eval_result["mc_score"],
        code_reading_score=eval_result["code_reading_score"],
        mini_task_score=eval_result["mini_task_score"],
        per_question_feedback=eval_result["per_question_feedback"],
        attempt_number=attempt_number,
    )
