import os
import re

from langchain.agents import create_agent
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
    pass


_SYSTEM_PROMPT = """\
Du bist ein Python-Tutor für Anfänger. Halte alle Antworten kurz und einfach.

Du hast Zugriff auf folgende Werkzeuge:
- explain_code_tool: Erklärt Python-Code kurz auf Deutsch.
- debug_code_tool: Findet Fehler im Code.
- exercise_tool: Generiert eine kurze Übungsaufgabe.
- rag_tool: Sucht im Lernmaterial (nur wenn verfügbar).

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
        pattern = rf"(?i){re.escape(label)}[:\s]+(.+?)(?=\n[A-ZÄÖÜa-zäöü][^\n]*:|$)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    explanation = extract("Erklärung") or text
    error_found_raw = (extract("Fehler gefunden") or "nein").lower()
    error_type = extract("Fehlertyp") or "Kein Fehler"
    suggestion = extract("Verbesserungsvorschlag") or "Keine Angabe"
    next_exercise = extract("Nächste Übung")

    return {
        "explanation": explanation,
        "error_found": "ja" in error_found_raw,
        "error_type": error_type,
        "suggestion": suggestion,
        "next_exercise": next_exercise,
    }


def _build_tools() -> list:
    """Erstellt die Tool-Liste; rag_tool wird nur eingebunden wenn der Vektorstore existiert."""
    tools = [explain_code_tool, debug_code_tool, exercise_tool]
    vectorstore_path = os.getenv(
        "RAG_VECTORSTORE_PATH",
        os.path.join(os.path.dirname(__file__), "..", "vectorstore"),
    )
    if os.path.isdir(vectorstore_path):
        from agent.tools.rag_tool import rag_tool
        tools.append(rag_tool)
    return tools


def _get_rag_sources(code: str) -> list[str]:
    """Gibt relevante RAG-Quellen zurück, wenn ein Vektorstore vorhanden ist."""
    try:
        from agent.rag.vectorstore import load, query as vs_query

        index_data = load()
        if index_data is None:
            return []
        top_k = int(os.getenv("RAG_TOP_K", "3"))
        return vs_query(index_data, code, top_k=top_k)
    except Exception:
        return []


def _build_chat_tools(user_level: str, skill_progress: list[dict]) -> list:
    """Baut Chat-Tools mit eingebettetem User-Kontext (Closure)."""
    skill_keys = ", ".join(s["skill_key"] for s in skill_progress) if skill_progress else "keine"

    @tool
    def suggest_personalized_exercise(skill_key: str) -> str:
        f"""Generiert eine personalisierte Übungsaufgabe basierend auf dem Lernfortschritt des Studenten.
        Verfügbare skill_keys: {skill_keys}.
        Wähle einen passenden skill_key aus der Liste."""
        skill = next((s for s in skill_progress if s["skill_key"] == skill_key), None)
        if not skill:
            return f"Skill '{skill_key}' nicht gefunden. Verfügbare Skills: {skill_keys}"
        return generate_exercise.invoke({
            "skill_key": skill_key,
            "skill_label": skill["skill_label"],
            "level": user_level,
            "completed_exercise_titles": skill.get("completed_titles", ""),
        })

    @tool
    def suggest_skill_test(skill_key: str) -> str:
        f"""Generiert einen Skill-Test zur Klausurvorbereitung.
        Verfügbare skill_keys: {skill_keys}.
        Wähle einen passenden skill_key aus der Liste."""
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

    vectorstore_path = os.getenv(
        "RAG_VECTORSTORE_PATH",
        os.path.join(os.path.dirname(__file__), "..", "vectorstore"),
    )
    if os.path.isdir(vectorstore_path):
        from agent.tools.rag_tool import rag_tool
        tools.append(rag_tool)

    return tools


def _build_chat_system_prompt(user_level: str, skill_progress: list[dict], code: str) -> str:
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
        "- rag_tool: Bei Fragen zum hochgeladenen Lernmaterial\n"
        "Du kannst auch direkt antworten ohne Tool wenn kein Tool passt."
    )


def run_chat(
    message: str,
    code: str,
    history: list,
    user_level: str,
    skill_progress: list[dict],
) -> str:
    """ReAct-Agent beantwortet Chat-Nachrichten mit dynamischer Tool-Selektion."""
    llm = get_llm()
    tools = _build_chat_tools(user_level, skill_progress)
    system_prompt = _build_chat_system_prompt(user_level, skill_progress, code)
    agent = create_agent(llm, tools, system_prompt=system_prompt)

    messages = []
    for msg in history:
        role = msg.role if hasattr(msg, "role") else msg.get("role", "user")
        content = msg.content if hasattr(msg, "content") else msg.get("content", "")
        messages.append((role, content))
    messages.append(("human", message))

    result = agent.invoke({"messages": messages})
    agent_messages = result.get("messages", [])
    return agent_messages[-1].content if agent_messages else ""


def run_analysis(code: str) -> dict:
    """ReAct-Agent analysiert den Code mit allen verfügbaren Tools und gibt ein strukturiertes Ergebnis zurück."""
    try:
        llm = get_llm()
        tools = _build_tools()
        agent = create_agent(llm, tools, system_prompt=_SYSTEM_PROMPT)
        result = agent.invoke({
            "messages": [("human", f"Analysiere diesen Python-Code:\n```python\n{code}\n```")]
        })
        messages = result.get("messages", [])
        final_text = messages[-1].content if messages else ""
        parsed = _parse_agent_output(final_text)
        parsed["sources"] = _get_rag_sources(code)
        return parsed
    except Exception as e:
        if _is_connection_error(e):
            raise ServiceUnavailableError(
                "LLM ist nicht erreichbar. Bitte prüfe die KI-Engine-Konfiguration."
            ) from e
        raise


def _is_connection_error(e: Exception) -> bool:
    msg = str(e).lower()
    class_name = type(e).__name__.lower()
    keywords = ["connection", "connect", "refused", "unreachable", "timeout"]
    return any(kw in msg or kw in class_name for kw in keywords)
