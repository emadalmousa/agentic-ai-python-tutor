"""ORM-Modelle für den Skill-Lernfortschritt (Tabellen: student_skill_progress, learning_events).

SKILL_TREE definiert alle verfügbaren Python-Skills in drei Levels:
- beginner:     13 Skills (Variables bis Functions)
- intermediate: 12 Skills (List Comprehension bis Map/Filter/Reduce)
- advanced:     12 Skills (Vererbung bis Testing)

unlocks_after: Vorgänger-Skill der >= 80 Punkte haben muss, damit dieser Skill freigeschaltet wird.
unlocks_after=None: immer freigeschaltet (Einstiegs-Skill jedes Levels).
"""
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base

SKILL_TREE = [
    # --- Beginner (13 Skills) ---
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
    # --- Intermediate (12 Skills) ---
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
    # --- Advanced (12 Skills) ---
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

# Flache Liste aller (key, label)-Paare — wird von mehreren Routers für Anzeige genutzt
FIXED_SKILLS = [(s["key"], s["label"]) for s in SKILL_TREE]


class StudentSkillProgress(Base):
    """Fortschritt eines Studenten bei einem einzelnen Skill.

    score: 0-100 — wird als Summe der ExerciseCompletion.score_granted berechnet.
    status: 'understood' (>= 80%), 'partial' (>= 40%), 'not_understood' (< 40%).
    UniqueConstraint verhindert doppelte Einträge für gleichen User+Skill.
    """
    __tablename__ = "student_skill_progress"

    __table_args__ = (UniqueConstraint("user_id", "skill_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    skill_key: Mapped[str] = mapped_column(String)                            # z.B. "variables"
    score: Mapped[int] = mapped_column(Integer, default=0)                    # 0-100
    status: Mapped[str] = mapped_column(String, default="not_understood")     # understood | partial | not_understood
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningEvent(Base):
    """Einzelnes Lern-Ereignis — wird bei jeder Analyse über /learning-progress/analyze gespeichert.

    Bildet die Aktivitäts-Timeline des Studenten. Score ist der Roh-Score (nicht geglättet).
    Wird für die "letzten 5 Aktivitäten" Anzeige im Frontend genutzt.
    """
    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    skill_key: Mapped[str] = mapped_column(String)
    score: Mapped[int] = mapped_column(Integer)                          # Roh-Score dieser Analyse
    mistakes: Mapped[list[Any] | None] = mapped_column(JSON, default=list)  # Liste gefundener Fehler
    feedback: Mapped[str | None] = mapped_column(Text)                   # LLM-Feedback auf Deutsch
    recommended_exercise: Mapped[str | None] = mapped_column(Text)       # Empfohlene nächste Übung
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
