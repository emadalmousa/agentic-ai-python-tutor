# Phase 3: Integration

**Status**: ✅ Completed
**Parent Tracker**: `docs/implementations/phase-2-langchain-ollama.md`

## Goal

Wire the LangChain tools from Phase 2 into the FastAPI service layer. Replace dummy implementations in `code_explainer.py` and `debugger.py` with real LLM-backed logic. Forward the `question` field from the router. Register a 503 error handler in `main.py`. After this phase, the system is fully functional with real AI responses.

## End-of-Phase System State

- `backend/agent/tutor_agent.py` orchestrates both tools and returns the shared analysis dict
- `backend/services/code_explainer.py` delegates to `tutor_agent.run_analysis()`, signature now accepts `question`
- `backend/services/debugger.py` delegates to `tutor_agent.run_analysis()`
- `backend/routers/tutor.py` forwards `request.question` to `explain_code()`
- `backend/main.py` handles `ServiceUnavailableError` and returns HTTP 503
- `POST /tutor/analyze` returns real LLM-generated explanations and debug results
- Ollama offline → HTTP 503 with clear error message
- **System runs without errors**

## Tasks

| Task | Files | Complexity | Status | Description |
|---|---|---|---|---|
| 3.1 | `backend/agent/tutor_agent.py` | Medium | ✅ | Orchestrator: run_analysis() + ServiceUnavailableError |
| 3.2 | `backend/services/code_explainer.py` | Low | ✅ | Replace dummy with agent delegation; add question param |
| 3.3 | `backend/services/debugger.py` | Low | ✅ | Replace rule-based logic with agent delegation |
| 3.4 | `backend/routers/tutor.py` | Low | ✅ | Forward question to explain_code() |
| 3.5 | `backend/main.py` | Low | ✅ | Register ServiceUnavailableError → HTTP 503 handler |

## Detailed Task Descriptions

### Task 3.1: Agent orchestrator (tutor_agent.py) ⏸️

**What needs to exist:**
A module `backend/agent/tutor_agent.py` that provides:

1. A custom exception class `ServiceUnavailableError` — raised when Ollama cannot be reached
2. A function `run_analysis(code: str, question: str | None = None) -> dict` that:
   - Calls `explain_code_tool` with `code` and `question`
   - Calls `debug_code_tool` with `code`
   - Assembles and returns `{"explanation": str, "error_found": bool, "suggestion": str}`
   - Catches any connection/timeout errors from either tool and raises `ServiceUnavailableError` with a German-language message

The function calls both tools every time (no conditional skipping). The return dict matches the Shared Definitions contract in the parent tracker exactly.

**Definition of Done:**
- [ ] `from agent.tutor_agent import run_analysis, ServiceUnavailableError` succeeds
- [ ] `run_analysis("print('hello')")` returns a dict with keys `explanation`, `error_found`, `suggestion` (requires Ollama running)
- [ ] `run_analysis` raises `ServiceUnavailableError` when Ollama is not reachable
- [ ] `ServiceUnavailableError` message is in German
- [ ] Return dict keys match Shared Definitions exactly (no extra keys, no missing keys)

**Integration points:**
- Imports `explain_code_tool` from `agent.tools.explain_tool` (Phase 2)
- Imports `debug_code_tool` from `agent.tools.debug_tool` (Phase 2)
- Called by `services/code_explainer.py` (Task 3.2) and `services/debugger.py` (Task 3.3)

**Pattern to follow:**
- Exception wrapping pattern: catch broad connection errors (e.g., `httpx.ConnectError`, `ConnectionRefusedError`) and re-raise as `ServiceUnavailableError`
- Return dict assembled from tool results directly — no additional LLM calls

**Files likely affected:**
- `backend/agent/tutor_agent.py` (new)

**Gotchas:**
- Both tools must be called regardless of whether the first succeeds — but if Ollama is down, the first call will already fail; no need to handle partial results
- The exact exception types raised by `langchain-ollama` on connection failure should be verified during implementation (likely `httpx` errors wrapped by LangChain)

---

### Task 3.2: Replace code_explainer.py ⏸️

**What needs to exist:**
`backend/services/code_explainer.py` is completely replaced. The new implementation exposes a single function `explain_code(code: str, question: str | None = None) -> str` that calls `run_analysis(code, question)` and returns the `explanation` field.

The function does not catch `ServiceUnavailableError` — it lets it propagate to `main.py`'s error handler.

