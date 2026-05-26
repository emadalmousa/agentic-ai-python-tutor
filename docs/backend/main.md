# main.py

**Pfad:** `backend/main.py`
**Zweck:** Einstiegspunkt der Anwendung. Wird von `uvicorn` geladen.

## Was diese Datei macht

- Erstellt die FastAPI-App
- Registriert CORS-Middleware (erlaubt dem Frontend auf Port 3000 das Backend auf Port 8000 anzusprechen)
- Bindet den Tutor-Router ein (`/tutor/...`)
- Registriert einen globalen Exception-Handler für `ServiceUnavailableError`
- Stellt einen Health-Check-Endpunkt bereit

## Funktionen

### `root()` — `GET /`

```python
@app.get("/")
def root():
    return {"message": "Python Tutor Backend läuft", "status": "ok"}
```

Gibt immer `{"status": "ok"}` zurück. Wird verwendet um zu prüfen ob das Backend erreichbar ist.

### `service_unavailable_handler(request, exc)` — Exception-Handler

```python
@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})
```

Fängt `ServiceUnavailableError` aus `agent/tutor_agent.py` ab und gibt HTTP 503 zurück.
Ohne diesen Handler würde ein LLM-Verbindungsfehler als unkontrollierter 500-Fehler ankommen.

## Abhängigkeiten

| Import | Woher |
|--------|-------|
| `FastAPI` | `fastapi` |
| `CORSMiddleware` | `fastapi.middleware.cors` |
| `tutor_router` | `routers/tutor.py` |
| `ServiceUnavailableError` | `agent/tutor_agent.py` |

## Starten

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

Swagger UI erreichbar unter: `http://127.0.0.1:8000/docs`
