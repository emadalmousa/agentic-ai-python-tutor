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
│
└── backend/                   ← Das gesamte Python-Backend
    │
    ├── main.py                ← Einstiegspunkt — FastAPI App starten
    ├── requirements.txt       ← Python-Pakete (fastapi, uvicorn, pydantic)
    │
    ├── models/                ← Datenstrukturen (was rein- und rausgeht)
    │   ├── __init__.py        ← Macht den Ordner zum Python-Paket
    │   └── schemas.py         ← CodeRequest und TutorResponse
    │
    ├── services/              ← Die eigentliche Logik / Fachfunktionen
    │   ├── __init__.py        ← Macht den Ordner zum Python-Paket
    │   ├── code_explainer.py  ← Funktion: Code erklären
    │   └── debugger.py        ← Funktion: Fehler im Code erkennen
    │
    └── routers/               ← API-Routen (URL-Endpunkte)
        ├── __init__.py        ← Macht den Ordner zum Python-Paket
        └── tutor.py           ← POST /tutor/analyze — Haupt-Endpunkt
```

**Warum diese Struktur?**
- `models/` beschreibt nur **was** — keine Logik, nur Datenformen
- `services/` enthält die **Logik** — unabhängig vom Web-Framework
- `routers/` verbindet **HTTP-Anfragen** mit den Services
- `main.py` ist nur der **Startpunkt** — so wenig Code wie möglich

Das macht es in Phase 2 einfach: Nur die Services werden ausgetauscht (Dummy → OpenAI/LangChain), der Rest bleibt identisch.

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

### `backend/services/code_explainer.py` — Code erklären

```python
def explain_code(code: str) -> str:
    lines = code.strip().splitlines()
    line_count = len(lines)
    return (
        f"Dein Code hat {line_count} Zeile(n). "
        "Ich analysiere ihn Schritt für Schritt: ..."
    )
```

**Was passiert hier:**
1. `code.strip()` — entfernt Leerzeichen am Anfang und Ende
2. `.splitlines()` — teilt den Code in eine Liste von Zeilen: `["for i in range(5):", "    print(i)"]`
3. `len(lines)` — zählt die Zeilen
4. Gibt eine Dummy-Erklärung zurück, die die Zeilenanzahl erwähnt

**Phase 1 → Phase 2 Übergang:**
Diese Funktion hat einen Kommentar: `# Phase 1 dummy — OpenAI/LangChain wird in Phase 2 hier eingebunden`
In Phase 2 wird die Rückgabe ersetzt durch einen echten OpenAI API-Aufruf. Der Rest des Systems ändert sich nicht — nur diese eine Funktion.

---

### `backend/services/debugger.py` — Fehler erkennen

```python
def debug_code(code: str) -> tuple[bool, str]:
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("for ") and not stripped.endswith(":"):
            return True, "Möglicher Syntaxfehler: Bei einer for-Schleife fehlt ein Doppelpunkt ':' am Ende."
        if stripped.startswith("if ") and not stripped.endswith(":"):
            return True, "Möglicher Syntaxfehler: Bei einer if-Bedingung fehlt ein Doppelpunkt ':' am Ende."

    if "print" not in code:
        return False, "Hinweis: Dein Code enthält keine Ausgabe mit print()."

    return False, "Kein offensichtlicher Fehler gefunden."
```

**Was passiert hier (Zeile für Zeile):**

1. Rückgabewert ist `tuple[bool, str]` — also immer zwei Werte: `(Fehler_gefunden, Nachricht)`
2. `code.splitlines()` — teilt den Code in Zeilen auf
3. `line.strip()` — entfernt Einrückungen (Tabs, Spaces) — wichtig, weil Zeilen oft mit 4 Spaces beginnen
4. **Regel 1:** Fängt eine Zeile mit `for ` an und endet NICHT mit `:` → Fehler gemeldet
5. **Regel 2:** Fängt eine Zeile mit `if ` an und endet NICHT mit `:` → Fehler gemeldet
6. **Regel 3:** Wenn `print` nirgends im Code vorkommt → Hinweis (kein Fehler, `error_found=False`)
7. Sonst: kein Problem gefunden

**Warum zeilenweise?**
Wenn wir nur `":" not in code` prüfen würden, würde ein Doppelpunkt in einer anderen Zeile (z.B. in einem Dictionary `{"key": "value"}`) die Prüfung kaputt machen. Die zeilenweise Prüfung ist präzise.

**Beispiele:**

| Code | error_found | suggestion |
|------|-------------|------------|
| `for i in range(5)\n    print(i)` | `true` | Doppelpunkt fehlt bei for |
| `if x > 5\n    print(x)` | `true` | Doppelpunkt fehlt bei if |
| `for i in range(5):\n    print(i)` | `false` | Kein Fehler |
| `x = 5` | `false` | Hinweis: kein print() |

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
    explanation = explain_code(request.code)
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
3. `explain_code(request.code)` wird aufgerufen → gibt eine Erklärung zurück
4. `debug_code(request.code)` wird aufgerufen → gibt `(bool, str)` zurück
5. Alles wird in ein `TutorResponse`-Objekt gepackt und als JSON zurückgeschickt
6. `response_model=TutorResponse` sorgt dafür, dass FastAPI die Antwort automatisch validiert

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
| `services/code_explainer.py` | `explain_code(code)` | `str` | `str` | Code erklären |
| `services/debugger.py` | `debug_code(code)` | `str` | `tuple[bool, str]` | Fehler finden |
| `routers/tutor.py` | `analyze_code(request)` | `CodeRequest` | `TutorResponse` | HTTP-Handler |
| `main.py` | `root()` | — | `dict` | Health Check |

