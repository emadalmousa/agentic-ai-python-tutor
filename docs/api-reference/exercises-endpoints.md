# Exercise Endpoints - API Reference

**Use this document to understand the exercise submission and retrieval API endpoints.**

## Base URL

All endpoints are prefixed with `/exercises` (e.g., `http://localhost:8000/exercises/...`)

## Endpoints

### GET /exercises/{skill_key}

Retrieves the list of 5 exercises for a given skill with their completion status.

**Parameters:**
- `skill_key` (path, required): Skill identifier (e.g., `"for_loop"`)

**Authentication:** Required (Bearer token)

**Response:**

```json
{
  "skill_key": "for_loop",
  "exercises": [
    {
      "id": "for_loop_1",
      "order": 1,
      "title": "Einfache for-Schleife",
      "description": "Schreibe eine for-Schleife, die die Zahlen 1 bis 5 ausgibt.",
      "hint": "Nutze range(5) und print(i) in der Schleife.",
      "is_unlocked": true,
      "is_locked": false,
      "score_granted": 0
    },
    {
      "id": "for_loop_2",
      "order": 2,
      "title": "Schleife mit Bedingung",
      "description": "Schreibe eine for-Schleife, die nur gerade Zahlen ausgibt.",
      "hint": "Nutze if i % 2 == 0 um gerade Zahlen zu filtern.",
      "is_unlocked": true,
      "is_locked": false,
      "score_granted": 0
    }
  ]
}
```

**Fields:**
- `is_unlocked`: true if skill prerequisites are met (predecessor score ≥80% or first skill in level)
- `is_locked`: true if this exercise is completed (score_granted=20); cannot be retaken once locked
- `score_granted`: 0 (not completed), 10 (partial), or 20 (complete)

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: Skill not found

---

### POST /exercises/submit

Submits student code for an exercise. Runs the code in a sandbox, evaluates it, and returns scoring feedback.

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "skill_key": "for_loop",
  "exercise_id": "for_loop_1",
  "code": "for i in range(1, 6):\n    print(i)"
}
```

**Response:**

```json
{
  "result": "richtig",
  "score_change": 20,
  "new_skill_score": 45,
  "what_was_good": "Dein Code ist syntaktisch korrekt und gibt die richtige Ausgabe aus.",
  "what_went_wrong": "",
  "hint": "",
  "stdout": "1\n2\n3\n4\n5\n",
  "stderr": "",
  "redirect_to_tutor": false,
  "analysis": "Der Code verwendet korrekt range(1, 6) und print(). Die Ausgabe passt genau."
}
```

**Response Fields:**
- `result`: "richtig" (correct, +20%), "teilweise" (partial, +10%), or "falsch" (wrong, +0%)
- `score_change`: Points added to skill score (0, 10, or 20)
- `new_skill_score`: Updated overall skill score (0–100)
- `what_was_good`: Positive feedback from LLM
- `what_went_wrong`: Explanation of what needs improvement
- `hint`: Suggestion for next attempt
- `stdout`: Actual program output
- `stderr`: Error messages from execution (if any)
- `redirect_to_tutor`: true if exercise is marked as "wrong" and student should return to main tutor; false if they can retry
- `analysis`: Detailed LLM analysis of the submission

**Status Codes:**
- `200 OK`: Evaluation successful
- `400 Bad Request`: Invalid skill_key or exercise_id
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: Skill or exercise not found

**Behavior:**
- If `result == "richtig"`: Exercise is marked as locked (is_locked=true); student moves to next exercise
- If `result == "teilweise"` or `"falsch"`: Exercise remains unlocked; student can retry immediately
- Skill score is updated even on wrong answers (to track engagement)

---

### POST /exercises/hint

Generates a contextual hint for an exercise based on student's current code.

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "skill_key": "for_loop",
  "exercise_id": "for_loop_1",
  "code": "for i in range(5)\n    print(i)",
  "hint_level": 1
}
```

**Response:**

```json
{
  "hint": "Du brauchst einen Doppelpunkt (:) nach der range()-Funktion in der for-Schleife. Das ist die Python-Syntax für Schleifen."
}
```

**Parameters:**
- `hint_level`: 1 (basic hint), 2 (intermediate hint with partial solution), 3 (advanced hint with almost full solution)

**Status Codes:**
- `200 OK`: Hint generated
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: Skill or exercise not found
- `500 Internal Server Error`: LLM unavailable

---

## Example Usage

### JavaScript/TypeScript

```typescript
import type { SkillProgress, Exercise, SubmitExerciseResponse } from "@/types/tutor"

const token = localStorage.getItem("ki_tutor_token")

// Get exercises for a skill
const getExercises = async (skillKey: string): Promise<Exercise[]> => {
  const response = await fetch(`http://localhost:8000/exercises/${skillKey}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!response.ok) throw new Error("Failed to fetch exercises")
  const data = await response.json()
  return data.exercises
}

// Submit exercise
const submitExercise = async (
  skillKey: string,
  exerciseId: string,
  code: string
): Promise<SubmitExerciseResponse> => {
  const response = await fetch("http://localhost:8000/exercises/submit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ skill_key: skillKey, exercise_id: exerciseId, code })
  })
  if (!response.ok) throw new Error("Failed to submit exercise")
  return response.json()
}

// Get hint
const getExerciseHint = async (
  skillKey: string,
  exerciseId: string,
  code: string,
  hintLevel: number
): Promise<string> => {
  const response = await fetch("http://localhost:8000/exercises/hint", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      skill_key: skillKey,
      exercise_id: exerciseId,
      code,
      hint_level: hintLevel
    })
  })
  if (!response.ok) throw new Error("Failed to get hint")
  const data = await response.json()
  return data.hint
}
```

**File Reference**: `frontend/lib/api.ts` contains the actual implementation.

## Error Responses

All error responses follow the format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common errors:
- `"Skill 'invalid_key' nicht gefunden."` - Skill does not exist
- `"Exercise 'invalid_id' nicht gefunden."` - Exercise does not exist
- `"Not authenticated"` - Missing or invalid bearer token
- `"LLM service unavailable"` - OpenAI API or Ollama not responding

## Related Topics

- [Exercise & Skill System Feature Guide](../understanding-features/exercise-skill-system.md)
- [Skill Tests Endpoints](skill-tests-endpoints.md)
- [Authentication](authentication-endpoints.md)
