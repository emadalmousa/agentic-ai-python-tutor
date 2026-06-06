# Agentic AI Python Tutor System

Ein intelligenter KI-gestützter Python-Tutor, der Schüler beim Lernen, Debuggen und Üben unterstützt.

---

## Inhaltsverzeichnis

1. [Ziel des Projekts](#ziel-des-projekts)
2. [Projektstruktur](#projektstruktur)
3. [Neue Features — Sprint 2](#neue-features--sprint-2)
4. [Datei-Erklärungen](#datei-erklärungen)
5. [Datenfluss](#datenfluss)
6. [Installation und Start](#installation-und-start)
7. [API-Endpunkte](#api-endpunkte)

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
- **Übungsaufgaben generiert** und bewertet (inkl. LLM-Feedback)
- Den **Lernfortschritt** pro Skill trackt (37 Skills, 3 Level)
- **PDF-Lernmaterial** einbindet und bei der Analyse berücksichtigt (RAG)
- **Skill-Tests** und **Level-Tests** automatisch generiert und auswertet

---

## Projektstruktur

```
/
├── README.md
├── start.sh                        ← Startet Backend + Frontend
│
├── backend/
│   ├── main.py                     ← FastAPI Einstiegspunkt — alle Router registriert
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── models/
│   │   ├── schemas.py              ← CodeRequest, TutorResponse, UploadResponse
│   │   ├── user.py                 ← User DB-Modell
│   │   ├── session.py              ← LearningSession DB-Modell
│   │   ├── skill_progress.py       ← StudentSkillProgress, LearningEvent, SKILL_TREE (37 Skills)
│   │   ├── exercise.py             ← ExerciseCompletion DB-Modell
│   │   ├── skill_test.py           ← SkillTestResult DB-Modell
│   │   └── level_test.py           ← LevelTestResult DB-Modell
│   │
│   ├── agent/
│   │   ├── config.py               ← LLM-Factory: get_llm(), get_embeddings()
│   │   ├── tutor_agent.py          ← ReAct-Agent: run_analysis()
│   │   ├── tools/
│   │   │   ├── explain_tool.py     ← Code erklären (Agent-Tool)
│   │   │   ├── debug_tool.py       ← Fehler analysieren (Agent-Tool)
│   │   │   ├── exercise_tool.py    ← Einfache Übung generieren (Agent-Tool)
│   │   │   ├── rag_tool.py         ← Lernmaterial durchsuchen (Agent-Tool)
│   │   │   ├── exercise_evaluator_tool.py  ← LLM bewertet Schüler-Lösung (direkt invoke)
│   │   │   ├── exercise_generator_tool.py  ← LLM generiert dynamische Übung (direkt invoke)
│   │   │   ├── hint_tool.py                ← Gestufter Hinweis Level 1–3 (direkt invoke)
│   │   │   ├── skill_test_generator_tool.py  ← LLM generiert Skill-Test (direkt invoke)
│   │   │   └── skill_test_evaluator_tool.py  ← LLM wertet Skill-Test aus (direkt invoke)
│   │   └── rag/
│   │       ├── loader.py           ← PDF → Text extrahieren (PyMuPDF)
│   │       ├── splitter.py         ← Text → Chunks (~500 Zeichen)
│   │       └── vectorstore.py      ← FAISS-Index: build/load/query/get_page
│   │
│   ├── services/
│   │   ├── skill_analyzer.py       ← LLM erkennt Skill + Score im Code (mit Fallback)
│   │   └── progress_service.py     ← get_or_create_skill_progress()
│   │
│   ├── data/
│   │   └── exercises.py            ← Statische Übungen für Beginner-Skills
│   │
│   ├── core/
│   │   ├── database.py             ← SQLAlchemy Engine + Session
│   │   ├── security.py             ← JWT: create_token, verify_token
│   │   └── code_runner.py          ← subprocess: Python-Code sicher ausführen
│   │
│   └── routers/
│       ├── tutor.py                ← /tutor/* (analyze, chat, run, upload-material)
│       ├── auth.py                 ← /auth/* (register, login, me)
│       ├── progress.py             ← /progress/* (sessions, summary)
│       ├── learning_progress.py    ← /learning-progress/* (skills, analyze, Fortschritt)
│       ├── exercises.py            ← /exercises/* (laden, submit, hint)
│       ├── skill_tests.py          ← /skill-tests/* (generate, submit)
│       ├── level_tests.py          ← /level-tests/* (generate, submit, status)
│       └── admin.py                ← /admin/* (Admin-Aktionen)
│
└── frontend/
    ├── app/
    │   ├── tutor/page.tsx          ← Tutor-Seite (Chat + Code-Editor)
    │   ├── progress/page.tsx       ← Lernfortschritt-Seite
    │   └── profile/page.tsx        ← Profil-Seite
    ├── components/
    │   ├── tutor/TutorView.tsx     ← Haupt-Layout Tutor
    │   ├── LearningProgressView.tsx← Skill-Liste + Detail-Panel
    │   ├── ExercisePanel.tsx       ← Übungs-UI
    │   ├── SkillTestModal.tsx      ← Skill-Test UI
    │   └── LevelTestModal.tsx      ← Level-Test UI
    └── lib/api.ts                  ← Alle API-Aufrufe zum Backend
```

---

## Neue Features — Sprint 2

### 1. PDF-Upload & RAG Pipeline

PDF als Lernmaterial hochladen — der Chat nutzt automatisch relevante Abschnitte.

```
POST /tutor/upload-material
  → PyMuPDF: Text pro Seite extrahieren
  → Splitter: ~500 Zeichen Chunks
  → LLM Embeddings (OpenAI oder Ollama)   ← LLM-Aufruf
  → FAISS-Index gespeichert (index.faiss + chunks.pkl)

Chat-Anfrage "erkläre Seite 5":
  → Regex erkennt Seitenzahl → get_page(5) direkt
  → + semantische FAISS-Suche
  → Chunks als Kontext in den System-Prompt injiziert
  → LLM antwortet mit Wissen aus dem PDF               ← LLM-Aufruf
```

### 2. Lernfortschritt & Skill-System

37 Skills in 3 Leveln. LLM erkennt Skill im Code und berechnet Score.

```
SKILL_TREE (models/skill_progress.py):
  Beginner (13):     Variablen → ... → Funktionen
  Intermediate (12): List Comprehension → ... → Map/Filter/Reduce
  Advanced (12):     Vererbung → ... → Testen

Score-Regeln:
  75–100 → "understood"      → Nächster Skill wird freigeschaltet (≥ 80)
  40–74  → "partial"
  0–39   → "not_understood"

Score-Update: neuer = alter × 0.7 + llm_score × 0.3  (gleitender Durchschnitt)
Fallback ohne LLM: Keyword-Matching (z.B. "for " → for_loop)
```

### 3. Übungen

5 Übungen pro Skill. Code wird ausgeführt und vom LLM bewertet.

```
POST /exercises/submit
  → Code ausführen (subprocess, Timeout 5s)
  → evaluate_exercise LLM-Tool (3 Fälle):     ← LLM-Aufruf
      Fall 1: stdout leer        → "falsch"
      Fall 2: stdout == expected → LLM prüft ob Konzept korrekt (nicht hardcodiert)
      Fall 3: stdout ≠ expected  → LLM: "teilweise" oder "falsch"

Score: richtig=20Pkt, teilweise=10Pkt, falsch=0Pkt
       5 Übungen × 20 = 100% Skill-Score
```

### 4. Skill-Tests

Wird freigeschaltet wenn alle 5 Übungen eines Skills abgeschlossen.

```
POST /skill-tests/generate
  → LLM generiert Test:                          ← LLM-Aufruf
      3 Multiple-Choice-Fragen
      1 Code-Lese-Aufgabe
      1 Mini-Aufgabe (Code schreiben)
  → Test serverseitig gespeichert (test_session_id)

POST /skill-tests/submit
  → MC: reiner String-Vergleich (kein LLM) → 30 Punkte max
  → Code-Lesen: LLM semantisch             → 30 Punkte max  ← LLM-Aufruf
  → Mini-Aufgabe: Code ausführen + LLM     → 40 Punkte max  ← LLM-Aufruf
  → Bestanden bei ≥ 60/100
```

### 5. Level-Tests

Wenn alle Skills eines Levels ≥ 80% Score haben.

```
POST /level-tests/generate  → LLM generiert Level-Test  ← LLM-Aufruf
POST /level-tests/submit    → LLM wertet aus            ← LLM-Aufrufe
```

### 6. Authentifizierung

```
POST /auth/register  → User erstellen, Passwort gehasht
POST /auth/login     → JWT Token zurück
GET  /auth/users/me  → Aktueller User
PATCH /auth/users/me → Profil aktualisieren (name, level, goal)
```

---

## Datei-Erklärungen

### `backend/agent/config.py`

```python
def get_llm():           # OpenAI gpt-4o wenn Key vorhanden, sonst Ollama llama3.2
def get_classifier_llm() # gpt-4o-mini oder Ollama — für Off-Topic-Filter im Chat
def get_embeddings()     # OpenAIEmbeddings oder OllamaEmbeddings — für RAG
```

Einzige Stelle wo Provider gewählt wird. Alle Tools rufen `get_llm()` auf.

### `backend/services/skill_analyzer.py`

```python
def analyze_skill(code, question) -> dict:
    # Versucht LLM → bei Fehler: Keyword-Fallback
    # LLM-Prompt fordert JSON: detected_skills, main_skill, score, status, mistakes, feedback
    # Whitelist: nur gültige skill_keys erlaubt
    # Fallback: _KEYWORD_MAP matcht z.B. "for " → for_loop, Score-Heuristik
```

### `backend/agent/tools/exercise_evaluator_tool.py`

LLM bewertet Schüler-Code in 3 Fällen:
1. **stdout leer** → direkt "falsch", LLM erklärt warum
2. **stdout == expected** → LLM prüft ob Konzept korrekt (nicht einfach hardcodiert)
3. **stdout ≠ expected** → LLM entscheidet "teilweise" oder "falsch"

### `backend/agent/tools/skill_test_evaluator_tool.py`

Scoring ohne LLM für MC (String-Vergleich) + mit LLM für Code-Lesen und Mini-Aufgabe:
- MC: 3 × 10 = 30 Punkte
- Code-Lesen: semantischer LLM-Vergleich = 30 Punkte
- Mini-Aufgabe: Code ausführen + LLM bewertet = 40 Punkte

---

## Datenfluss

### Code analysieren (Tutor)

```
Frontend → POST /tutor/analyze { code }
  → tutor_agent.run_analysis(code)
      → ReAct-Agent (LangChain):
          explain_code_tool  → LLM → Erklärung
          debug_code_tool    → LLM → {error_found, error_type, suggestion}
          exercise_tool      → LLM → Übungsaufgabe
          rag_tool           → FAISS → PDF-Stellen (wenn vorhanden)
      → _parse_agent_output() → 5 Felder
      → _get_rag_sources(code) → sources[]
  ← TutorResponse { explanation, error_found, error_type, suggestion, next_exercise, sources }
```

### Übung einreichen

```
Frontend → POST /exercises/submit { skill_key, exercise_id, code }
  → run_user_code(code) → subprocess → (stdout, stderr)
  → evaluate_exercise.invoke() → LLM → { result, what_was_good, what_went_wrong, hint }
  → ExerciseCompletion upsert → score_granted (0/10/20)
  → StudentSkillProgress.score = SUM(alle exercise scores)
  ← SubmitResponse { result, score_change, new_skill_score, ... }
```

---

## Installation und Start

**Option A — OpenAI:**
```bash
# backend/.env
OPENAI_API_KEY=sk-...
```

**Option B — Ollama (lokal):**
```bash
ollama pull llama3.2
```

**Start:**
```bash
./start.sh

# Oder manuell:
cd backend && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
# Frontend: cd frontend && npm run dev
```

---

## API-Endpunkte

| Method | URL | Auth | Beschreibung |
|---|---|---|---|
| GET | `/` | — | Health Check |
| POST | `/auth/register` | — | Registrieren |
| POST | `/auth/login` | — | Login → JWT Token |
| POST | `/tutor/analyze` | — | Code analysieren (ReAct-Agent) |
| POST | `/tutor/chat` | — | Chat mit RAG-Kontext |
| POST | `/tutor/upload-material` | — | PDF hochladen → FAISS |
| POST | `/tutor/run` | — | Code ausführen |
| GET | `/learning-progress/{id}` | ✓ | 37 Skills + Fortschritt |
| POST | `/learning-progress/analyze` | ✓ | Skill erkennen + Score |
| GET | `/exercises/{skill_key}` | ✓ | Übungen laden |
| POST | `/exercises/submit` | ✓ | Lösung einreichen → LLM bewertet |
| POST | `/exercises/hint` | ✓ | Gestufter Hinweis |
| POST | `/skill-tests/generate` | ✓ | Test generieren |
| POST | `/skill-tests/submit` | ✓ | Test einreichen + auswerten |
| POST | `/level-tests/generate` | ✓ | Level-Test generieren |
| POST | `/level-tests/submit` | ✓ | Level-Test auswerten |

**Swagger UI:** `http://127.0.0.1:8000/docs`
