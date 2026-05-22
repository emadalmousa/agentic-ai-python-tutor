from pydantic import BaseModel


# Eingabe vom Benutzer: der Python-Code und eine optionale Frage
class CodeRequest(BaseModel):
    code: str
    question: str | None = None  # optional — kann leer bleiben


# Ausgabe des Backends: Erklärung, Fehlerstatus, Hinweis und nächste Übung
class TutorResponse(BaseModel):
    explanation: str   # Erklärung des Codes
    error_found: bool  # True wenn ein Fehler erkannt wurde
    suggestion: str    # Hinweis oder Fehlerbeschreibung
    next_exercise: str | None = None  # optionale Übungsaufgabe
