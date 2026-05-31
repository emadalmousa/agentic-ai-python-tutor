# Skill Tests Endpoints - API Reference

**Use this document to understand the skill test generation and evaluation API endpoints.**

## Base URL

All endpoints are prefixed with `/skill-tests` (e.g., `http://localhost:8000/skill-tests/...`)

## Endpoints

### POST /skill-tests/generate

Generates a new skill test for a given skill. The test is stored server-side to prevent tampering. Returns a session ID and the test data.

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "skill_key": "for_loop"
}
```

**Response:**

```json
{
  "test_session_id": 42,
  "test_data": {
    "skill_key": "for_loop",
    "skill_label": "For-Schleifen",
    "multiple_choice": [
      {
        "id": "0",
        "question": "Was gibt folgender Code aus?\nfor i in range(3):\n    print(i * 2)",
        "options": {
          "A": "0 2 4",
          "B": "0\n2\n4",
          "C": "1 3 5",
          "D": "0\n1\n2"
        }
      },
      {
        "id": "1",
        "question": "Welche Schleife ist am besten zum Durchlaufen einer Liste geeignet?",
        "options": {
          "A": "while i < len(list)",
          "B": "for item in list",
          "C": "for i in range(list)",
          "D": "do-while (Python-Syntax)"
        }
      },
      {
        "id": "2",
        "question": "Wie oft wird dieser Code ausgeführt?\nfor i in range(5, 10):\n    print(i)",
        "options": {
          "A": "5 mal",
          "B": "10 mal",
          "C": "9 mal",
          "D": "6 mal"
        }
      }
    ],
    "code_reading": {
      "question": "Lese diesen Code und erkläre in 2-3 Sätzen, was er macht:\nfor name in ['Alice', 'Bob', 'Charlie']:\n    print(f'Hallo {name}!')",
      "expected_length": "2-3 sentences"
    },
    "mini_task": {
      "description": "Schreibe eine for-Schleife, die die Quadrate der Zahlen 1 bis 5 ausgibt.",
      "expected_output": "1\n4\n9\n16\n25",
      "test_type": "output_match"
    }
  }
}
```

**Test Structure:**
- **Multiple Choice (3 questions)**: Each with question and 4 options (A–D)
- **Code Reading**: Analyze given code and explain it in a few sentences
- **Mini Task**: Write code to solve a specific problem; output will be compared

**Status Codes:**
- `200 OK`: Test generated successfully
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: Skill not found
- `503 Service Unavailable`: LLM unavailable

---

### POST /skill-tests/submit

Submits student answers for a skill test. Uses the server-side test data (not client-supplied) to prevent tampering. Returns total score, per-question feedback, and attempt number.

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "test_session_id": 42,
  "skill_key": "for_loop",
  "mc_answers": {
    "0": "B",
    "1": "B",
    "2": "A"
  },
  "code_reading_answer": "Diese for-Schleife iteriert über eine Liste von Namen und gibt für jede Person eine Begrüßung aus.",
  "mini_task_code": "for i in range(1, 6):\n    print(i ** 2)"
}
```

**Response:**

```json
{
  "total_score": 73,
  "passed": true,
  "mc_score": 67,
  "code_reading_score": 80,
  "mini_task_score": 80,
  "per_question_feedback": [
    {
      "question_id": "0",
      "student_answer": "B",
      "correct_answer": "B",
      "points": 33,
      "feedback": "Korrekt! Die range(3) erzeugt 0, 1, 2. Multipliziert mit 2 ergibt das 0, 2, 4, jeweils auf einer neuen Zeile."
    },
    {
      "question_id": "1",
      "student_answer": "B",
      "correct_answer": "B",
      "points": 34,
      "feedback": "Sehr gut! 'for item in list' ist die pythonische und sicherste Methode."
    },
    {
      "question_id": "2",
      "student_answer": "A",
      "correct_answer": "D",
      "points": 0,
      "feedback": "Nicht ganz. range(5, 10) erzeugt 5, 6, 7, 8, 9 — das sind 5 Zahlen, aber startet bei 5. Also 6 Iterationen? Nein, es sind 5. Die Antwort ist D (6 mal ist falsch)."
    }
  ],
  "attempt_number": 1
}
```

