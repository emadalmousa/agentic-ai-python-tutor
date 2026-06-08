# PDF Upload Prozess — Vollständige technische Dokumentation

## Überblick

Der PDF-Upload-Prozess verwandelt eine beliebige PDF-Datei in ein durchsuchbares Wissenssystem (RAG — Retrieval Augmented Generation). Danach kann der Tutor-Chat gezielt Antworten aus dem hochgeladenen Lernmaterial ziehen, statt nur auf das allgemeine Trainingswissen des LLMs zu stützen.

Der Prozess besteht aus **5 Phasen**, von denen nur die letzte (Embedding) das LLM benötigt:

```
PDF-Datei → Text extrahieren → Chunks aufteilen → Vektoren berechnen → pgvector (PostgreSQL) speichern → Chat sucht darin
```

---

## Phase 0 — Frontend: Datei auswählen

**Dateien:** `frontend/components/tutor/ChatPanel.tsx`, `frontend/hooks/useChat.ts`

Der Nutzer klickt auf das Büroklammer-Icon im Chat-Eingabefeld. Dieses Icon löst `openFilePicker()` aus, das einen versteckten `<input type="file" accept=".pdf">` programmatisch anklickt:

```tsx
// ChatPanel.tsx — verstecktes Input-Element
<input
  ref={fileInputRef}
  type="file"
  accept=".pdf"
  className="hidden"
  onChange={onFileInput}
/>
```

Sobald der Nutzer eine Datei auswählt, feuert `handleFileInput`:

```typescript
// useChat.ts
function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
  const file = e.target.files?.[0]
  if (file) uploadPdf(file)
  e.target.value = ""  // Reset — erlaubt dieselbe Datei nochmal hochzuladen
}
```

Während des Uploads wird der gesamte Chat-Bereich gesperrt (`busy = loading || analyzing || uploading`) und ein Ladeindikator angezeigt.

---

## Phase 1 — Frontend: HTTP-Request senden

**Datei:** `frontend/lib/api.ts`

Die Datei wird als `multipart/form-data` an das Backend geschickt. Ein Bearer-Token ist erforderlich — der Endpoint ist JWT-geschützt:

