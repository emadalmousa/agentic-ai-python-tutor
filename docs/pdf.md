# PDF Upload Prozess — Vollständige technische Dokumentation

## Überblick

Der PDF-Upload-Prozess verwandelt eine beliebige PDF-Datei in ein durchsuchbares Wissenssystem (RAG — Retrieval Augmented Generation). Danach kann der Tutor-Chat gezielt Antworten aus dem hochgeladenen Lernmaterial ziehen, statt nur auf das allgemeine Trainingswissen des LLMs zu stützen.

```
PDF-Datei → Text extrahieren → Chunks aufteilen → Vektoren berechnen → pgvector (PostgreSQL) speichern → Chat sucht darin
```

> **`⚡ LLM-Aufruf`** tritt **einmalig** auf — nur beim Vektoren berechnen (Phase 5)
> **`🟡 LangChain`** wird für Embeddings und pgvector-Speicherung verwendet

---

## Phase 0 — Frontend: Datei auswählen

**Datei:** `frontend/components/tutor/ChatPanel.tsx`, `frontend/hooks/useChat.ts`

> Kein LLM, kein LangChain — reines Frontend.

Der Nutzer klickt auf das Büroklammer-Icon. Es öffnet ein verstecktes `<input type="file">`:

```tsx
// ChatPanel.tsx
<input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={onFileInput} />
```

Sobald eine Datei ausgewählt wird, feuert `handleFileInput`:

```typescript
// useChat.ts
function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
  const file = e.target.files?.[0]
  if (file) uploadPdf(file)
  e.target.value = ""  // Reset — erlaubt dieselbe Datei nochmal hochzuladen
}
```

Der gesamte Chat wird gesperrt (`busy = loading || analyzing || uploading`) bis der Upload fertig ist.

---

## Phase 1 — Frontend: HTTP-Request senden

**Datei:** `frontend/lib/api.ts`

> Kein LLM, kein LangChain — normaler HTTP-Request.

Die Datei wird als `multipart/form-data` mit Bearer-Token gesendet:

```typescript
export async function uploadMaterial(file: File, token?: string): Promise<UploadResponse> {
  const form = new FormData()
  form.append("file", file)
  const headers: Record<string, string> = {}
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_URL}/tutor/upload-material`, { method: "POST", headers, body: form })
  return res.json()  // { status: "ok", chunks: 42 }
}
```

---

## Phase 2 — Backend: Endpoint empfängt und validiert

**Datei:** `backend/routers/tutor.py`, Zeile 37–66

> Kein LLM, kein LangChain — Validierung und Routing.

```python
@router.post("/upload-material", response_model=UploadResponse)
async def upload_material(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),  # JWT-Check
```

### 2.1 Validierung

```python
# Doppelter Check: Content-Type UND Dateiendung
# Manche Browser senden application/octet-stream statt application/pdf
if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt.")
```

### 2.2 Bytes in RAM laden

```python
pdf_bytes = await file.read()  # gesamte PDF als bytes im RAM
```

---

## Phase 3 — Text extrahieren: `extract_pages()`

**Datei:** `backend/agent/rag/loader.py`

> Kein LLM, kein LangChain — pypdf liest die PDF-Struktur direkt.

```python
def extract_pages(source: bytes) -> list[tuple[int, str]]:
    reader = PdfReader(io.BytesIO(source))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():           # leere Seiten überspringen
            pages.append((i + 1, text))     # (Seitennummer 1-basiert, Text)
    return pages
```

**Ergebnis:** `[(1, "Text Seite 1"), (2, "Text Seite 2"), ...]`

**Einschränkung:** Eingescannte PDFs ohne Text-Layer liefern leere Seiten — pypdf braucht einen Text-Layer (kein OCR).

---

## Phase 4 — Text aufteilen: `split_pages()`

**Datei:** `backend/agent/rag/splitter.py`

> Kein LLM, kein LangChain — reiner Python-Algorithmus.

Embedding-Modelle haben Token-Limits und präzise Suche braucht kleine, fokussierte Abschnitte:

```python
def split_pages(pages: list[tuple[int, str]]) -> list[dict]:
    # chunk_size=500 Zeichen, chunk_overlap=50 Zeichen
    # Jeder Chunk: {"text": "...", "page": 3}
