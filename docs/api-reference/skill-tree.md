# Skill Tree Reference

**Use this document as a reference for the complete 37-skill progression system.**

## Overview

The KI Python Tutor features a structured skill progression across 3 levels with sequential unlock chains. Each skill must be mastered (skill test score ≥60%) before the next skill in the sequence becomes available.

## Beginner Level (13 Skills)

These are foundational Python concepts. All beginner exercises are static (defined in `backend/data/exercises.py`). Each skill has exactly 5 exercises.

| Order | Skill Key | German Label | Unlocks After | Min. Score to Unlock |
|-------|-----------|--------------|----------------|----------------------|
| 1 | `variables` | Variablen | — (Start) | 60% |
| 2 | `datatypes` | Datentypen | `variables` | 60% |
| 3 | `input_output` | Eingabe & Ausgabe | `datatypes` | 60% |
| 4 | `string_methods` | String-Methoden | `input_output` | 60% |
| 5 | `type_conversion` | Typumwandlung | `string_methods` | 60% |
| 6 | `if_else` | If/Else | `type_conversion` | 60% |
| 7 | `for_loop` | For-Schleifen | `if_else` | 60% |
| 8 | `while_loop` | While-Schleifen | `for_loop` | 60% |
| 9 | `lists` | Listen | `while_loop` | 60% |
| 10 | `tuples` | Tupel | `lists` | 60% |
| 11 | `sets` | Mengen | `tuples` | 60% |
| 12 | `dictionaries` | Dictionaries | `sets` | 60% |
| 13 | `functions` | Funktionen | `dictionaries` | 60% |

**Unlock Gate to Intermediate**: After passing the "functions" skill test, students can access intermediate level skills.

---

## Intermediate Level (12 Skills)

These cover intermediate Python concepts. Exercises are LLM-generated on-demand and adapt to student level.

| Order | Skill Key | German Label | Unlocks After | Min. Score to Unlock |
|-------|-----------|--------------|----------------|----------------------|
| 1 | `list_comprehension` | List Comprehension | — (Start) | 60% |
| 2 | `error_handling` | Fehlerbehandlung | `list_comprehension` | 60% |
| 3 | `file_io` | Datei-Ein/Ausgabe | `error_handling` | 60% |
| 4 | `classes_basic` | Klassen Grundlagen | `file_io` | 60% |
| 5 | `instance_methods` | Instanz-Methoden | `classes_basic` | 60% |
| 6 | `instance_variables` | Instanz-Variablen | `instance_methods` | 60% |
| 7 | `static_methods` | Statische Methoden | `instance_variables` | 60% |
| 8 | `class_methods` | Klassen-Methoden | `static_methods` | 60% |
| 9 | `magic_methods` | Magic Methods | `class_methods` | 60% |
| 10 | `modules_imports` | Module & Imports | `magic_methods` | 60% |
| 11 | `lambda_functions` | Lambda-Funktionen | `modules_imports` | 60% |
| 12 | `map_filter_reduce` | Map/Filter/Reduce | `lambda_functions` | 60% |

**Unlock Gate to Advanced**: After passing the "map_filter_reduce" skill test, students can access advanced level skills.

---

## Advanced Level (12 Skills)

These cover advanced Python concepts. Exercises are LLM-generated on-demand and highly customized for expert-level learners.

| Order | Skill Key | German Label | Unlocks After | Min. Score to Unlock |
|-------|-----------|--------------|----------------|----------------------|
| 1 | `inheritance` | Vererbung | — (Start) | 60% |
| 2 | `polymorphism` | Polymorphismus | `inheritance` | 60% |
| 3 | `abstract_classes` | Abstrakte Klassen | `polymorphism` | 60% |
| 4 | `interfaces` | Interfaces | `abstract_classes` | 60% |
| 5 | `decorators` | Dekoratoren | `interfaces` | 60% |
| 6 | `generators` | Generatoren | `decorators` | 60% |
| 7 | `context_managers` | Kontextmanager | `generators` | 60% |
| 8 | `recursion` | Rekursion | `context_managers` | 60% |
| 9 | `algorithms` | Algorithmen | `recursion` | 60% |
| 10 | `design_patterns` | Entwurfsmuster | `algorithms` | 60% |
| 11 | `async_await` | Async/Await | `design_patterns` | 60% |
| 12 | `testing` | Testen | `async_await` | 60% |

---

## Unlock Mechanism

### Skill Unlock Rules

A skill is **unlocked** (becomes available to the student) when:

1. **For level-start skills** (unlocks_after = None): Always unlocked if the student has unlocked any skill in that level
2. **For subsequent skills**: The predecessor skill has a score ≥60% (OR the student has passed the skill test for the predecessor)

### Checking Unlock Status

