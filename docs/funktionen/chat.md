# Chat-Ablauf — Vollständige technische Dokumentation

## Überblick

Jede Chat-Nachricht durchläuft denselben Einstiegspunkt und verzweigt sich dann in **3 verschiedene Szenarien** je nach Kontext.

```
POST /tutor/chat
        │
        ├─► Off-Topic? → Standardantwort (kein LLM für Antwort)
        ├─► PDF hochgeladen? → Pfad A: direktes LLM
        └─► kein PDF → Pfad B: ReAct-Agent
```

---

## Gemeinsamer Anfang — bei jeder Nachricht

**Datei:** `backend/routers/tutor.py`

### Schritt 1 — Off-Topic-Check

**Zeile 122** `_is_python_related(message, code)`
**Zeile 128** `llm = get_classifier_llm()`
**Zeile 131** `response = llm.invoke([_CLASSIFY_SYSTEM, HumanMessage(...)])`

> **`🟡 LangChain`** — `llm.invoke()` ist ein LangChain-Aufruf
> **`⚡ LLM-Aufruf`** — `gpt-4o-mini` entscheidet: Python-relevant ja/nein

```python
# System-Prompt sagt dem LLM: antworte nur "ja" oder "nein"
# Wenn "nein" → sofort zurück mit OFF_TOPIC_REPLY (kein weiterer LLM-Aufruf)
```

---

### Schritt 2 — Skill-Fortschritt laden

**Zeile 208** `progress_rows = db.query(StudentSkillProgress).filter_by(user_id=...).all()`
**Zeile 210** `skill_progress = [{"skill_key": ..., "status": ..., "score": ...}, ...]`

> Kein LLM — reine Datenbankabfrage.
> Lädt welche Skills der Schüler hat (understood / partial / not_understood) und übergibt das dem Agent.

---

### Schritt 3 — pgvector-Suche

**Zeile 135** `def _get_rag_context(message, user_id)`
**Zeile 147** `index_data = load(user_id)` → `backend/agent/rag/vectorstore.py`
**Zeile 167** `query_with_pages(index_data, message, top_k=3)`

> **`🟡 LangChain`** — `PGVector.similarity_search()` intern
> Kein LLM-Aufruf — nur Vektor-Vergleich in PostgreSQL.

Wenn Seitenzahl erkannt (`"Seite 5"`):
**Zeile 155** `_extract_page_number(message)` → Regex-Match
**Zeile 157** `get_page(index_data, page_num)` → direkte Chunk-Abfrage nach `cmetadata.page`

---

## Szenario 0 — Off-Topic (kein Python-Bezug)

```
Schüler: "Was ist das Wetter heute?"
        ↓
_is_python_related() → "nein"   ← ⚡ LLM-Aufruf (gpt-4o-mini)
        ↓
return OFF_TOPIC_REPLY           ← kein weiterer LLM-Aufruf
```

**LLM-Aufrufe gesamt: 1**

---

## Szenario A — Mit PDF, semantische Suche

```
Schüler: "Was ist eine Schleife?"  (PDF hochgeladen)
        ↓
_is_python_related() → "ja"        ← ⚡ LLM-Aufruf 1 (gpt-4o-mini)
        ↓
_get_rag_context()
  PGVector.similarity_search()      ← 🟡 LangChain, kein LLM
  → 3 Chunks gefunden
        ↓
run_chat_with_context()             ← ⚡ LLM-Aufruf 2 (gpt-4o)
  llm.invoke([system, human])
  PDF-Chunks direkt im Prompt
  LLM antwortet auf Basis Lernmaterial
```

**Datei:** `backend/agent/tutor_agent.py`
**Zeile 190** `def run_chat_with_context(message, code, history, user_level, rag_context)`
**Zeile 203** `llm = get_llm()`
**Zeile 227** `response = llm.invoke([system, human])`

> **`⚡ LLM-Aufruf`** — direkt, kein Agent, kein ReAct-Loop
> **`🟡 LangChain`** — `llm.invoke()`, `SystemMessage`, `HumanMessage`

**LLM-Aufrufe gesamt: 2**

---

## Szenario B — Mit PDF, Seitenzahl-Suche

```
Schüler: "Erkläre Seite 5"   (PDF hochgeladen)
        ↓
_is_python_related() → "ja"        ← ⚡ LLM-Aufruf 1 (gpt-4o-mini)
        ↓
_get_rag_context()
  _extract_page_number() → 5       ← Regex, kein LLM
  get_page(index_data, 5)          ← 🟡 LangChain PGVector, kein LLM
  + query_with_pages() semantisch  ← 🟡 LangChain PGVector, kein LLM
  → alle Chunks von Seite 5 + semantische Treffer
        ↓
run_chat_with_context()             ← ⚡ LLM-Aufruf 2 (gpt-4o)
```

