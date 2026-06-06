from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from core.database import Base


class ExerciseCompletion(Base):
    """Tracks one row per (user, skill, exercise) — records score and completion state."""
    __tablename__ = "exercise_completions"

    __table_args__ = (UniqueConstraint("user_id", "skill_key", "exercise_id"),)

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_key    = Column(String, nullable=False)          # e.g. "for_loop"
    exercise_id  = Column(String, nullable=False)          # e.g. "for_loop_1"
    score_granted = Column(Integer, default=0)             # 0 | 10 | 20
    is_locked    = Column(Boolean, default=False)          # True = completed (RICHTIG)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
