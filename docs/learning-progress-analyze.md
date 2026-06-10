# learning-progress/analyze — Vollständige technische Dokumentation

## Überblick

`POST /learning-progress/analyze` ist der Endpoint der automatisch den Skill-Fortschritt eines Schülers erkennt und in der Datenbank aktualisiert — ohne dass der Schüler etwas tun muss.

```
Schüler chattet → Frontend ruft im Hintergrund an → Skill erkannt → Score aktualisiert
```

> **`⚡ LLM-Aufruf`** — einmalig in `analyze_skill()` für Skill-Erkennung
> **`🟡 LangChain`** — `llm.invoke()`, `SystemMessage`, `HumanMessage`

---

## Wer ruft den Endpoint auf?

**Datei:** `frontend/hooks/useChat.ts`, Zeile 139–146

```typescript
// nach jeder Chat-Antwort — im Hintergrund, kein await
const token = getToken()
if (token) {
  analyzeSkill({ code, question: msg }, token).catch(() => {})
}
```

> Kein `await` — der Schüler sieht die Chat-Antwort sofort.
> Fehler werden still ignoriert — Skill-Tracking ist nicht kritisch.

---

## Vollständiger Ablauf

```
Schüler schickt Chat-Nachricht
        │
        ▼
[Frontend] send() — useChat.ts
        │  POST /tutor/chat → Antwort zurück (Schüler sieht sofort)
        │
        ▼ (parallel, kein await)
[Frontend] analyzeSkill({ code, question })   ← api.ts Zeile 58
        │  POST /learning-progress/analyze + Bearer-Token
        │
        ▼
[Backend] analyze_and_save()                  ← learning_progress.py Zeile 181
        │  JWT-Check: eingeloggter User?
        │
        ▼
[Backend] analyze_skill(code, question)       ← skill_analyzer.py Zeile 210
        │
        ├─► Pfad A: LLM verfügbar
        │     llm.invoke([system, human])      ← ⚡ LLM-Aufruf + 🟡 LangChain
        │     JSON parsen + Skill-Keys validieren
        │     → { main_skill, score, status, mistakes }
        │
        └─► Pfad B: LLM nicht verfügbar (Fallback)
              _rule_based_analysis()           ← kein LLM
              Keyword-Matching im Code
              → { main_skill, score=60, status }
        │
        ▼
[Backend] Score in DB aktualisieren           ← learning_progress.py Zeile 195–202
        │  alter_score × 0.7 + neuer_score × 0.3
        │  (gleitender Durchschnitt — verhindert starke Schwankungen)
        │
        ▼
[Backend] LearningEvent speichern             ← learning_progress.py Zeile 205–213
        │  Roh-Score für Timeline (unveränderlich)
        │
        ▼
[HTTP]  AnalyzeResponse zurück                ← Frontend ignoriert diese Antwort
```

---

## Szenario A — LLM verfügbar

**Datei:** `backend/services/skill_analyzer.py`, Zeile 220–233

> **`⚡ LLM-Aufruf`** — `llm.invoke()` mit strukturiertem JSON-Output
> **`🟡 LangChain`** — `llm.invoke()`, `SystemMessage`, `HumanMessage`

```python
llm.invoke([
    SystemMessage(content=_SYSTEM_PROMPT),   # Anweisung: gib nur JSON zurück
    HumanMessage(content="Code: ...\nFrage: ..."),
])
```

**LLM gibt zurück:**
```json
{
  "detected_skills": ["for_loop", "variables"],
  "main_skill": "for_loop",
  "score": 65,
  "status": "partial",
  "mistakes": ["Doppelpunkt am Ende fehlt"],
  "feedback": "Guter Ansatz, aber Einrückung prüfen",
  "recommended_next_exercise": "Schreibe eine Schleife die 1–10 ausgibt"
}
```

Danach: `_parse_llm_json()` validiert die Skill-Keys gegen die Whitelist (37 erlaubte Skills) und begrenzt Score auf 0–100.

**LLM-Aufrufe gesamt: 1**

---

## Szenario B — LLM nicht verfügbar (Fallback)

**Datei:** `backend/services/skill_analyzer.py`, Zeile 99–131

> Kein LLM, kein LangChain — reines Keyword-Matching.

```python
_rule_based_analysis(code, question)
# sucht Keywords im Code:
# "for ", " in ", "range(" → for_loop
# "def ", "return "        → functions
# "class ", "__init__"     → classes_basic
# ...
```

**Score-Heuristik:**
- SyntaxError erkannt → `score = 35` → `not_understood`
- sonst → `score = 60` → `partial`

**LLM-Aufrufe gesamt: 0**

---

## Score-Aktualisierung in der DB

**Datei:** `backend/routers/learning_progress.py`, Zeile 198

```python
row.score = round(row.score * 0.7 + result["score"] * 0.3)
```

**Warum gleitender Durchschnitt?**

```
Vorheriger Score: 80  (understood)
Neuer Roh-Score:  20  (schlechter Chat-Moment)

Ohne Glättung:  score = 20  → not_understood  (zu aggressiv)
Mit Glättung:   score = 80×0.7 + 20×0.3 = 56 + 6 = 62  → partial
```

Einzelne schlechte Momente zerstören nicht den ganzen Fortschritt.

---

## Score → Status-Regeln

**Datei:** `backend/services/skill_analyzer.py`, Zeile 33–38

| Score | Status | Bedeutung |
|---|---|---|
| 75–100 | `understood` | klares Verständnis |
| 40–74 | `partial` | kleinere Fehler |
| 0–39 | `not_understood` | Grundprobleme |

---

## Zwei gespeicherte Werte

| Was | Wo | Wert |
|---|---|---|
| Aktueller Score | `student_skill_progress.score` | geglättet (70/30) |
| History-Event | `learning_events` | Roh-Score — unveränderlich |

Der geglättete Score zeigt den **aktuellen Stand**, die Events zeigen die **Lernkurve** über Zeit.

---

## Was ist LangChain, was ist normaler Code

| Code | Typ | Datei / Zeile |
|---|---|---|
| `llm.invoke([system, human])` | **🟡 LangChain** | `skill_analyzer.py:225` |
| `SystemMessage`, `HumanMessage` | **🟡 LangChain** | `skill_analyzer.py:222` |
| `get_llm()` | **🟡 LangChain** abstrahiert | `config.py:75` |
| `_rule_based_analysis()` | normaler Code (Keyword-Matching) | `skill_analyzer.py:99` |
| `_parse_llm_json()` | normaler Code (JSON-Parsing) | `skill_analyzer.py:171` |
| `db.query(...)`, `db.add(...)` | normaler Code (SQLAlchemy) | `learning_progress.py` |
| `analyzeSkill()` im Frontend | normaler Code (fetch) | `api.ts:58` |

---

## LLM-Aufrufe gesamt

| Szenario | Aufrufe | Warum |
|---|---|---|
| LLM verfügbar | 1 | `llm.invoke()` in `analyze_skill()` |
| LLM nicht verfügbar | 0 | Keyword-Fallback |

---

## Konfiguration

| Variable | Standard | Bedeutung |
|---|---|---|
| `OPENAI_API_KEY` | — | OpenAI für LLM-Analyse (Ollama-Fallback wenn nicht gesetzt) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama-Server |
| `OLLAMA_MODEL` | `llama3.2` | Modell für Skill-Analyse |