```typescript
export async function uploadMaterial(file: File, token?: string): Promise<UploadResponse> {
  const form = new FormData()
  form.append("file", file)          // Schlüssel muss "file" heißen (passt zum FastAPI-Parameter)
  const headers: Record<string, string> = {}
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_URL}/tutor/upload-material`, {
    method: "POST",
    headers,
    body: form,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `Upload-Fehler: ${res.status}`)
  }
  return res.json()  // { status: "ok", chunks: 42 }
}
```

Nach Erfolg zeigt der Chat eine Bestätigungsnachricht mit der Chunk-Anzahl:

```typescript
// useChat.ts
const msg: ChatMessage = {
  role: "assistant",
  content: `📚 **${file.name}**\n\n${data.chunks} Chunks erstellt und indexiert.`,
}
```

---

## Phase 2 — Backend: Endpoint empfängt und validiert

**Datei:** `backend/routers/tutor.py`, Zeile 32–75

```
POST /tutor/upload-material
```

FastAPI nimmt die multipart-Form-Daten entgegen und stellt sie als `UploadFile` bereit. Der Endpoint erfordert einen gültigen JWT-Token:

```python
@router.post("/upload-material", response_model=UploadResponse)
async def upload_material(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
```

Die User-ID des eingeloggten Nutzers wird zu `build_and_save()` übergeben.

### 2.1 Validierung (kein LLM)

```python
content_type = file.content_type or ""
filename = file.filename or ""

# Doppelter Check: Content-Type UND Dateiendung
if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt.")
```

Warum doppelter Check? Manche Browser senden `application/octet-stream` statt `application/pdf` — der Dateiendungs-Fallback fängt das ab.

### 2.2 Bytes in RAM laden (kein LLM)

```python
pdf_bytes = await file.read()  # Gesamte Datei als bytes im Arbeitsspeicher

if not pdf_bytes:
    raise HTTPException(status_code=400, detail="Die hochgeladene Datei ist leer.")
```

Die gesamte PDF wird in den RAM geladen. Bei großen PDFs kann das viel Speicher brauchen — für den Tutor-Kontext (Lernmaterial) ist das kein Problem.

---

## Phase 3 — Text extrahieren: `extract_pages()`

**Datei:** `backend/agent/rag/loader.py`

```python
from pypdf import PdfReader

def extract_pages(source: bytes | str) -> list[tuple[int, str]]:
    reader = PdfReader(io.BytesIO(source))  # bytes → File-like-Object

    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()          # pypdf extrahiert Text aus PDF-Struktur
        if text and text.strip():           # Leere Seiten (z.B. Bilder) werden übersprungen
            pages.append((i + 1, text))     # (Seitennummer 1-basiert, Text)

    if not pages:
        raise ValueError("Kein Text aus der PDF extrahiert — Datei ist leer oder nicht lesbar.")

    return pages
```

**Was hier passiert:**
- `pypdf.PdfReader` parst die PDF-Binärstruktur
- Jede Seite wird in rohen Text umgewandelt (kein Layout, keine Formatierung)
- Seiten ohne Text (z.B. reine Bildseiten oder eingescannte PDFs ohne OCR) werden ignoriert
- Rückgabe: Liste von `(Seitennummer, Text)`-Tupeln, 1-basiert

**Wichtige Einschränkung:** Eingescannte PDFs ohne Text-Layer liefern leere Seiten. Das System kann dann keinen Text extrahieren.

---

## Phase 4 — Text aufteilen: `split_pages()`

**Datei:** `backend/agent/rag/splitter.py`

Langer Text kann nicht direkt als Ganzes in einen Vektor umgewandelt werden — Embedding-Modelle haben Token-Limits, und präzise Suche braucht kleine, fokussierte Abschnitte.

```python
def split_pages(pages: list[tuple[int, str]]) -> list[tuple[str, int]]:
    chunk_size    = int(os.getenv("RAG_CHUNK_SIZE", "500"))     # Standard: 500 Zeichen
    chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))   # Standard: 50 Zeichen Überlapp

    result: list[tuple[str, int]] = []
    for page_num, text in pages:
        chunks = _recursive_split(text, chunk_size, chunk_overlap)
        for chunk in chunks:
            result.append((chunk, page_num))  # Chunk behält seine Seitenreferenz

    return result
```

### 4.1 Wie das Splitten funktioniert: `_recursive_split()`

Der Algorithmus versucht den Text an natürlichen Grenzen zu teilen, in dieser Reihenfolge:

| Priorität | Separator | Bedeutung |
|-----------|-----------|-----------|
| 1 | `\n\n` | Absätze (beste Qualität) |
| 2 | `\n` | Zeilenumbrüche |
| 3 | ` ` (Leerzeichen) | Wortgrenzen |
| 4 | `""` (leer) | Zeichenweise (letzter Ausweg) |

### 4.2 Chunk-Aufbau mit Überlapp

```
Text: [Teil A][Teil B][Teil C][Teil D][Teil E]
                                  ↑chunk_size

Chunk 1: [Teil A][Teil B][Teil C]
Chunk 2:               [Teil C][Teil D][Teil E]   ← Überlapp: Teil C wiederholt
```

Der **Überlapp** (50 Zeichen) sorgt dafür, dass Sätze, die an einer Chunk-Grenze stehen, in beiden Chunks vorhanden sind. So geht kein Kontext verloren.

### 4.3 Ergebnis

```python
# Beispiel-Output für eine 3-seitige PDF
[
  ("Python ist eine interpretierte Sprache...", 1),
  ("...erleichtert die Lesbarkeit des Codes.", 1),
  ("Variablen müssen nicht deklariert werden...", 2),
  ("...Zuweisung erstellt automatisch eine Variable.", 2),
  # ...
]
```

Jeder Chunk weiß, von welcher Seite er stammt — wichtig für später: `"Erkläre Seite 3"`.

---

## Phase 5 — Vektoren berechnen und speichern: `build_and_save()`

**Datei:** `backend/agent/rag/vectorstore.py`

Hier kommt das LLM/Embedding-Modell zum ersten und einzigen Mal zum Einsatz.

### 5.1 Embedding-Modell auswählen: `get_embeddings()`

**Datei:** `backend/agent/config.py`

```python
def get_embeddings():
    api_key = os.getenv("OPENAI_API_KEY", "")

    if api_key and not api_key.startswith("sk-..."):
        try:
            # Prüft ob OpenAI wirklich erreichbar ist (kein Placeholder-Key)
            client = openai.OpenAI(api_key=api_key)
            client.models.list()
            return OpenAIEmbeddings(api_key=api_key)  # text-embedding-ada-002
        except Exception as e:
            logger.warning("OpenAI nicht verfügbar — Fallback auf Ollama")

    # Lokales Embedding-Modell (z.B. llama3.2 via Ollama)
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
    )
