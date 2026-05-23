# Einstiegspunkt der Anwendung — wird von uvicorn geladen
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers.tutor import router as tutor_router
from agent.tutor_agent import ServiceUnavailableError

# FastAPI-Anwendung erstellen
app = FastAPI(title="Agentic AI Python Tutor System")

# CORS aktivieren — erlaubt dem Frontend (Port 3000) das Backend (Port 8000) anzusprechen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tutor-Router einbinden — registriert alle /tutor/... Endpunkte
app.include_router(tutor_router)


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
