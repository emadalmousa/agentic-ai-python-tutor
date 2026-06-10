"""Pydantic-Schemas für den Tutor-Router.

Diese Schemas definieren die Request/Response-Strukturen für:
- Code-Analyse (/tutor/analyze)
- Chat (/tutor/chat)
- Code-Ausführung (/tutor/run)
- PDF-Upload (/tutor/upload-material)
"""
from pydantic import BaseModel


class CodeRequest(BaseModel):
    """Anfrage für die Code-Analyse."""
    code: str


class TutorResponse(BaseModel):
    """Strukturierte Antwort der Code-Analyse mit Erklärung, Fehler und Übungsvorschlag."""
    explanation: str
    error_found: bool
    error_type: str = "Kein Fehler"
    suggestion: str
    next_exercise: str | None = None  # None wenn Agent keine Übung generiert hat
    sources: list[str] = []           # RAG-Quellen (Seitenreferenzen aus dem PDF)


class ChatMessage(BaseModel):
    """Eine einzelne Nachricht im Chat-Verlauf."""
    role: str        # "user" (Student) oder "assistant" (Tutor)
    content: str


class ChatRequest(BaseModel):
    """Chat-Anfrage mit aktuellem Code, Nachricht und bisheriger History."""
    code: str
    message: str
    history: list[ChatMessage] = []   # leer beim ersten Chat-Aufruf


class ChatResponse(BaseModel):
    """Chat-Antwort mit der Tutor-Antwort und der aktualisierten History."""
    reply: str
    history: list[ChatMessage]  # enthält alle Nachrichten inkl. der neuen


class RunRequest(BaseModel):
    """Anfrage zur direkten Code-Ausführung ohne Bewertung."""
    code: str


class RunResponse(BaseModel):
    """Ergebnis der Code-Ausführung: stdout, stderr und Exit-Code."""
    stdout: str
    stderr: str
    exit_code: int  # 0 = erfolgreich, != 0 = Fehler aufgetreten


class UploadResponse(BaseModel):
    """Antwort nach erfolgreichem PDF-Upload."""
    status: str    # "ok"
    chunks: int    # Anzahl der erzeugten Vektorstore-Chunks
