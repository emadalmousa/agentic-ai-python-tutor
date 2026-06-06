from datetime import datetime, timedelta, timezone
import os

from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-ki-tutor")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 24 * 7  # 7 days — convenient for demo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
