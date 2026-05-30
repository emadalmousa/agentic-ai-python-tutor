from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    code_snippet = Column(Text)
    topics = Column(JSON)         # list[str] — erkannte Themen
    errors = Column(JSON)         # list[str] — erkannte Fehler
    chat_messages = Column(JSON)  # list[{role, content}]

    user = relationship("User", back_populates="sessions")
