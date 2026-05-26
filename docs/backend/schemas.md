# models/schemas.py

**Pfad:** `backend/models/schemas.py`
**Zweck:** Alle Pydantic-Modelle für HTTP-Requests und -Responses. FastAPI validiert automatisch gegen diese Schemas.

## Modelle

### `CodeRequest`

Eingehende Daten für `POST /tutor/analyze` und `POST /tutor/run`.

```python
class CodeRequest(BaseModel):
    code: str
```

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `code` | `str` | Python-Code des Schülers |

---

### `TutorResponse`

Antwort von `POST /tutor/analyze`.

```python
class TutorResponse(BaseModel):
    explanation: str
    error_found: bool
    error_type: str = "Kein Fehler"
    suggestion: str
    next_exercise: str | None = None
    sources: list[str] = []
```

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `explanation` | `str` | — | Schritt-für-Schritt-Erklärung auf Deutsch |
| `error_found` | `bool` | — | `true` wenn Fehler gefunden wurde |
| `error_type` | `str` | `"Kein Fehler"` | `"Syntaxfehler"` / `"Logikfehler"` / `"Kein Fehler"` |
| `suggestion` | `str` | — | Fehlerbeschreibung oder Verbesserungshinweis |
| `next_exercise` | `str\|None` | `None` | Übungsaufgabe vom `exercise_tool` |
| `sources` | `list[str]` | `[]` | Relevante Textstellen aus hochgeladenem Lernmaterial (RAG) |

---

### `ChatMessage`

Ein einzelner Eintrag in der Chat-History.

```python
class ChatMessage(BaseModel):
    role: str      # "user" oder "assistant"
    content: str
```

---

### `ChatRequest`

Eingehende Daten für `POST /tutor/chat`.

```python
class ChatRequest(BaseModel):
    code: str
    message: str
    history: list[ChatMessage] = []
```

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `code` | `str` | — | Aktueller Code des Schülers (wird als Kontext mitgesendet) |
| `message` | `str` | — | Neue Nachricht des Nutzers |
| `history` | `list[ChatMessage]` | `[]` | Bisheriger Gesprächsverlauf |

---

### `ChatResponse`

Antwort von `POST /tutor/chat`.

```python
class ChatResponse(BaseModel):
    reply: str
    history: list[ChatMessage]
```

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `reply` | `str` | Tutor-Antwort auf die neue Nachricht |
| `history` | `list[ChatMessage]` | Gesamte aktualisierte History inkl. neuer Nachricht |

---

### `RunRequest`

Eingehende Daten für `POST /tutor/run`.

```python
class RunRequest(BaseModel):
    code: str
```

---

### `RunResponse`

Antwort von `POST /tutor/run`.

```python
class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
```

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `stdout` | `str` | Ausgabe des Programms |
| `stderr` | `str` | Fehlermeldungen (leer wenn kein Fehler) |
| `exit_code` | `int` | `0` = Erfolg, `1` = Fehler |

---

### `UploadResponse`

Antwort von `POST /tutor/upload-material`.

```python
class UploadResponse(BaseModel):
    status: str
    chunks: int
```

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `status` | `str` | `"ok"` wenn erfolgreich |
| `chunks` | `int` | Anzahl der erstellten Text-Chunks im FAISS-Index |
