# Einstiegspunkt der Anwendung — wird von uvicorn geladen
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers.tutor import router as tutor_router
from agent.tutor_agent import ServiceUnavailableError

import models  # noqa: F401
from core.database import Base, engine

Base.metadata.create_all(bind=engine)

import subprocess, sys
subprocess.run([sys.executable, "seed_data.py"], cwd=__file__.rsplit("/", 1)[0])

app = FastAPI(title="Agentic AI Python Tutor System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tutor_router)


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


@app.get("/")
def root():
    return {"message": "Python Tutor Backend läuft", "status": "ok"}
