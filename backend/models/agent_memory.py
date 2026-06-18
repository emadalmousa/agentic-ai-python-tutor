"""ORM-Modell für das Agent-Gedächtnis (Tabelle: agent_memory).

Ein Eintrag pro User — enthält eine laufende LLM-generierte Zusammenfassung
aller bisherigen Chat-Sessions. Wird nach jedem Chat-Turn aktualisiert.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


class AgentMemory(Base):
    """Speichert die laufende Gedächtniszusammenfassung des Agenten pro User."""
    __tablename__ = "agent_memory"
    __table_args__ = (UniqueConstraint("user_id", name="uq_agent_memory_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    summary: Mapped[str | None] = mapped_column(Text)       # LLM-generierte Zusammenfassung
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
