"""ORM-Modell für Skill-Test-Ergebnisse (Tabelle: skill_test_results).

Jede Zeile repräsentiert einen Test-Versuch eines Studenten für einen Skill.
generated_test speichert die vollständigen Testfragen — server-seitig damit
der Student die richtigen Antworten nicht aus dem Client-Request lesen kann.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


class SkillTestResult(Base):
    """Speichert einen Test-Versuch: Fragen, Score und Bestanden-Status."""
    __tablename__ = "skill_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    skill_key: Mapped[str] = mapped_column(String)         # z.B. "variables", "for_loop"
    score: Mapped[int] = mapped_column(Integer)            # 0-100, wird nach Submit aktualisiert
    passed: Mapped[bool] = mapped_column(Boolean)          # True wenn score >= 60
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)  # fortlaufend pro User+Skill
    # Vollständige Testdaten inkl. richtiger Antworten — NICHT an Client gesendet
    generated_test: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
