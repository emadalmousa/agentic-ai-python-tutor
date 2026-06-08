"""Passwort-Hashing und JWT-Tokenverwaltung für die Authentifizierung."""
from datetime import datetime, timedelta, timezone
import os

from jose import jwt
from passlib.context import CryptContext

# SECRET_KEY sollte in Produktion als Umgebungsvariable gesetzt sein
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-ki-tutor")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 24 * 7  # 7 Tage — bequem für Demo, in Produktion kürzer wählen

# bcrypt ist der aktuelle Standard für sicheres Passwort-Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Gibt den bcrypt-Hash des Klartextpassworts zurück."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Prüft ob ein Klartext-Passwort zu einem gespeicherten bcrypt-Hash passt."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Erstellt ein JWT mit den übergebenen Claims und einem Ablauf-Zeitstempel."""
    payload = data.copy()
    # exp-Claim setzt die Gültigkeitsdauer des Tokens
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Dekodiert und validiert ein JWT. Gibt None zurück wenn abgelaufen oder ungültig."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        # Jede Exception (abgelaufen, manipuliert, falscher Key) → ungültig
        return None
