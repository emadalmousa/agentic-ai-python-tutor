# Phase 1: DB Models + Skill Tree Expansion

**Status**: Completed
**Parent Tracker**: `docs/implementations/exercise-skill-system.md`

## Goal

Replace the 7-skill flat list with the full 37-skill tree structure, add two new DB models for tracking exercise completions and skill test results, and add a unique constraint to `StudentSkillProgress`. After this phase the backend starts up cleanly with all new tables created, and the existing endpoints continue to work with the expanded skill set.

## End-of-Phase System State

- `SKILL_TREE` in `backend/models/skill_progress.py` contains all 37 skills with level/order/unlocks_after metadata.
- `FIXED_SKILLS` compatibility alias preserved so existing code in `learning_progress.py` and `skill_analyzer.py` that iterates `FIXED_SKILLS` does not break.
- `ExerciseCompletion` table exists in the DB.
- `SkillTestResult` table exists in the DB.
- `StudentSkillProgress` has a `UniqueConstraint` on (user_id, skill_key) in the model definition.
- `backend/models/__init__.py` exports all four models.
- `backend/main.py` imports all models before `create_all`.
- **Dev DB must be deleted and recreated** — document this in a comment in the model file.
- **System runs without errors** on a fresh DB.

## Tasks

| Task | Files | Complexity | Status | Description |
|------|-------|------------|--------|-------------|
| 1.1 | `backend/models/skill_progress.py` | Medium | Not Started | Expand FIXED_SKILLS to 37-skill SKILL_TREE |
| 1.2 | `backend/models/exercise.py` | Medium | Not Started | Create ExerciseCompletion model |
| 1.3 | `backend/models/skill_test.py` | Low | Not Started | Create SkillTestResult model |
| 1.4 | `backend/models/skill_progress.py` | Low | Not Started | Add UniqueConstraint to StudentSkillProgress |
| 1.5 | `backend/models/__init__.py` | Low | Not Started | Export new models |
| 1.6 | `backend/main.py` | Low | Not Started | Import new models before create_all |
| 1.7 | `backend/services/skill_analyzer.py` | Low | Not Started | Update VALID_SKILLS to all 37 keys |

## Detailed Task Descriptions

### Task 1.1: Expand Skill Tree ⏸️

**What needs to exist:**
The `FIXED_SKILLS` variable in `skill_progress.py` must be replaced by `SKILL_TREE` — a list of dicts, one per skill, with keys: `key`, `label`, `level`, `order`, `unlocks_after`. A backward-compatibility alias `FIXED_SKILLS` must be kept as a list of `(key, label)` tuples derived from `SKILL_TREE` so that existing code in `learning_progress.py` that does `for key, label in FIXED_SKILLS` continues to work without modification.

The full 37-skill table is defined in the **Shared Definitions** section of the parent tracker. Implementors must follow that table exactly — no skill keys, labels, or ordering changes.

**Definition of Done:**
- [ ] `SKILL_TREE` list contains exactly 37 entries matching the Shared Definitions table.
- [ ] Each entry has all five keys: key, label, level, order, unlocks_after.
- [ ] `FIXED_SKILLS = [(s["key"], s["label"]) for s in SKILL_TREE]` compatibility alias present.
- [ ] Existing `GET /learning-progress/skills` endpoint returns 37 skills (verified by running the server and calling the endpoint).

**Integration points:**
- `backend/routers/learning_progress.py` imports `FIXED_SKILLS` from this module — the alias must preserve this interface.
- `backend/services/skill_analyzer.py` has its own `VALID_SKILLS` set — updated separately in Task 1.7.

**Pattern to follow:**
- Current `FIXED_SKILLS` definition style at `backend/models/skill_progress.py:7`

**Files likely affected:**
- `backend/models/skill_progress.py`

**Gotchas:**
- `_SKILL_LABEL` dict in `learning_progress.py` is built from `FIXED_SKILLS` at module load time — this will automatically expand to all 37 skills via the alias.
- The `_build_progress_response` function iterates `FIXED_SKILLS` to produce output for every skill — this will now produce 37 entries instead of 7. No other change needed.

---

### Task 1.2: ExerciseCompletion Model ⏸️

**What needs to exist:**
A new SQLAlchemy model `ExerciseCompletion` in `backend/models/exercise.py` that tracks one row per (user, skill, exercise) with these fields:
- `id` — integer primary key
- `user_id` — FK to users.id, indexed
- `skill_key` — string (e.g. "for_loop")
- `exercise_id` — string (e.g. "for_loop_1")
- `score_granted` — integer, default 0 (possible values: 0, 10, 20)
- `is_locked` — boolean, default False (True means the exercise is completed/RICHTIG)
- `created_at` — timestamp with timezone, server default now

A `UniqueConstraint` on (user_id, skill_key, exercise_id) must be declared to prevent duplicate rows.

**Definition of Done:**
- [ ] `ExerciseCompletion` class exists in `backend/models/exercise.py`.
- [ ] All fields present with correct types and defaults.
- [ ] UniqueConstraint on (user_id, skill_key, exercise_id) declared.
- [ ] Table is created when `Base.metadata.create_all` runs (verified by checking the DB after startup).

**Integration points:**
- Imported by `backend/models/__init__.py` (Task 1.5).
- Written by the exercise submission endpoint in Phase 4.

