# Exercise & Skill Progress System — Implementation Plan

**Status**: Phase 1 Completed

**Last Updated**: 2026-05-31

## Requirements & Context

### Core Requirements
- **What:** Extend the KI Python Tutor with a progressive learning system: 37 skills across 3 levels, 5 exercises per skill, LangChain-powered exercise evaluation and skill tests, progressive unlock chain, and a complete frontend flow.
- **Why:** The current system only analyzes free-form code submissions and tracks 7 skills with scores. There is no guided practice path — learners have no structured way to prove understanding of a skill, unlock the next skill, or be directed to the right content.
- **Who requested:** Project owner (KI Tutor project)
- **Constraint:** SQLite in development; no breaking changes to existing `/learning-progress/analyze` and `/tutor/*` endpoints; all UI text in German; all LLM calls use existing `get_llm()` from `agent/config.py`.
- **Success metric:** A learner can open the progress page, click an unlocked skill, complete exercises, pass a skill test, and see the next skill unlock — without errors and without the existing tutor or analysis flows breaking.

### Feature Specifications

**Skill tree (37 skills, 3 levels):**
- Beginner (13): variables, datatypes, input_output, string_methods, type_conversion, if_else, for_loop, while_loop, lists, tuples, sets, dictionaries, functions
- Intermediate (12): list_comprehension, error_handling, file_io, classes_basic, instance_methods, instance_variables, static_methods, class_methods, magic_methods, modules_imports, lambda_functions, map_filter_reduce
- Advanced (12): inheritance, polymorphism, abstract_classes, interfaces, decorators, generators, context_managers, recursion, algorithms, design_patterns, async_await, testing

Each skill has: key, German label, level (beginner/intermediate/advanced), display order, and unlocks_after (the preceding skill key, or None for the first in each level).

**Exercise flow per skill:**
1. User opens skill card on progress page — modal appears with the current exercise (only the next uncompleted one is shown).
2. User writes code in the editor and clicks "Ausführen".
3. Backend runs the code (subprocess with timeout), then calls the LLM evaluator tool.
4. Result is RICHTIG / TEILWEISE / FALSCH:
   - RICHTIG: green banner, score +20, exercise locked, next exercise activates.
   - TEILWEISE: yellow banner, score +10 (only if not already at 10), retry allowed.
   - FALSCH: red banner, code + analysis saved to localStorage, redirect to /tutor.
5. When all 5 exercises are RICHTIG, the skill reaches score 100 and a "Skill-Test" button appears.

**Skill test flow:**
1. Three steps: 3× Multiple Choice → Code Reading → Mini Task.
2. Progress bar shows current step.
3. On submit, backend evaluates all answers, returns per-question feedback and total score.
4. >=60% → celebration message, next skill in chain unlocks.
5. <60% → retry button and improvement hints shown.

**Hint flow (during exercises):**
- "Tipp anfordern" button cycles through 3 hint levels (conceptual → syntax → near-solution).
- Each click calls the hint endpoint with the current hint_level.

**Wrong answer redirect:**
- On FALSCH, the frontend stores `{ code, analysis, exercise_title }` in localStorage under key `ki_tutor_exercise_redirect`.
- TutorView reads this key on mount, pre-fills the code editor, injects the analysis as the first assistant chat message, then deletes the key.

**Progress page changes:**
- User status badge at top: "Anfänger" / "Fortgeschritten" / "Profi" with level color.
- Skills grouped into three collapsible/scrollable sections: Beginner, Intermediate, Advanced.
- Locked skills: grayed card with lock icon.
- Unlocked skills: clickable card showing exercise count and score bar.
- "Letzte Analysen löschen" button with confirmation dialog.

### Current System State

