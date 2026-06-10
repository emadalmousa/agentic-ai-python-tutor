"""ORM-Modell für Lern-Sessions (Tabelle: learning_sessions).

Eine Session wird gespeichert nachdem ein Student Code analysiert hat.
Sie enthält den Code-Schnipsel, erkannte Themen, Fehler und den Chat-Verlauf.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class LearningSession(Base):
    """Speichert eine Analyse-Session des Studenten mit allen zugehörigen Daten."""
    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))  # Verknüpfung zum User
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    code_snippet: Mapped[str | None] = mapped_column(Text)                 # analysierter Code (kann None sein)
    topics: Mapped[list[str] | None] = mapped_column(JSON)                 # erkannte Python-Themen
    errors: Mapped[list[str] | None] = mapped_column(JSON)                 # gefundene Fehlertypen
    chat_messages: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)  # [{role, content}, ...]

    # Rückbeziehung zum User — für eager loading über User.sessions
    user: Mapped["User"] = relationship("User", back_populates="sessions")  # type: ignore[name-defined]
