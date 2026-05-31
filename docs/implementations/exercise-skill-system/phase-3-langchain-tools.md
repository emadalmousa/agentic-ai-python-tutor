# Phase 3: LangChain Tools

**Status**: Completed
**Parent Tracker**: `docs/implementations/exercise-skill-system.md`

## Goal

Create four new LangChain tools that the backend endpoints (Phase 4) will call: an exercise evaluator, a hint generator, a dynamic exercise generator (for Intermediate/Advanced skills), and a skill test generator + evaluator pair. After this phase all tools are individually importable and callable without errors; no endpoints exist yet.

## End-of-Phase System State

- `backend/agent/tools/exercise_evaluator_tool.py` exists and is callable.
- `backend/agent/tools/hint_tool.py` exists and is callable.
- `backend/agent/tools/exercise_generator_tool.py` exists and is callable.
- `backend/agent/tools/skill_test_tool.py` exists with both generator and evaluator functions.
- All tools follow the existing `@tool` + `get_llm()` pattern.
- **System runs without errors.**

## Tasks

| Task | Files | Complexity | Status | Description |
|------|-------|------------|--------|-------------|
| 3.1 | `backend/agent/tools/exercise_evaluator_tool.py` | High | Not Started | LLM-based exercise evaluation |
| 3.2 | `backend/agent/tools/hint_tool.py` | Medium | Not Started | Progressive 3-level hint generator |
| 3.3 | `backend/agent/tools/exercise_generator_tool.py` | Medium | Not Started | Dynamic exercise generation for Intermediate/Advanced |
| 3.4 | `backend/agent/tools/skill_test_tool.py` | Medium | Not Started | Skill test generator and evaluator |

## Detailed Task Descriptions

### Task 3.1: Exercise Evaluator Tool ⏸️

**What needs to exist:**
A `@tool` function `evaluate_exercise` in `exercise_evaluator_tool.py` that takes four string parameters and returns a JSON string matching the partial evaluation shape (without score_change — that is computed by the endpoint):

Input parameters:
- `code: str` — the user's submitted code
- `exercise_description: str` — the full German exercise description
- `expected_output: str` — the exact expected stdout
- `stdout: str` — the actual stdout produced by running the code

Output (JSON string):
```json
{
    "result": "richtig" | "teilweise" | "falsch",
    "what_was_good": "...",
    "what_went_wrong": "...",
    "hint": "..."
}
```

**Evaluation logic (priority order — implementor must respect this):**
1. If `stdout` exactly matches `expected_output` (stripped of trailing whitespace):
   - Call LLM to verify the code demonstrates the correct concept (not just a hardcoded print).
   - If concept correct: result = "richtig".
   - If code is a trivial workaround (e.g. `print("expected_output")` for a loop exercise): result = "teilweise".
2. If `stdout` does not match but is non-empty:
   - Call LLM to determine if the code shows partial understanding.
   - If partial understanding: result = "teilweise".
   - If clearly wrong: result = "falsch".
3. If `stdout` is empty (likely a runtime error or silent code):
   - result = "falsch".

The LLM system prompt must:
- Be in German.
- Return ONLY valid JSON — no markdown, no explanations outside the JSON.
- Use the exact field names: result, what_was_good, what_went_wrong, hint.
- Set `what_was_good` and `hint` to non-empty strings even for "falsch" (always give constructive feedback).

**Definition of Done:**
- [ ] Tool is decorated with `@tool`.
- [ ] Takes exactly: code, exercise_description, expected_output, stdout as string params.
- [ ] Returns a JSON string (parseable with `json.loads`).
- [ ] Returns result = "richtig" when stdout matches expected_output and code is not trivially hardcoded.
- [ ] Returns result = "falsch" when stdout is empty.
- [ ] Returns result = "teilweise" when output is close but not exact.
- [ ] `what_was_good` and `hint` are never empty strings.

**Integration points:**
- Called by the exercise submission endpoint in Phase 4, which parses the JSON and applies score update rules.
- Uses `get_llm()` from `agent/config.py`.

**Pattern to follow:**
- `backend/agent/tools/debug_tool.py` for the structured JSON return pattern.
- `backend/agent/tools/explain_tool.py` for the `@tool` + `get_llm()` pattern.

**Files likely affected:**
- `backend/agent/tools/exercise_evaluator_tool.py` (new file)

**Gotchas:**
- The stdout exact-match check must happen in Python before calling the LLM, not inside the LLM prompt. This prevents the LLM from marking a correct output as "teilweise" due to hallucination.
- Strip trailing newlines/whitespace from both expected and actual stdout before comparison.

---

### Task 3.2: Hint Tool ⏸️

**What needs to exist:**
A `@tool` function `get_hint` in `hint_tool.py` that returns a progressively more specific hint based on the level requested.

Input parameters:
- `code: str` — the user's current (possibly incomplete or wrong) code
- `exercise_description: str` — the full German exercise description
- `hint_level: int` — 1, 2, or 3

Output: a plain string (German hint), not JSON.

Hint levels:
- Level 1: Conceptual hint — which Python concept or approach to use, no syntax.
- Level 2: Syntax hint — mention the specific function, method, or keyword needed.
- Level 3: Near-solution hint — show the structure or a partial code snippet.

The LLM system prompt must tailor the hint specificity based on `hint_level`. It must not reveal the full solution.