- 7 skills hardcoded in `backend/models/skill_progress.py` as a flat list of (key, label) tuples.
- `StudentSkillProgress` has no unique constraint on (user_id, skill_key).
- `VALID_SKILLS` set in `backend/services/skill_analyzer.py` is hardcoded to the same 7 skills.
- No exercise or skill-test models, no exercise data, no evaluation tools.
- `LearningProgressView.tsx` shows a flat list of skill bars + free-form analysis panel.
- `TutorView.tsx` starts with a hardcoded code snippet, no localStorage integration.
- Existing tools: `explain_tool.py`, `debug_tool.py`, `exercise_tool.py`, `rag_tool.py` — all use `@tool` decorator + `get_llm()`.

### Out of Scope
- Exercise data for Intermediate and Advanced skills (dynamic LLM generation covers these).
- Gamification (badges, streaks, leaderboard).
- Admin dashboard for skill management.
- Email notifications on skill unlock.

### Related Decisions
- **Static exercise data for Beginner skills only** → rationale: Beginner exercises need precise expected output for automated checking; Intermediate/Advanced use LLM-generated exercises via `exercise_generator_tool` for variety.
- **Score stored as sum of exercise scores (0–100), not the existing weighted average** → the existing `StudentSkillProgress.score` field is reused but its meaning changes for exercise-tracked skills. The `/analyze` endpoint continues to use its own scoring logic for free-form analysis; the exercise endpoint sets score directly.
- **subprocess for code execution** → already used by `/tutor/run`; reuse the same pattern.
- **UniqueConstraint on (user_id, skill_key) added via Alembic-free approach** → recreate table using `CREATE TABLE IF NOT EXISTS` and migrate data (SQLite does not support ADD CONSTRAINT). Because the project uses `Base.metadata.create_all` (no migration framework), the constraint will be defined in the model and the dev DB dropped/recreated on first run. A note is placed in the tracker for production awareness.

## Overview

### What We Want to Do
Add a guided progressive learning system on top of the existing tutor: 37 skills with static/dynamic exercises, LLM-powered evaluation, a three-step skill test, and a frontend flow that takes the learner from skill selection through exercises to unlock.

### Why We Need This
- **Problem**: Learners submit free-form code without any structured progression path.
- **Gap**: No exercises, no unlock chain, no proof-of-understanding mechanism (skill test).
- **Impact**: Learners can use the tutor but have no clear "what to learn next" guidance.
- **Solution**: Layered progressive system: exercises accumulate points toward 100, then a skill test gates the next skill unlock.

### Approach
Build from the database upward: new models first, then static exercise data, then LangChain tools, then backend endpoints, then frontend components. Each phase leaves the system fully runnable.

### Architectural Decision

**Decision:** Reuse `StudentSkillProgress` for exercise-derived scores rather than adding a parallel skill-score table.

**Why this approach:**
- The existing `/learning-progress/{id}` endpoint already surfaces `StudentSkillProgress` scores to the frontend — no new response shape needed for the score display.
- The exercise submission endpoint becomes the authoritative score writer for exercise-tracked skills, while the `/analyze` endpoint continues to be the score writer for free-form analysis.
- Single source of truth per skill per user in one table.

**Alternatives considered:**
- **Separate exercise_skill_score table**: Rejected — doubles the skill-score data model with no benefit.
- **Derive skill score from ExerciseCompletion at query time**: Rejected — too expensive to compute on every progress fetch; would require aggregation query across potentially 37 × 5 = 185 rows per user per load.

**Pattern followed:**
- New LangChain tools follow the `@tool` decorator pattern from `backend/agent/tools/explain_tool.py`.
- New routers follow the `APIRouter` + `Depends(get_current_user)` + `Depends(get_db)` pattern from `backend/routers/learning_progress.py`.

## Shared Definitions

Definitions referenced by multiple phases. Subagents implementing individual phases should rely on these as the source of truth for cross-phase contracts.

### Skill Tree Structure

The expanded `FIXED_SKILLS` list must be replaced with `SKILL_TREE` — a list of dicts with this shape:

