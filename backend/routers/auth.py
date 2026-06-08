"""Auth-Router: Registrierung, Login und Profilverwaltung mit JWT-Authentifizierung."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import create_access_token, decode_access_token, hash_password, verify_password
from models.user import User, Role

router = APIRouter(prefix="/auth", tags=["auth"])

# HTTPBearer extrahiert den Bearer-Token aus dem Authorization-Header
_bearer = HTTPBearer()


# --- Pydantic schemas (inline, no separate schemas file needed for demo) ---

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    level: str = "Anfänger"
    goal: str = "Python Grundlagen"


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateMeRequest(BaseModel):
    name: str | None = None
    level: str | None = None
    goal: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    level: str
    goal: str
    role: str
    analyzed_count: int = 0

    model_config = {"from_attributes": True}


# --- Dependency: resolve current user from Bearer token ---

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI-Dependency: validiert den Bearer-Token und gibt den eingeloggten User zurück.

    Wirft 401 bei ungültigem/abgelaufenem Token oder nicht existierendem User.
    Wird von allen geschützten Endpunkten als Depends(get_current_user) genutzt.
    """
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Token")
    user_id = payload.get("sub")  # sub-Claim enthält die User-ID als String
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiger Token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        # Token gültig aber User wurde zwischenzeitlich gelöscht
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Benutzer nicht gefunden")
    return user


def _user_to_response(user: User, db: Session) -> UserResponse:
    """Konvertiert ein User-ORM-Objekt in eine UserResponse und zählt analysierte Sessions."""
    from models.session import LearningSession
    # Lazy-Import verhindert zirkuläre Importe zwischen auth und session-Modell
    analyzed_count = db.query(LearningSession).filter(LearningSession.user_id == user.id).count()
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        level=user.level,
        goal=user.goal,
        role=user.role,
        analyzed_count=analyzed_count,
    )


# --- Endpoints ---

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=400, detail="E-Mail bereits registriert")

    # Erster User in der Datenbank wird automatisch Admin
    is_first_user = db.query(User).count() == 0
    role = Role.ADMIN if is_first_user else Role.USER

    user = User(
        email=data.email.lower(),  # E-Mail immer lowercase speichern
        name=data.name,
        hashed_password=hash_password(data.password),
        level=data.level,
        goal=data.goal,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Token direkt nach Registrierung zurückgeben — kein separater Login nötig
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    # Beide Bedingungen (kein User, falsches Passwort) geben den gleichen Fehler
    # → kein Information-Leakage ob die E-Mail existiert
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Gibt das Profil des eingeloggten Users zurück."""
    return _user_to_response(current_user, db)


@router.put("/me", response_model=UserResponse)
def update_me(
    data: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aktualisiert Name, Level oder Lernziel des eingeloggten Users."""
    # None-Felder überspringen — nur gesetzte Werte aktualisieren (PATCH-Semantik via PUT)
    if data.name is not None:
        current_user.name = data.name
    if data.level is not None:
        current_user.level = data.level
    if data.goal is not None:
        current_user.goal = data.goal

    db.commit()
    db.refresh(current_user)
    return _user_to_response(current_user, db)
