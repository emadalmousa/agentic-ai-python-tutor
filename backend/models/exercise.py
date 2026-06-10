"""ORM-Modell für Übungsabschlüsse (Tabelle: exercise_completions).

Speichert welche Übung ein Student gelöst hat und wie viele Punkte vergeben wurden.
is_locked=True bedeutet: Übung vollständig abgeschlossen (score=20, Ergebnis "richtig").
score_granted kann 0, 10 (teilweise) oder 20 (richtig) sein.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


class ExerciseCompletion(Base):
    """Fortschritt eines Studenten bei einer einzelnen Übung."""
    __tablename__ = "exercise_completions"

    # Kein Student kann dieselbe Übung zweimal in der DB haben
    __table_args__ = (UniqueConstraint("user_id", "skill_key", "exercise_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    skill_key: Mapped[str] = mapped_column(String)        # z.B. "variables"
    exercise_id: Mapped[str] = mapped_column(String)      # z.B. "variables_1"
    score_granted: Mapped[int] = mapped_column(Integer, default=0)    # 0 | 10 | 20
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)   # True = vollständig gelöst
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
