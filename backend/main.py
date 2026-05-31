# Einstiegspunkt der Anwendung — wird von uvicorn geladen
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers.tutor import router as tutor_router
from routers.auth import router as auth_router
from routers.progress import router as progress_router
from routers.learning_progress import router as learning_progress_router
from routers.exercises import router as exercises_router
from routers.skill_tests import router as skill_tests_router
from agent.tutor_agent import ServiceUnavailableError

# Import all models so that create_all finds them
import models  # noqa: F401 — registers User and LearningSession with Base

from core.database import Base, engine

# Auto-create tables on startup (SQLite / demo — no migration needed)
Base.metadata.create_all(bind=engine)

# FastAPI-Anwendung erstellen
app = FastAPI(title="Agentic AI Python Tutor System")

# CORS aktivieren — erlaubt dem Frontend (Port 3000) das Backend (Port 8000) anzusprechen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router einbinden
app.include_router(tutor_router)
app.include_router(auth_router)
app.include_router(progress_router)
app.include_router(learning_progress_router)
app.include_router(exercises_router)
app.include_router(skill_tests_router)


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


# Health-Check — zeigt ob das Backend läuft
@app.get("/")
def root():
    return {"message": "Python Tutor Backend läuft", "status": "ok"}
