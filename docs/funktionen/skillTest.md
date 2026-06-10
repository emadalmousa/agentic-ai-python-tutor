# skill-tests/generate & skill-tests/submit — Vollständige technische Dokumentation

## Überblick

Zwei Endpoints — beide via LangChain `@tool` direkt aufgerufen, kein Agent-Loop.
Der Skill-Test wird in **zwei Szenarien** ausgelöst.

```
Szenario A: Button "Skill testen" (Frontend)
        │
        ├─► POST /skill-tests/generate   → LLM generiert Test
        └─► POST /skill-tests/submit     → LLM bewertet Antworten

Szenario B: Student schreibt im Chat
        │
        └─► ReAct-Agent wählt suggest_skill_test()
                └─► generate_skill_test.invoke()  → LLM generiert Test im Chat
```

---

## Szenario A — Button "Skill testen"

**Auslöser:** Student hat `score >= 100` bei einem Skill → Button erscheint neben dem Skill-Titel in `ExercisePanel`.

**Datei:** `frontend/components/ExercisePanel.tsx:249`

```
Button klick (score >= 100)
        ↓
onStartSkillTest()              ← kein API-Aufruf, nur State-Wechsel
        ↓
SkillTestModal öffnet sich      ← useEffect lädt sofort
        ↓
POST /skill-tests/generate      ← ⚡ LLM-Aufruf 1
        ↓
Student beantwortet 3 Teile
        ↓
POST /skill-tests/submit        ← ⚡ LLM-Aufruf 2 (+ ⚡ LLM-Aufruf 3)
```

---

## Szenario B — Chat-Agent

**Auslöser:** Student schreibt z.B. "Ich will mich für die Klausur testen".

**Datei:** `backend/agent/tutor_agent.py:154`

```
Student: "Ich will mich für die Klausur testen"
        ↓
_is_python_related()            ← ⚡ LLM-Aufruf 1 (Classifier)
        ↓
run_chat() → ReAct-Agent
  agent.invoke()                ← ⚡ LLM-Aufruf 2 — wählt suggest_skill_test
  suggest_skill_test(skill_key) ← Agent wählt Skill basierend auf weak_info
        ↓
generate_skill_test.invoke()    ← ⚡ LLM-Aufruf 3 — generiert Test
        ↓
Agent gibt Test als Chat-Nachricht zurück
        ↓
Student beantwortet → POST /skill-tests/submit  ← ⚡ LLM-Aufruf 4+5
```

> **Welchen Skill wählt der Agent?**
> **Zeile 141–142** `tutor_agent.py` — `weak_info` listet alle Skills mit Status `partial` oder `not_understood`.
> Der Agent entscheidet selbst — kein explizites "frage nach wenn unklar".
> Wenn der Student keinen Skill nennt, wählt der Agent den schwächsten.

---

## POST /skill-tests/generate

**Datei:** `backend/routers/skill_tests.py:58`

### Schritt 1 — LLM generiert Test

**Zeile 69** `raw_result = generate_skill_test.invoke({...})`

> **`🟡 LangChain`** — `@tool` Dekorator, `llm.invoke()`
> **`⚡ LLM-Aufruf`** — 1 Aufruf, generiert kompletten Test

Das LLM erstellt einen Test mit **3 Teilen** in einem einzigen Aufruf:

| Teil | Punkte | Bewertung |
|---|---|---|
| 3 × Multiple Choice (A/B/C/D) | 3 × 10 = 30 | Python-Vergleich, kein LLM |
| Code-Lese-Aufgabe | 30 | LLM semantisch |
| Mini-Task (Code schreiben) | 40 | LLM + subprocess |
| **Gesamt** | **100** | bestanden ≥ 60 |

### Schritt 2 — Test in DB speichern

**Zeile 77–94** `SkillTestResult` wird angelegt mit `score=0, passed=False, generated_test=test_data`.

> Kein LLM — reines DB-Insert.
> **Warum in der DB?** Richtige Antworten bleiben server-seitig — Client kann sie nicht manipulieren.

### Response

```json
{
  "test_session_id": 42,
  "test_data": {
    "multiple_choice": [...],
    "code_reading": {...},
    "mini_task": {...}
  }
}
```

**LLM-Aufrufe gesamt: 1**

---

## POST /skill-tests/submit

**Datei:** `backend/routers/skill_tests.py:103`

### Schritt 1 — Mini-Task Code ausführen

**Zeile 126** `mini_stdout, _ = run_user_code(data.mini_task_code)`

> Kein LLM — `subprocess.run()` mit Timeout 10s.

### Schritt 2 — MC auswerten (kein LLM)

**Zeile 129–137** — reiner Python-Stringvergleich.

```
answers[i] == corrects[i]   → 10 Punkte pro richtiger Antwort
```

