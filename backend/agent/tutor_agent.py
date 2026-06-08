"""Tutor-Agent: orchestriert LLM-Tools für Code-Analyse und Chat.

Zwei Haupt-Entry-Points:
  - run_analysis(): ReAct-Agent analysiert Code mit 3 Tools (explain, debug, exercise)
  - run_chat(): ReAct-Agent beantwortet Chat-Nachrichten mit dynamischen personalisierten Tools
  - run_chat_with_context(): Direktes LLM-Gespräch wenn RAG-Kontext verfügbar ist
"""
import os
import re

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from agent.config import get_llm
from agent.tools.explain_tool import explain_code_tool
from agent.tools.debug_tool import debug_code_tool
from agent.tools.exercise_tool import exercise_tool
from agent.tools.exercise_generator_tool import generate_exercise
from agent.tools.skill_test_generator_tool import generate_skill_test

# exercise_evaluator_tool, hint_tool, skill_test_evaluator_tool are invoked
# directly by routers — not bound to this agent.
# generate_exercise and generate_skill_test are used in the chat agent loop.


class ServiceUnavailableError(Exception):
    """Wird geworfen wenn das LLM nicht erreichbar ist (Verbindungsfehler)."""
    pass


_SYSTEM_PROMPT = """\
Du bist ein Python-Tutor für Anfänger. Halte alle Antworten kurz und einfach.

Du hast Zugriff auf folgende Werkzeuge:
- explain_code_tool: Erklärt Python-Code kurz auf Deutsch.
- debug_code_tool: Findet Fehler im Code.
- exercise_tool: Generiert eine kurze Übungsaufgabe.
Analysiere den Code:
1. Rufe explain_code_tool auf.
2. Rufe debug_code_tool auf.
3. Rufe exercise_tool auf.

Gib deine Antwort GENAU in diesem Format aus — KURZ und EINFACH:

Erklärung: <2-3 Sätze, einfache Sprache>
Fehler gefunden: <ja oder nein>
Fehlertyp: <kurz oder "Kein Fehler">
Verbesserungsvorschlag: <1 Satz oder "Kein Fehler gefunden.">
Nächste Übung: <kurze Aufgabe, max. 3 Sätze>
"""


def _parse_agent_output(text: str) -> dict:
    """Extrahiert die 5 Pflichtfelder aus der Agenten-Antwort. Gibt Defaults zurück wenn Felder fehlen."""
    def extract(label: str) -> str | None:
        # Regex sucht nach "Label: Inhalt" bis zum nächsten Label oder Textende
        pattern = rf"(?i){re.escape(label)}[:\s]+(.+?)(?=\n[A-ZÄÖÜa-zäöü][^\n]*:|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    explanation = extract("Erklärung") or text  # Fallback: gesamter Text wenn kein Feld gefunden
    error_found_raw = (extract("Fehler gefunden") or "nein").lower()
    error_type = extract("Fehlertyp") or "Kein Fehler"
    suggestion = extract("Verbesserungsvorschlag") or "Keine Angabe"
    next_exercise = extract("Nächste Übung")

    return {
        "explanation": explanation,
        "error_found": "ja" in error_found_raw,  # String "ja" → bool
        "error_type": error_type,
        "suggestion": suggestion,
        "next_exercise": next_exercise,
    }


def _build_tools() -> list:
    """Gibt die 3 Basis-Tools für die Code-Analyse zurück (explain, debug, exercise)."""
    return [explain_code_tool, debug_code_tool, exercise_tool]


