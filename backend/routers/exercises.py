"""Exercises router — serves exercise lists and handles code submission/hints."""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.code_runner import run_user_code
from data.exercises import EXERCISES
from models.exercise import ExerciseCompletion
from models.skill_progress import StudentSkillProgress, SKILL_TREE
from models.user import User
from routers.auth import get_current_user
from services.progress_service import get_or_create_skill_progress
from agent.tools.exercise_evaluator_tool import evaluate_exercise
from agent.tools.hint_tool import get_hint

router = APIRouter(prefix="/exercises", tags=["exercises"])

# Build a quick lookup: skill_key -> skill metadata
_SKILL_META: dict[str, dict] = {s["key"]: s for s in SKILL_TREE}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ExerciseOut(BaseModel):
    id: str
    order: int
    title: str
    description: str
    hint: str
    is_unlocked: bool
    is_locked: bool
    score_granted: int


class SkillExercisesResponse(BaseModel):
    skill_key: str
    exercises: list[ExerciseOut]


class SubmitRequest(BaseModel):
    skill_key: str
    exercise_id: str
    code: str


class SubmitResponse(BaseModel):
    result: str               # "richtig" | "teilweise" | "falsch"
    score_change: int
    new_skill_score: int
    what_was_good: str
    what_went_wrong: str
    hint: str
    stdout: str
    stderr: str
    redirect_to_tutor: bool
    analysis: str


class HintRequest(BaseModel):
    skill_key: str
    exercise_id: str
    code: str
    hint_level: int


class HintResponse(BaseModel):
    hint: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_completions(user_id: int, skill_key: str, db: Session) -> dict[str, ExerciseCompletion]:
    """Returns dict of exercise_id -> ExerciseCompletion for a user's skill."""
    rows = (
        db.query(ExerciseCompletion)
        .filter_by(user_id=user_id, skill_key=skill_key)
        .all()
    )
    return {r.exercise_id: r for r in rows}



# ---------------------------------------------------------------------------
# GET /exercises/{skill_key}
# ---------------------------------------------------------------------------

