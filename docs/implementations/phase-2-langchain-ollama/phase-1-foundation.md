# Phase 1: Foundation

**Status**: ✅ Completed
**Parent Tracker**: `docs/implementations/phase-2-langchain-ollama.md`

## Goal

Create all scaffolding required for LangChain + Ollama integration: package structure, environment configuration, LLM factory, and an updated `start.sh` that manages the Ollama process. After this phase the `agent/` package is importable and `get_llm()` returns a configured `ChatOllama` instance — but no existing behavior changes. The dummy services remain active.

## End-of-Phase System State

- `backend/agent/` package exists and is importable from within the backend
- `backend/agent/config.py` provides `get_llm()` returning a `ChatOllama` instance
- `backend/agent/tools/` sub-package exists (empty, ready for Phase 2)
- `backend/.env` and `backend/.env.example` exist with Ollama connection defaults
- `backend/requirements.txt` includes `langchain`, `langchain-ollama`, `python-dotenv`
- `start.sh` starts Ollama in background before backend and frontend; stops Ollama on exit
- Existing dummy services (`code_explainer.py`, `debugger.py`) are untouched and still active
- **System runs without errors** — `POST /tutor/analyze` still returns dummy responses

## Tasks

| Task | Files | Complexity | Status | Description |
|---|---|---|---|---|
| 1.1 | `backend/requirements.txt` | Low | ✅ | Add LangChain and dotenv packages |
| 1.2 | `backend/.env.example`, `backend/.env` | Low | ✅ | Create environment config files |
| 1.3 | `backend/agent/__init__.py`, `backend/agent/tools/__init__.py` | Low | ✅ | Create agent package skeleton |
| 1.4 | `backend/agent/config.py` | Low | ✅ | LLM factory: get_llm() with ChatOllama |
| 1.5 | `start.sh` | Low | ✅ | Add Ollama lifecycle to startup script |

## Detailed Task Descriptions

### Task 1.1: Extend requirements.txt ⏸️

**What needs to exist:**
`backend/requirements.txt` must list three additional packages so that `pip install -r requirements.txt` installs everything needed for LangChain + Ollama + environment config loading.

**Definition of Done:**
- [ ] `langchain` is listed
- [ ] `langchain-ollama` is listed
- [ ] `python-dotenv` is listed
- [ ] Existing entries (`fastapi`, `uvicorn[standard]`, `pydantic`) are unchanged
- [ ] `pip install -r requirements.txt` completes without errors inside `backend/venv/`

**Integration points:**
- All subsequent phases depend on these packages being installed

**Files likely affected:**
- `backend/requirements.txt`

---

### Task 1.2: Create environment configuration files ⏸️

**What needs to exist:**
Two files that document and provide Ollama connection parameters:
- `backend/.env.example` — committed to the repo, contains placeholder values with comments
- `backend/.env` — local developer copy, identical content, git-ignored (`.gitignore` already excludes `.env`)

Both files must define `OLLAMA_BASE_URL` and `OLLAMA_MODEL` with their defaults as described in the Shared Definitions section of the parent tracker.

**Definition of Done:**
- [ ] `backend/.env.example` exists and is committed (not git-ignored)
- [ ] `backend/.env` exists locally
- [ ] Both files contain `OLLAMA_BASE_URL=http://localhost:11434`
- [ ] Both files contain `OLLAMA_MODEL=llama3.2`
- [ ] A comment in `.env.example` explains each variable's purpose

**Integration points:**
- `agent/config.py` (Task 1.4) reads these variables at startup via `python-dotenv`

**Files likely affected:**
- `backend/.env.example` (new)
- `backend/.env` (new, not committed)

---

### Task 1.3: Create agent package skeleton ⏸️

**What needs to exist:**
Two empty `__init__.py` files that make `agent` and `agent/tools` into Python packages importable from the backend working directory.