def _build_chat_tools(user_level: str, skill_progress: list[dict]) -> list:
    """Baut Chat-Tools mit eingebettetem User-Kontext (Closure).

    suggest_personalized_exercise und suggest_skill_test werden als Closures definiert,
    damit sie direkten Zugriff auf user_level und skill_progress haben ohne Parameter-Übergabe.
    Das rag_tool wird nur geladen wenn ein Vektorstore auf Disk existiert.
    """
    skill_keys = ", ".join(s["skill_key"] for s in skill_progress) if skill_progress else "keine"

    @tool(description=(
        "Generiert eine personalisierte Übungsaufgabe basierend auf dem Lernfortschritt des Studenten. "
        f"Verfügbare skill_keys: {skill_keys}. Wähle einen passenden skill_key aus der Liste."
    ))
    def suggest_personalized_exercise(skill_key: str) -> str:
        """Generiert eine personalisierte Übungsaufgabe."""
        skill = next((s for s in skill_progress if s["skill_key"] == skill_key), None)
        if not skill:
            return f"Skill '{skill_key}' nicht gefunden. Verfügbare Skills: {skill_keys}"
        # generate_exercise.invoke() ruft das LangChain-Tool direkt auf (kein Agent-Umweg)
        return generate_exercise.invoke({
            "skill_key": skill_key,
            "skill_label": skill["skill_label"],
            "level": user_level,
            "completed_exercise_titles": skill.get("completed_titles", ""),
        })

    @tool(description=(
        "Generiert einen Skill-Test zur Klausurvorbereitung. "
        f"Verfügbare skill_keys: {skill_keys}. Wähle einen passenden skill_key aus der Liste."
    ))
    def suggest_skill_test(skill_key: str) -> str:
        """Generiert einen Skill-Test."""
        skill = next((s for s in skill_progress if s["skill_key"] == skill_key), None)
        if not skill:
            return f"Skill '{skill_key}' nicht gefunden. Verfügbare Skills: {skill_keys}"
        return generate_skill_test.invoke({
            "skill_key": skill_key,
            "skill_label": skill["skill_label"],
            "user_level": user_level,
        })

    tools = [explain_code_tool, debug_code_tool, exercise_tool,
             suggest_personalized_exercise, suggest_skill_test]

    # RAG-Tool nur laden wenn der Vektorstore für diesen User existiert
    vectorstore_path = os.getenv(
        "RAG_VECTORSTORE_PATH",
        os.path.join(os.path.dirname(__file__), "..", "vectorstore"),
    )
    if os.path.isdir(vectorstore_path):
        from agent.tools.rag_tool import rag_tool
        tools.append(rag_tool)

    return tools


def _build_chat_system_prompt(user_level: str, skill_progress: list[dict], code: str) -> str:
    """Erstellt den System-Prompt für den Chat-Agenten mit personalisierten Schüler-Infos."""
    # Schwache Bereiche helfen dem Agenten, die richtigen Tools zu priorisieren
    partial_skills = [s["skill_label"] for s in skill_progress if s["status"] in ("partial", "not_understood")]
    weak_info = ", ".join(partial_skills) if partial_skills else "keine bekannten Schwächen"

    return (
        "Du bist ein freundlicher Python-Tutor. Antworte auf Deutsch, kurz und verständlich.\n\n"
        f"Student-Level: {user_level}\n"
        f"Schwache Bereiche: {weak_info}\n"
        f"Aktueller Code des Schülers:\n```python\n{code}\n```\n\n"
        "Wähle das passende Tool:\n"
        "- explain_code_tool: Bei Verständnisfragen zum Code\n"
        "- debug_code_tool: Wenn der Code Fehler hat\n"
        "- exercise_tool: Für einfache Code-basierte Übungen\n"
        "- suggest_personalized_exercise: Wenn Student üben will (nutzt Lernfortschritt)\n"
        "- suggest_skill_test: Wenn Student Klausur üben oder sich testen will\n"
        "Du kannst auch direkt antworten ohne Tool wenn kein Tool passt."
    )


def run_chat(
    message: str,
    code: str,
    history: list,
    user_level: str,
    skill_progress: list[dict],
) -> str:
    """ReAct-Agent beantwortet Chat-Nachrichten mit dynamischer Tool-Selektion.

    Der Agent entscheidet selbst welche Tools er aufruft (ReAct-Muster: Reason + Act).
    Die Chat-History wird als Liste von (role, content)-Tuples übergeben.
    """
    llm = get_llm()
    tools = _build_chat_tools(user_level, skill_progress)
    system_prompt = _build_chat_system_prompt(user_level, skill_progress, code)
    agent = create_agent(llm, tools, system_prompt=system_prompt)

    # History-Objekte können Pydantic-Modelle (mit .role) oder Dicts sein → beide behandeln
    messages = []
    for msg in history:
        role = msg.role if hasattr(msg, "role") else msg.get("role", "user")
        content = msg.content if hasattr(msg, "content") else msg.get("content", "")
        messages.append((role, content))
    messages.append(("human", message))  # aktuelle Nachricht ans Ende

    result = agent.invoke({"messages": messages})
    agent_messages = result.get("messages", [])
    # Letzte Nachricht ist die finale Antwort des Agenten
    return agent_messages[-1].content if agent_messages else ""