> `corrects` kommen aus der DB (`session_row.generated_test`) — nicht vom Client.

### Schritt 3 — Code-Lesen bewerten (LLM)

**Zeile 65–96** `evaluate_skill_test.py`

> **`⚡ LLM-Aufruf`** — LLM prüft semantisch ob die Antwort korrekt ist.
> Kleine Formulierungsunterschiede werden toleriert.
> Fallback: exakter Stringvergleich wenn LLM fehlschlägt.

```
Student: "gibt 8 aus"
Richtig: "8"
        ↓
LLM: semantisch korrekt → 30 Punkte
```

### Schritt 4 — Mini-Task bewerten (LLM)

**Zeile 109–140** `evaluate_skill_test.py`

> **`⚡ LLM-Aufruf`** — LLM prüft ob Code die erwartete Ausgabe produziert.
> Hat `mini_task_actual_output` → LLM bekommt auch die echte Ausgabe von subprocess.

### Schritt 5 — Score berechnen und speichern

**Zeile 148–159** `evaluate_skill_test.py`

```
total_score = mc_score + code_reading_score + mini_task_score
passed = total_score >= 60
```

**Zeile 157–158** `skill_tests.py` — `session_row.score` und `session_row.passed` werden aktualisiert.

**LLM-Aufrufe gesamt: 2** (Code-Lesen + Mini-Task)

---

## Ablauf komplett — Szenario A

```
Button klick
        ↓
POST /skill-tests/generate
  generate_skill_test.invoke()      ← ⚡ LLM-Aufruf 1 — Test generieren
  SkillTestResult in DB (score=0)   ← kein LLM
        ↓
Student beantwortet MC + Code-Lesen + Mini-Task
        ↓
POST /skill-tests/submit
  subprocess.run(mini_task_code)    ← kein LLM
  MC auswerten                      ← kein LLM, Python-Vergleich
  evaluate_skill_test.invoke()
    llm.invoke() Code-Lesen         ← ⚡ LLM-Aufruf 2
    llm.invoke() Mini-Task          ← ⚡ LLM-Aufruf 3
  score speichern in DB             ← kein LLM
        ↓
Response: total_score, passed, per_question_feedback
```

**LLM-Aufrufe gesamt: 3**

---

## Ablauf komplett — Szenario B (Chat)

```
Student: "Ich will mich für die Klausur testen"
        ↓
_is_python_related()                ← ⚡ LLM-Aufruf 1 (Classifier)
        ↓
run_chat() → agent.invoke()         ← ⚡ LLM-Aufruf 2 — wählt suggest_skill_test
        ↓
generate_skill_test.invoke()        ← ⚡ LLM-Aufruf 3 — Test generieren
        ↓
Agent formuliert Antwort            ← ⚡ LLM-Aufruf 4
        ↓
Student beantwortet → /skill-tests/submit
  llm.invoke() Code-Lesen           ← ⚡ LLM-Aufruf 5
  llm.invoke() Mini-Task            ← ⚡ LLM-Aufruf 6
```

**LLM-Aufrufe gesamt: 6**

---

## Vergleich: Szenario A vs B

| | Szenario A (Button) | Szenario B (Chat) |
|---|---|---|
| Auslöser | score >= 100, Button klick | Freitext im Chat |
| Welcher Skill | vom Student gewählt (aktiver Skill) | Agent entscheidet (schwächster Skill) |
| Agent beteiligt | nein | ja |
| LLM-Aufrufe generate | 1 | 3 (Classifier + Agent + Tool) |
| LLM-Aufrufe submit | 2 | 2 |
| Gesamt | 3 | 6 |

---

## Überblick: Was ist LangChain, was ist normaler Code

| Code | Typ | Datei / Zeile |
|---|---|---|
| `generate_skill_test.invoke()` | **🟡 LangChain** | `skill_tests.py:69` |
| `evaluate_skill_test.invoke()` | **🟡 LangChain** | `skill_tests.py:143` |
| `@tool` Dekorator | **🟡 LangChain** | `skill_test_generator_tool.py:8`, `skill_test_evaluator_tool.py:8` |
| `llm.invoke([system, human])` | **🟡 LangChain** | `skill_test_generator_tool.py:53`, `skill_test_evaluator_tool.py:81,131` |
| `SystemMessage`, `HumanMessage` | **🟡 LangChain** | beide Tool-Dateien |
| `run_user_code()` | normaler Code (subprocess) | `skill_tests.py:126` |
| MC-Auswertung `answers[i] == corrects[i]` | normaler Code | `skill_test_evaluator_tool.py:46` |
| `db.query(SkillTestResult)` | normaler Code | `skill_tests.py:77,115` |
| Score-Berechnung | normaler Code | `skill_test_evaluator_tool.py:148` |
