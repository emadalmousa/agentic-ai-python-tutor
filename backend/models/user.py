"""ORM-Modell für den Benutzer (Tabelle: users)."""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class Level(str, enum.Enum):
    """Python-Kenntnisstufe des Studenten — wird im Profil gespeichert."""
    BEGINNER = "Anfänger"
    INTERMEDIATE = "Mittel"
    ADVANCED = "Fortgeschritten"


class Role(str, enum.Enum):
    """Zugriffsrolle: Admin darf alle Studenten einsehen, User nur sich selbst."""
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """Benutzer-Tabelle — speichert Anmeldedaten, Level und Lernziel."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)  # einzigartig, Index für schnelles Login
    name: Mapped[str] = mapped_column(String)
    hashed_password: Mapped[str] = mapped_column(String)  # bcrypt-Hash, niemals Klartext
    level: Mapped[str] = mapped_column(String, default="Anfänger")   # Anfänger | Mittel | Fortgeschritten
    goal: Mapped[str] = mapped_column(String, default="Python Grundlagen")  # persönliches Lernziel
    role: Mapped[str] = mapped_column(String, default=Role.USER)  # admin | user
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Beziehung zu allen Lern-Sessions des Users — lazy loaded
    sessions: Mapped[list["LearningSession"]] = relationship("LearningSession", back_populates="user")  # type: ignore[name-defined]
