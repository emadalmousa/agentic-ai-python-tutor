"""Service für das Agent-Gedächtnis — lädt und aktualisiert die Chat-Zusammenfassung per LLM."""
from sqlalchemy.orm import Session

from agent.config import get_classifier_llm
from langchain_core.messages import SystemMessage, HumanMessage
from models.agent_memory import AgentMemory

_SUMMARIZE_SYSTEM = SystemMessage(content=(
    "Du bist ein Gedächtnis-System für einen Python-Tutor. "
    "Du erhältst die bisherige Zusammenfassung (kann leer sein) und den neuesten Chat-Austausch. "
    "Erstelle eine aktualisierte, kompakte Zusammenfassung (max. 150 Wörter) auf Deutsch mit:\n"
    "- Welche Python-Themen wurden besprochen?\n"
    "- Welche Fehler oder Missverständnisse gab es?\n"
    "- Was hat der Student gut verstanden?\n"
    "Kein JSON, nur Fließtext. Nur die aktualisierte Zusammenfassung, nichts anderes."
))


def load_memory(user_id: int, db: Session) -> str | None:
    """Gibt die gespeicherte Zusammenfassung zurück oder None wenn noch keine existiert."""
    row = db.query(AgentMemory).filter_by(user_id=user_id).first()
    return row.summary if row else None


def update_memory(user_id: int, db: Session, user_msg: str, assistant_msg: str) -> None:
    """Aktualisiert die Zusammenfassung nach einem Chat-Turn per LLM.

    Fehler werden still ignoriert — das Gedächtnis ist non-critical.
    """
    try:
        existing = load_memory(user_id, db) or ""
        llm = get_classifier_llm()  # günstiges Modell reicht für Zusammenfassungen
        prompt = (
            f"Bisherige Zusammenfassung:\n{existing}\n\n"
            f"Neuer Austausch:\nSchüler: {user_msg[:500]}\nTutor: {assistant_msg[:500]}\n\n"
            "Erstelle die aktualisierte Zusammenfassung:"
        )
        result = llm.invoke([_SUMMARIZE_SYSTEM, HumanMessage(content=prompt)])
        new_summary = str(result.content).strip()[:2000]  # max 2000 Zeichen in DB

        row = db.query(AgentMemory).filter_by(user_id=user_id).first()
        if row:
            row.summary = new_summary
        else:
            db.add(AgentMemory(user_id=user_id, summary=new_summary))
        db.commit()
    except Exception:
        db.rollback()  # Memory-Update darf niemals den Chat-Flow unterbrechen