**Definition of Done:**
- [ ] `explain_code` accepts `code` and optional `question` parameters
- [ ] `explain_code("print('hello')")` returns the LLM explanation string (requires Ollama)
- [ ] `ServiceUnavailableError` propagates uncaught
- [ ] No rule-based or dummy logic remains in this file

**Integration points:**
- Called by `routers/tutor.py` (Task 3.4) with `explain_code(request.code, request.question)`
- Calls `run_analysis` from `agent.tutor_agent` (Task 3.1)

**Files likely affected:**
- `backend/services/code_explainer.py` (existing, full replacement)

---

### Task 3.3: Replace debugger.py ⏸️

**What needs to exist:**
`backend/services/debugger.py` is completely replaced. The new implementation exposes `debug_code(code: str) -> tuple[bool, str]` — maintaining the same external signature as before. Internally it calls `run_analysis(code)` and returns `(result["error_found"], result["suggestion"])`.

The function does not catch `ServiceUnavailableError`.

**Definition of Done:**
- [ ] `debug_code` returns `tuple[bool, str]` (external contract unchanged)
- [ ] `debug_code("for i in range(5)\n    print(i)")` returns `(True, <suggestion string>)` (requires Ollama)
- [ ] `debug_code("for i in range(5):\n    print(i)")` returns `(False, <string>)`
- [ ] `ServiceUnavailableError` propagates uncaught
- [ ] No rule-based logic remains in this file

**Integration points:**
- Called by `routers/tutor.py` — signature unchanged, no router modification needed for this service
- Calls `run_analysis` from `agent.tutor_agent` (Task 3.1)

**Files likely affected:**
- `backend/services/debugger.py` (existing, full replacement)

**Gotchas:**
- `run_analysis` is called once per service function — both `code_explainer.py` and `debugger.py` will each call it separately for a single HTTP request, resulting in two LLM round-trips per request. This is intentional for Phase 2 simplicity; optimization is a Phase 3 concern.

---

### Task 3.4: Forward question in tutor router ⏸️

**What needs to exist:**
`backend/routers/tutor.py` passes `request.question` as the second argument when calling `explain_code()`. This is the only change to this file.

Before: `explain_code(request.code)`
After: `explain_code(request.code, request.question)`

**Definition of Done:**
- [ ] `explain_code` is called with both `request.code` and `request.question`
- [ ] No other lines in `tutor.py` are changed
- [ ] `POST /tutor/analyze` with `{"code": "...", "question": "..."}` passes the question to the LLM

**Integration points:**
- Depends on updated `explain_code` signature from Task 3.2

**Files likely affected:**
- `backend/routers/tutor.py` (existing, one-line change)

---

### Task 3.5: Register 503 error handler in main.py ⏸️

**What needs to exist:**
`backend/main.py` registers a FastAPI exception handler for `ServiceUnavailableError` that returns an HTTP 503 response with a German-language JSON body explaining that the AI service is unavailable.

Example response body:
```json
{"detail": "Der KI-Dienst ist momentan nicht erreichbar. Bitte stelle sicher, dass Ollama läuft."}
```

No other part of `main.py` changes (CORS config, router registration, health-check endpoint remain untouched).

**Definition of Done:**
- [ ] `ServiceUnavailableError` raised anywhere in the request lifecycle returns HTTP 503 (not 500)
- [ ] The 503 response body contains a German-language `detail` message
- [ ] `GET /` health-check still returns `{"message": "Python Tutor Backend läuft", "status": "ok"}`
- [ ] CORS middleware and router registration are unchanged

**Integration points:**
- Imports `ServiceUnavailableError` from `agent.tutor_agent` (Task 3.1)
- Handles exceptions raised anywhere in the `services/` → `agent/` call chain

**Pattern to follow:**
- FastAPI exception handler: `@app.exception_handler(ServiceUnavailableError)` returning `JSONResponse(status_code=503, content={...})`

**Files likely affected:**
- `backend/main.py` (existing, add import + one exception handler)

**Gotchas:**
- The exception handler import adds a dependency from `main.py` to `agent/tutor_agent.py` — verify this does not create a circular import (it should not, given the layer structure)

## Phase Completion Criteria
- [ ] All tasks 3.1–3.5 completed and Definition of Done satisfied
- [ ] Code reviewed and approved
- [ ] Tests written and passing: end-to-end happy path + 503 scenario
- [ ] Git commits: `[impl] Phase 3: Wire LangChain tools into FastAPI service layer`, `[test] Phase 3: integration and 503 error handler tests`
