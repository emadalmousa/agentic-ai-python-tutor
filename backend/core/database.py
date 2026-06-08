"""Datenbankverbindung und Session-Management für SQLAlchemy.

Unterstützt SQLite (Entwicklung) und PostgreSQL (Produktion) über DATABASE_URL.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

# .env-Datei laden — liegt ein Verzeichnis über diesem Modul (backend/)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Standard: lokale SQLite-Datei; Produktion: PostgreSQL-URL aus .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tutor.db")

engine = create_engine(
    DATABASE_URL,
    # check_same_thread=False ist nur für SQLite nötig:
    # FastAPI nutzt mehrere Threads, SQLite erlaubt standardmäßig nur einen.
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# autocommit=False: Änderungen müssen explizit mit db.commit() gespeichert werden.
# autoflush=False: SQLAlchemy schreibt nicht automatisch vor jeder Abfrage.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Basisklasse für alle ORM-Modelle — registriert Tabellen bei create_all()."""
    pass


def get_db():
    """FastAPI-Dependency: öffnet eine DB-Session und schließt sie nach dem Request.

    Das yield-Pattern stellt sicher, dass die Session auch bei Exceptions geschlossen wird.
    Verwendung: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db  # Session wird dem Router übergeben
    finally:
        db.close()  # immer schließen — auch bei Fehlern
