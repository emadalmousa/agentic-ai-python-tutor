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
- **PDF-Lernmaterial** einbindet und bei der Analyse berücksichtigt (RAG)

Der Kern ist ein **LangChain-Agent**, der bei jeder Anfrage die passenden Tools aufruft.

---

## Projektstruktur

```
/home/emad-almousa/src/test/KI/
│
├── README.md                  ← Diese Dokumentation
├── .gitignore
├── start.sh                   ← Startet Backend, Frontend und Ollama
├── dataflow.html              ← Visueller Datenfluss der App
│
└── backend/
    │
    ├── main.py                ← Einstiegspunkt — FastAPI App
    ├── requirements.txt       ← Python-Pakete
    ├── .env.example           ← Template für Konfiguration
    │
    ├── models/
    │   └── schemas.py         ← CodeRequest, TutorResponse, UploadResponse
    │
    ├── agent/                 ← KI-Orchestrierung
    │   ├── config.py          ← LLM-Factory: get_llm(), get_embeddings()
    │   ├── tutor_agent.py     ← Orchestrator: run_analysis()
    │   ├── tools/
    │   │   ├── explain_tool.py  ← Code erklären
    │   │   ├── debug_tool.py    ← Fehler analysieren
    │   │   ├── exercise_tool.py ← Übung generieren
    │   │   └── rag_tool.py      ← Lernmaterial durchsuchen (RAG)
    │   └── rag/
    │       ├── loader.py        ← PDF-Text extrahieren
    │       ├── splitter.py      ← Text in Chunks aufteilen
    │       └── vectorstore.py   ← FAISS-Index speichern/laden/suchen
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
    sources: list[str] = []        # RAG-Quellen (leer wenn kein PDF hochgeladen)

class UploadResponse(BaseModel):
    status: str
    chunks: int
```

---

### `backend/agent/config.py`

```python
def get_llm():          # OpenAI (gpt-4o) wenn Key vorhanden, sonst Ollama
def get_classifier_llm() # gpt-4o-mini oder Ollama — für Off-Topic-Filter
def get_embeddings()    # OpenAIEmbeddings oder OllamaEmbeddings — für RAG
```

Einzige Stelle wo Provider gewählt wird. Alle Tools rufen `get_llm()` auf — kein Provider-Wissen im Tool selbst.

---

### `backend/agent/tutor_agent.py`

```python
def run_analysis(code: str) -> dict:
    llm = get_llm()
    tools = _build_tools()          # explain + debug + exercise + rag_tool (wenn Index vorhanden)
    agent = create_agent(llm, tools, system_prompt=_SYSTEM_PROMPT)
    result = agent.invoke({"messages": [("human", f"Analysiere: {code}")]})
    parsed = _parse_agent_output(result["messages"][-1].content)
    parsed["sources"] = _get_rag_sources(code)
    return parsed
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
| `rag_tool` | `query: str` | `str` | Sucht relevante Stellen im hochgeladenen Lernmaterial |

---

### `backend/agent/rag/`

| Datei | Was sie macht |
|---|---|
| `loader.py` | Extrahiert Text aus PDF-Bytes (`pypdf`) |
| `splitter.py` | Teilt Text in Chunks (500 Zeichen, 50 Overlap) |
| `vectorstore.py` | FAISS-Index: `build_and_save()`, `load()`, `query()` |

Vektorstore wird in `backend/vectorstore/` gespeichert. Wenn kein PDF hochgeladen: `sources = []`.

---

### `backend/routers/tutor.py`

| Endpoint | Was er macht |
|---|---|
| `POST /tutor/analyze` | Code analysieren — ruft `run_analysis()` auf |
| `POST /tutor/upload-material` | PDF hochladen → FAISS-Index aufbauen |
| `POST /tutor/run` | Code direkt ausführen (subprocess, kein LLM) |
| `POST /tutor/chat` | Chat mit History + Off-Topic-Filter |

---

## Funktionen im Detail

| Datei | Funktion | Eingabe | Ausgabe |
|---|---|---|---|
| `agent/config.py` | `get_llm()` | — | `ChatOpenAI` oder `ChatOllama` |
| `agent/config.py` | `get_embeddings()` | — | `OpenAIEmbeddings` oder `OllamaEmbeddings` |
| `agent/tutor_agent.py` | `run_analysis(code)` | `str` | `dict` |
| `agent/tools/explain_tool.py` | `explain_code_tool(code)` | `str` | `str` |
| `agent/tools/debug_tool.py` | `debug_code_tool(code)` | `str` | `dict` |
| `agent/tools/exercise_tool.py` | `exercise_tool(code, error_found, suggestion)` | `str, bool, str` | `str` |
| `agent/tools/rag_tool.py` | `rag_tool(query)` | `str` | `str` |
| `agent/rag/vectorstore.py` | `build_and_save(chunks)` | `list[str]` | — |
| `agent/rag/vectorstore.py` | `query(index, text, top_k)` | — | `list[str]` |
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
                  │         ├──► exercise_tool      → LLM → Übungsaufgabe (str)
                  │         └──► rag_tool           → FAISS → PDF-Stellen (wenn vorhanden)
                  │
                  ├──► _parse_agent_output(final_text) → dict mit 5 Feldern
                  └──► _get_rag_sources(code) → sources: list[str]
        │
        ▼
    TutorResponse {
        explanation, error_found, error_type,
        suggestion, next_exercise, sources
    }
```

**PDF hochladen:**
```
POST /tutor/upload-material  (PDF-Datei)
    → loader.py: Text extrahieren
    → splitter.py: Text in Chunks aufteilen
    → vectorstore.py: FAISS-Index aufbauen + speichern
    → ab jetzt: sources in jeder /analyze-Antwort befüllt
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
| POST | `/tutor/upload-material` | PDF als Lernmaterial hochladen |
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
  "next_exercise": "🎯 Aufgabe: Korrigiere die Schleife...",
  "sources": ["Seite 12: Eine for-Schleife braucht einen Doppelpunkt..."]
}
```

**PDF hochladen:**
```bash
curl -X POST http://localhost:8000/tutor/upload-material \
  -F "file=@python_buch.pdf"
```

```json
{ "status": "ok", "chunks": 142 }
```