**Pattern to follow:**
- `backend/models/skill_progress.py` for SQLAlchemy column/FK/DateTime patterns.

**Files likely affected:**
- `backend/models/exercise.py` (new file)

**Gotchas:**
- `UniqueConstraint` must be in `__table_args__` as a tuple, e.g. `__table_args__ = (UniqueConstraint("user_id", "skill_key", "exercise_id"),)`.

---

### Task 1.3: SkillTestResult Model ⏸️

**What needs to exist:**
A new SQLAlchemy model `SkillTestResult` in `backend/models/skill_test.py` with these fields:
- `id` — integer primary key
- `user_id` — FK to users.id, indexed
- `skill_key` — string
- `score` — integer (0–100, percentage)
- `passed` — boolean
- `attempt_number` — integer, default 1 (incremented on each retry)
- `created_at` — timestamp with timezone, server default now

**Definition of Done:**
- [ ] `SkillTestResult` class exists in `backend/models/skill_test.py`.
- [ ] All fields present with correct types and defaults.
- [ ] Table is created on startup.

**Integration points:**
- Imported by `backend/models/__init__.py` (Task 1.5).
- Written by the skill test submission endpoint in Phase 4.

**Pattern to follow:**
- `backend/models/skill_progress.py` for column patterns.

**Files likely affected:**
- `backend/models/skill_test.py` (new file)

---

### Task 1.4: UniqueConstraint on StudentSkillProgress ⏸️

**What needs to exist:**
`StudentSkillProgress` in `backend/models/skill_progress.py` must declare a `UniqueConstraint` on (user_id, skill_key) via `__table_args__`. This prevents duplicate skill progress rows for the same user+skill combination that the existing `_get_or_create_progress` helper tries to avoid with a `.first()` query.

**Definition of Done:**
- [ ] `UniqueConstraint("user_id", "skill_key")` present in `StudentSkillProgress.__table_args__`.
- [ ] A comment in the file notes: "Dev DB must be deleted before first run — SQLite cannot add constraints to existing tables."

**Integration points:**
- The existing `_get_or_create_progress` in `learning_progress.py` does `.filter_by(user_id, skill_key).first()` — this already handles the uniqueness correctly at the application level; the DB constraint is belt-and-suspenders.

**Files likely affected:**
- `backend/models/skill_progress.py`

**Gotchas:**
- SQLite does not support `ALTER TABLE ... ADD CONSTRAINT`. The constraint only takes effect on a freshly created table. On an existing dev DB, delete `backend/tutor.db` before running the server.

---

### Task 1.5: Export New Models ⏸️

**What needs to exist:**
`backend/models/__init__.py` must export `ExerciseCompletion` and `SkillTestResult` alongside the existing exports.

**Definition of Done:**
- [ ] `from models.exercise import ExerciseCompletion` present.
- [ ] `from models.skill_test import SkillTestResult` present.
- [ ] `__all__` updated to include both new models.

**Files likely affected:**
- `backend/models/__init__.py`

---

### Task 1.6: Register New Models in main.py ⏸️

**What needs to exist:**
`backend/main.py` must import the new models (or the updated `models` package) before `Base.metadata.create_all(bind=engine)` runs, so that SQLAlchemy sees all table definitions and creates the new tables on startup.

The existing comment `# Import all models so that create_all finds them` is the right location.

**Definition of Done:**
- [ ] After startup, `exercise_completions` and `skill_test_results` tables exist in the DB.
- [ ] No import errors on startup.

**Files likely affected:**
- `backend/main.py`

**Gotchas:**
- The existing `import models  # noqa: F401` already imports `__init__.py` which re-exports everything. Verify that the new models are included in the `__init__.py` exports (Task 1.5) — if so, no change to `main.py` is needed beyond confirming the import chain. If not, add explicit imports.

---

### Task 1.7: Update VALID_SKILLS in skill_analyzer.py ⏸️

**What needs to exist:**
The `VALID_SKILLS` set in `backend/services/skill_analyzer.py` must contain all 37 skill keys from `SKILL_TREE`. The LLM system prompt listing "Erlaubte skill_keys" must also be updated to include all 37 keys.

This keeps the LLM-based skill analyzer from rejecting newly added skills as invalid.

**Definition of Done:**
- [ ] `VALID_SKILLS` set contains all 37 keys from the Shared Definitions skill tree table.
- [ ] The `_SYSTEM_PROMPT` string's "Erlaubte skill_keys" list is updated to match.
- [ ] The `_KEYWORD_MAP` dict has keyword entries for the 24 new skills (can be minimal/heuristic — exact LLM analysis is the primary path).

**Integration points:**
- `analyze_skill()` function is called by `POST /learning-progress/analyze` — this must continue to work after the expansion.

**Files likely affected:**
- `backend/services/skill_analyzer.py`

**Gotchas:**
- The `_KEYWORD_MAP` fallback only needs to be reasonable, not perfect. If a keyword mapping is unclear, use a conservative set of identifiable keywords for that skill (e.g. for `classes_basic`: `["class ", "def __init__"]`).

---

## Phase Completion Criteria
- [ ] All tasks completed
- [ ] Code reviewed and approved
- [ ] Tests written and passing (unit tests: SKILL_TREE has 37 entries, all required keys present per entry; ExerciseCompletion and SkillTestResult tables created on startup)
- [ ] Git commits: `[impl]`, `[test]` (and `[fix]` if needed)
