from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    code_snippet: Mapped[str | None] = mapped_column(Text)
    topics: Mapped[list[str] | None] = mapped_column(JSON)
    errors: Mapped[list[str] | None] = mapped_column(JSON)
    chat_messages: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)

    user: Mapped["User"] = relationship("User", back_populates="sessions")  # type: ignore[name-defined]
