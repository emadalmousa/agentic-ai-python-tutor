# Agentic AI Python Tutor System

Ein intelligenter KI-gestützter Python-Tutor, der Schüler beim Lernen, Debuggen und Üben unterstützt.

---

## Inhaltsverzeichnis

1. [Ziel des Projekts](#ziel-des-projekts)
2. [Projektstruktur](#projektstruktur)
3. [Datei-Erklärungen](#datei-erklärungen)
4. [Funktionen im Detail](#funktionen-im-detail)
5. [Datenfluss — Was passiert bei einer Anfrage?](#datenfluss)
6. [Installation und Start](#installation-und-start)
7. [API-Endpunkte](#api-endpunkte)
8. [Beispiel-Request und Response](#beispiel-request-und-response)
9. [Sprint-Plan und Roadmap](#sprint-plan-und-roadmap)
10. [Definition of Done](#definition-of-done)

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
- den **Lernfortschritt speichert** (ab Phase 3)

Der Kern ist ein **LangChain-Agent**, der bei jeder Anfrage selbst entscheidet, welches Tool er benutzt.

---

## Projektstruktur

```
/home/emad-almousa/src/test/KI/
│
├── README.md                  ← Diese Dokumentation
├── .gitignore                 ← Git ignoriert venv, __pycache__, .env etc.
├── start.sh                   ← Startet Backend, Frontend und Ollama (Phase 2+)
│
└── backend/                   ← Das gesamte Python-Backend
    │
    ├── main.py                ← Einstiegspunkt — FastAPI App starten
    ├── requirements.txt       ← Python-Pakete (fastapi, uvicorn, pydantic, langchain)
    ├── .env.example           ← Template für Konfiguration (Phase 2+)
    │
    ├── models/                ← Datenstrukturen (was rein- und rausgeht)
    │   ├── __init__.py        ← Macht den Ordner zum Python-Paket
    │   └── schemas.py         ← CodeRequest und TutorResponse
    │
    ├── services/              ← Die eigentliche Logik / Fachfunktionen
    │   ├── __init__.py        ← Macht den Ordner zum Python-Paket
    │   ├── code_explainer.py  ← Funktion: Code erklären (delegiert zu Agent)
    │   └── debugger.py        ← Funktion: Fehler im Code erkennen (delegiert zu Agent)
    │
    ├── agent/                 ← LLM-Orchestrierung (Phase 2+)
    │   ├── __init__.py        ← Macht den Ordner zum Python-Paket
    │   ├── config.py          ← LLM-Factory: get_llm() → ChatOllama
    │   ├── tutor_agent.py     ← Hauptorchestrator: run_analysis()
    │   └── tools/             ← LangChain Tools
    │       ├── __init__.py    ← Macht den Ordner zum Python-Paket
    │       ├── explain_tool.py  ← LangChain @tool: Code erklären mit Ollama
    │       └── debug_tool.py    ← LangChain @tool: Fehler analysieren mit Ollama
    │
    └── routers/               ← API-Routen (URL-Endpunkte)
        ├── __init__.py        ← Macht den Ordner zum Python-Paket
        └── tutor.py           ← POST /tutor/analyze — Haupt-Endpunkt
```

**Warum diese Struktur?**
- `models/` beschreibt nur **was** — keine Logik, nur Datenformen
- `services/` enthält die **Logik** — unabhängig vom Web-Framework
- `agent/` (Phase 2+) orchestriert LLM-Tools — trennt LLM-Concerns von HTTP-Concerns
- `routers/` verbindet **HTTP-Anfragen** mit den Services
- `main.py` ist nur der **Startpunkt** — so wenig Code wie möglich

Das macht es wartbar: Phase 1 hatte Dummy-Services. Phase 2 ändert nur `agent/` und Services (delegieren jetzt zur Agent-Orchestrierung). Router und Schemas bleiben identisch.

---

## Datei-Erklärungen

### `backend/main.py` — Einstiegspunkt der Anwendung

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.tutor import router as tutor_router

app = FastAPI(title="Agentic AI Python Tutor System")
```

- Erstellt die FastAPI-Anwendung mit einem Namen (erscheint in der Swagger UI)
- `FastAPI` ist das Web-Framework — ähnlich wie Flask, aber moderner und schneller

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

- **CORS** = Cross-Origin Resource Sharing
- Erlaubt dem Browser (z.B. React-Frontend auf Port 3000), das Backend auf Port 8000 anzusprechen
- `allow_origins=["*"]` erlaubt alle Quellen — in Produktion würde man nur die eigene Domain eintragen

```python
app.include_router(tutor_router)
```

- Bindet alle Routen aus `routers/tutor.py` ein
- Alle URLs die mit `/tutor/...` beginnen, werden dadurch registriert

```python
@app.get("/")
def root():
    return {"message": "Python Tutor Backend läuft", "status": "ok"}
```

- Einfacher Health-Check: Wenn du `http://127.0.0.1:8000` öffnest, siehst du ob das Backend läuft

---

### `backend/models/schemas.py` — Datenstrukturen

```python
class CodeRequest(BaseModel):
    code: str
    question: str | None = None
```

- **CodeRequest** ist das, was der Benutzer (Frontend/Postman) **schickt**
- `code: str` — der Python-Code, der analysiert werden soll (Pflichtfeld)
- `question: str | None = None` — optionale Frage des Schülers ("Warum funktioniert das nicht?")
- Pydantic validiert automatisch: Fehlt `code`, gibt FastAPI einen 422-Fehler zurück

```python
class TutorResponse(BaseModel):
    explanation: str
    error_found: bool
    suggestion: str
    next_exercise: str | None = None
```

- **TutorResponse** ist das, was das Backend **zurückschickt**
- `explanation` — die Erklärung des Codes
- `error_found` — `true` wenn ein Fehler gefunden wurde, sonst `false`
- `suggestion` — Hinweis oder Fehlerbeschreibung
- `next_exercise` — eine Übungsaufgabe (optional, kann `null` sein)

---

### `backend/services/code_explainer.py` — Code erklären (Phase 2+)

```python
def explain_code(code: str, question: str | None = None) -> str:
    result = run_analysis(code, question)
    return result["explanation"]
```

**Was passiert hier (Phase 2+):**
1. `run_analysis()` wird mit Code und optionaler Frage aufgerufen
2. Die Orchestrierung erfolgt jetzt im `agent/`-Paket — nicht hier
3. Diese Datei delegiert nur noch — sie ist ein **Adapter** zwischen HTTP-Anfrage und Agent

**Phase 1 → Phase 2 Änderung:**
- Phase 1: Dummy-Erklärung basierend auf Zeilenanzahl
- Phase 2: Echte LLM-Erklärung von Ollama über LangChain Tools
- Signatur erweitert: `explain_code(code, question)` — `question` wird jetzt weitergeleitet

---

### `backend/services/debugger.py` — Fehler erkennen (Phase 2+)

```python
def debug_code(code: str) -> tuple[bool, str]:
    result = run_analysis(code, None)
    return result["error_found"], result["suggestion"]
```

**Was passiert hier (Phase 2+):**
1. `run_analysis()` wird mit Code aufgerufen
2. Die LLM-gestützte Fehleranalyse erfolgt im `agent/`-Paket
3. Diese Datei extrahiert nur noch die Error-Felder — es ist ein **Adapter**

**Phase 1 → Phase 2 Änderung:**
- Phase 1: Regelbasierte zeilenweise Prüfung (hardcodierte Regeln für `for`, `if`, fehlenden Doppelpunkt)
- Phase 2: LLM-gestützte Analyse mit echtem Verständnis für Python-Fehler
- Rückgabewert bleibt identisch: `tuple[bool, str]`

---

### `backend/agent/config.py` — LLM-Konfiguration (Phase 2+)

```python
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

def get_llm() -> ChatOllama:
    load_dotenv()
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    return ChatOllama(base_url=base_url, model=model)
```

**Was passiert hier:**
1. `get_llm()` ist eine Factory-Funktion — sie erstellt eine `ChatOllama`-Verbindung
2. Umgebungsvariablen werden aus `.env` geladen (via `python-dotenv`)
3. `OLLAMA_BASE_URL` — standardmäßig `http://localhost:11434` (Ollama Standardport)
4. `OLLAMA_MODEL` — standardmäßig `llama3.2` (lokal bereitgestelltes Modell)
5. Tools rufen `get_llm()` auf — nicht hardcodiert, konfigurierbar

**Warum so?**
- Zentrale Stelle für LLM-Konfiguration
- Einfach zu testen (Mock `get_llm()`)
- Einstellungen ohne Code-Änderung möglich (nur `.env` editieren)

---

### `backend/agent/tutor_agent.py` — Orchestrator (Phase 2+)

```python
from agent.tools.explain_tool import explain_code_tool
from agent.tools.debug_tool import debug_code_tool

class ServiceUnavailableError(Exception):
    """Raised when Ollama is unreachable."""
    pass

def run_analysis(code: str, question: str | None = None) -> dict:
    """
    Orchestriert beide Tools und gibt ein einheitliches Ergebnis zurück.
    
    Returns:
        {
            "explanation": str,
            "error_found": bool,
            "suggestion": str
        }
    
    Raises:
        ServiceUnavailableError: wenn Ollama nicht erreichbar ist
    """
    try:
        explanation = explain_code_tool.invoke({"code": code, "question": question})
        error_found, suggestion = debug_code_tool.invoke({"code": code})
        
        return {
            "explanation": explanation,
            "error_found": error_found,
            "suggestion": suggestion
        }
    except ConnectionError as e:
        raise ServiceUnavailableError(f"Ollama nicht erreichbar: {e}")
```

**Was passiert hier:**
1. `run_analysis()` ist der zentrale Einstiegspunkt für alle KI-Anfragen
2. Ruft beide Tools auf (Erklärung + Debugging)
3. Gibt ein einheitliches Dict zurück — alle Services nutzen das gleiche Format
4. Wirft `ServiceUnavailableError` wenn Ollama nicht erreichbar ist (wird in `main.py` zu HTTP 503)

**Warum so?**
- Einheitliche Schnittstelle: Services brauchen nur diesen einen Aufruf
- Fehlerbehandlung: `ServiceUnavailableError` unterscheidet Offline-Ollama von Programmierfehlern
- Später erweiterbar: Agent könnte ReAct-Pattern nutzen (Phase 3)

---

### `backend/agent/tools/explain_tool.py` — Code-Erklärung Tool (Phase 2+)

```python
from langchain.tools import tool
from agent.config import get_llm

@tool
def explain_code_tool(code: str, question: str | None = None) -> str:
    """
    Erklärt Python-Code auf Deutsch, Schritt für Schritt.
    
    Args:
        code: Der zu erklärende Python-Code
        question: Optionale Frage des Schülers (z.B. "Warum funktioniert das nicht?")
    
    Returns:
        Deutsch-sprachige Erklärung des Codes
    """
    llm = get_llm()
    system_prompt = "Du bist ein freundlicher Python-Tutor. Erkläre Code auf Deutsch, Schritt für Schritt."
    
    user_message = f"Erkläre diesen Code:\n\n{code}"
    if question:
        user_message += f"\n\nFrage des Schülers: {question}"
    
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ])
    
    return response.content
```

**Was passiert hier:**
1. `@tool` macht diese Funktion zu einem LangChain-Tool
2. Holt LLM-Instanz via `get_llm()` (mit Ollama-Verbindung)
3. Baut Prompt auf: System-Nachricht + Schüler-Code + optionale Frage
4. Ruft LLM auf und gibt die Antwort zurück
5. Alle Prompts sind **auf Deutsch** — für deutsche Schüler

---

### `backend/agent/tools/debug_tool.py` — Fehleranalyse Tool (Phase 2+)

```python
from langchain.tools import tool
from agent.config import get_llm
import json

@tool
def debug_code_tool(code: str) -> tuple[bool, str]:
    """
    Analysiert Python-Code auf Fehler mit dem LLM.
    
    Returns:
        (error_found: bool, suggestion: str)
    """
    llm = get_llm()
    system_prompt = "Du bist ein Python-Debugger. Antworte IMMER mit validem JSON: {\"error_found\": bool, \"suggestion\": str}"
    
    user_message = f"Analysiere diesen Code auf Fehler:\n\n{code}"
    
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ])
    
    # Robust JSON parsing
    try:
        result_text = response.content.strip()
        # Strip markdown code fences if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        
        data = json.loads(result_text)
        return data.get("error_found", False), data.get("suggestion", "Analyse nicht möglich.")
    except (json.JSONDecodeError, AttributeError):
        # Fallback wenn LLM kein gültiges JSON zurückgibt
        return False, "Analyse nicht möglich."
```

**Was passiert hier:**
1. `@tool` macht diese Funktion zu einem LangChain-Tool
2. Explizite JSON-Anforderung im System-Prompt — nicht lassen
3. Robust JSON-Parsing: LLMs wrappen JSON oft in Markdown-Code-Fences
4. Fallback: Wenn Parsing fehlschlägt, `error_found=False` statt Crash
5. Gibt `tuple[bool, str]` zurück — kompatibel mit altem `debug_code()`

---

### `backend/.env.example` — Konfigurationsvorlage (Phase 2+)

```
# Ollama LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Verwendung:**
1. Kopiere diese Datei zu `.env`: `cp backend/.env.example backend/.env`
2. Editiere `.env` nach Bedarf (normalerweise nicht nötig für lokale Entwicklung)
3. `.env` wird von `agent/config.py` geladen und ist in `.gitignore` (niemals committen!)

---

### `backend/routers/tutor.py` — API-Endpunkt

```python
router = APIRouter(prefix="/tutor", tags=["Tutor"])
```

- `prefix="/tutor"` — alle Routen in dieser Datei beginnen mit `/tutor`
- `tags=["Tutor"]` — Gruppenname in der Swagger UI

```python
NEXT_EXERCISE = "Schreibe eine for-Schleife, die die Zahlen von 1 bis 10 ausgibt."
```

- Konstante für die nächste Übung — in Phase 3 wird das dynamisch aus dem Lernfortschritt des Schülers generiert

```python
@router.post("/analyze", response_model=TutorResponse)
def analyze_code(request: CodeRequest) -> TutorResponse:
    explanation = explain_code(request.code, request.question)  # Phase 2+: question weitergeleitet
    error_found, suggestion = debug_code(request.code)
    return TutorResponse(
        explanation=explanation,
        error_found=error_found,
        suggestion=suggestion,
        next_exercise=NEXT_EXERCISE,
    )
```

**Was passiert hier:**
1. FastAPI empfängt einen `POST /tutor/analyze` Request
2. Der JSON-Body wird automatisch in ein `CodeRequest`-Objekt umgewandelt (Pydantic)
3. `explain_code(request.code, request.question)` wird aufgerufen (Phase 2+: `question` wird mitgegeben)
4. `debug_code(request.code)` wird aufgerufen → gibt `(bool, str)` zurück
5. Alles wird in ein `TutorResponse`-Objekt gepackt und als JSON zurückgeschickt
6. `response_model=TutorResponse` sorgt dafür, dass FastAPI die Antwort automatisch validiert

**Phase 2+ Änderung:**
- Vorher: `explain_code(request.code)` — `question` wurde ignoriert
- Jetzt: `explain_code(request.code, request.question)` — `question` fließt zum LLM

---

### `backend/requirements.txt` — Abhängigkeiten

```
fastapi        ← Das Web-Framework
uvicorn[standard]  ← Der ASGI-Server (startet FastAPI)
pydantic       ← Datenvalidierung (wird auch von FastAPI intern genutzt)
```

`uvicorn[standard]` ist der Server, der die FastAPI-App ausführt — ähnlich wie Apache/Nginx, aber für Python.

---

### `.gitignore` — Was Git ignoriert

Folgendes wird **nicht** ins Repository hochgeladen:
- `venv/` und `.venv/` — die virtuelle Python-Umgebung (zu groß, jeder installiert sie selbst)
- `__pycache__/` und `*.pyc` — kompilierte Python-Dateien (automatisch generiert)
- `.env` — API-Keys und Passwörter (niemals ins Repo!)
- `.vscode/`, `.idea/` — IDE-Einstellungen (persönlich, nicht projektrelevant)

---

## Funktionen im Detail

| Datei | Funktion | Eingabe | Ausgabe | Zweck |
|---|---|---|---|---|
| `agent/config.py` | `get_llm()` | — | `ChatOllama` | LLM-Verbindung (Phase 2+) |
| `agent/tutor_agent.py` | `run_analysis(code, question)` | `str, str\|None` | `dict` | Orchest. beide Tools (Phase 2+) |
| `agent/tools/explain_tool.py` | `explain_code_tool(code, question)` | `str, str\|None` | `str` | LLM-Erklärung (Phase 2+) |
| `agent/tools/debug_tool.py` | `debug_code_tool(code)` | `str` | `tuple[bool, str]` | LLM-Fehleranalyse (Phase 2+) |
| `services/code_explainer.py` | `explain_code(code, question)` | `str, str\|None` | `str` | Delegiert an Agent (Phase 2+) |
| `services/debugger.py` | `debug_code(code)` | `str` | `tuple[bool, str]` | Delegiert an Agent (Phase 2+) |
| `routers/tutor.py` | `analyze_code(request)` | `CodeRequest` | `TutorResponse` | HTTP-Handler |
| `main.py` | `root()` | — | `dict` | Health Check |

---

## Datenfluss

So läuft eine Anfrage durch das System (Phase 2+):

```
Browser / Postman / Frontend
        │
        │  POST /tutor/analyze
        │  { "code": "for i in range(5)\n    print(i)", "question": "Warum fehlt das?" }
        ▼
    main.py  (FastAPI empfängt die Anfrage)
        │
        │  leitet weiter an routers/tutor.py
        ▼
    routers/tutor.py  → analyze_code(request)
        │
        ├──► services/code_explainer.py → explain_code(code, question)
        │         │
        │         └──► agent/tutor_agent.py → run_analysis(code, question)
        │                   │
        │                   └──► agent/tools/explain_tool.py
        │                         → ChatOllama → Ollama Server
        │                         → "Dein Code hat eine for-Schleife, aber..."
        │
        └──► services/debugger.py → debug_code(code)
                  │
                  └──► agent/tutor_agent.py → run_analysis(code, question)
                        │
                        └──► agent/tools/debug_tool.py
                              → ChatOllama → Ollama Server
                              → {"error_found": true, "suggestion": "..."}
        │
        │  Baut TutorResponse zusammen
        ▼
    Antwort an den Browser:
    {
      "explanation": "Dein Code hat eine for-Schleife, die über Zahlen von 0 bis 4 iteriert...",
      "error_found": true,
      "suggestion": "Fehler gefunden: for-Schleife fehlt ein Doppelpunkt ':' am Ende der Zeile",
      "next_exercise": "Schreibe eine for-Schleife..."
    }
```

**Phase 1 → Phase 2 Unterschied:**
- Phase 1: Services geben statische Dummy-Werte zurück
- Phase 2: Services delegieren an `agent/`, der echte LLM-Ausgaben von Ollama orchestriert

---

## Installation und Start

### Voraussetzungen (Phase 2+)

1. **Ollama installieren** — kostenlos von https://ollama.ai
   ```bash
   # Nach Installation das Modell herunterladen (einmalig, ca. 5 GB)
   ollama pull llama3.2
   ```

2. **Python 3.12+** — für LangChain und Dependencies

### Schnellstart mit `start.sh` (empfohlen, Phase 2+)

```bash
cd /home/emad-almousa/src/test/KI

# Alles starten: Ollama + Backend + Frontend
./start.sh

# Mit Ctrl+C stoppen — alle Prozesse werden sauber beendet
```

`start.sh` kümmert sich um:
- Ollama Lifecycle (startet/stoppt den Server)
- Backend-Activation (venv + requirements)
- Frontend-Start (falls vorhanden)

### Manuelle Installation (Entwicklung)

```bash
# 1. In das Backend-Verzeichnis wechseln
cd /home/emad-almousa/src/test/KI/backend

# 2. Virtuelle Umgebung erstellen (einmalig)
python3 -m venv venv

# 3. Virtuelle Umgebung aktivieren
source venv/bin/activate

# 4. Abhängigkeiten installieren (einmalig)
pip install -r requirements.txt

# 5. .env-Datei erstellen (einmalig)
cp .env.example .env
# Optional: Editiere .env falls Ollama nicht auf localhost:11434 läuft

# 6. Backend-Server starten
uvicorn main:app --reload
```

**Wichtig:**
- `--reload` bedeutet: Der Server startet automatisch neu, wenn du eine Datei änderst
- Phase 2+: Ollama muss bereits laufen (`ollama serve`) oder in separatem Terminal gestartet sein
- Erste LLM-Anfrage dauert länger (Modell wird geladen)

---

## API-Endpunkte

| Method | URL | Beschreibung |
|--------|-----|--------------|
| GET | `/` | Health Check — ist das Backend erreichbar? |
| POST | `/tutor/analyze` | Code analysieren — Hauptfunktion |

**Swagger UI (interaktive Dokumentation):** `http://127.0.0.1:8000/docs`

Dort kannst du alle Endpunkte direkt im Browser testen, ohne Postman oder curl.

---

## Beispiel-Request und Response

**Request (Phase 2+):**
```json
POST http://127.0.0.1:8000/tutor/analyze
Content-Type: application/json

{
  "code": "for i in range(5)\n    print(i)",
  "question": "Warum funktioniert meine for-Schleife nicht?"
}
```

**Response (Phase 2+ — echte LLM-Antwort von Ollama):**
```json
{
  "explanation": "Hallo! Dein Code hat ein Problem mit der Syntax. Die for-Schleife in Python erfordert einen Doppelpunkt (:) am Ende der Zeile, bevor der eingerückte Code-Block beginnt.\n\nDein Code:\n```\nfor i in range(5)\n    print(i)\n```\n\nSollte so aussehen:\n```\nfor i in range(5):\n    print(i)\n```\n\nDie for-Schleife iteriert über die Zahlen 0, 1, 2, 3, 4 und gibt jede davon mit print() aus.\n\nDeine Frage war 'Warum funktioniert meine for-Schleife nicht?' — genau das ist der Grund: der fehlende Doppelpunkt nach `range(5)`.",
  "error_found": true,
  "suggestion": "Syntaxfehler: for-Schleife fehlt ein Doppelpunkt ':' nach der Schleifenkopfzeile.",
  "next_exercise": "Schreibe eine for-Schleife, die die Zahlen von 1 bis 10 ausgibt."
}
```

**Hinweis zu Phase 1 vs Phase 2:**
- **Phase 1**: `explanation` war ein statischer Dummy-Text ("Dein Code hat 2 Zeile(n)...")
- **Phase 2+**: `explanation` ist eine echte, von Ollama generierte, deutsch-sprachige Erklärung
- Die `question` fließt jetzt in die LLM-Prompt ein und wird berücksichtigt

---

## Sprint-Plan und Roadmap

### Sprint 1 — Basis (abgeschlossen ✅)
- [x] Projektstruktur erstellt
- [x] FastAPI Backend mit CORS
- [x] Pydantic Schemas (CodeRequest, TutorResponse)
- [x] Dummy-Code-Erklärung
- [x] Regelbasierter Debugger (zeilenweise)
- [x] Swagger UI erreichbar

### Sprint 2 — KI-Integration (abgeschlossen ✅)
- [x] Ollama-Integration via LangChain
- [x] Neues Verzeichnis `backend/agent/` mit `config.py`, `tutor_agent.py`, `tools/`
- [x] LangChain Tools: `explain_code_tool` und `debug_code_tool`
- [x] Services delegieren an `agent/tutor_agent.py`
- [x] `question`-Feld wird jetzt ans LLM weitergeleitet
- [x] `.env`-Konfiguration (OLLAMA_BASE_URL, OLLAMA_MODEL)
- [x] `start.sh` mit Ollama-Lifecycle-Management
- [x] HTTP 503 Handler wenn Ollama nicht erreichbar

### Sprint 3 — RAG + Memory (geplant 🔄)
Was hinzukommt:
- [ ] `rag/` — PDFs hochladen, in Vector-DB speichern, bei Anfragen durchsuchen
- [ ] `memory/` — Lernfortschritt pro Schüler speichern (Stärken, Schwächen, abgeschlossene Übungen)
- [ ] Neue Endpunkte: `POST /upload-material`, `GET /progress/{user_id}`
- [ ] ReAct-Agent-Pattern (Agent entscheidet selbst, welche Tools er braucht)

---

## Definition of Done

### Phase 1 ✅
- [x] FastAPI-Backend startet fehlerfrei
- [x] `GET /` gibt `{"status": "ok"}` zurück
- [x] `POST /tutor/analyze` nimmt Code entgegen und gibt TutorResponse zurück
- [x] Debugger erkennt fehlenden Doppelpunkt bei `for` und `if` (zeilenweise)
- [x] Debugger gibt Hinweis wenn kein `print()` vorhanden
- [x] Swagger UI unter `/docs` erreichbar

### Phase 2 ✅
- [x] Ollama erfolgreich integriert (LangChain + ChatOllama)
- [x] `backend/agent/` Verzeichnis mit config, tutor_agent, tools erstellt
- [x] `explain_code_tool` gibt echte LLM-Erklärung zurück (auf Deutsch)
- [x] `debug_code_tool` gibt gültiges JSON zurück: `{"error_found": bool, "suggestion": str}`
- [x] Services delegieren an `agent/run_analysis()`
- [x] `question`-Parameter wird durch die Call-Chain weitergeleitet zum LLM
- [x] `.env` mit OLLAMA_BASE_URL und OLLAMA_MODEL
- [x] `start.sh` startet/stoppt Ollama korrekt
- [x] HTTP 503 Handler bei Ollama-Ausfall implementiert
- [x] README aktualisiert mit Phase 2 Inhalten

### Gesamtprojekt (alle Sprints)
- [ ] Alle 5 Features funktionieren: Code erklären ✅, Fehler erkennen ✅, Übungen generieren, PDFs einbinden, Fortschritt speichern
- [ ] Alle API-Endpunkte dokumentiert
- [ ] Demo-Journey läuft fehlerfrei (Schüler fragt → Agent analysiert → Erklärung + Übung)
- [ ] Keine offenen Bugs im Sprint-Scope
- [ ] Code auf GitHub gepusht
- [ ] Peer Review abgeschlossen
