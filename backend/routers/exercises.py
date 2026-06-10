"""Exercises-Router: Übungslisten und Code-Abgabe mit LLM-Bewertung."""
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

# Schneller Lookup: skill_key → skill-Metadaten (label, level, order, unlocks_after)
_SKILL_META: dict[str, dict] = {s["key"]: s for s in SKILL_TREE}


# ---------------------------------------------------------------------------
# Pydantic-Schemas
# ---------------------------------------------------------------------------

class ExerciseOut(BaseModel):
    """Eine einzelne Übungsaufgabe mit Freischalt- und Abschluss-Status."""
    id: str
    order: int
    title: str
    description: str
    hint: str
    is_unlocked: bool   # True wenn Vorgänger-Übung abgeschlossen
    is_locked: bool     # True wenn diese Übung vollständig gelöst (score=20, "richtig")
    score_granted: int  # 0 | 10 | 20


class SkillExercisesResponse(BaseModel):
    """Liste aller Übungen für einen Skill mit Fortschritts-Status."""
    skill_key: str
    exercises: list[ExerciseOut]


class SubmitRequest(BaseModel):
    """Abgabe einer Übungslösung."""
    skill_key: str
    exercise_id: str
    code: str


class SubmitResponse(BaseModel):
    """Bewertungsergebnis einer Code-Abgabe."""
    result: str               # "richtig" | "teilweise" | "falsch"
    score_change: int         # Punktzahl-Änderung (0-20)
    new_skill_score: int      # neuer Gesamt-Score für den Skill (0-100)
    what_was_good: str        # positives Feedback vom LLM
    what_went_wrong: str      # Verbesserungsvorschlag vom LLM
    hint: str                 # konkreter Tipp vom LLM
    stdout: str               # tatsächliche Ausgabe des Schüler-Codes
    stderr: str               # Fehlermeldungen (Syntax- oder Laufzeitfehler)
    redirect_to_tutor: bool   # True wenn "falsch" → Frontend leitet zum Chat weiter
    analysis: str             # Zusammenfassung für die Chat-Weiterleitung


class HintRequest(BaseModel):
    """Anfrage für einen gestuften Tipp zu einer Übung."""
    skill_key: str
    exercise_id: str
    code: str
    hint_level: int  # 1 (Konzept), 2 (Syntax), 3 (lösungsnah)