```
{
    "key": str,          # snake_case identifier, unique
    "label": str,        # German display label
    "level": str,        # "beginner" | "intermediate" | "advanced"
    "order": int,        # display/unlock order within the level, 1-based
    "unlocks_after": str | None   # key of preceding skill, or None
}
```

Full list (37 entries):

| key | label | level | order | unlocks_after |
|-----|-------|-------|-------|---------------|
| variables | Variablen | beginner | 1 | None |
| datatypes | Datentypen | beginner | 2 | variables |
| input_output | Eingabe & Ausgabe | beginner | 3 | datatypes |
| string_methods | String-Methoden | beginner | 4 | input_output |
| type_conversion | Typumwandlung | beginner | 5 | string_methods |
| if_else | If/Else | beginner | 6 | type_conversion |
| for_loop | For-Schleifen | beginner | 7 | if_else |
| while_loop | While-Schleifen | beginner | 8 | for_loop |
| lists | Listen | beginner | 9 | while_loop |
| tuples | Tupel | beginner | 10 | lists |
| sets | Mengen | beginner | 11 | tuples |
| dictionaries | Dictionaries | beginner | 12 | sets |
| functions | Funktionen | beginner | 13 | dictionaries |
| list_comprehension | List Comprehension | intermediate | 1 | None |
| error_handling | Fehlerbehandlung | intermediate | 2 | list_comprehension |
| file_io | Datei-Ein/Ausgabe | intermediate | 3 | error_handling |
| classes_basic | Klassen Grundlagen | intermediate | 4 | file_io |
| instance_methods | Instanz-Methoden | intermediate | 5 | classes_basic |
| instance_variables | Instanz-Variablen | intermediate | 6 | instance_methods |
| static_methods | Statische Methoden | intermediate | 7 | instance_variables |
| class_methods | Klassen-Methoden | intermediate | 8 | static_methods |
| magic_methods | Magic Methods | intermediate | 9 | class_methods |
| modules_imports | Module & Imports | intermediate | 10 | magic_methods |
| lambda_functions | Lambda-Funktionen | intermediate | 11 | modules_imports |
| map_filter_reduce | Map/Filter/Reduce | intermediate | 12 | lambda_functions |
| inheritance | Vererbung | advanced | 1 | None |
| polymorphism | Polymorphismus | advanced | 2 | inheritance |
| abstract_classes | Abstrakte Klassen | advanced | 3 | polymorphism |
| interfaces | Interfaces | advanced | 4 | abstract_classes |
| decorators | Dekoratoren | advanced | 5 | interfaces |
| generators | Generatoren | advanced | 6 | decorators |
| context_managers | Kontextmanager | advanced | 7 | generators |
| recursion | Rekursion | advanced | 8 | context_managers |
| algorithms | Algorithmen | advanced | 9 | recursion |
| design_patterns | Entwurfsmuster | advanced | 10 | algorithms |
| async_await | Async/Await | advanced | 11 | design_patterns |
| testing | Testen | advanced | 12 | async_await |

Unlock rule: within a level, the first skill (unlocks_after = None) starts unlocked; all others require the preceding skill's test to have passed. Level entry unlocks are independent per level — Beginner level 1 is always unlocked, Intermediate level 1 and Advanced level 1 start locked and unlock only when the respective preceding level's final skill test passes. (Exact cross-level gating is left to the backend unlock logic in Phase 4.)

### Exercise Data Shape

Each static exercise (used in `backend/data/exercises.py` and returned by API):

```
{
    "id": str,               # "{skill_key}_{order}" e.g. "variables_1"
    "skill_key": str,
    "order": int,            # 1–5
    "title": str,            # short German title
    "description": str,      # full German task description
    "expected_output": str,  # exact stdout string the correct solution produces
    "test_type": "output_match"
}
```

### Exercise Evaluation Result Contract

Returned by the exercise submission endpoint and consumed by the frontend modal:

```
{
    "result": "richtig" | "teilweise" | "falsch",
    "score_change": int,        # points actually added: 0 | 10 | 20
    "new_skill_score": int,     # updated StudentSkillProgress.score after this submission
    "what_was_good": str,
    "what_went_wrong": str,
    "hint": str,
    "redirect_to_tutor": bool,  # true when result == "falsch"
    "analysis": str             # analysis text for localStorage redirect payload
}
```

Score update rules (applied in the exercise submission endpoint):
- RICHTIG: set `ExerciseCompletion.score_granted = 20`, `is_locked = True`
- TEILWEISE: if `score_granted < 10`, set `score_granted = 10`; if already 10 and new result is RICHTIG, set 20 and lock
- FALSCH: no change to `score_granted`
- `StudentSkillProgress.score` = sum of all `score_granted` for the skill's exercises (max 100)

### Skill Test Question Shape

```
{
    "multiple_choice": [
        {
            "question": str,
            "options": {"A": str, "B": str, "C": str, "D": str},
            "correct": str,       # "A" | "B" | "C" | "D"
            "explanation": str
        }
    ],   # exactly 3 items
    "code_reading": {
        "code": str,
        "question": str,
        "correct_answer": str
    },
    "mini_task": {
        "description": str,
        "expected_output": str
    }
}
```

### localStorage Key for Wrong Answer Redirect

```
Key:   "ki_tutor_exercise_redirect"
Value: JSON.stringify({
    code: string,
    analysis: string,
    exercise_title: string
})
```

### API Endpoint Summary (new endpoints only)

| Method | Path | Auth | Phase |
|--------|------|------|-------|
| GET | `/exercises/{skill_key}` | Bearer | 4 |
| POST | `/exercises/submit` | Bearer | 4 |
| POST | `/exercises/hint` | Bearer | 4 |
| POST | `/skill-tests/generate` | Bearer | 4 |
| POST | `/skill-tests/submit` | Bearer | 4 |
| DELETE | `/learning-progress/events` | Bearer | 4 |

### Frontend TypeScript Types (new/updated)

```typescript
// Added to SkillProgress
interface SkillProgress {
  skill_key: string
  skill_label: string
  score: number
  status: "understood" | "partial" | "not_understood"
  updated_at: string | null
  // New fields:
  level: "beginner" | "intermediate" | "advanced"
  order: number
  is_unlocked: boolean
  exercises_completed: number   // count of RICHTIG exercises
  test_passed: boolean
}

// Added to ProgressResponse
interface ProgressResponse {
  student_id: number
  overall_score: number
  skills: SkillProgress[]
  recent_events: LearningEvent[]
  // New field:
  user_status: "Anfänger" | "Fortgeschritten" | "Profi"
}

interface Exercise {
  id: string
  skill_key: string
  order: number
  title: string
  description: string
  expected_output: string
  test_type: string
  is_completed: boolean   // RICHTIG
  score_granted: number
}

interface EvaluationResult {
  result: "richtig" | "teilweise" | "falsch"
  score_change: number
  new_skill_score: number
  what_was_good: string
  what_went_wrong: string
  hint: string
  redirect_to_tutor: boolean
  analysis: string
}

interface SkillTestData {
  skill_key: string
  multiple_choice: MCQuestion[]
  code_reading: CodeReadingQuestion
  mini_task: MiniTask
}

interface MCQuestion {
  question: string
  options: Record<"A" | "B" | "C" | "D", string>
  correct: string
  explanation: string
}

interface CodeReadingQuestion {
  code: string
  question: string
  correct_answer: string
}

interface MiniTask {
  description: string
  expected_output: string
}

interface SkillTestResult {
  total_score: number
  passed: boolean
  per_question_feedback: Array<{ question_type: string; correct: boolean; explanation: string }>
  next_skill_unlocked: string | null
}
```