```

**Fallback-Logik:**
- OpenAI verfügbar → `text-embedding-ada-002` (1536 Dimensionen, hohe Qualität)
- OpenAI nicht verfügbar → Ollama lokal (Dimension abhängig vom Modell, z.B. llama3.2: 3072)

### 5.2 Embedding berechnen und pgvector-Index aufbauen

```python
def build_and_save(chunks: list[dict], user_id: int) -> None:
    texts = [c["text"] for c in chunks]         # Nur die Texte für das Embedding
    metadatas = [{"page": c["page"]} for c in chunks]  # Seitennummer als Metadaten

    embeddings_model = get_embeddings()
    # PGVector.from_texts ruft embed_documents() intern auf → LLM-Aufruf: Text → Zahlenvektor
    #  Beispiel: "Python ist eine Sprache" → [0.021, -0.153, 0.847, ...]
    #                                          ↑ 1536 oder 3072 Zahlen pro Chunk

    PGVector.from_texts(
        texts=texts,
        embedding=embeddings_model,
        metadatas=metadatas,
        collection_name=f"user_{user_id}",   # Pro-User-Isolation via Collection-Name
        connection=_get_connection(),          # postgresql+psycopg://... (psycopg3-Format)
        pre_delete_collection=True,           # Alten Index löschen → frischer Upload
    )
```

**Was `PGVector.from_texts()` macht:**
- Jeder Text-Chunk wird in einen hochdimensionalen Zahlenvektor umgewandelt
- Texte mit ähnlicher Bedeutung landen geometrisch nah beieinander
- `"Python Variable"` und `"Variable in Python deklarieren"` haben einen ähnlichen Vektor
- Das ist die Grundlage für semantische Suche (nicht nur Keyword-Suche)

### 5.3 In PostgreSQL speichern

```python
# PGVector speichert automatisch in zwei PostgreSQL-Tabellen:
# langchain_pg_collection → { name: "user_42", ... }
# langchain_pg_embedding  → { collection_id, embedding: vector, document: text, cmetadata: {"page": 3} }
```

**PostgreSQL-Tabellen:**

| Tabelle | Inhalt |
|---------|--------|
| `langchain_pg_collection` | Index-Name (`user_<id>`) und UUID |
| `langchain_pg_embedding` | Vektoren, Original-Texte und Seitennummern (cmetadata) |

Der Index lebt in PostgreSQL — kein Filesystem, kein Datenverlust bei Redeploy.

---

## Phase 6 — Backend antwortet

```python
return UploadResponse(status="ok", chunks=len(chunks))
# → { "status": "ok", "chunks": 42 }
```

Das Frontend zeigt im Chat:
> 📚 **mein_lernmaterial.pdf**
> 42 Chunks erstellt und indexiert.

---

## Phase 7 — Wie die Suche danach funktioniert

**Dateien:** `backend/agent/rag/vectorstore.py`, `backend/routers/tutor.py`, `backend/agent/tutor_agent.py`

### 7.1 Chat mit PDF: Direkter LLM-Aufruf via `_get_rag_context()`

```python
# routers/tutor.py — bei jeder Chat-Anfrage
rag_context = _get_rag_context(request.message, current_user.id)

if rag_context:
    # PDF hochgeladen → direkter LLM-Aufruf, KEIN Agent, KEIN ReAct-Loop
    reply = run_chat_with_context(
        message=request.message,
        code=request.code,
        history=request.history,
        user_level=current_user.level,
        rag_context=rag_context,
    )
else:
    # Kein PDF → normaler ReAct-Agent mit Tools
    reply = run_chat(message=..., code=..., history=..., ...)
