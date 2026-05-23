from agent.tutor_agent import run_analysis


def explain_code(code: str, question: str | None = None) -> str:
    result = run_analysis(code, question)
    return result["explanation"]
