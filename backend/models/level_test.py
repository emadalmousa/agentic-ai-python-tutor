"""ORM-Modell für Level-Test-Ergebnisse (Tabelle: level_test_results).

Ein Level-Test deckt alle Skills eines Levels ab (z.B. alle 13 Beginner-Skills).
Strukturell identisch mit SkillTestResult — aber level statt skill_key als Schlüssel.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


class LevelTestResult(Base):
    """Speichert einen Level-Test-Versuch: Fragen, Score und Bestanden-Status."""
    __tablename__ = "level_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    level: Mapped[str] = mapped_column(String)              # "beginner" | "intermediate" | "advanced"
    score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100, nach Submit aktualisiert
    passed: Mapped[bool] = mapped_column(Boolean, default=False)  # True wenn score >= 60
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    # Vollständige Testdaten inkl. richtiger Antworten — server-seitig gespeichert
    generated_test: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