The frontend checks unlock status on each request using the formula:

```python
def is_unlocked(skill_key: str, user_id: int, db: Session) -> bool:
    skill_meta = SKILL_TREE_LOOKUP[skill_key]
    
    # Level-start skills are always unlocked for enrolled users
    if skill_meta["unlocks_after"] is None:
        return True
    
    # Other skills: predecessor must have score >= 60
    predecessor_key = skill_meta["unlocks_after"]
    predecessor_progress = db.query(StudentSkillProgress).filter(
        StudentSkillProgress.user_id == user_id,
        StudentSkillProgress.skill_key == predecessor_key
    ).first()
    
    if not predecessor_progress:
        return False
    
    return predecessor_progress.score >= 60
```

### Database Schema

Skills are stored in `backend/models/skill_progress.py:SKILL_TREE` as Python data structures (not in DB). Student progress is tracked in:

- **`student_skill_progress`**: `(user_id, skill_key) → score, status, updated_at)`
- **`skill_test_results`**: `(user_id, skill_key) → score, passed, attempt_number, created_at)`

---

## User Level Assignment

Each user's level is assigned based on their highest unlocked (not just attempted) skill:

| User Level | Condition |
|-----------|-----------|
| **Anfänger** | Highest unlocked skill is in Beginner level |
| **Fortgeschritten** | Highest unlocked skill is in Intermediate level |
| **Profi** | Highest unlocked skill is in Advanced level |

Example:
- Student completes `functions` (Beginner #13) → level = "Anfänger"
- Student completes `list_comprehension` (Intermediate #1) → level = "Fortgeschritten"
- Student completes `inheritance` (Advanced #1) → level = "Profi"

This is computed dynamically on each login and used for:
- Personalizing LLM prompts in exercise generation
- Difficulty of hints
- Threshold for skill test passing (always 60%, regardless of level)

---

## Exercise Allocation

### Beginner Skills (Static)

Each beginner skill has exactly 5 static exercises defined in `backend/data/exercises.py`:

```python
EXERCISES = {
    "variables": [
        {
            "id": "variables_1",
            "skill_key": "variables",
            "order": 1,
            "title": "Einfache Variable",
            "description": "Erstelle eine Variable `name` mit dem Wert `'Python'` und gib sie aus.",
            "expected_output": "Python",
            "test_type": "output_match",
            "hint": "Verwende das = Zeichen um einer Variable einen Wert zuzuweisen."
        },
        # ... 4 more exercises
    ],
    # ... 12 more skills
}
```

### Intermediate & Advanced Skills (LLM-Generated)

Exercises are generated on-demand via `exercise_generator_tool.invoke()` when a student accesses the skill. The tool receives:

- `skill_key`: The skill identifier
- `skill_label`: German label (for LLM context)
- `user_level`: Student's current level (Anfänger/Fortgeschritten/Profi)

The LLM generates exercises that:
- Match the skill difficulty
- Are appropriate for the student's level
- Include step-by-step explanations
- Have verifiable expected outputs

---

## Skill Test Structure

Every skill (beginner, intermediate, advanced) can have a skill test. The test has 3 sections:

1. **Multiple Choice (3 questions)**: Test conceptual understanding
2. **Code Reading**: Analyze given code and explain it
3. **Mini Task**: Write code to solve a problem

**Passing Score**: ≥60% overall

Tests are generated via `skill_test_generator_tool.invoke()` which receives:
- `skill_key`: The skill identifier
- `skill_label`: German label
- `user_level`: Student's level (for difficulty calibration)

---

## API References

### Getting Skill Information

All skill metadata is available via the `/exercises/{skill_key}` endpoint:

```json
GET /exercises/for_loop
Authorization: Bearer <token>

Response:
{
  "skill_key": "for_loop",
  "exercises": [...]
}
```

### Checking Unlock Status

The `is_unlocked` field in exercise responses indicates whether the skill is available:

```json
{
  "skill_key": "for_loop",
  "exercises": [
    {
      "id": "for_loop_1",
      "is_unlocked": true,  // ← Skill is available
      ...
    }
  ]
}
```

### Viewing Skill Progress

Student progress is tracked in the database. To get current progress for a user:

```python
from models.skill_progress import StudentSkillProgress

progress = db.query(StudentSkillProgress).filter(
    StudentSkillProgress.user_id == user_id,
    StudentSkillProgress.skill_key == skill_key
).first()

print(f"Score: {progress.score}/100")
print(f"Status: {progress.status}")  # "understood" | "partial" | "not_understood"
```

---

## Related Topics

- [Exercise Endpoints](exercises-endpoints.md)
- [Skill Tests Endpoints](skill-tests-endpoints.md)
- [Exercise & Skill System Feature Guide](../understanding-features/exercise-skill-system.md)