```

```python
# tutor_agent.py
def run_chat_with_context(message, code, history, user_level, rag_context) -> str:
    llm = get_llm()
    system = SystemMessage(content="Du bist ein freundlicher Python-Tutor...")
    human = HumanMessage(content=(
        f"Aus dem hochgeladenen Lernmaterial wurden folgende relevante Passagen gefunden:\n\n"
        f"{rag_context}\n\n"
        f"Frage des Schülers: {message}\n\n"
        "Beantworte die Frage auf Basis der Passagen aus dem Lernmaterial..."
    ))
    response = llm.invoke([system, human])
    return str(response.content)
```

**Ablauf bei einer Chat-Frage wenn PDF hochgeladen:**
1. `_get_rag_context(message, user_id)` sucht im pgvector-Index des Users
2. Wenn Kontext gefunden → `run_chat_with_context()` aufgerufen (kein Agent)
3. PDF-Chunks werden direkt in den Prompt eingebettet
4. LLM antwortet mit Bezug auf das Lernmaterial — deterministisch, ohne ReAct-Loop

### 7.2 Seitenzahl-Suche: `"Erkläre Seite 5"`

```python
# tutor.py — _get_rag_context()
_PAGE_PATTERN = re.compile(r"\b(?:seite|page|s\.)\s*(\d+)\b", re.IGNORECASE)

def _get_rag_context(message: str, user_id: int) -> str:
    index_data = load(user_id)  # lädt pgvector-Collection user_{user_id} aus PostgreSQL
    
    page_num = _extract_page_number(message)  # Erkennt "Seite 5", "page 5", "s. 5"

    if page_num is not None:
        # Direkte Suche: alle Chunks dieser Seite (kein Vektor-Vergleich nötig)
        page_chunks = get_page(index_data, page_num)

    # Zusätzlich: semantische Suche nach dem Rest der Frage
    semantic_chunks = query_with_pages(index_data, message, top_k=3)

    # Duplikate entfernen, Seiteninhalte zuerst
    # → Kombiniertes Ergebnis als Kontext für das LLM
```

Diese hybride Strategie kombiniert:
- **Direkte Suche** (wenn Seitenzahl genannt wird) — 100% präzise
- **Semantische Suche** (pgvector) — findet thematisch ähnliche Stellen

---

## Vollständiger Datenfluss (Zusammenfassung)

```
Nutzer klickt Büroklammer
        │
        ▼
[Frontend] fileInputRef.current.click()
        │  → Nutzer wählt PDF aus
        ▼
[Frontend] handleFileInput() → uploadPdf(file)
        │  → FormData({ file: <PDF-Bytes> })
        ▼
[HTTP]  POST /tutor/upload-material
        │  Content-Type: multipart/form-data
        ▼
[Backend] Validierung: PDF? Nicht leer?
        │
        ▼
[Backend] extract_pages(pdf_bytes)
        │  pypdf.PdfReader → [(1, "Text Seite 1"), (2, "Text Seite 2"), ...]
        ▼
[Backend] split_pages(pages)
        │  Rekursives Splitten an \n\n → \n → " "
        │  chunk_size=500, chunk_overlap=50
        │  → [("chunk text...", page_num), ...]
        ▼
[Backend] build_and_save(chunks, user_id)
        │
        ├─► get_embeddings()
        │     OpenAI verfügbar? → OpenAIEmbeddings (text-embedding-ada-002)
        │     sonst             → OllamaEmbeddings (llama3.2 lokal)
        │
        ├─► embed_documents(texts)   ← EINZIGER LLM-AUFRUF beim Upload
        │     ["chunk1", "chunk2", ...] → [[0.02, -0.15, ...], ...]
        │
        ├─► PGVector.from_texts()
        │     → langchain_pg_collection + langchain_pg_embedding (PostgreSQL)
        │       collection_name: "user_42", cmetadata: {"page": 3}
        │
        ▼
[HTTP]  { "status": "ok", "chunks": 42 }
        │
        ▼
[Frontend] Chat zeigt: "📚 dokument.pdf — 42 Chunks indexiert"
        │
        ▼
[Ab jetzt] Jede Chat-Frage sucht automatisch im pgvector-Index des Users
           → wenn Kontext gefunden: run_chat_with_context() — kein Agent
           → wenn kein PDF:        run_chat() — ReAct-Agent mit Tools
