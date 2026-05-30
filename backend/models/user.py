import enum

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class Level(str, enum.Enum):
    BEGINNER = "Anfänger"
    INTERMEDIATE = "Mittel"
    ADVANCED = "Fortgeschritten"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    level = Column(String, default="Anfänger")
    goal = Column(String, default="Python Grundlagen")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("LearningSession", back_populates="user")