---

## Datenfluss

So läuft eine Anfrage durch das System:

```
Browser / Postman / Frontend
        │
        │  POST /tutor/analyze
        │  { "code": "for i in range(5)\n    print(i)" }
        ▼
    main.py  (FastAPI empfängt die Anfrage)
        │
        │  leitet weiter an routers/tutor.py
        ▼
    routers/tutor.py  → analyze_code(request)
        │
        ├──► services/code_explainer.py → explain_code(code)
        │         → "Dein Code hat 2 Zeile(n)..."
        │
        └──► services/debugger.py → debug_code(code)
                  → (True, "Doppelpunkt fehlt bei for...")
        │
        │  Baut TutorResponse zusammen
        ▼
    Antwort an den Browser:
    {
      "explanation": "Dein Code hat 2 Zeile(n)...",
      "error_found": true,
      "suggestion": "Möglicher Syntaxfehler: Bei einer for-Schleife...",
      "next_exercise": "Schreibe eine for-Schleife..."
    }
```

---

## Installation und Start

```bash
# 1. In das Backend-Verzeichnis wechseln
cd /home/emad-almousa/src/test/KI/backend

# 2. Virtuelle Umgebung erstellen (einmalig)
python3 -m venv venv

# 3. Virtuelle Umgebung aktivieren
source venv/bin/activate

# 4. Abhängigkeiten installieren (einmalig)
pip install -r requirements.txt

# 5. Server starten
uvicorn main:app --reload
```

`--reload` bedeutet: Der Server startet automatisch neu, wenn du eine Datei änderst.

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

**Request:**
```json
POST http://127.0.0.1:8000/tutor/analyze
Content-Type: application/json

{
  "code": "for i in range(5)\n    print(i)",
  "question": "Warum funktioniert meine for-Schleife nicht?"
}
```

**Response:**
```json
{
  "explanation": "Dein Code hat 2 Zeile(n). Ich analysiere ihn Schritt für Schritt: Zunächst lese ich die Struktur, prüfe Einrückungen und Syntax. In Phase 2 übernimmt ein OpenAI/LangChain-Agent diese Erklärung und gibt dir eine detaillierte, personalisierte Antwort.",
  "error_found": true,
  "suggestion": "Möglicher Syntaxfehler: Bei einer for-Schleife fehlt ein Doppelpunkt ':' am Ende.",
  "next_exercise": "Schreibe eine for-Schleife, die die Zahlen von 1 bis 10 ausgibt."
}
```

---

## Sprint-Plan und Roadmap

### Sprint 1 — Basis (aktuell abgeschlossen)
- Projektstruktur erstellt
- FastAPI Backend mit CORS
- Pydantic Schemas (CodeRequest, TutorResponse)
- Dummy-Code-Erklärung
- Regelbasierter Debugger (zeilenweise)
- Swagger UI erreichbar

### Sprint 2 — KI-Integration
Was sich ändert:
- `services/code_explainer.py` → `explain_code()` wird durch echten OpenAI API-Aufruf ersetzt
- `services/debugger.py` → `debug_code()` wird durch LangChain-Tool ersetzt
- Neues Verzeichnis `agent/` mit `tutor_agent.py` und `tools/`
- Der LangChain-Agent entscheidet selbst, welches Tool er für eine Anfrage benutzt

### Sprint 3 — RAG + Memory
Was hinzukommt:
- `rag/` — PDFs hochladen, in Vector-DB speichern, bei Anfragen durchsuchen
- `memory/` — Lernfortschritt pro Schüler speichern (Stärken, Schwächen, abgeschlossene Übungen)
- Neue Endpunkte: `POST /upload-material`, `GET /progress/{user_id}`

---

## Definition of Done

### Phase 1
- [x] FastAPI-Backend startet fehlerfrei
- [x] `GET /` gibt `{"status": "ok"}` zurück
- [x] `POST /tutor/analyze` nimmt Code entgegen und gibt TutorResponse zurück
- [x] Debugger erkennt fehlenden Doppelpunkt bei `for` und `if` (zeilenweise)
- [x] Debugger gibt Hinweis wenn kein `print()` vorhanden
- [x] Swagger UI unter `/docs` erreichbar
- [ ] Code auf GitHub gepusht
- [ ] Peer Review abgeschlossen

### Gesamtprojekt (alle Sprints)
- [ ] Alle 5 Features funktionieren: Code erklären, Fehler erkennen, Übungen generieren, PDFs einbinden, Fortschritt speichern
- [ ] Alle API-Endpunkte dokumentiert
- [ ] Demo-Journey läuft fehlerfrei (Schüler fragt → Agent analysiert → Erklärung + Übung)
- [ ] Keine offenen Bugs im Sprint-Scope
- [ ] Peer Review abgeschlossen
