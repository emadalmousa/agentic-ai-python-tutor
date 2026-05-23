from agent.tools.explain_tool import explain_code_tool
from agent.tools.debug_tool import debug_code_tool
from agent.tools.exercise_tool import exercise_tool


class ServiceUnavailableError(Exception):
    pass


def run_analysis(code: str, question: str | None = None) -> dict:
    """Ruft explain, debug und exercise Tools auf, gibt strukturiertes Ergebnis zurück."""
    try:
        explanation = explain_code_tool.invoke({"code": code, "question": question})
        debug_result = debug_code_tool.invoke({"code": code})
        next_exercise = exercise_tool.invoke({
            "code": code,
            "error_found": debug_result["error_found"],
            "suggestion": debug_result["suggestion"],
        })
        return {
            "explanation": explanation,
            "error_found": debug_result["error_found"],
            "error_type": debug_result.get("error_type", "Kein Fehler"),
            "suggestion": debug_result["suggestion"],
            "next_exercise": next_exercise,
        }
    except Exception as e:
        if _is_connection_error(e):
            raise ServiceUnavailableError("Ollama ist nicht erreichbar. Bitte starte die KI-Engine.") from e
        raise


def _is_connection_error(e: Exception) -> bool:
    msg = str(e).lower()
    class_name = type(e).__name__.lower()
    keywords = ["connection", "connect", "refused", "unreachable", "timeout"]
    return any(kw in msg or kw in class_name for kw in keywords)