**LLM-Aufrufe gesamt: 2**

---

## Szenario C — Ohne PDF, normaler Chat

```
Schüler: "Warum funktioniert mein Code nicht?"  (kein PDF)
        ↓
_is_python_related() → "ja"        ← ⚡ LLM-Aufruf 1 (gpt-4o-mini)
        ↓
_get_rag_context() → leer          ← kein LLM
        ↓
run_chat()                          ← ReAct-Agent startet
  _build_chat_tools()               ← kein LLM, nur Tool-Objekte bauen
  _build_chat_system_prompt()       ← kein LLM, nur String
  agent.invoke()                    ← ⚡ LLM-Aufruf 2 (gpt-4o) — entscheidet Tool
  → Tool ausführen                  ← z.B. debug_code_tool
  → LLM formuliert Antwort          ← ⚡ LLM-Aufruf 3 (gpt-4o)
```

**Datei:** `backend/agent/tutor_agent.py`
**Zeile 159** `def run_chat(message, code, history, user_level, skill_progress)`
**Zeile 171** `llm = get_llm()`
**Zeile 172** `tools = _build_chat_tools(user_level, skill_progress)`
**Zeile 173** `system_prompt = _build_chat_system_prompt(user_level, skill_progress, code)`
**Zeile 174** `agent = create_agent(llm, tools, system_prompt=system_prompt)`
**Zeile 184** `result = agent.invoke({"messages": messages})`

> **`⚡ LLM-Aufruf`** — `agent.invoke()` ist der ReAct-Loop
> **`🟡 LangChain`** — `create_agent()`, `agent.invoke()`, Tool-Dekoratoren

**LLM-Aufrufe gesamt: 2–3** (abhängig ob Tool aufgerufen wird)

---

## Szenario D — Ohne PDF, Student will üben

```
Schüler: "Gib mir eine Übung zu Schleifen"
        ↓
_is_python_related() → "ja"        ← ⚡ LLM-Aufruf 1
        ↓
run_chat() → ReAct-Agent
  agent.invoke()                    ← ⚡ LLM-Aufruf 2 — wählt suggest_personalized_exercise
  suggest_personalized_exercise()   ← 🟡 LangChain @tool
    generate_exercise.invoke()      ← ⚡ LLM-Aufruf 3 — generiert Aufgabe
  LLM formuliert Antwort            ← ⚡ LLM-Aufruf 4
```

**Datei:** `backend/agent/tutor_agent.py`
**Zeile 82** `def _build_chat_tools(user_level, skill_progress)`
**Zeile 95** `def suggest_personalized_exercise(skill_key)` — `@tool` Closure
**Zeile 101** `generate_exercise.invoke({...})`

> **`🟡 LangChain`** — `@tool` Dekorator macht normale Python-Funktion zum LangChain-Tool

**LLM-Aufrufe gesamt: 3–4**

---

## Überblick: LLM-Aufrufe pro Szenario

| Szenario | Aufrufe | Warum |
|---|---|---|
| Off-Topic | 1 | nur Classifier |
| Mit PDF (semantisch) | 2 | Classifier + run_chat_with_context |
| Mit PDF (Seitenzahl) | 2 | Classifier + run_chat_with_context |
| Ohne PDF, einfach | 2–3 | Classifier + Agent + Tool optional |
| Ohne PDF, Übung | 3–4 | Classifier + Agent + Tool + Antwort |

---

## Überblick: Was ist LangChain, was ist normaler Code

| Code | Typ | Datei / Zeile |
|---|---|---|
| `llm.invoke()` | **🟡 LangChain** | `tutor_agent.py:227` |
| `agent.invoke()` | **🟡 LangChain** | `tutor_agent.py:184` |
| `PGVector.similarity_search()` | **🟡 LangChain** | `vectorstore.py` |
| `PGVector.from_texts()` | **🟡 LangChain** | `vectorstore.py` |
| `@tool` Dekorator | **🟡 LangChain** | `tutor_agent.py:91` |
| `SystemMessage`, `HumanMessage` | **🟡 LangChain** | `tutor_agent.py:212` |
| `create_agent()` | **🟡 LangChain** | `tutor_agent.py:174` |
| `get_llm()`, `get_embeddings()` | **🟡 LangChain** abstrahiert | `config.py:75` |
| `db.query(StudentSkillProgress)` | normaler Code | `tutor.py:208` |
| `_extract_page_number()` | normaler Code (Regex) | `tutor.py:117` |
| `subprocess.run()` | normaler Code | `tutor.py:80` |
