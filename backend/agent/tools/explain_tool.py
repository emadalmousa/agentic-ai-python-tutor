from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm


@tool
def explain_code_tool(code: str, question: str | None = None) -> str:
    """Erklärt Python-Code Schritt für Schritt auf Deutsch."""
    llm = get_llm()
    system = SystemMessage(content=(
        "Du bist ein freundlicher Python-Tutor für Anfänger. "
        "Erkläre den folgenden Code Schritt für Schritt, klar und auf Deutsch. "
        "Nutze einfache Sprache, keine Fachbegriffe ohne Erklärung."
    ))
    user_content = f"Code:\n```python\n{code}\n```"
    if question:
        user_content += f"\n\nFrage des Schülers: {question}"
    human = HumanMessage(content=user_content)
    response = llm.invoke([system, human])
    return response.content
