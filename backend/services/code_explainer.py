"""Dünne Service-Schicht für Code-Erklärungen.

Delegiert an run_analysis() im tutor_agent — extrahiert nur den Erklärungs-Teil.
Wird von Legacy-Routers genutzt die nur die Erklärung brauchen, nicht das volle Analyse-Dict.
"""
from agent.tutor_agent import run_analysis


def explain_code(code: str) -> str:
    """Gibt nur die Erklärung aus der vollständigen Code-Analyse zurück."""
    result = run_analysis(code)
    return result["explanation"]