### Conventions
- All LangChain tools: file in `backend/agent/tools/`, decorated with `@tool`, take typed primitive params, return str or JSON str.
- New routers: one file per resource group in `backend/routers/`, prefix declared in router definition.
- New models: one file per model group in `backend/models/`, all inherit from `core.database.Base`.
- Static exercise data: `backend/data/exercises.py` — a plain Python dict `EXERCISES: dict[str, list[dict]]` keyed by skill_key.

## Phase Summary

| Phase | Delivers | Status | Detail File |
|-------|----------|--------|-------------|
| 1: DB Models + Skill Tree | Expanded skill tree, 3 new DB models, unique constraint | Completed | `exercise-skill-system/phase-1-db-models.md` |
| 2: Static Exercise Data | 65 exercises for all 13 Beginner skills | Not Started | `exercise-skill-system/phase-2-exercise-data.md` |
| 3: LangChain Tools | 4 new tools: evaluator, hint, exercise generator, test generator+evaluator | Not Started | `exercise-skill-system/phase-3-langchain-tools.md` |
| 4: Backend Endpoints | exercises router, skill-tests router, updated learning-progress router | Not Started | `exercise-skill-system/phase-4-backend-endpoints.md` |
| 5: Frontend Types + API Client | Updated TypeScript types, 5 new api.ts functions | Not Started | `exercise-skill-system/phase-5-frontend-types-api.md` |
| 6: Frontend Progress Page | Grouped skill tree, user status badge, delete events button | Not Started | `exercise-skill-system/phase-6-progress-page.md` |
| 7: Frontend Modals + Tutor Redirect | ExerciseModal, SkillTestModal, TutorView localStorage flow | Not Started | `exercise-skill-system/phase-7-modals-and-redirect.md` |
| Quality Gate | Full test suite, regression check, pre-commit pass | Not Started | *(in this file)* |
| Documentation | Updated docs for new system | Not Started | *(in this file)* |

Each implementation phase follows the **implement → review → test** cycle before the next phase begins.

## Architecture and Design

### System Changes

```mermaid
graph TB
    FE_Progress[Progress Page] -->|GET /exercises/{key}| BE_Exercises[exercises router]
    FE_Progress -->|POST /exercises/submit| BE_Exercises
    FE_Progress -->|POST /exercises/hint| BE_Exercises
    FE_Progress -->|POST /skill-tests/generate| BE_SkillTests[skill-tests router]
    FE_Progress -->|POST /skill-tests/submit| BE_SkillTests
    FE_Progress -->|DELETE /learning-progress/events| BE_LP[learning-progress router]
    FE_Tutor[Tutor View] -->|reads localStorage| LS[(localStorage)]
    FE_ExModal[ExerciseModal] -->|writes on FALSCH| LS

    BE_Exercises --> Tools[LangChain Tools]
    BE_SkillTests --> Tools
    Tools --> LLM[get_llm()]

    BE_Exercises --> DB_EC[(ExerciseCompletion)]
    BE_Exercises --> DB_SP[(StudentSkillProgress)]
    BE_SkillTests --> DB_ST[(SkillTestResult)]
    BE_SkillTests --> DB_SP

    subgraph "New Backend"
        BE_Exercises
        BE_SkillTests
        Tools
        DB_EC
        DB_ST
    end

    subgraph "Extended Backend"
        BE_LP
        DB_SP
    end

    subgraph "New Frontend"
        FE_ExModal
        FE_TestModal[SkillTestModal]
    end

    subgraph "Extended Frontend"
        FE_Progress
        FE_Tutor
    end
```

### Data Flow