**Response Fields:**
- `total_score`: Combined score across all sections (0–100, percentage)
- `passed`: true if total_score ≥ 60 (threshold for unlocking next skill)
- `mc_score`: Multiple choice section score (0–100)
- `code_reading_score`: Code reading section score (0–100)
- `mini_task_score`: Mini-task execution score (0–100)
- `per_question_feedback`: Detailed feedback for each question with LLM explanation
- `attempt_number`: Which attempt this is (1 for first, increments on retry)

**Passing Criteria:**
- Must score ≥60% overall to unlock the next skill
- Students can retry the same skill test multiple times
- Each attempt is recorded in the database

**Status Codes:**
- `200 OK`: Test evaluated successfully
- `400 Bad Request`: Invalid session ID or missing fields
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: Test session not found
- `503 Service Unavailable`: LLM unavailable for evaluation

---

## How Tests Unlock Skills

After a successful submission with `passed: true`:

1. The next skill in the progression chain is automatically unlocked
2. If the test is for a level-start skill (e.g., "list_comprehension"), only that skill is unlocked
3. The student's user level may be updated (Anfänger → Fortgeschritten → Profi)
4. Student is returned to the progress view with the newly unlocked skill highlighted

---

## Example Usage

### JavaScript/TypeScript

```typescript
import type { SkillTestData, SubmitTestResponse } from "@/types/tutor"

const token = localStorage.getItem("ki_tutor_token")

// Generate a skill test
const generateSkillTest = async (skillKey: string): Promise<{ test_session_id: number; test_data: SkillTestData }> => {
  const response = await fetch("http://localhost:8000/skill-tests/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ skill_key: skillKey })
  })
  if (!response.ok) throw new Error("Failed to generate test")
  return response.json()
}

// Submit skill test answers
const submitSkillTest = async (
  testSessionId: number,
  skillKey: string,
  mcAnswers: Record<string, string>,
  codeReadingAnswer: string,
  miniTaskCode: string
): Promise<SubmitTestResponse> => {
  const response = await fetch("http://localhost:8000/skill-tests/submit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      test_session_id: testSessionId,
      skill_key: skillKey,
      mc_answers: mcAnswers,
      code_reading_answer: codeReadingAnswer,
      mini_task_code: miniTaskCode
    })
  })
  if (!response.ok) throw new Error("Failed to submit test")
  return response.json()
}
```

**File Reference**: `frontend/lib/api.ts` contains the actual implementation.

---

## Test Scoring Details

### Multiple Choice (Section Weight: ~33%)
- Each correct answer: +33 points toward section score
- 3 questions total
- Exact match required for full credit

### Code Reading (Section Weight: ~33%)
- LLM evaluates semantic understanding
- Full score if explanation captures key concepts
- Partial credit for partial understanding
- 0 if completely off-topic

### Mini Task (Section Weight: ~33%)
- Code is executed and output compared to expected
- Full score if output matches exactly
- Partial score if output is close but incorrect format
- 0 if execution fails or output is completely wrong

**Final Score**: Average of the three section scores

---

## Retrying Failed Tests

Students can retry a skill test as many times as needed:

1. If `passed: false`, the skill remains locked
2. Student can click "Retry Test" and generate a new test (with different questions)
3. Each attempt is logged with `attempt_number` incremented
4. First attempt with `passed: true` unlocks the skill (subsequent attempts are optional)

---

## Test Server-Side Storage

Tests are generated server-side and stored in `skill_test_results.generated_test` (JSON) to prevent tampering:

- Client cannot modify test data or answers before submission
- If server restarts or DB is cleared, test becomes inaccessible
- Each call to `/generate` creates a new test session with unique `test_session_id`

---

## Error Responses

All error responses follow the format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common errors:
- `"Skill 'invalid_key' nicht gefunden."` - Skill does not exist
- `"Test session not found"` - Session ID is invalid or expired
- `"Not authenticated"` - Missing or invalid bearer token
- `"LLM service unavailable"` - OpenAI API or Ollama not responding

---

## Related Topics

- [Exercise & Skill System Feature Guide](../understanding-features/exercise-skill-system.md)
- [Exercise Endpoints](exercises-endpoints.md)
- [Authentication](authentication-endpoints.md)
- [Skill Tree Reference](skill-tree.md)
