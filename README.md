# Agentic AI Python Tutor System

Ein intelligenter KI-gestützter Python-Tutor, der Schüler beim Lernen, Debuggen und Üben unterstützt.

---

## Inhaltsverzeichnis

1. [Ziel des Projekts](#ziel-des-projekts)
2. [Projektstruktur](#projektstruktur)
3. [Datei-Erklärungen](#datei-erklärungen)
4. [Funktionen im Detail](#funktionen-im-detail)
5. [Datenfluss](#datenfluss)
6. [Installation und Start](#installation-und-start)
7. [API-Endpunkte](#api-endpunkte)
8. [Beispiel-Request und Response](#beispiel-request-und-response)

---

## Ziel des Projekts

Schüler scheitern oft beim Einstieg in Python, weil:
- Grundkonzepte wie Schleifen und Funktionen abstrakt wirken
- Fehlersuche ohne Hilfe viel Zeit kostet
- Lehrkräfte nicht jeden Schüler einzeln betreuen können
- Klassische Tools keine Personalisierung bieten

Dieses System löst das Problem mit einem **KI-Agenten**, der automatisch:
- Python-Code **erklärt** (Schritt für Schritt)
- **Fehler erkennt** und Lösungshinweise gibt
- **Übungsaufgaben generiert**, die zum aktuellen Lernstand passen

Der Kern ist ein **LangChain-Agent**, der bei jeder Anfrage die passenden Tools aufruft.

---

## Projektstruktur

```
/home/emad-almousa/src/test/KI/
│
├── README.md                  ← Diese Dokumentation
├── .gitignore
├── start.sh                   ← Startet Backend, Frontend und Ollama
│
└── backend/
    │
    ├── main.py                ← Einstiegspunkt — FastAPI App
    ├── requirements.txt       ← Python-Pakete
    ├── .env.example           ← Template für Konfiguration
    │
    ├── models/
    │   └── schemas.py         ← CodeRequest, TutorResponse, ChatRequest, ChatResponse
    │
    ├── agent/                 ← KI-Orchestrierung
    │   ├── config.py          ← LLM-Factory: get_llm(), get_classifier_llm()
    │   ├── tutor_agent.py     ← Orchestrator: run_analysis()
    │   └── tools/
    │       ├── explain_tool.py  ← Code erklären
    │       ├── debug_tool.py    ← Fehler analysieren
    │       └── exercise_tool.py ← Übung generieren
    │
    ├── services/
    │   ├── code_explainer.py  ← Adapter → run_analysis()
    │   └── debugger.py        ← Adapter → run_analysis()
    │
    ├── routers/
    │   └── tutor.py           ← Alle HTTP-Endpunkte
    │
    └── tests/
        ├── test_config.py     ← Tests: LLM-Factory
        ├── test_tools.py      ← Tests: alle Tools
        └── test_integration.py ← Tests: Endpoint + Orchestrator
```

---

## Datei-Erklärungen

### `backend/main.py`

```python
app = FastAPI(title="Agentic AI Python Tutor System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(tutor_router)
```

- CORS erlaubt dem Frontend (Port 3000) das Backend (Port 8000) anzusprechen
- `ServiceUnavailableError` → HTTP 503 (wenn LLM-Provider nicht erreichbar)
- Health-Check: `GET /` gibt `{"status": "ok"}` zurück

---

### `backend/models/schemas.py`

```python
class CodeRequest(BaseModel):
    code: str

class TutorResponse(BaseModel):
    explanation: str
    error_found: bool
    error_type: str = "Kein Fehler"
    suggestion: str
    next_exercise: str | None = None
```

---

### `backend/agent/config.py`

```python
def get_llm()            # OpenAI (gpt-4o) wenn Key vorhanden, sonst Ollama
def get_classifier_llm() # gpt-4o-mini oder Ollama — für Off-Topic-Filter
```

Einzige Stelle wo Provider gewählt wird. Alle Tools rufen `get_llm()` auf — kein Provider-Wissen im Tool selbst.

---

### `backend/agent/tutor_agent.py`

```python
def run_analysis(code: str) -> dict:
    llm = get_llm()
    tools = _build_tools()          # explain + debug + exercise
    agent = create_agent(llm, tools, system_prompt=_SYSTEM_PROMPT)
    result = agent.invoke({"messages": [("human", f"Analysiere: {code}")]})
    return _parse_agent_output(result["messages"][-1].content)
```

**ReAct-Agent** (`create_agent` aus LangChain 1.3.x / LangGraph): der Agent entscheidet selbst welche Tools er aufruft.
`_parse_agent_output()` extrahiert 5 Felder aus dem Free-Text der Final Answer (Regex, Safe Defaults).
Fängt Verbindungsfehler → `ServiceUnavailableError`.

---

### `backend/agent/tools/`

| Tool | Eingabe | Ausgabe | Was es macht |
|---|---|---|---|
| `explain_code_tool` | `code: str` | `str` | Schritt-für-Schritt-Erklärung auf Deutsch |
| `debug_code_tool` | `code: str` | `dict` | `{error_found, error_type, suggestion}` als JSON |
| `exercise_tool` | `code, error_found, suggestion` | `str` | Passende Übungsaufgabe |

---

### `backend/routers/tutor.py`

| Endpoint | Was er macht |
|---|---|
| `POST /tutor/analyze` | Code analysieren — ruft `run_analysis()` auf |
| `POST /tutor/run` | Code direkt ausführen (subprocess, kein LLM) |
| `POST /tutor/chat` | Chat mit History + Off-Topic-Filter |

---

## Funktionen im Detail

| Datei | Funktion | Eingabe | Ausgabe |
|---|---|---|---|
| `agent/config.py` | `get_llm()` | — | `ChatOpenAI` oder `ChatOllama` |
| `agent/tutor_agent.py` | `run_analysis(code)` | `str` | `dict` |
| `agent/tools/explain_tool.py` | `explain_code_tool(code)` | `str` | `str` |
| `agent/tools/debug_tool.py` | `debug_code_tool(code)` | `str` | `dict` |
| `agent/tools/exercise_tool.py` | `exercise_tool(code, error_found, suggestion)` | `str, bool, str` | `str` |
| `routers/tutor.py` | `analyze_code(request)` | `CodeRequest` | `TutorResponse` |

---

## Datenfluss

```
Browser / Frontend
        │
        │  POST /tutor/analyze  { "code": "..." }
        ▼
    routers/tutor.py → analyze_code(request)
        │
        └──► agent/tutor_agent.py → run_analysis(code)
                  │
                  ├──► create_agent(llm, tools)  ← ReAct-Agent (LangGraph)
                  │         │
                  │         │  ReAct-Loop (Reason → Act → Observe):
                  │         ├──► explain_code_tool  → LLM → Erklärung (str)
                  │         ├──► debug_code_tool    → LLM → {error_found, error_type, suggestion}
                  │         └──► exercise_tool      → LLM → Übungsaufgabe (str)
                  │
                  └──► _parse_agent_output(final_text) → dict mit 5 Feldern
        │
        ▼
    TutorResponse {
        explanation, error_found, error_type,
        suggestion, next_exercise
    }
```

---

## Installation und Start

### Voraussetzungen

**Option A — OpenAI (empfohlen):**
```bash
# backend/.env
OPENAI_API_KEY=sk-...
```

**Option B — Ollama (lokal, kostenlos):**
```bash
ollama pull llama3.2
```

### Start

```bash
# Schnellstart
./start.sh

# Oder manuell
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## API-Endpunkte

| Method | URL | Beschreibung |
|---|---|---|
| GET | `/` | Health Check |
| POST | `/tutor/analyze` | Code analysieren |
| POST | `/tutor/run` | Code direkt ausführen |
| POST | `/tutor/chat` | Chat mit dem Tutor |

**Swagger UI:** `http://127.0.0.1:8000/docs`

---

## Beispiel-Request und Response

**Analyse:**
```json
POST /tutor/analyze
{ "code": "for i in range(5)\n    print(i)" }
```

```json
{
  "explanation": "Dein Code hat ein Problem mit der Syntax...",
  "error_found": true,
  "error_type": "Syntaxfehler",
  "suggestion": "Fehlender Doppelpunkt ':' nach der for-Schleife.",
  "next_exercise": "🎯 Aufgabe: Korrigiere die Schleife..."
}
```
