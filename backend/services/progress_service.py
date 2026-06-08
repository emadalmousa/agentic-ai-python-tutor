"""Gemeinsamer Service für Skill-Fortschritt-Datenbankoperationen."""
from sqlalchemy.orm import Session

from models.skill_progress import StudentSkillProgress


def get_or_create_skill_progress(user_id: int, skill_key: str, db: Session) -> StudentSkillProgress:
    """Gibt den Skill-Fortschritt-Eintrag zurück, erstellt ihn falls er nicht existiert.

    Wird von mehreren Routers (exercises, learning_progress) verwendet um
    doppelten DB-Code zu vermeiden. Der neue Eintrag startet mit score=0 und
    status='not_understood'.
    """
    progress = db.query(StudentSkillProgress).filter_by(user_id=user_id, skill_key=skill_key).first()
    if not progress:
        # Neuer Skill-Eintrag: Startzustand für alle neuen Skills
        progress = StudentSkillProgress(user_id=user_id, skill_key=skill_key, score=0, status="not_understood")
        db.add(progress)
        db.commit()
        db.refresh(progress)  # refresh lädt die server-generierten Felder (id, created_at)
    return progress