@router.get("/{skill_key}", response_model=SkillExercisesResponse)
def get_exercises(
    skill_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all exercises for a skill with unlock/completion status."""
    if skill_key not in EXERCISES:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_key}' nicht gefunden.")

    raw_exercises = sorted(EXERCISES[skill_key], key=lambda e: e["order"])
    completions = _get_completions(current_user.id, skill_key, db)

    exercises_out: list[ExerciseOut] = []
    for ex in raw_exercises:
        ex_id = ex["id"]
        completion = completions.get(ex_id)
        score_granted = completion.score_granted if completion else 0
        is_locked = completion.is_locked if completion else False

        # Unlock logic: first exercise always visible;
        # exercise N is visible only if exercise N-1 is completed (score_granted > 0)
        if ex["order"] == 1:
            is_unlocked = True
        else:
            prev_ex = raw_exercises[ex["order"] - 2]  # order is 1-based
            prev_completion = completions.get(prev_ex["id"])
            prev_score = prev_completion.score_granted if prev_completion else 0
            is_unlocked = prev_score > 0

        exercises_out.append(ExerciseOut(
            id=ex_id,
            order=ex["order"],
            title=ex["title"],
            description=ex["description"],
            hint=ex["hint"],
            is_unlocked=is_unlocked,
            is_locked=is_locked,
            score_granted=score_granted,
        ))

    return SkillExercisesResponse(skill_key=skill_key, exercises=exercises_out)


# ---------------------------------------------------------------------------
# POST /exercises/submit
# ---------------------------------------------------------------------------

@router.post("/submit", response_model=SubmitResponse)
def submit_exercise(
    data: SubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Runs user code, evaluates it, updates progress, and returns feedback."""
    # 1. Validate exercise exists
    skill_exercises = EXERCISES.get(data.skill_key)
    if not skill_exercises:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    exercise = next((e for e in skill_exercises if e["id"] == data.exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Übung '{data.exercise_id}' nicht gefunden.")

    # 2. Check if already locked (score == 20, completed with RICHTIG)
    completion = (
        db.query(ExerciseCompletion)
        .filter_by(user_id=current_user.id, skill_key=data.skill_key, exercise_id=data.exercise_id)
        .first()
    )
    if completion and completion.is_locked:
        raise HTTPException(status_code=400, detail="Übung bereits abgeschlossen.")

    current_score_granted = completion.score_granted if completion else 0

    # 3. Run user code
    stdout, stderr = run_user_code(data.code)

    # 4. Call evaluate_exercise tool
    raw_result = evaluate_exercise.invoke({
        "code": data.code,
        "exercise_description": exercise["description"],
        "expected_output": exercise["expected_output"],
        "stdout": stdout,
    })
    eval_result = json.loads(raw_result)

    result_str = eval_result.get("result", "falsch")
    what_was_good = eval_result.get("what_was_good", "")
    what_went_wrong = eval_result.get("what_went_wrong", "")
    hint_text = eval_result.get("hint", "")

    # 5. Calculate score_change and new score_granted
    if result_str == "richtig":
        new_score_granted = 20
        score_change = 20 - current_score_granted
        new_is_locked = True
    elif result_str == "teilweise":
        new_score_granted = max(10, current_score_granted)
        score_change = max(0, 10 - current_score_granted)
        new_is_locked = False
    else:  # falsch
        new_score_granted = current_score_granted  # no change
        score_change = 0
        new_is_locked = False

    # 6. Upsert ExerciseCompletion
    if completion:
        completion.score_granted = new_score_granted
        completion.is_locked = new_is_locked
    else:
        completion = ExerciseCompletion(
            user_id=current_user.id,
            skill_key=data.skill_key,
            exercise_id=data.exercise_id,
            score_granted=new_score_granted,
            is_locked=new_is_locked,
        )
        db.add(completion)
    db.flush()

    # 7. Update StudentSkillProgress.score = sum of all exercise score_granted for this skill
    all_completions = (
        db.query(ExerciseCompletion)
        .filter_by(user_id=current_user.id, skill_key=data.skill_key)
        .all()
    )
    total_exercise_score = sum(c.score_granted for c in all_completions)
    # Cap at 100 (5 exercises * 20 = 100 max)
    new_skill_score = min(total_exercise_score, 100)

    skill_progress = get_or_create_skill_progress(current_user.id, data.skill_key, db)
    skill_progress.score = new_skill_score
    if new_skill_score >= 80:
        skill_progress.status = "understood"
    elif new_skill_score >= 40:
        skill_progress.status = "partial"
    else:
        skill_progress.status = "not_understood"

    db.commit()

    # 8. Build response
    redirect_to_tutor = result_str == "falsch"
    analysis = f"{what_went_wrong} {hint_text}".strip() if redirect_to_tutor else ""

    return SubmitResponse(
        result=result_str,
        score_change=score_change,
        new_skill_score=new_skill_score,
        what_was_good=what_was_good,
        what_went_wrong=what_went_wrong,
        hint=hint_text,
        stdout=stdout,
        stderr=stderr,
        redirect_to_tutor=redirect_to_tutor,
        analysis=analysis,
    )


# ---------------------------------------------------------------------------
# POST /exercises/hint
# ---------------------------------------------------------------------------

@router.post("/hint", response_model=HintResponse)
def get_exercise_hint(
    data: HintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns a levelled hint for an exercise."""
    skill_exercises = EXERCISES.get(data.skill_key)
    if not skill_exercises:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    exercise = next((e for e in skill_exercises if e["id"] == data.exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Übung '{data.exercise_id}' nicht gefunden.")

    hint_text = get_hint.invoke({
        "code": data.code,
        "exercise_description": exercise["description"],
        "hint_level": data.hint_level,
    })

    return HintResponse(hint=hint_text)
