# Feature: Agent-Gedächtnis (ConversationSummaryMemory)

## Was ist das?

Der Tutor-Agent fasst nach jedem Chat-Turn die Unterhaltung per LLM zusammen und speichert diese Zusammenfassung in der Datenbank. Bei der nächsten Frage — auch in einer völlig neuen Session — wird die Zusammenfassung automatisch in den System-Prompt injiziert. Der Agent "erinnert" sich dadurch an frühere Fehler, besprochene Themen und den Lernfortschritt des Schülers.

## Datenfluss

```
Schüler schickt Nachricht
         │
         ▼
tutor.py → chat()
         │
         ├── load_memory(user_id, db)
         │       SELECT summary FROM agent_memory WHERE user_id = ?
         │       → None wenn noch keine Session existiert
         │
         ├── run_chat(..., memory_summary=summary)
         │       → _build_chat_system_prompt() injiziert Memory-Block:
         │         "Gedächtnis (frühere Sessions): ..."
         │       → Agent antwortet mit Kontext aus früheren Sessions
         │
         └── update_memory(user_id, db, user_msg, reply)
                 → get_classifier_llm().invoke([...])        ← LLM-AUFRUF
                   System: "Erstelle kompakte Zusammenfassung (max. 150 Wörter)"
                   Input:  alte Zusammenfassung + neuer Austausch
                   Output: neue Zusammenfassung
                 → UPSERT agent_memory WHERE user_id = ?
```

## Datenbankmodell

```
agent_memory
  id          INTEGER PRIMARY KEY
  user_id     INTEGER UNIQUE FK → users.id
  summary     TEXT              (max. 2000 Zeichen, LLM-generiert)
  updated_at  TIMESTAMP
```

Ein Eintrag pro User — kein Wachstum über Zeit, immer nur die aktuellste Zusammenfassung.

## Schlüsseldateien

| Datei | Funktion |
|---|---|
| `backend/models/agent_memory.py` | DB-Modell: AgentMemory |
| `backend/services/memory_service.py` | `load_memory()` + `update_memory()` |
| `backend/agent/tutor_agent.py` | `_build_chat_system_prompt()` — Memory-Block Injektion |
| `backend/routers/tutor.py` | Memory laden + nach Antwort updaten |

## LLM-Aufrufe

| Aufruf | Modell | Zweck |
|---|---|---|
| `update_memory()` | `get_classifier_llm()` (gpt-4o-mini / Ollama) | Zusammenfassung komprimieren |

## Beispiel System-Prompt (mit Gedächtnis)

```
Du bist ein freundlicher Python-Tutor. Antworte auf Deutsch, kurz und verständlich.

Student-Level: Anfänger
Schwache Bereiche: For-Schleifen, Funktionen

Gedächtnis (frühere Sessions):
Der Student hat For-Schleifen besprochen und hatte Probleme mit der Einrückung.
Er hat Funktionen noch nicht vollständig verstanden. Beim letzten Mal hat er
erfolgreich eine einfache while-Schleife geschrieben.

Aktueller Code des Schülers:
```python
for i in range(5):
print(i)
```
```

## Fehlerbehandlung

`update_memory()` fängt alle Exceptions still ab und macht ein `db.rollback()`. Das Gedächtnis ist non-critical — ein Fehler beim Updaten darf niemals den Chat-Flow unterbrechen.
