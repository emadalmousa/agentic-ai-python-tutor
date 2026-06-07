import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class Level(str, enum.Enum):
    BEGINNER = "Anfänger"
    INTERMEDIATE = "Mittel"
    ADVANCED = "Fortgeschritten"


class Role(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    hashed_password: Mapped[str] = mapped_column(String)
    level: Mapped[str] = mapped_column(String, default="Anfänger")
    goal: Mapped[str] = mapped_column(String, default="Python Grundlagen")
    role: Mapped[str] = mapped_column(String, default=Role.USER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions: Mapped[list["LearningSession"]] = relationship("LearningSession", back_populates="user")  # type: ignore[name-defined]
