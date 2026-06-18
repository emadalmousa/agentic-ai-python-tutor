"""Lernfortschritt-API — Skill-basierte Fortschrittsverfolgung."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agent.tools.nudge_tool import generate_nudge_text
from core.database import get_db
from models.skill_progress import StudentSkillProgress, LearningEvent, FIXED_SKILLS, SKILL_TREE
from models.user import User
from routers.auth import get_current_user

router = APIRouter(prefix="/learning-progress", tags=["learning-progress"])


# ---------------------------------------------------------------------------
# Pydantic-Schemas
# ---------------------------------------------------------------------------

class SkillInfo(BaseModel):
    key:   str
    label: str


class WeaknessNudgeResponse(BaseModel):
    has_weakness: bool
    skill_key:    str | None = None
    skill_label:  str | None = None
    score:        int | None = None
    nudge_text:   str | None = None


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



# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

_SKILL_LABEL = dict(FIXED_SKILLS)

# Build a lookup from skill_key -> full skill metadata (level, order, unlocks_after)
_SKILL_META: dict[str, dict] = {s["key"]: s for s in SKILL_TREE}



def _build_progress_response(user_id: int, db: Session) -> ProgressResponse:
    """Baut die vollständige Fortschrittsantwort für einen Studenten.

    Lädt alle Skill-Zeilen aus der DB, befüllt fehlende Skills mit Defaults (score=0),
    berechnet den Overall-Score als Durchschnitt und bestimmt den User-Status.
    Unlock-Logik: Skill ist freigeschalten wenn kein Vorgänger (unlocks_after=None)
    oder der Vorgänger einen Score >= 80 hat.
    """
    rows = {
        r.skill_key: r
        for r in db.query(StudentSkillProgress).filter_by(user_id=user_id).all()
    }

    # Schneller Score-Lookup für Unlock-Checks ohne weitere DB-Abfragen
    scores_by_key: dict[str, int] = {key: (rows[key].score if key in rows else 0) for key, _ in FIXED_SKILLS}

    skills_out: list[SkillProgressOut] = []
    for key, label in FIXED_SKILLS:
        row = rows.get(key)
        meta = _SKILL_META.get(key, {})

        unlocks_after = meta.get("unlocks_after")
        if unlocks_after is None:
            # Kein Vorgänger → immer freigeschalten (Einstiegs-Skills)
            is_unlocked = True
        else:
            # Vorgänger muss >= 80 Punkte haben
            predecessor_score = scores_by_key.get(unlocks_after, 0)
            is_unlocked = predecessor_score >= 80

        skills_out.append(SkillProgressOut(
            skill_key   = key,
            skill_label = label,
            score       = row.score if row else 0,         # 0 wenn noch kein Eintrag
            status      = row.status if row else "not_understood",
            updated_at  = row.updated_at.isoformat() if row and row.updated_at else None,
            level       = meta.get("level", "beginner"),
            is_unlocked = is_unlocked,
            order       = meta.get("order", 0),
        ))

    scores = [s.score for s in skills_out]
    overall = round(sum(scores) / len(scores)) if scores else 0

    # User-Status: Anfänger/Fortgeschritten/Profi basierend auf Skill-Scores
    beginner_skills = [s for s in skills_out if s.level == "beginner"]
    all_max = all(s.score == 100 for s in skills_out)
    all_beginner_advanced = all(s.score >= 80 for s in beginner_skills)

    if all_max:
        user_status = "Profi"
    elif all_beginner_advanced:
        user_status = "Fortgeschritten"
    else:
        user_status = "Anfänger"

    # Letzte 5 Lern-Ereignisse für die Aktivitäts-Timeline
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
            "skill_label":           _SKILL_LABEL.get(e.skill_key, e.skill_key),  # Fallback: key selbst
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

def _pick_weakness(user_id: int, db: Session) -> tuple[str, str, int] | None:
    """Wählt die dringendste Schwäche nach Priorität. Gibt (skill_key, skill_label, score) zurück."""
    rows = {
        r.skill_key: r
        for r in db.query(StudentSkillProgress).filter_by(user_id=user_id).all()
    }
    if not rows:
        return None

    now = datetime.now(timezone.utc)

    # Fundament-Skills (unlocks_after=None) — höchste Priorität wenn not_understood
    foundation_keys = {s["key"] for s in SKILL_TREE if s.get("unlocks_after") is None}

    # Letzte Event-Zeitstempel pro Skill (für "lange nicht geübt"-Check)
    last_events: dict[str, datetime] = {}
    for e in db.query(LearningEvent).filter_by(user_id=user_id).all():
        ts = e.created_at
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts and (e.skill_key not in last_events or ts > last_events[e.skill_key]):
            last_events[e.skill_key] = ts

    candidates: list[tuple[int, str]] = []  # (priority, skill_key)

    for key, row in rows.items():
        score = row.score
        if score >= 80:
            continue  # Kein Problem

        days_since = (now - last_events[key]).days if key in last_events else 999

        if score < 40 and key in foundation_keys:
            candidates.append((1, key))
        elif score < 40 and days_since > 7:
            candidates.append((2, key))
        elif 40 <= score < 80:
            candidates.append((3, key))
        else:
            candidates.append((4, key))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    best_key = candidates[0][1]
    best_row = rows[best_key]
    label = _SKILL_LABEL.get(best_key, best_key)
    return best_key, label, best_row.score


@router.get("/weakness-nudge", response_model=WeaknessNudgeResponse)
def get_weakness_nudge(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gibt die dringendste Schwäche + LLM-generierten Motivationstext zurück.

    Priorität: Fundament-Skills not_understood > lange nicht geübt > partial > allgemein.
    LLM wird nur aufgerufen wenn LearningEvents für den Skill existieren.
    """
    result = _pick_weakness(current_user.id, db)
    if result is None:
        return WeaknessNudgeResponse(has_weakness=False)

    skill_key, skill_label, score = result

    # Letztes Event für diesen Skill holen (für personalisierter Text)
    last_event = (
        db.query(LearningEvent)
        .filter_by(user_id=current_user.id, skill_key=skill_key)
        .order_by(LearningEvent.created_at.desc())
        .first()
    )

    if last_event:
        nudge_text = generate_nudge_text(
            skill_label=skill_label,
            mistakes=last_event.mistakes or [],
            feedback=last_event.feedback,
        )
    else:
        nudge_text = f"Du hast '{skill_label}' noch nicht geübt. Fang jetzt an?"

    return WeaknessNudgeResponse(
        has_weakness=True,
        skill_key=skill_key,
        skill_label=skill_label,
        score=score,
        nudge_text=nudge_text,
    )


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