```

---

## Konfiguration via Umgebungsvariablen

| Variable | Standard | Bedeutung |
|----------|----------|-----------|
| `RAG_CHUNK_SIZE` | `500` | Maximale Zeichenanzahl pro Chunk |
| `RAG_CHUNK_OVERLAP` | `50` | Überlapp zwischen aufeinanderfolgenden Chunks |
| `DATABASE_URL` | `postgresql://app:app@localhost:5432/ki_tutor` | PostgreSQL-Verbindung (psycopg3-Format wird automatisch angepasst) |
| `RAG_TOP_K` | `3` | Anzahl der zurückgegebenen Chunks bei Suche |
| `OPENAI_API_KEY` | — | OpenAI-Key für Embeddings (Ollama-Fallback wenn nicht gesetzt) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama-Server-URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama-Modell (für Embeddings und Chat) |

---

## Wichtige Einschränkungen

1. **Per-User-Index** — jeder User hat seine eigene pgvector-Collection `user_{id}` in PostgreSQL. Ein neuer Upload überschreibt nur seine eigene Collection (`pre_delete_collection=True`).
2. **Eingescannte PDFs** ohne Text-Layer funktionieren nicht — pypdf braucht einen Text-Layer (kein OCR).
3. **RAM-Limit** — die gesamte PDF wird beim Upload in den RAM geladen.
4. **Kein Hot-Reload** — der Index wird bei jedem Aufruf frisch aus PostgreSQL geladen (kein In-Memory-Cache).
5. **Render-Persistenz** — Vektoren überleben Redeploys, da sie in PostgreSQL gespeichert sind (kein Datenverlust wie bei Filesystem-basiertem FAISS).

---

## Zusammenfassung — Fokus LLM & LangChain

### Was passiert wenn ein User ein PDF hochlädt?

```
User lädt PDF hoch
        ↓
1. PyPDF liest jede Seite → Text extrahieren
        ↓
2. Text in Chunks schneiden (500 Zeichen, 50 Überlappung)
        ↓
3. LangChain ruft Embedding-Modell auf (OpenAI / Ollama)
        ↓
4. PGVector speichert die Vektoren in PostgreSQL  →  collection: user_42
```

### Die Rolle von LangChain

LangChain ist der **Vermittler** zwischen dem Text und dem LLM:

| LangChain | Was es macht |
|---|---|
| `PGVector.from_texts()` | ruft Embedding-Modell auf, speichert Vektoren in PostgreSQL |
| `PGVector(...)` | verbindet sich mit bestehender Collection in PostgreSQL |
| `similarity_search()` | sucht semantisch ähnliche Chunks via pgvector |

Ohne LangChain müsste man das alles selbst bauen — API-Aufrufe, Vektoren speichern, Ähnlichkeit berechnen.

### Die Rolle des LLM (Embedding-Modell)

Das LLM macht **Text → Zahlen**:

```
"for-Schleife wiederholt Code"  →  [0.23, -0.11, 0.87, ...]
"Schleife läuft mehrmals"       →  [0.21, -0.09, 0.84, ...]  ← nah dran
"Hund bellt laut"               →  [-0.92, 0.45, -0.33, ...]  ← weit weg
```

Ähnliche Bedeutung → ähnliche Zahlen. Das erlaubt semantische Suche.

### Beim Chat danach

```
Schüler fragt: "Was ist eine Schleife?"
        ↓
LangChain: Frage → Embedding-Modell → Vektor
        ↓
pgvector (PostgreSQL) vergleicht gegen alle gespeicherten Vektoren
        ↓
Top-3 ähnlichste Chunks aus dem PDF zurück
        ↓
LLM (gpt-4o / Ollama) beantwortet Frage MIT diesem Kontext
```

### Kernaussage

> Das PDF wird **einmalig** beim Upload in Vektoren umgewandelt und in PostgreSQL gespeichert. Bei jeder Chat-Frage sucht LangChain+pgvector semantisch die passenden Stellen — und das LLM antwortet dann auf Basis des echten Lernmaterials, nicht aus seinem allgemeinen Wissen. Die Vektoren überleben Redeploys, da sie in der Datenbank leben.