```mermaid
flowchart TD
    A[User clicks skill card] --> B[GET /exercises/{skill_key}]
    B --> C[ExerciseModal opens with current exercise]
    C --> D[User writes code + clicks Ausführen]
    D --> E[POST /exercises/submit]
    E --> F[Backend runs code via subprocess]
    F --> G[exercise_evaluator_tool called]
    G --> H{Result?}
    H -->|RICHTIG| I[score_granted=20, lock exercise]
    H -->|TEILWEISE| J[score_granted=10 if not set]
    H -->|FALSCH| K[no score change]
    I --> L[Update StudentSkillProgress.score]
    J --> L
    K --> M[Save to localStorage]
    M --> N[Redirect to /tutor]
    L --> O{All 5 exercises RICHTIG?}
    O -->|yes| P[Show Skill Test button]
    O -->|no| Q[Show next exercise]
    P --> R[POST /skill-tests/generate]
    R --> S[3-step test wizard]
    S --> T[POST /skill-tests/submit]
    T --> U{Score >= 60%?}
    U -->|yes| V[Unlock next skill]
    U -->|no| W[Show retry + hints]
```

### Key Integration Points
- **`get_llm()` from `agent/config.py`**: All new LangChain tools import and call `get_llm()` — no changes needed to LLM config.
- **`StudentSkillProgress` table**: Exercise submission endpoint writes scores directly; the existing `/analyze` endpoint continues to write scores via its own logic — both share the same table, different access paths.
- **`Base.metadata.create_all`**: New models must be imported in `backend/main.py` before `create_all` runs so tables are created on startup.
- **`get_current_user` from `routers/auth.py`**: All new endpoints use this dependency unchanged.
- **Code execution**: The `/exercises/submit` endpoint runs user code the same way `/tutor/run` does (subprocess + timeout). Reuse the pattern from `backend/routers/tutor.py`.

## Configuration

### New Environment Variables
None required. The system uses the existing `DATABASE_URL` and LLM configuration.

### Database Changes
- **New tables**: `exercise_completions`, `skill_test_results`
- **Constraint added**: `UniqueConstraint("user_id", "skill_key")` on `student_skill_progress`
- **Migration strategy**: Because the project uses `Base.metadata.create_all` without Alembic, new tables are created automatically. The unique constraint on `student_skill_progress` requires the dev database to be dropped and recreated (delete `tutor.db`). For any production deployment, a manual migration script is needed.
- **Backward compatibility**: The existing `StudentSkillProgress` columns are unchanged. The `/analyze` endpoint and all existing progress endpoints continue to work without modification.

## Final Quality Gate

After all implementation phases complete their individual implement → review → test cycles, this phase validates the full system.

**Focus:**
- End-to-end exercise flow: submit code → evaluation → score update → modal feedback
- End-to-end skill test flow: generate → 3-step wizard → submit → unlock
- Wrong-answer redirect: FALSCH exercise → localStorage written → /tutor reads it
- Existing `/tutor/analyze`, `/tutor/chat`, `/tutor/run`, `/learning-progress/analyze` endpoints still return correct responses
- Full pre-commit + pytest pass (100%)

**Process:**
- `qa-guard` or `test-executor` runs full test suite
- If existing tests broke: escalate to the implementation phase that caused the regression
- If integration gaps found: create targeted fix phase

**Definition of Done:**
- [ ] All existing tests still pass
- [ ] Pre-commit hooks pass (100%)
- [ ] No regressions from combined phase changes
- [ ] Integration between phases verified (exercise → score → unlock → test → unlock)
- [ ] Wrong-answer localStorage redirect works end-to-end

**Git Commit:** `[test] Quality gate: Integration and regression verification`

---

## Documentation

**Handled by:** `doc-writer` agent

**Areas affected by this implementation:**
- `docs/learning-progress-feature.md` — needs full update: skill tree, exercise system, scoring rules, skill test flow, unlock chain
- New API endpoints: `/exercises/*`, `/skill-tests/*`, updated `/learning-progress/events`
- New LangChain tools: evaluator, hint, exercise generator, test generator
- DB schema: two new tables, one updated constraint

**Git Commit:** `[docs] Documentation for exercise & skill progress system`

---

## Testing Strategy