```

**Splitter-Reihenfolge** (natürliche Grenzen bevorzugt):

| Priorität | Separator | Bedeutung |
|-----------|-----------|-----------|
| 1 | `\n\n` | Absätze (beste Qualität) |
| 2 | `\n` | Zeilenumbrüche |
| 3 | ` ` | Wortgrenzen |
| 4 | `""` | Zeichenweise (letzter Ausweg) |

**Überlapp:** 50 Zeichen Wiederholung zwischen Chunks — verhindert Kontext-Verlust an Grenzen.

**Ergebnis:** `[{"text": "Python ist...", "page": 1}, {"text": "...Sprache.", "page": 1}, ...]`

---

## Phase 5 — Vektoren berechnen und speichern: `build_and_save()`

**Datei:** `backend/agent/rag/vectorstore.py`

> **`⚡ LLM-Aufruf`** — einziger LLM-Aufruf beim gesamten Upload-Prozess
> **`🟡 LangChain`** — `get_embeddings()`, `PGVector.from_texts()`

### 5.1 Embedding-Modell auswählen: `get_embeddings()`

**Datei:** `backend/agent/config.py`, Zeile 75

> **`🟡 LangChain`** — gibt `OpenAIEmbeddings` oder `OllamaEmbeddings` zurück (beide LangChain-Klassen)

```python
def get_embeddings():
    # OpenAI verfügbar? → OpenAIEmbeddings (text-embedding-ada-002, 1536 Dimensionen)
    # sonst             → OllamaEmbeddings (llama3.2 lokal, 3072 Dimensionen)
```

Gleiche Schnittstelle für beide — `PGVector.from_texts()` merkt keinen Unterschied.

### 5.2 Vektoren berechnen und in PostgreSQL speichern

**Zeile ca. 20** `build_and_save(chunks, user_id)`

> **`⚡ LLM-Aufruf`** — `PGVector.from_texts()` ruft intern das Embedding-Modell auf
> **`🟡 LangChain`** — `PGVector.from_texts()` ist eine LangChain-Funktion

```python
PGVector.from_texts(
    texts=texts,                           # ["chunk1 text", "chunk2 text", ...]
    embedding=embeddings_model,            # OpenAIEmbeddings oder OllamaEmbeddings
    metadatas=[{"page": c["page"]} for c in chunks],  # Seitennummer pro Chunk
    collection_name=f"user_{user_id}",    # Pro-User-Isolation
    connection=_get_connection(),          # postgresql+psycopg://...
    pre_delete_collection=True,           # alten Index löschen bei neuem Upload
)
```

**Was `PGVector.from_texts()` intern macht:**
1. `embeddings_model.embed_documents(texts)` aufrufen → `⚡ LLM-Aufruf`
2. `"Python ist eine Sprache"` → `[0.021, -0.153, 0.847, ...]` (1536 oder 3072 Zahlen)
3. Vektoren + Texte + Metadaten in PostgreSQL speichern

**PostgreSQL-Tabellen danach:**

| Tabelle | Inhalt |
|---------|--------|
| `langchain_pg_collection` | Index-Name (`user_42`) und UUID |
| `langchain_pg_embedding` | Vektoren, Original-Texte, `cmetadata: {"page": 3}` |

Der Index lebt in PostgreSQL — kein Filesystem, kein Datenverlust bei Redeploy.

---

## Phase 6 — Backend antwortet

**Datei:** `backend/routers/tutor.py`, Zeile 66

> Kein LLM, kein LangChain.

```python
return UploadResponse(status="ok", chunks=len(chunks))
# → { "status": "ok", "chunks": 42 }
```

Frontend zeigt im Chat:
> 📚 **mein_lernmaterial.pdf** — 42 Chunks erstellt und indexiert.

---

## Phase 7 — Wie die Suche beim Chat funktioniert

**Dateien:** `backend/routers/tutor.py`, `backend/agent/rag/vectorstore.py`

### 7.1 Semantische Suche: `query_with_pages()`

> **`🟡 LangChain`** — `PGVector.similarity_search()` intern
> Kein LLM-Aufruf — nur Vektor-Vergleich in PostgreSQL

```python
def query_with_pages(index_data, message, top_k=3):
    store = index_data["store"]
    docs = store.similarity_search(message, k=top_k)  # 🟡 LangChain
    return [(doc.page_content, doc.metadata.get("page", 0)) for doc in docs]
```

### 7.2 Seitenzahl-Suche: `get_page()`

> Kein LLM — Regex erkennt Seitenzahl, pgvector filtert nach `cmetadata`

**Datei:** `backend/routers/tutor.py`, Zeile 113

```python
_PAGE_PATTERN = re.compile(r"\b(?:seite|page|s\.)\s*(\d+)\b", re.IGNORECASE)
# Erkennt: "Seite 5", "page 5", "s. 5"
```

```python
def get_page(index_data, page_num):
    store = index_data["store"]
    docs = store.similarity_search(" ", k=50, filter={"page": page_num})  # 🟡 LangChain
    return [(doc.page_content, page_num) for doc in docs]
```

---

## Vollständiger Datenfluss

```
Nutzer klickt Büroklammer
        │
        ▼
