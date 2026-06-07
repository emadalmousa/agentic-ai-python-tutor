from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import get_llm


@tool
def exercise_tool(code: str, error_found: bool, suggestion: str) -> str:
    """Generiert eine passende Übungsaufgabe basierend auf dem Code und gefundenen Fehlern."""
    llm = get_llm()
    system = SystemMessage(content=(
        "Du bist ein kreativer Python-Tutor für Anfänger.\n"
        "Erstelle eine motivierende, konkrete Übungsaufgabe auf Deutsch.\n\n"
        "Die Aufgabe MUSS folgende Struktur haben:\n"
        "🎯 Aufgabe: [Ein klarer Satz was der Schüler programmieren soll]\n"
        "💡 Tipp: [Ein hilfreicher Hinweis wie man anfangen kann]\n"
        "✅ Ziel: [Was der fertige Code ausgeben oder tun soll — mit konkretem Beispiel]\n\n"
        "Die Aufgabe soll zum Code und zum Lernstand des Schülers passen. "
        "Sei kreativ — keine langweiligen Standard-Aufgaben!"
    ))
    if error_found:
        context = (
            f"Der Schüler hat diesen Code geschrieben:\n```python\n{code}\n```\n\n"
            f"Problem gefunden: {suggestion}\n\n"
            "Erstelle eine Übung die genau dieses Konzept übt, damit der Schüler den Fehler versteht und nicht wiederholt."
        )
    else:
        context = (
            f"Der Schüler hat diesen korrekten Code geschrieben:\n```python\n{code}\n```\n\n"
            "Erstelle eine leicht fortgeschrittenere Übung die auf diesem Code aufbaut "
            "und ein neues spannendes Konzept einführt."
        )
    human = HumanMessage(content=context)
    response = llm.invoke([system, human])
    return str(response.content)