class HintResponse(BaseModel):
    """Antwort mit dem generierten Tipp."""
    hint: str


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _get_completions(user_id: int, skill_key: str, db: Session) -> dict[str, ExerciseCompletion]:
    """Gibt alle Übungsabschlüsse eines Users für einen Skill als {exercise_id: Completion} zurück."""
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
    """Gibt alle Übungen eines Skills mit Freischalt- und Abschluss-Status zurück.

    Freischalt-Logik:
    - Übung 1 ist immer sichtbar
    - Übung N ist sichtbar wenn Übung N-1 vollständig gelöst ist (is_locked=True)
    """
    if skill_key not in EXERCISES:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_key}' nicht gefunden.")

    # Übungen nach order sortieren (order ist 1-basiert)
    raw_exercises = sorted(EXERCISES[skill_key], key=lambda e: e["order"])
    # DB-Abschlüsse einmal laden — vermeidet N+1 Abfragen in der Schleife
    completions = _get_completions(current_user.id, skill_key, db)

    exercises_out: list[ExerciseOut] = []
    for ex in raw_exercises:
        ex_id = ex["id"]
        completion = completions.get(ex_id)
        score_granted = completion.score_granted if completion else 0
        is_locked = completion.is_locked if completion else False

        # Freischalt-Logik: erste Übung immer; jede weitere nur wenn Vorgänger gelöst
        if ex["order"] == 1:
            is_unlocked = True
        else:
            # order ist 1-basiert → Index des Vorgängers ist order-2
            prev_ex = raw_exercises[ex["order"] - 2]
            prev_completion = completions.get(prev_ex["id"])
            is_unlocked = prev_completion.is_locked if prev_completion else False

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
    """Führt den Schüler-Code aus, bewertet ihn per LLM und aktualisiert den Fortschritt.

    Ablauf:
    1. Übung validieren (existiert im EXERCISES-Dict)
    2. Lock-Check: bereits "richtig" gelöste Übungen können nicht erneut bewertet werden
    3. Code ausführen via subprocess
    4. LLM-Bewertung über evaluate_exercise-Tool
    5. Score berechnen und ExerciseCompletion aktualisieren (upsert)
    6. StudentSkillProgress.score = Summe aller Exercise-Scores für diesen Skill
    """
    # 1. Übung in der statischen Bibliothek suchen
    skill_exercises = EXERCISES.get(data.skill_key)
    if not skill_exercises:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    exercise = next((e for e in skill_exercises if e["id"] == data.exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Übung '{data.exercise_id}' nicht gefunden.")

    # 2. Lock-Check: is_locked=True bedeutet bereits vollständig gelöst (score=20)
    completion = (
        db.query(ExerciseCompletion)
        .filter_by(user_id=current_user.id, skill_key=data.skill_key, exercise_id=data.exercise_id)
        .first()
    )
    if completion and completion.is_locked:
        # Student darf die Übung noch öffnen und Code schreiben, aber sie wird nicht mehr bewertet
        raise HTTPException(status_code=400, detail="Übung bereits abgeschlossen.")

    current_score_granted = completion.score_granted if completion else 0

    # 3. Schüler-Code in Subprocess ausführen (isoliert, max. 10 Sekunden)
    stdout, stderr = run_user_code(data.code)

    # 4. LLM-Bewertung: evaluate_exercise vergleicht stdout mit expected_output
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

    # 5. Score berechnen: richtig=20, teilweise=10 (nie unter aktuellem Wert), falsch=unverändert
    if result_str == "richtig":
        new_score_granted = 20
        score_change = 20 - current_score_granted  # Differenz damit Score nicht doppelt gezählt wird
        new_is_locked = True   # Übung wird gesperrt — fertig
    elif result_str == "teilweise":
        new_score_granted = max(10, current_score_granted)  # kein Rückschritt möglich
        score_change = max(0, 10 - current_score_granted)
        new_is_locked = False  # Student kann nochmal versuchen
    else:  # falsch
        new_score_granted = current_score_granted  # Score bleibt unverändert
        score_change = 0
        new_is_locked = False

    # 6. ExerciseCompletion upsert: aktualisieren wenn vorhanden, sonst neu anlegen
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
    db.flush()  # flush vor dem Score-Aggregat damit die neue Zeile mit gezählt wird

    # 7. Skill-Score = Summe aller Exercise-Scores, max. 100 (5 × 20 = 100 möglich)
    all_completions = (
        db.query(ExerciseCompletion)
        .filter_by(user_id=current_user.id, skill_key=data.skill_key)
        .all()
    )
    total_exercise_score = sum(c.score_granted for c in all_completions)
    new_skill_score = min(total_exercise_score, 100)

    skill_progress = get_or_create_skill_progress(current_user.id, data.skill_key, db)
    skill_progress.score = new_skill_score
    # Status basierend auf Score setzen
    if new_skill_score >= 80:
        skill_progress.status = "understood"
    elif new_skill_score >= 40:
        skill_progress.status = "partial"
    else:
        skill_progress.status = "not_understood"

    db.commit()

    # Bei "falsch": redirect_to_tutor=True → Frontend leitet nach kurzer Pause zum Chat
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
    """Gibt einen gestuften Tipp für eine Übungsaufgabe zurück.

    hint_level 1 = konzeptueller Tipp (kein Spoiler)
    hint_level 2 = Syntax-Tipp (welche Funktion/Methode)
    hint_level 3 = lösungsnaher Code-Schnipsel mit Lücken
    """
    skill_exercises = EXERCISES.get(data.skill_key)
    if not skill_exercises:
        raise HTTPException(status_code=404, detail=f"Skill '{data.skill_key}' nicht gefunden.")

    exercise = next((e for e in skill_exercises if e["id"] == data.exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Übung '{data.exercise_id}' nicht gefunden.")

    # LangChain-Tool direkt aufrufen — kein Agent-Loop nötig für einfache Tipp-Anfrage
    hint_text = get_hint.invoke({
        "code": data.code,
        "exercise_description": exercise["description"],
        "hint_level": data.hint_level,
    })

    return HintResponse(hint=hint_text)
