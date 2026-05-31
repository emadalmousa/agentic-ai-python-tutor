from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from core.database import Base

# DEV NOTE: If the DB already exists without this UniqueConstraint, delete the
# existing DB before starting the server — PostgreSQL/SQLite cannot add constraints
# to existing tables without a migration. The constraint is created fresh on startup
# via Base.metadata.create_all.

# Full 37-skill tree. order is level-local (1-based within each level).
# Each entry: key, German label, level, level-local order, unlocks_after (previous skill key or None).
SKILL_TREE = [
    # --- Beginner (13 skills) ---
    {"key": "variables",        "label": "Variablen",             "level": "beginner",     "order": 1,  "unlocks_after": None},
    {"key": "datatypes",        "label": "Datentypen",            "level": "beginner",     "order": 2,  "unlocks_after": "variables"},
    {"key": "input_output",     "label": "Eingabe & Ausgabe",     "level": "beginner",     "order": 3,  "unlocks_after": "datatypes"},
    {"key": "string_methods",   "label": "String-Methoden",       "level": "beginner",     "order": 4,  "unlocks_after": "input_output"},
    {"key": "type_conversion",  "label": "Typumwandlung",         "level": "beginner",     "order": 5,  "unlocks_after": "string_methods"},
    {"key": "if_else",          "label": "If/Else",               "level": "beginner",     "order": 6,  "unlocks_after": "type_conversion"},
    {"key": "for_loop",         "label": "For-Schleifen",         "level": "beginner",     "order": 7,  "unlocks_after": "if_else"},
    {"key": "while_loop",       "label": "While-Schleifen",       "level": "beginner",     "order": 8,  "unlocks_after": "for_loop"},
    {"key": "lists",            "label": "Listen",                "level": "beginner",     "order": 9,  "unlocks_after": "while_loop"},
    {"key": "tuples",           "label": "Tupel",                 "level": "beginner",     "order": 10, "unlocks_after": "lists"},
    {"key": "sets",             "label": "Mengen",                "level": "beginner",     "order": 11, "unlocks_after": "tuples"},
    {"key": "dictionaries",     "label": "Dictionaries",          "level": "beginner",     "order": 12, "unlocks_after": "sets"},
    {"key": "functions",        "label": "Funktionen",            "level": "beginner",     "order": 13, "unlocks_after": "dictionaries"},
    # --- Intermediate (12 skills) ---
    {"key": "list_comprehension","label": "List Comprehension",   "level": "intermediate", "order": 1,  "unlocks_after": None},
    {"key": "error_handling",   "label": "Fehlerbehandlung",      "level": "intermediate", "order": 2,  "unlocks_after": "list_comprehension"},
    {"key": "file_io",          "label": "Datei-Ein/Ausgabe",     "level": "intermediate", "order": 3,  "unlocks_after": "error_handling"},
    {"key": "classes_basic",    "label": "Klassen Grundlagen",    "level": "intermediate", "order": 4,  "unlocks_after": "file_io"},
    {"key": "instance_methods", "label": "Instanz-Methoden",      "level": "intermediate", "order": 5,  "unlocks_after": "classes_basic"},
    {"key": "instance_variables","label": "Instanz-Variablen",    "level": "intermediate", "order": 6,  "unlocks_after": "instance_methods"},
    {"key": "static_methods",   "label": "Statische Methoden",    "level": "intermediate", "order": 7,  "unlocks_after": "instance_variables"},
    {"key": "class_methods",    "label": "Klassen-Methoden",      "level": "intermediate", "order": 8,  "unlocks_after": "static_methods"},
    {"key": "magic_methods",    "label": "Magic Methods",         "level": "intermediate", "order": 9,  "unlocks_after": "class_methods"},
    {"key": "modules_imports",  "label": "Module & Imports",      "level": "intermediate", "order": 10, "unlocks_after": "magic_methods"},
    {"key": "lambda_functions", "label": "Lambda-Funktionen",     "level": "intermediate", "order": 11, "unlocks_after": "modules_imports"},
    {"key": "map_filter_reduce","label": "Map/Filter/Reduce",     "level": "intermediate", "order": 12, "unlocks_after": "lambda_functions"},
    # --- Advanced (12 skills) ---
    {"key": "inheritance",      "label": "Vererbung",             "level": "advanced",     "order": 1,  "unlocks_after": None},
    {"key": "polymorphism",     "label": "Polymorphismus",        "level": "advanced",     "order": 2,  "unlocks_after": "inheritance"},
    {"key": "abstract_classes", "label": "Abstrakte Klassen",     "level": "advanced",     "order": 3,  "unlocks_after": "polymorphism"},
    {"key": "interfaces",       "label": "Interfaces",            "level": "advanced",     "order": 4,  "unlocks_after": "abstract_classes"},
    {"key": "decorators",       "label": "Dekoratoren",           "level": "advanced",     "order": 5,  "unlocks_after": "interfaces"},
    {"key": "generators",       "label": "Generatoren",           "level": "advanced",     "order": 6,  "unlocks_after": "decorators"},
    {"key": "context_managers", "label": "Kontextmanager",        "level": "advanced",     "order": 7,  "unlocks_after": "generators"},
    {"key": "recursion",        "label": "Rekursion",             "level": "advanced",     "order": 8,  "unlocks_after": "context_managers"},
    {"key": "algorithms",       "label": "Algorithmen",           "level": "advanced",     "order": 9,  "unlocks_after": "recursion"},
    {"key": "design_patterns",  "label": "Entwurfsmuster",        "level": "advanced",     "order": 10, "unlocks_after": "algorithms"},
    {"key": "async_await",      "label": "Async/Await",           "level": "advanced",     "order": 11, "unlocks_after": "design_patterns"},
    {"key": "testing",          "label": "Testen",                "level": "advanced",     "order": 12, "unlocks_after": "async_await"},
]

# Backward-compatibility alias — existing code that does `for key, label in FIXED_SKILLS` continues to work.
FIXED_SKILLS = [(s["key"], s["label"]) for s in SKILL_TREE]


class StudentSkillProgress(Base):
    """Aktueller Wissensstand eines Studenten pro Skill (wird bei jeder Analyse aktualisiert)."""
    __tablename__ = "student_skill_progress"

    # DEV NOTE: UniqueConstraint added — existing DB must be dropped before first run.
    __table_args__ = (UniqueConstraint("user_id", "skill_key"),)

    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_key = Column(String, nullable=False)           # z. B. "for_loop"
    score     = Column(Integer, default=0)               # 0–100
    status    = Column(String, default="not_understood") # understood | partial | not_understood
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class LearningEvent(Base):
    """Einzelnes Analyse-Ereignis — unveränderlich, dient als History."""
    __tablename__ = "learning_events"

    id                    = Column(Integer, primary_key=True)
    user_id               = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_key             = Column(String, nullable=False)
    score                 = Column(Integer, nullable=False)
    mistakes              = Column(JSON, default=list)   # list[str]
    feedback              = Column(Text)
    recommended_exercise  = Column(Text)
    created_at            = Column(DateTime(timezone=True), server_default=func.now())
