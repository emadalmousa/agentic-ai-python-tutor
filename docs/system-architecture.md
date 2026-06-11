# KI Python Tutor — Vollständige System-Dokumentation

## Inhaltsverzeichnis
1. [Überblick](#überblick)
2. [Feature: PDF-Upload & RAG](#feature-pdf-upload--rag)
3. [Feature: Lernfortschritt (Learning Progress)](#feature-lernfortschritt-learning-progress)
4. [Feature: Übungen (Exercises)](#feature-übungen-exercises)
5. [Feature: Skill-Tests](#feature-skill-tests)
6. [Feature: Level-Tests](#feature-level-tests)
7. [Feature: Profil (Profile)](#feature-profil-profile)
8. [LangChain / LLM — wo und wie](#langchain--llm--wo-und-wie)
9. [Datenbank-Modelle](#datenbank-modelle)
10. [Vollständiger Datenfluss: Übung einreichen](#vollständiger-datenfluss-übung-einreichen)
11. [Vollständiger Datenfluss: Skill-Test](#vollständiger-datenfluss-skill-test)

---

## Überblick

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js, Port 3000)                             │
│                                                             │
│  /tutor      → TutorView  (Chat + Code-Editor)             │
│  /progress   → LearningProgressView  (Skills + Übungen)    │
│  /profile    → ProfileView  (Nutzerprofil)                  │
└──────────────────┬──────────────────────────────────────────┘
                   │  HTTP / JSON (Bearer Token)
┌──────────────────▼──────────────────────────────────────────┐
│  BACKEND  (FastAPI, Port 8000)                              │
│                                                             │
│  Routers:                                                   │
│    /tutor            → Analyse, Chat, Code ausführen        │
│    /learning-progress→ Skill-Fortschritt, Skill-Analyse     │
│    /exercises        → Übungen laden, einreichen, Hinweis   │
│    /skill-tests      → Skill-Test generieren/auswerten      │
│    /level-tests      → Level-Test generieren/auswerten      │
│    /auth             → Login, Register, Token               │
│    /progress         → Sessions (älteres System)            │
└──────────────────┬──────────────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  LangChain / LLM   │
         │                    │
         │  OpenAI (bevorzugt)│
         │  Ollama (Fallback) │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  PostgreSQL-DB     │
         │  (pgvector)        │
         │                    │
         │  users             │
         │  learning_sessions │
         │  student_skill_p.. │
         │  learning_events   │
         │  exercise_comp..   │
         │  skill_test_res..  │
         │  level_test_res..  │
         └────────────────────┘
```

---

## Feature: PDF-Upload & RAG

### Was ist das?
Der Nutzer (oder Admin) kann ein PDF-Lernmaterial hochladen. Das System zerlegt den Inhalt in Text-Chunks, erstellt daraus Vektor-Embeddings und speichert sie in einem FAISS-Index. Bei Code-Analysen kann der Tutor-Agent daraus relevante Abschnitte abrufen.

### Datenfluss

```
Nutzer wählt PDF-Datei
         │
         ▼
Frontend: uploadMaterial(file)          [lib/api.ts:74]
         │  POST /tutor/upload-material
         │  multipart/form-data
         ▼
Backend: routers/tutor.py → upload_material()
         │
         ▼
agent/rag/loader.py → extract_pages(file_bytes)
         │  pypdf: extrahiert Text seitenweise
         │  Gibt liste[(text, page_number)] zurück
         ▼
agent/rag/splitter.py → split_chunks(pages)
         │  Teilt langen Text in 500-Zeichen-Chunks
         │  Behält Seiten-Nummer pro Chunk
         ▼
agent/rag/vectorstore.py → build_and_save(chunks, user_id)
         │
         ├── get_embeddings()            [config.py]
         │       ├── OpenAI: text-embedding-ada-002  ← LLM-AUFRUF
         │       └── Ollama: embed_documents()        ← LLM-AUFRUF
         │
         └── PGVector.from_texts(texts, embeddings, metadatas)
         │   → speichert Vektoren in PostgreSQL, collection: "user_{id}"
         │   (kein Filesystem, kein Datenverlust bei Redeploy)
         │
         ▼
Response: { status: "ok", chunks: 42 }
```

### RAG-Abfrage im Chat

```
POST /tutor/chat
         │
         ▼
_get_rag_context(message, current_user.id)   [tutor.py]
         │
         ├── load(user_id)                   # lädt pgvector-Collection aus PostgreSQL
         │       → None wenn kein PDF hochgeladen
         │
         ├── Regex: Seitenzahl in Nachricht? → get_page(index_data, page_num)
         │
         └── pgvector semantische Suche: query_with_pages(index_data, message, top_k=3)
         │
         ▼
wenn rag_context vorhanden:
  run_chat_with_context()              [tutor_agent.py]
         │  → direkter llm.invoke([system, human])
         │  → kein Agent, kein ReAct-Loop
         │  → PDF-Chunks eingebettet im Prompt
         ▼
wenn kein rag_context:
  run_chat()                           [tutor_agent.py]
         │  → ReAct-Agent mit 5 Tools
```

### Schlüsseldateien
| Datei | Funktion |
|---|---|
| `backend/agent/rag/loader.py` | PDF → Seiten-Text |
| `backend/agent/rag/splitter.py` | Text → Chunks |
| `backend/agent/rag/vectorstore.py` | pgvector-Index bauen/laden/abfragen |
| `backend/agent/config.py` | `get_embeddings()` — OpenAI oder Ollama |
| `backend/agent/tools/rag_tool.py` | LangChain-Tool, das der Agent aufrufen kann |

---

## Feature: Lernfortschritt (Learning Progress)

### Was ist das?
Jeder Nutzer hat einen Fortschrittswert (0–100%) pro Skill. 37 Skills sind in drei Level aufgeteilt. Skills werden durch Übungen freigeschaltet. Der Fortschritt basiert auf abgeschlossenen Übungen.

### Skill-Baum
```
Beginner (13 Skills):
  Variablen → Datentypen → Eingabe/Ausgabe → ... → Funktionen

Intermediate (12 Skills):
  List Comprehension → Fehlerbehandlung → ... → Map/Filter/Reduce

Advanced (12 Skills):
  Vererbung → Polymorphismus → ... → Testen
```
Unlock-Regel: Ein Skill wird freigeschaltet wenn der vorherige Skill **Score ≥ 80** hat.

### Datenfluss: Fortschritt laden

```
LearningProgressView (Mount)            [LearningProgressView.tsx:260]
         │
         ├── getLearningProgress(userId, token)     [api.ts:48]
         │        GET /learning-progress/{student_id}
         │
         ▼
Backend: learning_progress.py → get_progress()    [learning_progress.py:167]
         │
         ▼
_build_progress_response(user_id, db)             [learning_progress.py:71]
         │
         ├── Lädt alle StudentSkillProgress-Rows für diesen User aus DB
         │       SELECT * FROM student_skill_progress WHERE user_id = ?
         │
         ├── Für jeden der 37 Skills (FIXED_SKILLS):
         │       - Holt score und status aus DB (Default: 0 / not_understood)
         │       - Berechnet is_unlocked:
         │           unlocks_after == None → immer freigeschaltet
         │           sonst: predecessor.score >= 80
         │       - Bestimmt level (beginner/intermediate/advanced)
         │       - Bestimmt order (Position innerhalb des Levels)
         │
         ├── overall_score = Durchschnitt aller Skill-Scores
         │
         ├── user_status:
         │       alle Skills 100% → "Profi"
         │       alle Beginner ≥ 80% → "Fortgeschritten"
         │       sonst → "Anfänger"
         │
         └── recent_events: letzte 5 LearningEvent-Rows
         │
         ▼
Response: ProgressResponse {
  student_id, overall_score, skills[37], recent_events[5], user_status
}
         │
         ▼
Frontend: setProgress(data)
         │
         ├── Zeigt Ring-Diagramm mit overall_score
         ├── Zeigt Level-Tabs (Beginner / Intermediate / Advanced)
         ├── Zeigt SkillListItem pro Skill (mit Balken + Prozent)
         └── Bei Skill-Auswahl: SkillDetail mit Übungsfortschritt
```

### Datenfluss: Skill analysieren (aus Tutor-Sicht)

```
Nutzer schreibt Code im Tutor → Klick "Analysieren"
         │
         ├── analyzeSkill({ code, question }, token)  [api.ts:56]
         │        POST /learning-progress/analyze
         │
         ▼
Backend: analyze_and_save()                          [learning_progress.py:180]
         │
         ▼
services/skill_analyzer.py → analyze_skill(code, question)
         │
         ├── Versucht LLM-Analyse:
         │       get_llm().invoke([SystemMessage, HumanMessage])   ← LLM-AUFRUF
         │
         │       System-Prompt:
         │         "Gib NUR gültiges JSON zurück mit:
         │          detected_skills, main_skill, score (0-100),
         │          status, mistakes, feedback, recommended_next_exercise"
         │
         │       _parse_llm_json(response):
         │         - Entfernt Markdown-Wrapper
         │         - Validiert skill_keys gegen Whitelist (37 gültige Keys)
         │         - Begrenzt score auf 0-100
         │
         └── Bei LLM-Fehler: _rule_based_analysis()
                 - Keyword-Matching (z.B. "for " → for_loop)
                 - Heuristik-Score (Syntaxfehler → 35, sonst → 60)
         │
         ▼
Zurück in analyze_and_save():
         │
         ├── StudentSkillProgress aktualisieren:
         │       Neuer Score = alter_score * 0.7 + neuer_score * 0.3
         │       (gleitender Durchschnitt — Lernfortschritt bleibt stabil)
         │
         ├── LearningEvent erstellen (unveränderliche History):
         │       INSERT INTO learning_events (user_id, skill_key, score, ...)
         │
         └── _build_progress_response() für aktuellen Stand
```

### Schlüsseldateien
| Datei | Funktion |
|---|---|
| `backend/models/skill_progress.py` | DB-Modelle: StudentSkillProgress, LearningEvent, SKILL_TREE |
| `backend/routers/learning_progress.py` | API-Endpunkte + Logik |
| `backend/services/skill_analyzer.py` | LLM-Skill-Erkennung + Fallback |
| `frontend/components/LearningProgressView.tsx` | Haupt-UI: Skill-Liste, Detail-Panel |

---

## Feature: Übungen (Exercises)

### Was ist das?
Pro Skill gibt es 5 Übungsaufgaben. Der Nutzer schreibt Code, klickt "Einreichen". Das Backend führt den Code aus und lässt das LLM die Lösung bewerten. Jede korrekte Übung gibt 20 Punkte, was den Skill-Score erhöht.

### Übungs-Daten
- **Beginner-Skills**: Feste Aufgaben in `backend/data/exercises.py` (statisch definiert)
- **Intermediate + Advanced**: Dynamisch vom LLM generiert (`generate_exercise_tool.py`)

### Score-System
```
Übung "richtig"   → 20 Punkte, Übung gesperrt (kein Wiederholen)
Übung "teilweise" → 10 Punkte (kann erneut versucht werden)
Übung "falsch"    → 0 Punkte, Weiterleitung zum Tutor empfohlen

5 Übungen × 20 Punkte = 100% Skill-Score
Skill-Status:
  Score ≥ 80 → "understood"   → nächster Skill freigeschaltet
  Score ≥ 40 → "partial"
  Score < 40 → "not_understood"
```

### Datenfluss: Übung einreichen

```
Nutzer schreibt Code → Klick "Lösung einreichen"
         │
         ├── submitExercise({ skill_key, exercise_id, code }, token) [api.ts:98]
         │        POST /exercises/submit
         │
         ▼
Backend: exercises.py → submit_exercise()          [exercises.py:153]
         │
         ├── 1. Übung aus EXERCISES[skill_key] laden
         │       exercise = { id, title, description, expected_output, hint }
         │
         ├── 2. Prüfen: ist Übung bereits gesperrt (RICHTIG gelöst)?
         │       → HTTP 400 wenn ja
         │
         ├── 3. Code ausführen
         │       core/code_runner.py → run_user_code(code)
         │         subprocess.run(["python3", "-c", code], timeout=5)
         │         Gibt (stdout, stderr) zurück
         │
         ├── 4. LLM-Bewertung
         │       evaluate_exercise.invoke({           ← LLM-AUFRUF (1-3x)
         │         code, exercise_description,
         │         expected_output, stdout
         │       })
         │
         │       Bewertungs-Logik (exercise_evaluator_tool.py):
         │
         │       Fall 1: stdout ist leer
         │         → System-Prompt: "Code hat keine Ausgabe produziert"
         │         → LLM gibt: result=falsch, what_went_wrong, hint
         │
         │       Fall 2: stdout == expected_output (exakte Übereinstimmung)
         │         → System-Prompt: "Prüfe ob Konzept richtig verwendet"
         │         → LLM prüft: Hat Nutzer einfach hardcodiert? (print("5") statt Schleife)
         │         → LLM gibt: result=richtig oder teilweise
         │
         │       Fall 3: stdout ≠ expected_output (aber nicht leer)
         │         → System-Prompt: "Beurteile teilweise vs falsch"
         │         → LLM gibt: result=teilweise oder falsch
         │
         │       Alle LLM-Antworten als JSON:
         │         { result, what_was_good, what_went_wrong, hint }
         │
         ├── 5. Score berechnen
         │       richtig  → new_score_granted = 20
         │       teilweise→ new_score_granted = max(10, aktueller_wert)
         │       falsch   → kein Änderung
         │
         ├── 6. ExerciseCompletion in DB upserten
         │       INSERT OR UPDATE exercise_completions
         │         (user_id, skill_key, exercise_id, score_granted, is_locked)
         │
         ├── 7. StudentSkillProgress aktualisieren
         │       total = SUM(score_granted) aller Übungen für diesen Skill
         │       student_skill_progress.score = min(total, 100)
         │
         └── 8. Response senden
                 { result, score_change, new_skill_score,
                   what_was_good, what_went_wrong, hint,
                   stdout, stderr, redirect_to_tutor }
```

### Datenfluss: Hinweis anfordern

```
Nutzer klickt "Hinweis" (hint_level = 1, 2 oder 3)
         │
         ├── getExerciseHint({ skill_key, exercise_id, code, hint_level }, token)
         │        POST /exercises/hint
         │
         ▼
Backend: exercises.py → get_exercise_hint()
         │
         └── get_hint.invoke({ code, exercise_description, hint_level })  ← LLM-AUFRUF
                 System-Prompt: Gib Hinweis passend zum Level (1=vage, 2=konkreter, 3=fast Lösung)
                 Response: { hint: "..." }
```

### Dynamische Übungs-Generierung (Intermediate/Advanced)

```
Wenn keine statischen Aufgaben vorhanden → generate_exercise.invoke({
  skill_key, skill_label, level,
  completed_exercise_titles  ← verhindert Wiederholung!
})                                                        ← LLM-AUFRUF

LLM erstellt:
  { title, description, expected_output, hint }

System-Prompt gibt vor:
  - Kein input()
  - Keine externen Bibliotheken
  - Deterministisches expected_output
  - Bereits abgeschlossene Titel NICHT wiederverwenden
```

### Schlüsseldateien
| Datei | Funktion |
|---|---|
| `backend/data/exercises.py` | Statische Beginner-Übungen |
| `backend/agent/tools/exercise_evaluator_tool.py` | LLM-Bewertung (3 Fälle) |
| `backend/agent/tools/exercise_generator_tool.py` | LLM-Generierung (dyn. Übungen) |
| `backend/agent/tools/hint_tool.py` | LLM-Hinweis je Level |
| `backend/core/code_runner.py` | subprocess Python-Ausführung |
| `backend/routers/exercises.py` | API-Endpunkte |
| `frontend/components/ExercisePanel.tsx` | Übungs-UI |
| `frontend/components/ExerciseModal.tsx` | Modal-Wrapper |

---

## Feature: Skill-Tests

### Was ist das?
Nachdem alle 5 Übungen eines Skills abgeschlossen wurden, kann der Nutzer einen Skill-Test starten. Das LLM generiert einen vollständigen Test: 3 Multiple-Choice-Fragen, 1 Code-Lese-Aufgabe, 1 Mini-Aufgabe. Bestanden bei ≥ 60 Punkten.

### Score-System
```
Multiple Choice:  3 × 10 Punkte  = 30 Punkte max  (kein LLM, reiner String-Vergleich)
Code-Lesen:       1 × 30 Punkte  = 30 Punkte max  (LLM — semantischer Vergleich)
Mini-Aufgabe:     1 × 40 Punkte  = 40 Punkte max  (LLM — Code-Ausführung + Bewertung)
─────────────────────────────────────────────────
Gesamt:                           100 Punkte max
Bestanden:                        ≥ 60 Punkte
```

### Datenfluss: Test generieren

```
Nutzer klickt "Skill-Test starten"
         │
         ├── generateSkillTest(skill_key, token)  [api.ts:120]
         │        POST /skill-tests/generate
         │
         ▼
Backend: skill_tests.py → generate_test()         [skill_tests.py:62]
         │
         ├── generate_skill_test.invoke({          ← LLM-AUFRUF (skill_tests.py:84)
         │     skill_key, skill_label, user_level
         │   })
         │
         │   LLM erstellt JSON mit GENAU dieser Struktur:
         │   {
         │     "multiple_choice": [            ← 3 Fragen
         │       { "question", "options": {A,B,C,D}, "correct": "A", "explanation" }
         │     ],
         │     "code_reading": {
         │       "code": "x=5; print(x+3)",
         │       "question": "Was gibt aus?",
         │       "correct_answer": "8"
         │     },
         │     "mini_task": {
         │       "description": "Schreibe eine Funktion...",
         │       "expected_output": "Hallo Welt"
         │     }
         │   }
         │
         │   Validierung: genau 3 MC-Fragen, code_reading + mini_task vorhanden
         │   Bei Fehler: Fallback-Test mit Basis-Fragen
         │
         ├── Ergebnis in DB speichern:
         │       INSERT INTO skill_test_results
         │         (user_id, skill_key, score=0, passed=False,
         │          attempt_number, generated_test=test_data)
         │
         └── Response: { test_session_id, test_data }
                 test_session_id ist wichtig: verhindert Client-Manipulation der Fragen
```

### Datenfluss: Test auswerten

```
Nutzer beantwortet Test → Klick "Einreichen"
         │
         ├── submitSkillTest({ test_session_id, skill_key,
         │     mc_answers, code_reading_answer, mini_task_code }, token)
         │        POST /skill-tests/submit
         │
         ▼
Backend: skill_tests.py → submit_test()
         │
         ├── Session-Row aus DB laden (sicherheitshalber user_id prüfen)
         │       test_data = session_row.generated_test  ← aus DB, nicht vom Client!
         │
         ├── Mini-Task-Code ausführen:
         │       run_user_code(mini_task_code) → (stdout, stderr)
         │
         └── evaluate_skill_test.invoke({            ← LLM-AUFRUF 2x (skill_tests.py:168)
               mc_answers, mc_correct,
               code_reading_answer, code_reading_correct,
               mini_task_code, mini_task_expected, mini_task_actual_output
             })
         │
         │   Bewertungs-Logik (skill_test_evaluator_tool.py):
         │
         │   MC-Bewertung (kein LLM):
         │     for i in range(3):
         │       is_correct = answers[i] == corrects[i]
         │       mc_score += 10 if correct
         │
         │   Code-Lesen (LLM):                        ← LLM-AUFRUF 1
         │     System: "Ist die Antwort semantisch korrekt?"
         │     (kleine Formulierungs-Unterschiede sind OK)
         │     → { correct: true/false, explanation }
         │
         │   Mini-Aufgabe (LLM):                      ← LLM-AUFRUF 2
         │     System: "Würde der Code die erwartete Ausgabe produzieren?"
         │     Nutzt auch tatsächliche stdout-Ausgabe
         │     → { correct: true/false, explanation }
         │
         ├── total_score = mc_score + code_reading_score + mini_task_score
         ├── passed = total_score >= 60
         │
         ├── session_row.score und session_row.passed in DB aktualisieren
         │
         └── Response: { total_score, passed, mc_score, code_reading_score,
                          mini_task_score, per_question_feedback, attempt_number }
```

### Schlüsseldateien
| Datei | Funktion |
|---|---|
| `backend/agent/tools/skill_test_generator_tool.py` | LLM: Test generieren |
| `backend/agent/tools/skill_test_evaluator_tool.py` | LLM: Test auswerten |
| `backend/models/skill_test.py` | DB-Modell: SkillTestResult |
| `backend/routers/skill_tests.py` | API-Endpunkte |
| `frontend/components/SkillTestModal.tsx` | Test-UI |

---

## Feature: Level-Tests

### Was ist das?
Wenn alle Skills eines Levels ≥ 80 Score haben, erscheint der Button "Level-Test starten". Ein Level-Test ist ein umfassenderer Test über alle Skills des Levels.

### Datenfluss

```
Frontend prüft:
  levelSkills(activeLevel).every(s => s.score >= 80)  → Button wird sichtbar
  (Button ist immer am Ende jedes Level-Tabs sichtbar sobald alle Skills ≥ 80%)
         │
         ├── generateLevelTest(level, token)  [api.ts:142]
         │        POST /level-tests/generate
         │
         ▼ (analog zu Skill-Tests)
LLM generiert Test für alle Skills des Levels           ← LLM-AUFRUF
         │
         ├── submitLevelTest(...)  [api.ts:152]
         │        POST /level-tests/submit
         │
         ▼
LLM wertet aus (Code-Lesen + Mini-Task)                 ← LLM-AUFRUF
```

### Schlüsseldateien
| Datei | Funktion |
|---|---|
| `backend/routers/level_tests.py` | API-Endpunkte |
| `frontend/components/LevelTestModal.tsx` | Level-Test-UI |

---

## Feature: Profil (Profile)

### Was ist das?
Das Profil-Feature zeigt Nutzerinformationen und ermöglicht die Bearbeitung von Name, Erfahrungslevel und Lernziel.

### Aktueller Stand (wichtig: teilweise noch Mock-Daten!)
```typescript
// ProfileView.tsx:17-21 — HARDCODIERTE Werte, noch nicht aus DB:
const LEARNED_TOPICS = ["Variablen", "Schleifen", "Bedingungen"]
const WEAKNESSES = ["Syntaxfehler", "Einrückung"]
const NEXT_GOAL = "Funktionen"
const PROGRESS_PERCENT = 45
```
Diese sollten in Zukunft aus der echten `/learning-progress` API kommen.

### Datenfluss: Profil bearbeiten

```
Nutzer klickt "Bearbeiten"
         │
         ├── Felder editierbar: name, level (Anfänger/Mittel/Fortgeschritten), goal
         │
         ▼
Klick "Speichern"
         │
         ├── updateUser({ name, level, goal })    [AuthContext.tsx]
         │        PATCH /auth/users/me
         │        Bearer Token
         │
         ▼
Backend: auth.py → update_user()
         │
         └── UPDATE users SET name=?, level=?, goal=? WHERE id=?
```

### Was aus der DB kommt (echte Daten)
```typescript
user.name          // aus JWT / users-Tabelle
user.email         // aus JWT / users-Tabelle
user.level         // "Anfänger" | "Mittel" | "Fortgeschritten"
user.goal          // Lernziel-String
user.analyzedCount // aus LearningSession-Tabelle (COUNT)
```

### Schlüsseldateien
| Datei | Funktion |
|---|---|
| `frontend/components/ProfileView.tsx` | UI — aktuell noch teilweise Mock |
| `frontend/context/AuthContext.tsx` | User-State + updateUser() |
| `backend/routers/auth.py` | Nutzer-Endpunkte |
| `backend/models/user.py` | DB-Modell: User |

---

## LangChain / LLM — wo und wie

### LLM-Auswahl (`agent/config.py`)

```python
def get_llm():
    # 1. Versuch: OpenAI (wenn OPENAI_API_KEY gesetzt)
    #    Modell: gpt-4o (oder LLM_MODEL env var)
    #    Verbindungstest: client.models.list()
    #    → ChatOpenAI(model="gpt-4o", temperature=0)

    # 2. Fallback: Ollama (lokal)
    #    URL: OLLAMA_BASE_URL (Default: http://localhost:11434)
    #    Modell: OLLAMA_MODEL (Default: llama3.2)
    #    → ChatOllama(model="llama3.2", temperature=0)

def get_embeddings():
    # Gleiche Logik: OpenAI (text-embedding) → Ollama (embed)

def get_classifier_llm():
    # Wie get_llm() aber für schnelle Klassifikation
    # OpenAI: gpt-4o-mini (günstiger/schneller)
```

### Alle LLM-Aufrufe im System

| Aufruf | Datei | Verwendungszweck |
|---|---|---|
| `explain_code_tool` | `tools/explain_tool.py` | Code erklären (ReAct-Agent) |
| `debug_code_tool` | `tools/debug_tool.py` | Fehler finden (ReAct-Agent) |
| `exercise_tool` | `tools/exercise_tool.py` | Übung vorschlagen (ReAct-Agent) |
| `rag_tool` | `tools/rag_tool.py` | Lernmaterial suchen (nur im Analyze-Agent verfügbar, nicht im Chat) |
| `run_chat_with_context` | `tutor_agent.py` | Direkter LLM-Aufruf mit PDF-Kontext — bypasses Agent |
| `analyze_skill` | `services/skill_analyzer.py` | Skill erkennen, Score berechnen |
| `generate_exercise` | `tools/exercise_generator_tool.py` | Dynamische Übung generieren |
| `evaluate_exercise` | `tools/exercise_evaluator_tool.py` | Übungs-Lösung bewerten |
| `get_hint` | `tools/hint_tool.py` | Gestufter Hinweis geben |
| `generate_skill_test` | `tools/skill_test_generator_tool.py` | Test-Fragen generieren |
| `evaluate_skill_test` | `tools/skill_test_evaluator_tool.py` | Test auswerten (Code-Lesen + Mini) |
| `get_embeddings()` | `config.py` | PDF-Chunks → Vektoren (Upload) |
| `embed_query()` | `vectorstore.py` | Nutzer-Frage → Vektor (RAG-Suche im Chat) |

### ReAct-Agent (`tutor_agent.py`)

```python
# LangChain create_agent() — ReAct-Pattern
agent = create_agent(llm, tools, system_prompt=_SYSTEM_PROMPT)
result = agent.invoke({
    "messages": [("human", f"Analysiere diesen Code:\n```python\n{code}\n```")]
})

# Ablauf:
# 1. LLM bekommt System-Prompt + Nutzer-Code
# 2. LLM entscheidet: welches Tool aufrufen?
# 3. Tool wird aufgerufen (z.B. explain_code_tool(code))
# 4. Ergebnis geht zurück zum LLM
# 5. LLM entscheidet weiter oder gibt finale Antwort
# 6. _parse_agent_output() extrahiert 5 Felder aus Antwort
```

### LangChain-Tools: Wie sie funktionieren

```python
# Alle Tools sind mit @tool dekoriert:
@tool
def explain_code_tool(code: str) -> str:
    llm = get_llm()  # Frisches LLM-Objekt bei jedem Aufruf
    system = SystemMessage(content="Du bist ein Python-Tutor...")
    human = HumanMessage(content=f"Code:\n```python\n{code}\n```")
    response = llm.invoke([system, human])
    return response.content

# Direkte Tool-Aufrufe (NICHT über Agent):
evaluate_exercise.invoke({ "code": ..., "expected_output": ..., ... })
# → ruft .invoke() direkt auf, umgeht ReAct-Loop
```

---

## Datenbank-Modelle

```
users
  id, name, email, password_hash, role, level, goal, analyzed_count

learning_sessions                    (älteres System, für Tutor-Chat)
  id, user_id, code_snippet, topics, errors, chat_messages, created_at

student_skill_progress               (aktuelles Kern-Modell)
  id, user_id, skill_key, score (0-100), status, updated_at
  UNIQUE(user_id, skill_key)

learning_events                      (unveränderliche History)
  id, user_id, skill_key, score, mistakes, feedback, recommended_exercise, created_at

exercise_completions
  id, user_id, skill_key, exercise_id, score_granted (0/10/20), is_locked, created_at
  UNIQUE(user_id, skill_key, exercise_id)

skill_test_results
  id, user_id, skill_key, score, passed, attempt_number, generated_test (JSON), created_at

level_test_results
  id, user_id, level, score, passed, attempt_number, created_at
```

---

## Vollständiger Datenfluss: Übung einreichen

```
FRONTEND                          BACKEND                          LLM / DB
─────────                         ───────                          ────────
ExercisePanel
 └─ Nutzer schreibt Code
    klickt "Einreichen"
         │
         ├──► POST /exercises/submit
         │      { skill_key: "for_loop",
         │        exercise_id: "for_loop_2",
         │        code: "for i in range(5): print(i)" }
         │                                    │
         │                              exercises.py
         │                                    │
         │                              run_user_code()
         │                                    │─────────────────► subprocess python3
         │                                    │◄─────────────────  stdout: "0\n1\n2\n3\n4"
         │                                    │
         │                              evaluate_exercise.invoke()
         │                                    │─────────────────► LLM (gpt-4o/llama3.2)
         │                                    │  "stdout == expected? Konzept korrekt?"
         │                                    │◄─────────────────  { result: "richtig",
         │                                    │                       what_was_good: "...",
         │                                    │                       hint: "..." }
         │                                    │
         │                              DB UPDATE:
         │                                    │─────────────────► exercise_completions
         │                                    │                    score_granted=20, is_locked=true
         │                                    │─────────────────► student_skill_progress
         │                                    │                    score=40 (2 von 5 Übungen)
         │                                    │
         │◄── Response:
         │      { result: "richtig",
         │        score_change: 20,
         │        new_skill_score: 40,
         │        what_was_good: "Perfekte Schleife!",
         │        redirect_to_tutor: false }
         │
 └─ Zeigt Erfolg-Feedback
    Aktualisiert Skill-Score-Anzeige
    Nächste Übung wird freigeschaltet
```

---

## Vollständiger Datenfluss: Skill-Test

```
FRONTEND                          BACKEND                          LLM / DB
─────────                         ───────                          ────────
LearningProgressView
 └─ Klick "Skill-Test starten"
         │
         ├──► POST /skill-tests/generate
         │      { skill_key: "for_loop" }
         │                                    │
         │                              generate_skill_test.invoke()
         │                                    │─────────────────► LLM
         │                                    │  "Erstelle Test zu For-Schleifen,
         │                                    │   Niveau: Anfänger"
         │                                    │◄─────────────────  {
         │                                    │                     multiple_choice: [3 Fragen],
         │                                    │                     code_reading: {...},
         │                                    │                     mini_task: {...}
         │                                    │                    }
         │                                    │
         │                              DB INSERT:
         │                                    │─────────────────► skill_test_results
         │                                    │                    generated_test=test_data
         │                                    │                    → test_session_id = 42
         │◄── { test_session_id: 42,
         │      test_data: { ... } }
         │
 └─ SkillTestModal zeigt Test
    Nutzer beantwortet Fragen
    Schreibt Mini-Aufgabe-Code
    Klickt "Test einreichen"
         │
         ├──► POST /skill-tests/submit
         │      { test_session_id: 42,
         │        mc_answers: {0:"A", 1:"C", 2:"B"},
         │        code_reading_answer: "8",
         │        mini_task_code: "for i in range(3): print(i)" }
         │                                    │
         │                              session = DB.get(42, user_id)
         │                              test_data = session.generated_test  ← aus DB!
         │                                    │
         │                              run_user_code(mini_task_code)
         │                                    │─────────────────► subprocess
         │                                    │◄─────────────────  stdout: "0\n1\n2"
         │                                    │
         │                              evaluate_skill_test.invoke()
         │                                    │
         │                              MC: reiner String-Vergleich (kein LLM)
         │                                    → A==A? ja (+10), C==B? nein, B==C? nein
         │                                    → mc_score = 10
         │                                    │
         │                              Code-Lesen: LLM            ← LLM-AUFRUF 1
         │                                    │─────────────────► "Ist '8' semantisch korrekt?"
         │                                    │◄─────────────────  { correct: true } → +30
         │                                    │
         │                              Mini-Aufgabe: LLM          ← LLM-AUFRUF 2
         │                                    │─────────────────► "Produziert der Code '0\n1\n2'?"
         │                                    │◄─────────────────  { correct: true } → +40
         │                                    │
         │                              total = 10+30+40 = 80, passed = true
         │                              DB UPDATE: session.score=80, passed=true
         │◄── { total_score: 80, passed: true,
         │      mc_score: 10, code_reading_score: 30,
         │      mini_task_score: 40,
         │      per_question_feedback: [...] }
         │
 └─ Zeigt Ergebnis
    "Bestanden! 80/100 Punkte"
    Fortschritt wird neu geladen
```
