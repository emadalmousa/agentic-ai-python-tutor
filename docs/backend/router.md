# routers/tutor.py

**Pfad:** `backend/routers/tutor.py`
**Zweck:** Alle HTTP-Endpunkte der Anwendung. Jeder Endpunkt empfängt einen validierten Request, delegiert an die passende Business-Logik und gibt eine typisierte Response zurück.

## Endpunkte

### `POST /tutor/analyze` — Code analysieren

```python
@router.post("/analyze", response_model=TutorResponse)
def analyze_code(request: CodeRequest) -> TutorResponse
```

Ruft `run_analysis(request.code)` auf und baut daraus eine `TutorResponse`.

**Request:** `{"code": "for i in range(5)\n    print(i)"}`

**Response:** `TutorResponse` mit allen 6 Feldern inkl. `sources`

**Fehlerfall:** Wenn `run_analysis` eine `ServiceUnavailableError` wirft → HTTP 503 (wird in `main.py` abgefangen).

---

### `POST /tutor/upload-material` — PDF hochladen

```python
@router.post("/upload-material", response_model=UploadResponse)
async def upload_material(file: UploadFile = File(...)) -> UploadResponse
```

Nimmt eine PDF-Datei entgegen, verarbeitet sie durch die RAG-Pipeline und speichert den FAISS-Index.

**Ablauf:**
1. Prüft Content-Type und Dateiendung (nur `.pdf` erlaubt → HTTP 400 sonst)
2. Prüft ob Datei nicht leer ist → HTTP 400 sonst
3. `extract_text(pdf_bytes)` → Text extrahieren
4. `split_text(text)` → Chunks erzeugen
5. `build_and_save(chunks)` → FAISS-Index speichern
6. Gibt `{"status": "ok", "chunks": N}` zurück

**Response:** `{"status": "ok", "chunks": 142}`

---

### `POST /tutor/run` — Code ausführen

```python
@router.post("/run", response_model=RunResponse)
def run_code(request: RunRequest) -> RunResponse
```

Führt Python-Code direkt im lokalen Interpreter aus. **Kein LLM involviert.**

**Ablauf:**
1. Code in temporäre `.py`-Datei schreiben (`tempfile.NamedTemporaryFile`)
2. `subprocess.run([sys.executable, tmp_path], timeout=10)` ausführen
3. Temporäre Datei löschen (`finally`-Block → läuft immer)
4. `stdout`, `stderr` und `exit_code` zurückgeben

**Schutzmaßnahmen:**
- `timeout=10` — bricht nach 10 Sekunden ab (Schutz vor Endlosschleifen)
- `sys.executable` — nutzt denselben Python-Interpreter wie das Backend (aus dem venv)

**Response-Beispiele:**

```json
{"stdout": "Hallo Welt\n", "stderr": "", "exit_code": 0}
{"stdout": "", "stderr": "SyntaxError: ...", "exit_code": 1}
{"stdout": "", "stderr": "Timeout: Code lief länger als 10 Sekunden.", "exit_code": 1}
```

---

### `POST /tutor/chat` — Chat

```python
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse
```

Freier Chat mit dem Tutor. Nutzt Off-Topic-Filter bevor das teure Hauptmodell aufgerufen wird.

**Ablauf:**

**Schritt 1 — Off-Topic-Filter:**
`_is_python_related(request.message)` ruft `get_classifier_llm()` auf (günstiges Modell).
- System-Prompt: "Antworte NUR mit 'ja' oder 'nein' ob die Nachricht mit Python zu tun hat."
- Antwort beginnt mit "ja" → Weiter zu Schritt 2
- Sonst → sofort zurück mit Off-Topic-Antwort (kein teures Hauptmodell aufgerufen)

**Schritt 2 — LLM-Chat mit History:**
Baut die Nachrichten-Liste für das LLM auf:
```
SystemMessage: "Du bist ein Python-Tutor... Aktueller Code: [code]"
HumanMessage:  [History-Eintrag 1]
AIMessage:     [History-Eintrag 2]
...
HumanMessage:  [Neue Nachricht]
```
Das LLM sieht den gesamten Verlauf → kann sich auf frühere Nachrichten beziehen.

**Response:** `{"reply": "range() erzeugt eine Zahlenfolge...", "history": [...]}`

**Warum LLM-Klassifikation statt Keywords?**
Ein lokaler Keyword-Filter ist unzuverlässig. Das kleine LLM versteht Kontext und erkennt zuverlässig ob eine Frage wirklich mit Python zusammenhängt.
