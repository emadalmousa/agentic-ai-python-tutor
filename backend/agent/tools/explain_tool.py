from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm


@tool
def explain_code_tool(code: str, question: str | None = None) -> str:
    """Erklärt Python-Code Schritt für Schritt auf Deutsch."""
    llm = get_llm()
    system = SystemMessage(content=(
        "Du bist ein erfahrener Python-Tutor für Anfänger. "
        "Erkläre den folgenden Code so, dass ein kompletter Anfänger ihn versteht.\n\n"
        "Strukturiere deine Antwort GENAU so:\n"
        "1. Beginne mit einem Satz: was der Code insgesamt macht.\n"
        "2. Erkläre dann jede wichtige Zeile oder jeden Block einzeln — nummeriert.\n"
        "3. Erkläre verwendete Python-Konzepte kurz (z.B. was ist range(), was macht print()).\n"
        "4. Falls der Code einen Fehler hat: erkläre auch was der Fehler bewirkt.\n\n"
        "Schreibe klar, freundlich und auf Deutsch. Keine langen Fachbegriffe ohne Erklärung."
    ))
    user_content = f"Code:\n```python\n{code}\n```"
    if question:
        user_content += f"\n\nFrage des Schülers: {question}"
    human = HumanMessage(content=user_content)
    response = llm.invoke([system, human])
    return response.content
