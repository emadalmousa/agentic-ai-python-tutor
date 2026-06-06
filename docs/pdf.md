# PDF Upload Prozess — Vollständige technische Dokumentation

## Überblick

Der PDF-Upload-Prozess verwandelt eine beliebige PDF-Datei in ein durchsuchbares Wissenssystem (RAG — Retrieval Augmented Generation). Danach kann der Tutor-Chat gezielt Antworten aus dem hochgeladenen Lernmaterial ziehen, statt nur auf das allgemeine Trainingswissen des LLMs zu stützen.

Der Prozess besteht aus **5 Phasen**, von denen nur die letzte (Embedding) das LLM benötigt:

```
PDF-Datei → Text extrahieren → Chunks aufteilen → Vektoren berechnen → FAISS speichern → Chat sucht darin
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

Die Datei wird als `multipart/form-data` an das Backend geschickt. Kein Auth-Token notwendig — der Upload-Endpoint ist öffentlich:

```typescript
export async function uploadMaterial(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append("file", file)          // Schlüssel muss "file" heißen (passt zum FastAPI-Parameter)

  const res = await fetch(`${API_URL}/tutor/upload-material`, {
    method: "POST",
    body: form,
    // Content-Type wird automatisch auf multipart/form-data gesetzt (mit Boundary)
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

FastAPI nimmt die multipart-Form-Daten entgegen und stellt sie als `UploadFile` bereit:

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

### 5.2 Embedding berechnen und FAISS-Index aufbauen

```python
def build_and_save(chunks: list[tuple[str, int]]) -> None:
    texts = [c for c, _ in chunks]              # Nur die Texte für das Embedding

    embeddings_model = get_embeddings()
    vectors = embeddings_model.embed_documents(texts)  # ← LLM-Aufruf: Text → Zahlenvektor
    #  Beispiel: "Python ist eine Sprache" → [0.021, -0.153, 0.847, ...]
    #                                          ↑ 1536 oder 3072 Zahlen pro Chunk

    vectors_array = np.array(vectors, dtype="float32")

    dimension = vectors_array.shape[1]          # Dimension des Embedding-Modells
    index = faiss.IndexFlatL2(dimension)        # L2-Distanz (euklidische Ähnlichkeit)
    index.add(vectors_array)                    # Alle Vektoren in den Index laden
```

**Was `embed_documents()` macht:**
- Jeder Text-Chunk wird in einen hochdimensionalen Zahlenvektor umgewandelt
- Texte mit ähnlicher Bedeutung landen geometrisch nah beieinander
- `"Python Variable"` und `"Variable in Python deklarieren"` haben einen ähnlichen Vektor
- Das ist die Grundlage für semantische Suche (nicht nur Keyword-Suche)

### 5.3 Auf Disk speichern

```python
    vectorstore_path = Path(_get_vectorstore_path())
    # Standard: backend/agent/rag/vectorstore/
    # Überschreibbar mit RAG_VECTORSTORE_PATH env var

    vectorstore_path.mkdir(parents=True, exist_ok=True)

    # FAISS-Index: die rohen Vektoren
    faiss.write_index(index, str(vectorstore_path / "index.faiss"))

    # Chunk-Metadaten: Texte + Seitennummern
    with open(vectorstore_path / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)  # [(text, page_number), ...]
```

**Zwei Dateien werden gespeichert:**

| Datei | Inhalt | Größe (Beispiel) |
|-------|--------|-----------------|
| `index.faiss` | Nur die Zahlenvektoren (binär) | ~1–5 MB pro 100 Chunks |
| `chunks.pkl` | Original-Texte + Seitennummern | ~200 KB pro 100 Chunks |

Diese zwei Dateien bilden zusammen den vollständigen Index. Beim nächsten Start des Backends werden sie automatisch geladen.

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

**Dateien:** `backend/agent/rag/vectorstore.py`, `backend/routers/tutor.py`

### 7.1 Normaler Chat: Semantische Suche via `rag_tool`

```python
# rag_tool.py — wird vom Agenten bei passenden Fragen aufgerufen
def rag_tool(query: str) -> str:
    index_data = load()           # index.faiss + chunks.pkl laden
    passages = vs_query(index_data, query, top_k=3)
    return "\n\n---\n\n".join(passages)
```

```python
# vectorstore.py — die eigentliche Suche
def query_with_pages(index_data, question: str, top_k: int = 3):
    query_vector = embeddings_model.embed_query(question)  # Frage → Vektor
    query_array = np.array([query_vector], dtype="float32")

    _, indices = index.search(query_array, top_k)  # k nächste Vektoren finden
    return [chunks[i] for i in indices[0]]         # Zugehörige Texte zurückgeben
```

**Ablauf bei einer Chat-Frage:**
1. Nutzer schreibt: `"Wie funktioniert eine for-Schleife?"`
2. Frage wird in einen Vektor umgewandelt (`embed_query`)
3. FAISS sucht die 3 geometrisch nächsten Vektoren im Index (`top_k=3`)
4. Die dazugehörigen Original-Texte werden als Kontext dem LLM gegeben
5. Das LLM antwortet mit Bezug auf das Lernmaterial

### 7.2 Seitenzahl-Suche: `"Erkläre Seite 5"`

```python
# tutor.py — _get_rag_context()
_PAGE_PATTERN = re.compile(r"\b(?:seite|page|s\.)\s*(\d+)\b", re.IGNORECASE)

def _get_rag_context(message: str) -> str:
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
- **Semantische Suche** (FAISS) — findet thematisch ähnliche Stellen

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
[Backend] build_and_save(chunks)
        │
        ├─► get_embeddings()
        │     OpenAI verfügbar? → OpenAIEmbeddings (text-embedding-ada-002)
        │     sonst             → OllamaEmbeddings (llama3.2 lokal)
        │
        ├─► embed_documents(texts)   ← EINZIGER LLM-AUFRUF beim Upload
        │     ["chunk1", "chunk2", ...] → [[0.02, -0.15, ...], ...]
        │
        ├─► faiss.IndexFlatL2 aufbauen + Vektoren hinzufügen
        │
        ├─► index.faiss speichern    (Vektoren, binär)
        └─► chunks.pkl speichern     (Texte + Seitennummern)
        │
        ▼
[HTTP]  { "status": "ok", "chunks": 42 }
        │
        ▼
[Frontend] Chat zeigt: "📚 dokument.pdf — 42 Chunks indexiert"
        │
        ▼
[Ab jetzt] Jede Chat-Frage kann über rag_tool in diesem Index suchen
```

---

## Konfiguration via Umgebungsvariablen

| Variable | Standard | Bedeutung |
|----------|----------|-----------|
| `RAG_CHUNK_SIZE` | `500` | Maximale Zeichenanzahl pro Chunk |
| `RAG_CHUNK_OVERLAP` | `50` | Überlapp zwischen aufeinanderfolgenden Chunks |
| `RAG_VECTORSTORE_PATH` | `backend/agent/rag/vectorstore/` | Speicherort für index.faiss und chunks.pkl |
| `RAG_TOP_K` | `3` | Anzahl der zurückgegebenen Chunks bei Suche |
| `OPENAI_API_KEY` | — | OpenAI-Key für Embeddings (Ollama-Fallback wenn nicht gesetzt) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama-Server-URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama-Modell (für Embeddings und Chat) |

---

## Wichtige Einschränkungen

1. **Kein persistenter Multi-User-Support** — der FAISS-Index ist global. Ein neuer Upload überschreibt den vorherigen für alle Nutzer.
2. **Eingescannte PDFs** ohne Text-Layer funktionieren nicht — pypdf braucht einen Text-Layer (kein OCR).
3. **RAM-Limit** — die gesamte PDF wird beim Upload in den RAM geladen.
4. **Kein Hot-Reload** — der Index wird bei jedem `rag_tool`-Aufruf frisch von Disk geladen (kein In-Memory-Cache).
