# exercises/submit & exercises/hint — Vollständige technische Dokumentation

## Überblick

Zwei Endpoints — beide rufen das LLM direkt auf, kein Agent, kein ReAct-Loop.

```
POST /exercises/submit
        │
        ├─► 1. Code ausführen     → subprocess.run()
        ├─► 2. LLM bewerten       → evaluate_exercise.invoke()
        └─► 3. Score in DB        → ExerciseCompletion + StudentSkillProgress

POST /exercises/hint
        │
        └─► LLM Tipp generieren   → get_hint.invoke()
```

---

## POST /exercises/submit

**Datei:** `backend/routers/exercises.py`

### Schritt 1 — Code ausführen

**Zeile 169** `stdout, stderr = run_user_code(data.code)`

> Kein LLM — reines `subprocess.run()` mit Timeout 10s.
> Liefert `stdout` und `stderr` für den nächsten Schritt.

---

### Schritt 2 — LLM bewerten

**Datei:** `backend/agent/tools/exercise_evaluator_tool.py`
**Zeile 172** `raw_result = evaluate_exercise.invoke({...})`

> **`🟡 LangChain`** — `@tool` Dekorator, `llm.invoke()`
> **`⚡ LLM-Aufruf`** — 1 Aufruf, direkt, kein Agent

Das Tool entscheidet anhand von `stdout` welchen Prompt es schickt — **3 Szenarien**:

#### Szenario 1 — stdout leer

```
subprocess.run() → stdout = ""
        ↓
LLM bekommt: "Code hat keine Ausgabe produziert"
        ↓
result = "falsch"   ← LLM muss das bestätigen
```

> **Zeile 23** `if not stdout.strip():`
> LLM gibt zurück: `what_was_good`, `what_went_wrong`, `hint`

#### Szenario 2 — stdout == expected_output (exakter Treffer)

```
stdout = "Hello World"
expected_output = "Hello World"
        ↓
LLM prüft: richtiges Konzept, oder hardcodiert?
        ↓
result = "richtig"    ← Konzept korrekt
result = "teilweise"  ← print("Hello World") statt Schleife
```

> **Zeile 56** `if stdout.strip() == expected_output.strip():`
> Schützt vor `print("5")` statt echter Berechnung.

#### Szenario 3 — stdout vorhanden aber falsch

```
stdout = "10"
expected_output = "15"
        ↓
LLM entscheidet: teilweise (richtiges Konzept, kleiner Fehler)
                 falsch     (falsches Konzept)
```

> **Zeile 103** — dritter `llm.invoke()` Aufruf
> LLM gibt `teilweise` oder `falsch` zurück.

---

### Schritt 3 — Score berechnen und speichern

**Zeile 186** — Score-Logik (reines Python, kein LLM):

| Ergebnis | Score-Änderung | is_locked |
|---|---|---|
| `richtig` | +20 (fix) | `True` — Aufgabe abgeschlossen |
| `teilweise` | +10 (max) | `False` |
| `falsch` | 0 | `False` |

**Zeile 220** `total_exercise_score = sum(c.score_granted for c in all_completions)`

> Skill-Score = Summe aller Aufgaben des Skills (max 100 = 5 × 20)

**Zeile 226** Status-Update:
- `score >= 80` → `understood`
- `score >= 40` → `partial`
- `score < 40`  → `not_understood`

---

### Ablauf komplett

```
Student schickt Code
        ↓
subprocess.run()                    ← kein LLM
        ↓
evaluate_exercise.invoke()          ← ⚡ LLM-Aufruf 1
  stdout leer?     → "falsch"
  stdout korrekt?  → "richtig" oder "teilweise"
  stdout falsch?   → "teilweise" oder "falsch"
        ↓
Score berechnen + DB schreiben      ← kein LLM
        ↓
Response: result, score_change, new_skill_score, what_was_good, hint, stdout
```

**LLM-Aufrufe gesamt: 1**

---

## POST /exercises/hint

**Datei:** `backend/routers/exercises.py` Zeile 257
**Tool:** `backend/agent/tools/hint_tool.py`

**Zeile 272** `hint_text = get_hint.invoke({...})`

> **`🟡 LangChain`** — `@tool` Dekorator, `llm.invoke()`
> **`⚡ LLM-Aufruf`** — 1 Aufruf, kein Agent

Student schickt `hint_level` (1, 2 oder 3) — 3 verschiedene System-Prompts:

| Level | Was das LLM bekommt | Was es zurückgibt |
|---|---|---|
| 1 | „Erkläre das Konzept — keine Syntax" | Idee und Denkansatz |
| 2 | „Nenne die Funktion — kein Beispiel" | Funktion/Schlüsselwort + kurze Erklärung |
| 3 | „Zeig Code-Struktur mit `...`" | Partieller Code, Kernstück offen |

```
Student: code + hint_level=2
        ↓
get_hint.invoke()                   ← ⚡ LLM-Aufruf 1
  level_instruction = Level-2-Prompt
  LLM bekommt: Aufgabe + aktuellen Code des Students
        ↓
Response: hint (Klartext, kein JSON)
```

> **Zeile 36** `level = max(1, min(3, int(hint_level)))` — Absicherung gegen ungültige Werte
> LLM gibt immer Klartext zurück (kein JSON wie bei evaluate_exercise)

**LLM-Aufrufe gesamt: 1**

---

## Vergleich: submit vs hint

| | `/exercises/submit` | `/exercises/hint` |
|---|---|---|
| LLM-Aufrufe | 1 | 1 |
| Rückgabe | JSON (result, score, feedback) | Klartext (Tipp) |
| DB-Schreibzugriff | ja | nein |
| Szenarien | 3 (leer / korrekt / falsch) | 3 (Level 1–3) |
| Agent | nein | nein |

---

## Überblick: Was ist LangChain, was ist normaler Code

| Code | Typ | Datei / Zeile |
|---|---|---|
| `evaluate_exercise.invoke()` | **🟡 LangChain** | `exercises.py:172` |
| `get_hint.invoke()` | **🟡 LangChain** | `exercises.py:272` |
| `@tool` Dekorator | **🟡 LangChain** | `exercise_evaluator_tool.py:8`, `hint_tool.py:28` |
| `llm.invoke([system, human])` | **🟡 LangChain** | `exercise_evaluator_tool.py:44,81,126` |
| `SystemMessage`, `HumanMessage` | **🟡 LangChain** | beide Tool-Dateien |
| `run_user_code()` | normaler Code (subprocess) | `exercises.py:169` |
| `db.query(ExerciseCompletion)` | normaler Code | `exercises.py:158` |
| Score-Berechnung | normaler Code | `exercises.py:186` |
