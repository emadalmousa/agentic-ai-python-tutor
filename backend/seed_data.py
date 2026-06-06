"""
Seed script — fills the database with realistic test data.
Run from the backend directory:
    python seed_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from core.database import engine, Base
from core.security import hash_password
from models.user import User, Role
from models.skill_progress import StudentSkillProgress, LearningEvent, SKILL_TREE
from models.exercise import ExerciseCompletion
from models.skill_test import SkillTestResult
from models.session import LearningSession

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_skill_progress(db: Session, user_id: int, scores: dict[str, int]):
    """Insert StudentSkillProgress rows. scores = {skill_key: score}"""
    for skill in SKILL_TREE:
        key = skill["key"]
        score = scores.get(key, 0)
        if score == 0:
            continue
        status = "understood" if score >= 75 else "partial" if score >= 40 else "not_understood"
        db.add(StudentSkillProgress(user_id=user_id, skill_key=key, score=score, status=status))


def _add_exercise_completions(db: Session, user_id: int, completions: dict[str, int]):
    """completions = {exercise_id: score_granted (0|10|20)}"""
    for exercise_id, score in completions.items():
        skill_key = exercise_id.rsplit("_", 1)[0]
        db.add(ExerciseCompletion(
            user_id=user_id,
            skill_key=skill_key,
            exercise_id=exercise_id,
            score_granted=score,
            is_locked=(score == 20),
        ))


def _add_events(db: Session, user_id: int, events: list[dict]):
    for e in events:
        db.add(LearningEvent(
            user_id=user_id,
            skill_key=e["skill_key"],
            score=e["score"],
            mistakes=e.get("mistakes", []),
            feedback=e["feedback"],
            recommended_exercise=e.get("recommended_exercise", ""),
        ))


# ---------------------------------------------------------------------------
# Main seed
# ---------------------------------------------------------------------------

with Session(engine) as db:

    # Skip if already seeded
    if db.query(User).first():
        print("✓ DB already seeded, skipping")
        raise SystemExit(0)

    # -----------------------------------------------------------------------
    # 1. Admin — Emad Almousa (Fortgeschritten, alle Beginner-Skills ≥ 80%)
    # -----------------------------------------------------------------------
    emad = User(
        name="Emad Almousa",
        email="almousa.emad.92@gmail.com",
        hashed_password=hash_password("Emad/magster92"),
        level="Fortgeschritten",
        goal="Python Mastery & KI-Entwicklung",
        role=Role.ADMIN,
    )
    db.add(emad)
    db.flush()

    _add_skill_progress(db, emad.id, {
        "variables":       100,
        "datatypes":       100,
        "input_output":    100,
        "string_methods":  95,
        "type_conversion": 90,
        "if_else":         100,
        "for_loop":        100,
        "while_loop":      95,
        "lists":           90,
        "tuples":          85,
        "sets":            80,
        "dictionaries":    85,
        "functions":       100,
        "list_comprehension": 70,
        "error_handling":  60,
    })

    _add_exercise_completions(db, emad.id, {
        "variables_1": 20, "variables_2": 20, "variables_3": 20, "variables_4": 20, "variables_5": 20,
        "datatypes_1": 20, "datatypes_2": 20, "datatypes_3": 20, "datatypes_4": 20, "datatypes_5": 20,
        "for_loop_1":  20, "for_loop_2":  20, "for_loop_3":  20, "for_loop_4":  20, "for_loop_5":  20,
        "functions_1": 20, "functions_2": 20, "functions_3": 20, "functions_4": 20, "functions_5": 20,
    })

    _add_events(db, emad.id, [
        {"skill_key": "list_comprehension", "score": 70, "feedback": "Gute Grundkenntnisse, aber verschachtelte Comprehensions noch üben.", "mistakes": ["Kein Filter verwendet"]},
        {"skill_key": "error_handling",     "score": 60, "feedback": "try/except wird verstanden, finally noch nicht sicher eingesetzt.", "mistakes": ["finally vergessen"]},
    ])

    db.add(SkillTestResult(user_id=emad.id, skill_key="variables", score=90, passed=True, attempt_number=1))
    db.add(SkillTestResult(user_id=emad.id, skill_key="for_loop",  score=85, passed=True, attempt_number=1))

    # -----------------------------------------------------------------------
    # 2. Anna Schmidt — Anfänger, gerade bei Schleifen angekommen
    # -----------------------------------------------------------------------
    anna = User(
        name="Anna Schmidt",
        email="anna.schmidt@example.com",
        hashed_password=hash_password("Anna2024!"),
        level="Anfänger",
        goal="Python Grundlagen lernen",
        role=Role.USER,
    )
    db.add(anna)
    db.flush()

    _add_skill_progress(db, anna.id, {
        "variables":    100,
        "datatypes":    90,
        "input_output": 80,
        "string_methods": 60,
        "type_conversion": 40,
        "if_else":      20,
    })

    _add_exercise_completions(db, anna.id, {
        "variables_1": 20, "variables_2": 20, "variables_3": 20, "variables_4": 20, "variables_5": 20,
        "datatypes_1": 20, "datatypes_2": 20, "datatypes_3": 20, "datatypes_4": 20, "datatypes_5": 20,
        "if_else_1":   20, "if_else_2":   10,
    })

    _add_events(db, anna.id, [
        {"skill_key": "string_methods", "score": 60, "feedback": "Grundmethoden bekannt, replace() und split() noch üben.", "mistakes": ["split() vergessen"]},
        {"skill_key": "if_else",        "score": 20, "feedback": "if/else Grundstruktur verstanden, elif noch unklar.", "mistakes": ["elif nicht verwendet", "Einrückungsfehler"]},
    ])

    db.add(SkillTestResult(user_id=anna.id, skill_key="variables", score=95, passed=True, attempt_number=1))

    # -----------------------------------------------------------------------
    # 3. Max Müller — Profi-Anwärter, fast alle Skills auf 100%
    # -----------------------------------------------------------------------
    max_user = User(
        name="Max Müller",
        email="max.mueller@example.com",
        hashed_password=hash_password("Max2024!"),
        level="Fortgeschritten",
        goal="Alle Python-Skills meistern",
        role=Role.USER,
    )
    db.add(max_user)
    db.flush()

    _add_skill_progress(db, max_user.id, {
        "variables":       100, "datatypes":       100, "input_output":    100,
        "string_methods":  100, "type_conversion": 100, "if_else":         100,
        "for_loop":        100, "while_loop":      100, "lists":           100,
        "tuples":          100, "sets":            100, "dictionaries":    100,
        "functions":       100,
        "list_comprehension": 90, "error_handling": 85, "file_io": 80,
        "classes_basic":   75,
    })

    _add_exercise_completions(db, max_user.id, {
        f"{skill}_{i}": 20
        for skill in ["variables","datatypes","input_output","string_methods","type_conversion",
                      "if_else","for_loop","while_loop","lists","tuples","sets","dictionaries","functions"]
        for i in range(1, 6)
    })

    _add_events(db, max_user.id, [
        {"skill_key": "classes_basic", "score": 75, "feedback": "Klassen gut verstanden, self-Parameter noch unsicher.", "mistakes": ["self vergessen"]},
    ])

    for skill in ["variables","datatypes","for_loop","functions","lists","if_else"]:
        db.add(SkillTestResult(user_id=max_user.id, skill_key=skill, score=92, passed=True, attempt_number=1))

    # -----------------------------------------------------------------------
    # 4. Lena Weber — Kompletter Neuling, nur Variables angefangen
    # -----------------------------------------------------------------------
    lena = User(
        name="Lena Weber",
        email="lena.weber@example.com",
        hashed_password=hash_password("Lena2024!"),
        level="Anfänger",
        goal="Python für Data Science",
        role=Role.USER,
    )
    db.add(lena)
    db.flush()

    _add_skill_progress(db, lena.id, {
        "variables": 40,
    })

    _add_exercise_completions(db, lena.id, {
        "variables_1": 20, "variables_2": 10,
    })

    _add_events(db, lena.id, [
        {"skill_key": "variables", "score": 40, "feedback": "Variable erstellen klappt, aber Datentypen noch unklar.", "mistakes": ["Variablenname mit Zahl begonnen", "Kein Wert zugewiesen"]},
    ])

    # -----------------------------------------------------------------------
    # 5. Tom Becker — Mittelstufe, stockt bei Klassen
    # -----------------------------------------------------------------------
    tom = User(
        name="Tom Becker",
        email="tom.becker@example.com",
        hashed_password=hash_password("Tom2024!"),
        level="Fortgeschritten",
        goal="OOP und Klassen verstehen",
        role=Role.USER,
    )
    db.add(tom)
    db.flush()

    _add_skill_progress(db, tom.id, {
        "variables":       100, "datatypes":       100, "input_output":    100,
        "string_methods":  95,  "type_conversion": 90,  "if_else":         100,
        "for_loop":        100, "while_loop":      90,  "lists":           85,
        "tuples":          80,  "sets":            80,  "dictionaries":    80,
        "functions":       90,
        "list_comprehension": 80, "error_handling": 75, "file_io": 60,
        "classes_basic":   30,
    })

    _add_events(db, tom.id, [
        {"skill_key": "classes_basic", "score": 30, "feedback": "__init__ wird oft vergessen, self-Parameter unklar.", "mistakes": ["__init__ fehlt", "self nicht übergeben"]},
        {"skill_key": "file_io",       "score": 60, "feedback": "open() bekannt, with-Statement noch nicht verwendet.", "mistakes": ["File nicht geschlossen"]},
    ])

    for skill in ["variables","for_loop","if_else","functions"]:
        db.add(SkillTestResult(user_id=tom.id, skill_key=skill, score=88, passed=True, attempt_number=1))

    db.add(SkillTestResult(user_id=tom.id, skill_key="classes_basic", score=45, passed=False, attempt_number=2))

    db.commit()
    print("✓ Seed erfolgreich — 5 User angelegt:")
    print("  Admin : Emad Almousa       — almousa.emad.92@gmail.com  / Emad/magster92")
    print("  User  : Anna Schmidt       — anna.schmidt@example.com   / Anna2024!")
    print("  User  : Max Müller         — max.mueller@example.com    / Max2024!")
    print("  User  : Lena Weber         — lena.weber@example.com     / Lena2024!")
    print("  User  : Tom Becker         — tom.becker@example.com     / Tom2024!")
