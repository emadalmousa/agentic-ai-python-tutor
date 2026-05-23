from agent.tutor_agent import run_analysis


def debug_code(code: str) -> tuple[bool, str]:
    result = run_analysis(code)
    return result["error_found"], result["suggestion"]