**Definition of Done:**
- [ ] Tool is decorated with `@tool`.
- [ ] Takes code, exercise_description, hint_level as parameters.
- [ ] Returns a German plain-text string.
- [ ] Level 1 hint does not mention specific syntax.
- [ ] Level 3 hint shows partial code without giving away the full solution.

**Integration points:**
- Called by the `POST /exercises/hint` endpoint in Phase 4.
- Uses `get_llm()` from `agent/config.py`.

**Pattern to follow:**
- `backend/agent/tools/explain_tool.py` for plain-string return pattern.

**Files likely affected:**
- `backend/agent/tools/hint_tool.py` (new file)

---

### Task 3.3: Exercise Generator Tool ⏸️

**What needs to exist:**
A `@tool` function `generate_exercise` in `exercise_generator_tool.py` that dynamically generates an exercise for Intermediate or Advanced skills.

Input parameters:
- `skill_key: str` — the skill to generate an exercise for
- `skill_label: str` — German label for context
- `level: str` — "intermediate" or "advanced"
- `completed_exercise_titles: str` — comma-separated list of already completed exercise titles (to avoid repetition)

Output (JSON string):
```json
{
    "title": "...",
    "description": "...",
    "expected_output": "...",
    "hint": "..."
}
```

The LLM must generate exercises that:
- Are in German.
- Are solvable without external libraries.
- Have a clear, deterministic expected_output.
- Are appropriate difficulty for the level.
- Do not repeat titles from `completed_exercise_titles`.

**Definition of Done:**
- [ ] Tool is decorated with `@tool`.
- [ ] Returns a parseable JSON string with all 4 fields.
- [ ] Generated exercises do not require `input()`.
- [ ] Generated exercises specify a concrete expected_output.

**Integration points:**
- Called by the `GET /exercises/{skill_key}` endpoint in Phase 4 for Intermediate/Advanced skills.

**Pattern to follow:**
- `backend/agent/tools/debug_tool.py` for JSON return pattern.

**Files likely affected:**
- `backend/agent/tools/exercise_generator_tool.py` (new file)

---

### Task 3.4: Skill Test Tool ⏸️

**What needs to exist:**
`backend/agent/tools/skill_test_tool.py` with two `@tool` functions:

**`generate_skill_test(skill_key: str, skill_label: str, user_level: str) -> str`**

Generates a full three-part test. Returns JSON matching the **Skill Test Question Shape** from Shared Definitions:
```json
{
    "multiple_choice": [ ... ],   // exactly 3 items
    "code_reading": { ... },
    "mini_task": { ... }
}
```

- Multiple choice: each question has options A/B/C/D, a correct answer key, and a German explanation.
- Code reading: a short Python snippet, a question about what it does, and the correct answer as a string.
- Mini task: a German description of a small coding task and the expected output string.
- All content in German.
- Questions appropriate for the skill and user_level.

**`evaluate_skill_test(skill_key: str, mc_answers: str, mc_correct: str, mini_task_description: str, mini_task_expected: str, mini_task_code: str, code_reading_answer: str, code_reading_correct: str) -> str`**

Evaluates a submitted test. Returns JSON:
```json
{
    "total_score": 0-100,
    "passed": true | false,
    "per_question_feedback": [
        { "question_type": "mc_1", "correct": true, "explanation": "..." },
        { "question_type": "mc_2", "correct": true, "explanation": "..." },
        { "question_type": "mc_3", "correct": false, "explanation": "..." },
        { "question_type": "code_reading", "correct": true, "explanation": "..." },
        { "question_type": "mini_task", "correct": false, "explanation": "..." }
    ]
}
```

Scoring:
- Each of 3 MC questions: 20 points (exact string match of selected answer key vs correct key).
- Code reading: 20 points (LLM evaluates if user's answer is semantically correct).
- Mini task: 20 points (LLM evaluates if submitted code would produce expected output).
- Total = sum of points earned. passed = total_score >= 60.

MC evaluation is done in Python (no LLM needed — exact string comparison). Code reading and mini task use the LLM.

Parameters are passed as primitives (strings/JSON strings) rather than complex objects because LangChain `@tool` works best with flat primitive signatures.

**Definition of Done:**
- [ ] Both functions are decorated with `@tool` and importable.
- [ ] `generate_skill_test` returns valid JSON with all three sections.
- [ ] `evaluate_skill_test` returns valid JSON with total_score, passed, and per_question_feedback for all 5 question types.
- [ ] MC evaluation uses Python string comparison, not LLM.
- [ ] passed = (total_score >= 60).

**Integration points:**
- `generate_skill_test` called by `POST /skill-tests/generate` in Phase 4.
- `evaluate_skill_test` called by `POST /skill-tests/submit` in Phase 4.

**Pattern to follow:**
- `backend/agent/tools/debug_tool.py` for structured JSON output.

**Files likely affected:**
- `backend/agent/tools/skill_test_tool.py` (new file)

**Gotchas:**
- LangChain `@tool` signature parsing: keep all parameters as `str` or `int` — avoid `list` or `dict` parameters.
- For `evaluate_skill_test`, pass MC answers and correct keys as comma-separated strings (e.g. `mc_answers="A,B,C"`, `mc_correct="A,C,D"`) and split them in the function body.

---

## Phase Completion Criteria
- [ ] All tasks completed
- [ ] Code reviewed and approved
- [ ] Tests written: unit tests for each tool (mock `get_llm()`, assert JSON shape, assert MC evaluation logic, assert score calculation)
- [ ] Git commits: `[impl]`, `[test]`