[Frontend] handleFileInput() → uploadPdf(file)
        │  FormData({ file: <PDF-Bytes> }) + Bearer-Token
        ▼
[HTTP]  POST /tutor/upload-material
        │
        ▼
[Backend] Validierung: PDF? Nicht leer?          ← kein LLM
        │
        ▼
[Backend] extract_pages(pdf_bytes)               ← kein LLM
        │  pypdf → [(1, "Text..."), (2, "Text...")]
        ▼
[Backend] split_pages(pages)                     ← kein LLM
        │  → [{"text": "...", "page": 1}, ...]
        ▼
[Backend] build_and_save(chunks, user_id)
        │
        ├─► get_embeddings()                     ← 🟡 LangChain
        │     OpenAI? → OpenAIEmbeddings
        │     sonst   → OllamaEmbeddings
        │
        └─► PGVector.from_texts()                ← ⚡ LLM-AUFRUF + 🟡 LangChain
              Text → Vektor → PostgreSQL speichern
              collection: "user_42"
        │
        ▼
[HTTP]  { "status": "ok", "chunks": 42 }
        │
        ▼
[Frontend] "📚 dokument.pdf — 42 Chunks indexiert"
        │
        ▼
[Ab jetzt] jede Chat-Frage sucht im pgvector-Index   ← 🟡 LangChain, kein LLM
           → Kontext gefunden: run_chat_with_context() ← ⚡ LLM-Aufruf
           → kein PDF:         run_chat() ReAct-Agent  ← ⚡ LLM-Aufruf
```

---

## LLM-Aufrufe beim Upload

| Phase | LLM-Aufruf | LangChain |
|-------|-----------|-----------|
| Phase 0–4 | keiner | nein |
| Phase 5 `PGVector.from_texts()` | **ja** — Text → Vektor | **ja** |
| Phase 6 | keiner | nein |
| Phase 7 Suche `similarity_search()` | keiner | **ja** |
| Phase 7 Chat-Antwort `llm.invoke()` | **ja** — LLM antwortet | **ja** |

**LLM-Aufrufe gesamt beim Upload: 1**
**LLM-Aufrufe gesamt beim Chat mit PDF: 2** (Classifier + Antwort)

---

## Was ist LangChain, was ist normaler Code

| Code | Typ | Datei / Zeile |
|---|---|---|
| `PGVector.from_texts()` | **🟡 LangChain** | `vectorstore.py` |
| `PGVector.similarity_search()` | **🟡 LangChain** | `vectorstore.py` |
| `OpenAIEmbeddings`, `OllamaEmbeddings` | **🟡 LangChain** | `config.py:75` |
| `get_embeddings()` | **🟡 LangChain** abstrahiert | `config.py:75` |
| `PdfReader`, `extract_text()` | normaler Code (pypdf) | `loader.py` |
| `split_pages()`, `_recursive_split()` | normaler Code | `splitter.py` |
| `_extract_page_number()` | normaler Code (Regex) | `tutor.py:117` |
| `db.query(...)`, `HTTPException` | normaler Code | `tutor.py` |

---

## Konfiguration via Umgebungsvariablen

| Variable | Standard | Bedeutung |
|----------|----------|-----------|
| `RAG_CHUNK_SIZE` | `500` | Maximale Zeichenanzahl pro Chunk |
| `RAG_CHUNK_OVERLAP` | `50` | Überlapp zwischen aufeinanderfolgenden Chunks |
| `DATABASE_URL` | `postgresql://app:app@localhost:5432/ki_tutor` | PostgreSQL-Verbindung |
| `RAG_TOP_K` | `3` | Anzahl der zurückgegebenen Chunks bei Suche |
| `OPENAI_API_KEY` | — | OpenAI-Key für Embeddings (Ollama-Fallback wenn nicht gesetzt) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama-Server-URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama-Modell (für Embeddings und Chat) |

---

## Wichtige Einschränkungen

1. **Per-User-Index** — jeder User hat seine eigene pgvector-Collection `user_{id}`. Ein neuer Upload überschreibt nur seine eigene Collection (`pre_delete_collection=True`).
2. **Eingescannte PDFs** ohne Text-Layer funktionieren nicht — pypdf braucht einen Text-Layer (kein OCR).
3. **RAM-Limit** — die gesamte PDF wird beim Upload in den RAM geladen.
4. **Kein Hot-Reload** — der Index wird bei jedem Aufruf frisch aus PostgreSQL geladen (kein In-Memory-Cache).
5. **Render-Persistenz** — Vektoren überleben Redeploys, da sie in PostgreSQL gespeichert sind (kein Datenverlust wie bei Filesystem-basiertem FAISS).
