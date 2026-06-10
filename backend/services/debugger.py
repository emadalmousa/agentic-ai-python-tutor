"""Dünne Service-Schicht für Code-Debugging.

Delegiert an run_analysis() im tutor_agent — extrahiert nur die Fehlerinfo.
Gibt (error_found, suggestion) als Tupel zurück für direkte Verwendung in Routers.
"""
from agent.tutor_agent import run_analysis


def debug_code(code: str) -> tuple[bool, str]:
    """Gibt (error_found, suggestion) aus der vollständigen Code-Analyse zurück."""
    result = run_analysis(code)
    return result["error_found"], result["suggestion"]
