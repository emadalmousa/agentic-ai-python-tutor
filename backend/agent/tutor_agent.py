from agent.tools.explain_tool import explain_code_tool
from agent.tools.debug_tool import debug_code_tool


class ServiceUnavailableError(Exception):
    pass


def run_analysis(code: str, question: str | None = None) -> dict:
    """Ruft explain und debug Tools auf, gibt strukturiertes Ergebnis zurück."""
    try:
        explanation = explain_code_tool.invoke({"code": code, "question": question})
        debug_result = debug_code_tool.invoke({"code": code})
        return {
            "explanation": explanation,
            "error_found": debug_result["error_found"],
            "suggestion": debug_result["suggestion"],
        }
    except Exception as e:
        if _is_connection_error(e):
            raise ServiceUnavailableError("Ollama ist nicht erreichbar. Bitte starte die KI-Engine.") from e
        raise


def _is_connection_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(kw in msg for kw in ["connection", "connect", "refused", "unreachable", "timeout"])
