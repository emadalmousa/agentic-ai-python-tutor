from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from models.session import LearningSession
from models.user import User
from routers.auth import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])


# --- Pydantic schemas ---

class SessionCreate(BaseModel):
    code: str = ""
    topics: list[str] = []
    errors: list[str] = []
    chat_messages: list[dict] = []


class SessionResponse(BaseModel):
    id: int
    code_snippet: str | None
    topics: list[str]
    errors: list[str]
    chat_messages: list[dict]

    model_config = {"from_attributes": True}


class ProgressSummary(BaseModel):
    analyzed_count: int
    topics: list[str]
    frequent_errors: list[str]
    recent_sessions: list[SessionResponse]


# --- Endpoints ---

@router.post("/session", response_model=SessionResponse, status_code=201)
def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = LearningSession(
        user_id=current_user.id,
        code_snippet=data.code or None,
        topics=data.topics,
        errors=data.errors,
        chat_messages=data.chat_messages,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(
        id=session.id,
        code_snippet=session.code_snippet,
        topics=session.topics or [],
        errors=session.errors or [],
        chat_messages=session.chat_messages or [],
    )


@router.get("/summary", response_model=ProgressSummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(LearningSession)
        .filter(LearningSession.user_id == current_user.id)
        .order_by(LearningSession.created_at.desc())
        .all()
    )

    all_topics: list[str] = []
    all_errors: list[str] = []
    for s in sessions:
        all_topics.extend(s.topics or [])
        all_errors.extend(s.errors or [])

    error_counts = Counter(all_errors)
    frequent_errors = [err for err, count in error_counts.items() if count >= 2]

    recent = sessions[:10]
    recent_sessions = [
        SessionResponse(
            id=s.id,
            code_snippet=s.code_snippet,
            topics=s.topics or [],
            errors=s.errors or [],
            chat_messages=s.chat_messages or [],
        )
        for s in recent
    ]

    return ProgressSummary(
        analyzed_count=len(sessions),
        topics=list(dict.fromkeys(all_topics)),  # unique, preserving order
        frequent_errors=frequent_errors,
        recent_sessions=recent_sessions,
    )