### Unit Testing
- **exercise_evaluator_tool**: Test RICHTIG/TEILWEISE/FALSCH classification with mock stdout and LLM responses
- **hint_tool**: Test that hint_level 1/2/3 produce progressively more specific hints
- **Score update logic** in exercises router: Test all score-change branches (RICHTIG on fresh, RICHTIG on TEILWEISE, TEILWEISE on FALSCH, FALSCH on fresh)
- **Skill unlock logic**: Test that passing a skill test sets the next skill's unlock state

### Integration Testing
- POST `/exercises/submit` → check ExerciseCompletion row, StudentSkillProgress.score updated
- POST `/skill-tests/submit` with passing score → check SkillTestResult row, next skill unlocked
- DELETE `/learning-progress/events` → check LearningEvent rows deleted for user

### Manual Testing
- [ ] Complete exercises 1–5 for a beginner skill, verify score reaches 100
- [ ] Trigger FALSCH, verify localStorage written and /tutor pre-fills code
- [ ] Pass skill test (>=60%), verify next skill card becomes clickable
- [ ] Fail skill test (<60%), verify retry button appears
- [ ] Verify existing /tutor and /learning-progress/analyze flows still work

## Risks and Mitigation

### Technical Risks
- **Risk**: LLM evaluation is inconsistent (RICHTIG for wrong output or vice versa)
- **Impact**: Learner gets wrong score, frustration or gaming
- **Mitigation**: Stdout exact-match is checked first in the evaluator; LLM only used for concept correctness. Phase 3 task description specifies the priority order.
- **Likelihood**: Medium

- **Risk**: Subprocess code execution timeout / security
- **Impact**: Server hangs or arbitrary code runs
- **Mitigation**: Reuse the existing `/tutor/run` subprocess pattern which already has timeout handling.
- **Likelihood**: Low

- **Risk**: UniqueConstraint migration breaks dev DB
- **Impact**: Startup error until DB is dropped
- **Mitigation**: Document explicitly in Phase 1 that dev DB must be deleted before first run of this phase.
- **Likelihood**: High (expected, documented)

### Operational Risks
- **Risk**: 37-skill data causes slow progress fetch
- **Impact**: Progress page feels slow
- **Mitigation**: All skill data is static; DB query fetches at most 37 rows per user. Acceptable for SQLite dev; for production PostgreSQL with proper indexes this is trivial.
- **Likelihood**: Low

## Success Criteria

1. A learner can complete all 5 exercises for any Beginner skill and reach score 100.
2. A FALSCH exercise result always pre-fills the TutorView with the submitted code and analysis text.
3. Passing a skill test (>=60%) always unlocks the next skill in the chain on the progress page.
4. All existing tutor and learning-progress endpoints return correct responses unchanged.
5. Full pytest suite passes with pre-commit hooks on the final combined codebase.

## Implementation Updates

**2026-05-31**: Plan created. Complication noted: `StudentSkillProgress` has no unique constraint — adding it requires dev DB reset (no Alembic). This is expected and documented. Score semantics for exercise-tracked skills differ from the existing weighted-average approach in `/analyze`; both coexist in the same table but write through separate code paths.

**2026-05-31**: Phase 1 completed. The project uses PostgreSQL (not SQLite as the main tracker stated). Because the `student_skill_progress` table already existed without the UniqueConstraint, `create_all` did not apply it. Constraint was applied with `ALTER TABLE ... ADD CONSTRAINT` after verifying no duplicate rows. Both new tables (`exercise_completions`, `skill_test_results`) were created cleanly by `create_all`. The `FIXED_SKILLS` alias was preserved exactly — `learning_progress.py` imports and iterates it without any changes needed.

---

## Related Documentation

- `docs/learning-progress-feature.md` — current learning progress feature overview
- `docs/implementations/phase-2-langchain-ollama.md` — LangChain tool pattern reference
- `docs/implementations/sprint-3-react-rag.md` — frontend component pattern reference