def run_chat_with_context(
    message: str,
    code: str,
    history: list,
    user_level: str,
    rag_context: str,
) -> str:
    """Beantwortet eine Frage direkt mit dem gefundenen PDF-Inhalt — kein Agent, kein Tool-Aufruf.

    Wird verwendet wenn _get_rag_context() relevante Passagen gefunden hat.
    Direktes LLM-Gespräch ist schneller als Agent-Loop für RAG-Antworten.
    Nur die letzten 6 Nachrichten (3 Runden) werden als Kontext übergeben.
    """
    llm = get_llm()

    history_text = ""
    for msg in history[-6:]:  # letzte 3 Runden — mehr würde den Kontext unnötig verlängern
        role = msg.role if hasattr(msg, "role") else msg.get("role", "user")
        content = msg.content if hasattr(msg, "content") else msg.get("content", "")
        prefix = "Schüler" if role == "user" else "Tutor"
        history_text += f"{prefix}: {content}\n"

    system = SystemMessage(content=(
        "Du bist ein freundlicher Python-Tutor. Antworte auf Deutsch, klar und verständlich.\n"
        f"Student-Level: {user_level}\n"
        f"Aktueller Code des Schülers:\n```python\n{code}\n```"
    ))
    human = HumanMessage(content=(
        f"Aus dem hochgeladenen Lernmaterial wurden folgende relevante Passagen gefunden:\n\n"
        f"{rag_context}\n\n"
        f"{'Bisheriger Chatverlauf:' + chr(10) + history_text if history_text else ''}"
        f"Frage des Schülers: {message}\n\n"
        "Beantworte die Frage auf Basis der Passagen aus dem Lernmaterial. "
        "Wenn die Antwort direkt im Material steht, zitiere die relevante Stelle und erkläre sie. "
        "Ergänze mit deinem Wissen nur wenn nötig."
    ))

    response = llm.invoke([system, human])
    return str(response.content)


def run_analysis(code: str) -> dict:
    """ReAct-Agent analysiert den Code mit allen verfügbaren Tools und gibt ein strukturiertes Ergebnis zurück.

    Der Agent ruft explain_code_tool, debug_code_tool und exercise_tool auf und
    parst die finale Textantwort in ein strukturiertes Dict.
    Bei Verbindungsfehlern wird ServiceUnavailableError geworfen (→ 503-Response).
    """
    try:
        llm = get_llm()
        tools = _build_tools()
        agent = create_agent(llm, tools, system_prompt=_SYSTEM_PROMPT)
        result = agent.invoke({  # type: ignore[arg-type]
            "messages": [("human", f"Analysiere diesen Python-Code:\n```python\n{code}\n```")]
        })
        messages = result.get("messages", [])
        final_text = messages[-1].content if messages else ""
        return _parse_agent_output(final_text)
    except Exception as e:
        # Verbindungsfehler → 503 statt 500 damit das Frontend klar kommunizieren kann
        if _is_connection_error(e):
            raise ServiceUnavailableError(
                "LLM ist nicht erreichbar. Bitte prüfe die KI-Engine-Konfiguration."
            ) from e
        raise


def _is_connection_error(e: Exception) -> bool:
    """Erkennt ob eine Exception ein Netzwerk/Verbindungsproblem zum LLM ist."""
    msg = str(e).lower()
    class_name = type(e).__name__.lower()
    keywords = ["connection", "connect", "refused", "unreachable", "timeout"]
    # Prüft sowohl die Exception-Message als auch den Klassennamen (z.B. ConnectionRefusedError)
    return any(kw in msg or kw in class_name for kw in keywords)
