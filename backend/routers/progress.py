"""Progress-Router: speichert und aggregiert Lern-Sessions für Fortschrittsanzeige."""
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


class ChatHistoryItem(BaseModel):
    id: int
    title: str          # Erste User-Nachricht als Titel (max 60 Zeichen)
    created_at: str
    message_count: int


class SaveChatRequest(BaseModel):
    messages: list[dict]   # [{role, content}, ...]
    code: str = ""


class LoadChatResponse(BaseModel):
    id: int
    messages: list[dict]
    code: str | None
    created_at: str


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
    """Speichert eine neue Lern-Session mit Code, Themen, Fehlern und Chat-Verlauf."""
    session = LearningSession(
        user_id=current_user.id,
        code_snippet=data.code or None,  # leerer String → None in DB
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
        topics=session.topics or [],      # None → leere Liste für konsistente API
        errors=session.errors or [],
        chat_messages=session.chat_messages or [],
    )


@router.get("/summary", response_model=ProgressSummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gibt eine aggregierte Übersicht aller Lern-Sessions zurück.

    frequent_errors: Fehler die mindestens 2-mal aufgetreten sind → zeigt Muster.
    topics: dedupliziert aber reihenfolge-erhaltend via dict.fromkeys().
    recent_sessions: nur die letzten 10 Sessions für die Anzeige.
    """
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
    # Nur Fehler die mehrfach vorkommen sind relevant für das Fortschritts-Feedback
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
        topics=list(dict.fromkeys(all_topics)),  # dict.fromkeys() dedupliziert ohne Reihenfolge zu ändern
        frequent_errors=frequent_errors,
        recent_sessions=recent_sessions,
    )


@router.post("/chat", response_model=ChatHistoryItem, status_code=201)
def save_chat(
    data: SaveChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Speichert einen vollständigen Chat als neue Session."""
    if not data.messages:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="messages darf nicht leer sein")

    session = LearningSession(
        user_id=current_user.id,
        code_snippet=data.code or None,
        topics=[],
        errors=[],
        chat_messages=data.messages,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    first_user = next((m["content"] for m in data.messages if m.get("role") == "user"), "Chat")
    title = first_user[:60] + ("…" if len(first_user) > 60 else "")
    return ChatHistoryItem(
        id=session.id,
        title=title,
        created_at=session.created_at.isoformat(),
        message_count=len(data.messages),
    )


@router.get("/chats", response_model=list[ChatHistoryItem])
def list_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Listet alle gespeicherten Chats des Nutzers (neueste zuerst)."""
    sessions = (
        db.query(LearningSession)
        .filter(
            LearningSession.user_id == current_user.id,
            LearningSession.chat_messages.isnot(None),
        )
        .order_by(LearningSession.created_at.desc())
        .limit(50)
        .all()
    )
    result = []
    for s in sessions:
        msgs = s.chat_messages or []
        if not msgs:
            continue
        first_user = next((m["content"] for m in msgs if m.get("role") == "user"), "Chat")
        title = first_user[:60] + ("…" if len(first_user) > 60 else "")
        result.append(ChatHistoryItem(
            id=s.id,
            title=title,
            created_at=s.created_at.isoformat(),
            message_count=len(msgs),
        ))
    return result


@router.put("/chat/{session_id}", response_model=ChatHistoryItem)
def update_chat(
    session_id: int,
    data: SaveChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aktualisiert Nachrichten und Code einer bestehenden Chat-Session."""
    from fastapi import HTTPException
    session = db.query(LearningSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat nicht gefunden")
    session.chat_messages = data.messages
    if data.code:
        session.code_snippet = data.code
    db.commit()
    db.refresh(session)
    first_user = next((m["content"] for m in data.messages if m.get("role") == "user"), "Chat")
    title = first_user[:60] + ("…" if len(first_user) > 60 else "")
    return ChatHistoryItem(
        id=session.id,
        title=title,
        created_at=session.created_at.isoformat(),
        message_count=len(data.messages),
    )


@router.get("/chat/{session_id}", response_model=LoadChatResponse)
def load_chat(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lädt einen einzelnen Chat anhand der Session-ID."""
    from fastapi import HTTPException
    session = db.query(LearningSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat nicht gefunden")
    return LoadChatResponse(
        id=session.id,
        messages=session.chat_messages or [],
        code=session.code_snippet,
        created_at=session.created_at.isoformat(),
    )
