"""Lernfortschritt-API — Skill-basierte Fortschrittsverfolgung."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from models.skill_progress import StudentSkillProgress, LearningEvent, FIXED_SKILLS, SKILL_TREE
from models.user import User
from routers.auth import get_current_user
from services.progress_service import get_or_create_skill_progress
from services.skill_analyzer import analyze_skill

router = APIRouter(prefix="/learning-progress", tags=["learning-progress"])


# ---------------------------------------------------------------------------
# Pydantic-Schemas
# ---------------------------------------------------------------------------

class SkillInfo(BaseModel):
    key:   str
    label: str


class SkillProgressOut(BaseModel):
    skill_key:   str
    skill_label: str
    score:       int
    status:      str  # understood | partial | not_understood
    updated_at:  str | None = None
    level:       str          # beginner | intermediate | advanced
    is_unlocked: bool
    order:       int


class ProgressResponse(BaseModel):
    student_id:    int
    overall_score: int          # Durchschnitt aller Skill-Scores
    skills:        list[SkillProgressOut]
    recent_events: list[dict]   # letzte 5 Analyse-Ereignisse
    user_status:   str          # Anfänger | Fortgeschritten | Profi


class AnalyzeRequest(BaseModel):
    code:     str = ""
    question: str = ""


class AnalyzeResponse(BaseModel):
    detected_skills:         list[str]
    main_skill:              str
    score:                   int
    status:                  str
    mistakes:                list[str]
    feedback:                str
    recommended_next_exercise: str
    updated_progress:        ProgressResponse


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

_SKILL_LABEL = dict(FIXED_SKILLS)

# Build a lookup from skill_key -> full skill metadata (level, order, unlocks_after)
_SKILL_META: dict[str, dict] = {s["key"]: s for s in SKILL_TREE}



def _build_progress_response(user_id: int, db: Session) -> ProgressResponse:
    rows = {
        r.skill_key: r
        for r in db.query(StudentSkillProgress).filter_by(user_id=user_id).all()
    }

    # Build a score lookup for unlock checks
    scores_by_key: dict[str, int] = {key: (rows[key].score if key in rows else 0) for key, _ in FIXED_SKILLS}

    skills_out: list[SkillProgressOut] = []
    for key, label in FIXED_SKILLS:
        row = rows.get(key)
        meta = _SKILL_META.get(key, {})

        # Unlock logic: skill is unlocked if it has no predecessor (unlocks_after is None)
        # or its predecessor has score >= 80
        unlocks_after = meta.get("unlocks_after")
        if unlocks_after is None:
            is_unlocked = True
        else:
            predecessor_score = scores_by_key.get(unlocks_after, 0)
            is_unlocked = predecessor_score >= 80

        skills_out.append(SkillProgressOut(
            skill_key   = key,
            skill_label = label,
            score       = row.score if row else 0,
            status      = row.status if row else "not_understood",
            updated_at  = row.updated_at.isoformat() if row and row.updated_at else None,
            level       = meta.get("level", "beginner"),
            is_unlocked = is_unlocked,
            order       = meta.get("order", 0),
        ))

    scores = [s.score for s in skills_out]
    overall = round(sum(scores) / len(scores)) if scores else 0

    # Determine user_status
    beginner_skills = [s for s in skills_out if s.level == "beginner"]
    all_max = all(s.score == 100 for s in skills_out)
    all_beginner_advanced = all(s.score >= 80 for s in beginner_skills)

    if all_max:
        user_status = "Profi"
    elif all_beginner_advanced:
        user_status = "Fortgeschritten"
    else:
        user_status = "Anfänger"

    recent = (
        db.query(LearningEvent)
        .filter_by(user_id=user_id)
        .order_by(LearningEvent.created_at.desc())
        .limit(5)
        .all()
    )
    recent_events = [
        {
            "skill_key":             e.skill_key,
            "skill_label":           _SKILL_LABEL.get(e.skill_key, e.skill_key),
            "score":                 e.score,
            "mistakes":              e.mistakes or [],
            "feedback":              e.feedback,
            "recommended_exercise":  e.recommended_exercise,
            "created_at":            e.created_at.isoformat() if e.created_at else None,
        }
        for e in recent
    ]

    return ProgressResponse(
        student_id=user_id,
        overall_score=overall,
        skills=skills_out,
        recent_events=recent_events,
        user_status=user_status,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/skills", response_model=list[SkillInfo])
def get_skills():
    """Gibt die feste Skill-Liste zurück."""
    return [SkillInfo(key=k, label=l) for k, l in FIXED_SKILLS]


@router.get("/{student_id}", response_model=ProgressResponse)
def get_progress(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liefert den aktuellen Lernfortschritt für einen Studenten."""
    # Admins dürfen alle Studenten abrufen; normale Nutzer nur sich selbst
    if current_user.role != "admin" and current_user.id != student_id:
        student_id = current_user.id
    return _build_progress_response(student_id, db)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_and_save(
    data: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analysiert Code / Frage, erkennt den Skill, berechnet Score und
    speichert das Ergebnis. Gibt den aktualisierten Gesamtfortschritt zurück.
    """
    result = analyze_skill(data.code, data.question)

    # Skill-Fortschritt aktualisieren (gleitender Durchschnitt mit neuem Score)
    skill_key = result["main_skill"]
    row = get_or_create_skill_progress(current_user.id, skill_key, db)
    # Neuer Score = 70 % alter Wert + 30 % neuer Wert (sanfte Aktualisierung)
    row.score  = round(row.score * 0.7 + result["score"] * 0.3) if row.score else result["score"]
    row.status = result["status"]
    # Timestamp manuell setzen (server_default gilt nur beim INSERT)
    from datetime import datetime, timezone
    row.updated_at = datetime.now(timezone.utc)

    # Ereignis speichern
    event = LearningEvent(
        user_id             = current_user.id,
        skill_key           = skill_key,
        score               = result["score"],
        mistakes            = result["mistakes"],
        feedback            = result["feedback"],
        recommended_exercise= result["recommended_next_exercise"],
    )
    db.add(event)
    db.commit()

    updated = _build_progress_response(current_user.id, db)

    return AnalyzeResponse(
        detected_skills          = result["detected_skills"],
        main_skill               = result["main_skill"],
        score                    = result["score"],
        status                   = result["status"],
        mistakes                 = result["mistakes"],
        feedback                 = result["feedback"],
        recommended_next_exercise= result["recommended_next_exercise"],
        updated_progress         = updated,
    )


@router.delete("/events")
def delete_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Löscht alle Lern-Ereignisse des aktuellen Nutzers."""
    deleted_count = (
        db.query(LearningEvent)
        .filter_by(user_id=current_user.id)
        .delete()
    )
    db.commit()
    return {"deleted_count": deleted_count}
