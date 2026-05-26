from agent.tutor_agent import run_analysis


def explain_code(code: str) -> str:
    result = run_analysis(code)
    return result["explanation"]
