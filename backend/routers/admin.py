from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.database import get_db
from models import User, LearningSession, StudentSkillProgress, LearningEvent, ExerciseCompletion, SkillTestResult

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reset-db")
def reset_db(db: Session = Depends(get_db)):
    db.execute(text("TRUNCATE users, learning_sessions, student_skill_progress, learning_events, exercise_completions, skill_test_results RESTART IDENTITY CASCADE"))
    db.commit()
    return {"message": "Datenbank wurde geleert", "status": "ok"}