**Definition of Done:**
- [ ] `backend/agent/__init__.py` exists (empty file)
- [ ] `backend/agent/tools/__init__.py` exists (empty file)
- [ ] `import agent` succeeds when run from `backend/` with the venv active
- [ ] `import agent.tools` succeeds

**Integration points:**
- Required before `agent/config.py` (Task 1.4) and all Phase 2 tool files can be imported

**Pattern to follow:**
- Mirrors existing empty `__init__.py` files in `backend/models/__init__.py`, `backend/services/__init__.py`, `backend/routers/__init__.py`

**Files likely affected:**
- `backend/agent/__init__.py` (new)
- `backend/agent/tools/__init__.py` (new)

---

### Task 1.4: Create LLM factory (agent/config.py) ⏸️

**What needs to exist:**
A module `backend/agent/config.py` that exposes a single function `get_llm()`. When called, it reads `OLLAMA_BASE_URL` and `OLLAMA_MODEL` from the environment (loaded from `backend/.env` via `python-dotenv`) and returns a configured `ChatOllama` instance.

The function does not initiate a connection to Ollama when called — it only constructs the client object. Actual connection attempts happen when a tool invokes the LLM.

**Definition of Done:**
- [ ] `from agent.config import get_llm` succeeds from `backend/`
- [ ] `get_llm()` returns a `ChatOllama` instance
- [ ] `get_llm()` uses `OLLAMA_BASE_URL` from env (not hardcoded)
- [ ] `get_llm()` uses `OLLAMA_MODEL` from env (not hardcoded)
- [ ] If env vars are absent, defaults from `.env.example` apply (`http://localhost:11434`, `llama3.2`)

**Integration points:**
- Called by both LangChain tools in Phase 2 (`explain_tool.py`, `debug_tool.py`)

**Files likely affected:**
- `backend/agent/config.py` (new)

**Gotchas:**
- `python-dotenv`'s `load_dotenv()` should be called once at module load, not inside `get_llm()` on every call
- The `.env` file path is relative to where uvicorn is launched (`backend/`), not to `config.py` itself — use `dotenv_path` or rely on the default search behavior

---

### Task 1.5: Update start.sh with Ollama lifecycle ⏸️

**What needs to exist:**
The existing `start.sh` in the project root must be extended to:
1. Start Ollama in the background before the backend and frontend
2. Record the Ollama PID
3. On SIGINT or EXIT: stop Ollama together with the backend and frontend processes

The script must handle the case where Ollama is already running (do not start a second instance or fail).

**Definition of Done:**
- [ ] `start.sh` starts Ollama (`ollama serve`) in the background before uvicorn
- [ ] Ollama PID is captured alongside `BACKEND_PID` and `FRONTEND_PID`
- [ ] `trap` kills all three PIDs on SIGINT/TERM/EXIT
- [ ] If Ollama is already running, script continues without error (check with `pgrep` or port probe before starting)
- [ ] `start.sh` remains executable (`chmod +x` applied or already set)
- [ ] Running `./start.sh` from the project root starts all three processes and prints their URLs

**Integration points:**
- Prerequisite for manual end-to-end testing in Phase 3 and Quality Gate

**Pattern to follow:**
- Extends existing `start.sh` — current structure captures `BACKEND_PID` and `FRONTEND_PID` with a `trap` for `INT TERM`; add `OLLAMA_PID` to the same pattern

**Files likely affected:**
- `start.sh` (existing, modified)

**Gotchas:**
- `ollama serve` blocks if port 11434 is already in use — check before starting to avoid script failure
- The `cd` commands in the current script use `$(dirname "$0")` — be careful the Ollama start command runs before any `cd` that changes working directory

## Phase Completion Criteria
- [ ] All tasks 1.1–1.5 completed and Definition of Done satisfied
- [ ] Code reviewed and approved
- [ ] Tests written and passing (at minimum: `import agent.config` + `get_llm()` returns ChatOllama)
- [ ] Git commits: `[impl] Phase 1: Foundation scaffold for LangChain + Ollama`, `[test] Phase 1: agent/config import and get_llm() tests`
