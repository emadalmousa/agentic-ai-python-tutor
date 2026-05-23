# Phase 2: LangChain Tools

**Status**: ⏸️ Not Started
**Parent Tracker**: `docs/implementations/phase-2-langchain-ollama.md`

## Goal

Implement two LangChain `@tool` functions — one for code explanation and one for debug analysis — that call the Ollama LLM via `get_llm()`. After this phase, both tools are independently invokable and return correct results. The FastAPI service layer still uses the dummy implementations; integration happens in Phase 3.

## End-of-Phase System State

- `backend/agent/tools/explain_tool.py` exists with `explain_code_tool`
- `backend/agent/tools/debug_tool.py` exists with `debug_code_tool`
- Both tools call `get_llm()` from `agent/config.py`
- Both tools are importable and invokable directly (outside FastAPI context)
- Existing dummy services remain active — `POST /tutor/analyze` still returns dummy responses
- **System runs without errors**

## Tasks

| Task | Files | Complexity | Status | Description |
|---|---|---|---|---|
| 2.1 | `backend/agent/tools/explain_tool.py` | Medium | ⏸️ | LangChain @tool for German step-by-step code explanation |
| 2.2 | `backend/agent/tools/debug_tool.py` | Medium | ⏸️ | LangChain @tool for structured JSON debug analysis |

## Detailed Task Descriptions

### Task 2.1: explain_code_tool ⏸️

**What needs to exist:**
A LangChain `@tool` named `explain_code_tool` in `backend/agent/tools/explain_tool.py`. When invoked with `code` (required) and optionally `question`, the tool sends a German-language prompt to the Ollama LLM and returns the model's explanation as a plain string.

The system prompt instructs the LLM to explain Python code step-by-step in German at a level suitable for beginners. When `question` is provided, the explanation must address the student's specific question. When `question` is absent, a general step-by-step explanation is produced.

**Definition of Done:**
- [ ] `from agent.tools.explain_tool import explain_code_tool` succeeds
- [ ] `explain_code_tool.invoke({"code": "print('hello')"})` returns a non-empty string (requires Ollama running)
- [ ] `explain_code_tool.invoke({"code": "print('hello')", "question": "Was macht print?"})` returns a string that addresses the question
- [ ] The system prompt is in German
- [ ] The tool uses `get_llm()` from `agent.config` — no hardcoded model or URL

**Integration points:**
- Called by `agent/tutor_agent.py` in Phase 3 as part of `run_analysis()`
- Depends on `agent/config.get_llm()` (Phase 1)

**Pattern to follow:**
- LangChain `@tool` decorator pattern from `langchain_core.tools`
- Prompt assembled as a list of messages passed to the LLM: system message (role instructions) + human message (code + optional question)

**Files likely affected:**
- `backend/agent/tools/explain_tool.py` (new)

**Gotchas:**
- `question` parameter should be optional with a default of `None` or `""` — LangChain tool parameters must be typed; use `Optional[str]` or `str = ""`
- The tool should not swallow Ollama connection errors — let them propagate so `tutor_agent.py` can catch them as `ServiceUnavailableError`

---

### Task 2.2: debug_code_tool ⏸️

**What needs to exist:**
A LangChain `@tool` named `debug_code_tool` in `backend/agent/tools/debug_tool.py`. When invoked with `code`, the tool sends a prompt to the Ollama LLM asking it to analyze the code for errors and return a structured JSON response.

The expected JSON structure:
```
{"error_found": bool, "suggestion": str}
```

The tool must parse the LLM's output robustly:
- Strip markdown code fences (` ```json ... ``` ` or ` ``` ... ``` `) before parsing
- Parse with `json.loads`
- On parse failure or missing keys: return `{"error_found": False, "suggestion": "Analyse nicht möglich."}`

The tool returns a Python `dict` (not a string) — the parsed JSON object.

**Definition of Done:**
- [ ] `from agent.tools.debug_tool import debug_code_tool` succeeds
- [ ] `debug_code_tool.invoke({"code": "for i in range(5)\n    print(i)"})` returns a dict with `error_found: True` and a non-empty `suggestion` (requires Ollama running)
- [ ] `debug_code_tool.invoke({"code": "for i in range(5):\n    print(i)"})` returns a dict with `error_found: False`
- [ ] When the LLM wraps JSON in markdown fences, the tool still parses successfully
- [ ] When the LLM returns non-parseable output, the tool returns `{"error_found": False, "suggestion": "Analyse nicht möglich."}` without raising
- [ ] The tool uses `get_llm()` from `agent.config`

**Integration points:**
- Called by `agent/tutor_agent.py` in Phase 3 as part of `run_analysis()`
- Depends on `agent/config.get_llm()` (Phase 1)

**Pattern to follow:**
- Same `@tool` decorator pattern as `explain_tool.py`
- System prompt instructs the LLM to respond ONLY with valid JSON — no surrounding text
- JSON parsing in a `try/except` block with explicit fallback

**Files likely affected:**
- `backend/agent/tools/debug_tool.py` (new)

**Gotchas:**
- LLMs reliably wrap JSON in markdown code fences even when instructed not to — the stripping step is not optional
- The LLM prompt should explicitly state the expected JSON schema and that no other text is allowed
- Return type annotation of the `@tool` should be `dict` so callers know what to expect

## Phase Completion Criteria
- [ ] Both tasks 2.1 and 2.2 completed and Definition of Done satisfied
- [ ] Code reviewed and approved
- [ ] Tests written and passing for both tools (import checks + behavior with mock or live Ollama)
- [ ] Git commits: `[impl] Phase 2: LangChain explain and debug tools`, `[test] Phase 2: tool invocation tests`
