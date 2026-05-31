"""Shared service for skill progress DB operations."""
from sqlalchemy.orm import Session

from models.skill_progress import StudentSkillProgress


def get_or_create_skill_progress(user_id: int, skill_key: str, db: Session) -> StudentSkillProgress:
    """Returns the skill-progress row for a user+skill, creating it if absent."""
    progress = db.query(StudentSkillProgress).filter_by(user_id=user_id, skill_key=skill_key).first()
    if not progress:
        progress = StudentSkillProgress(user_id=user_id, skill_key=skill_key, score=0, status="not_understood")
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress
