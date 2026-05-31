from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from core.database import Base


class SkillTestResult(Base):
    """Records each skill test attempt for a user — score, pass/fail, and attempt count."""
    __tablename__ = "skill_test_results"

    id             = Column(Integer, primary_key=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_key      = Column(String, nullable=False)   # e.g. "for_loop"
    score          = Column(Integer, nullable=False)  # 0–100 percentage
    passed         = Column(Boolean, nullable=False)  # score >= 60
    attempt_number = Column(Integer, default=1)       # incremented on each retry
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
