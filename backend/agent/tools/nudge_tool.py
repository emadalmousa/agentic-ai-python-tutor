"""Generiert einen personalisierten Motivationstext für die dringendste Schwäche des Studenten."""
from langchain_core.messages import HumanMessage, SystemMessage

from agent.config import get_classifier_llm


def generate_nudge_text(skill_label: str, mistakes: list[str], feedback: str | None) -> str:
    """Gibt einen kurzen deutschen Motivationssatz zurück der auf die letzten Fehler eingeht.

    Wird nur aufgerufen wenn tatsächlich LearningEvents für diesen Skill existieren.
    Bei LLM-Fehler → generischer Fallback-Text.
    """
    mistake_summary = ", ".join(mistakes[:3]) if mistakes else ""
    feedback_snippet = (feedback or "")[:200]

    prompt = (
        f"Ein Python-Lernender hat Probleme mit dem Thema '{skill_label}'.\n"
    )
    if mistake_summary:
        prompt += f"Letzte Fehler: {mistake_summary}\n"
    if feedback_snippet:
        prompt += f"Letztes Feedback: {feedback_snippet}\n"
    prompt += (
        "\nSchreibe EINEN kurzen, motivierenden deutschen Satz (max. 20 Wörter) "
        "der konkret auf diese Fehler eingeht und fragt ob der Student jetzt üben möchte. "
        "Kein JSON, nur der reine Satz."
    )

    try:
        llm = get_classifier_llm()
        result = llm.invoke([
            SystemMessage(content="Du bist ein freundlicher Python-Tutor. Antworte auf Deutsch."),
            HumanMessage(content=prompt),
        ])
        text = result.content.strip().strip('"').strip("'")
        return text if text else f"Du hattest zuletzt Schwierigkeiten mit {skill_label}. Kurze Übung gefällig?"
    except Exception:
        return f"Du hattest zuletzt Schwierigkeiten mit '{skill_label}'. Kurze Übung gefällig?"
