from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.sql import func
from core.database import Base


class LevelTestResult(Base):
    __tablename__ = "level_test_results"

    id             = Column(Integer, primary_key=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    level          = Column(String, nullable=False)   # "beginner" | "intermediate" | "advanced"
    score          = Column(Integer, nullable=False, default=0)
    passed         = Column(Boolean, nullable=False, default=False)
    attempt_number = Column(Integer, default=1)
    generated_test = Column(JSON, nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
