from fastapi import APIRouter
from models.schemas import CodeRequest, TutorResponse
from services.code_explainer import explain_code
from services.debugger import debug_code

# Router mit Präfix /tutor — alle Endpunkte hier beginnen mit /tutor/...
router = APIRouter(prefix="/tutor", tags=["Tutor"])

# Nächste Übung — in Phase 3 wird das dynamisch aus dem Lernfortschritt generiert
NEXT_EXERCISE = "Schreibe eine for-Schleife, die die Zahlen von 1 bis 10 ausgibt."


# Haupt-Endpunkt: nimmt Code entgegen und gibt eine Tutor-Analyse zurück
@router.post("/analyze", response_model=TutorResponse)
def analyze_code(request: CodeRequest) -> TutorResponse:
    # Code erklären
    explanation = explain_code(request.code, request.question)

    # Fehler suchen — gibt (bool, str) zurück
    error_found, suggestion = debug_code(request.code)

    # Alles zusammenpacken und als JSON zurückschicken
    return TutorResponse(
        explanation=explanation,
        error_found=error_found,
        suggestion=suggestion,
        next_exercise=NEXT_EXERCISE,
    )
