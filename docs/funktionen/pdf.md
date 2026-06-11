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
<input ref={fileInputRef} type="file" accept=".pdf" className="hidden" onChange={onFileInput} />
```

---

## Phase 1 — Frontend: HTTP-Request senden

**Datei:** `frontend/lib/api.ts`

> Kein LLM, kein LangChain — normaler HTTP-Request.

Die Datei wird als `multipart/form-data` mit Bearer-Token gesendet.

---

## Phase 2 — Backend: Endpoint empfängt und validiert

**Datei:** `backend/routers/tutor.py`, Zeile 37–66

> Kein LLM, kein LangChain — Validierung und Routing.

### 2.1 Validierung

**Zeile 45** — doppelter Check: Content-Type UND Dateiendung
```python
if content_type != "application/pdf" and not filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt.")
```

### 2.2 Bytes in RAM laden

**Zeile 48** `pdf_bytes = await file.read()`

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

**Einschränkung:** Eingescannte PDFs ohne Text-Layer liefern leere Seiten — pypdf braucht einen Text-Layer (kein OCR).

---

## Phase 4 — Text aufteilen: `split_pages()`

**Datei:** `backend/agent/rag/splitter.py`

> Kein LLM, kein LangChain — reiner Python-Algorithmus.

**Splitter-Reihenfolge** (natürliche Grenzen bevorzugt):

| Priorität | Separator | Bedeutung |
|-----------|-----------|-----------|
| 1 | `\n\n` | Absätze (beste Qualität) |
| 2 | `\n` | Zeilenumbrüche |
| 3 | ` ` | Wortgrenzen |
| 4 | `""` | Zeichenweise (letzter Ausweg) |

**Überlapp:** 50 Zeichen Wiederholung zwischen Chunks — verhindert Kontext-Verlust an Grenzen.

---

## Phase 5 — Vektoren berechnen und speichern: `build_and_save()`

**Datei:** `backend/agent/rag/vectorstore.py`

> **`⚡ LLM-Aufruf`** — einziger LLM-Aufruf beim gesamten Upload-Prozess
> **`🟡 LangChain`** — `get_embeddings()`, `PGVector.from_texts()`

### 5.1 Embedding-Modell: `get_embeddings()`

**Datei:** `backend/agent/config.py`

> **`🟡 LangChain`** — gibt `OpenAIEmbeddings` oder `OllamaEmbeddings` zurück

Gleiche Schnittstelle für beide — `PGVector.from_texts()` merkt keinen Unterschied.

### 5.2 Vektoren berechnen und in PostgreSQL speichern

**Datei:** `vectorstore.py`, Zeile 28–47 `build_and_save(chunks, user_id)`

> **`⚡ LLM-Aufruf`** — `PGVector.from_texts()` ruft intern das Embedding-Modell auf
> **`🟡 LangChain`** — `PGVector.from_texts()` ist eine LangChain-Funktion

```python
PGVector.from_texts(
    texts=texts,
    embedding=embeddings,
    metadatas=[{"page": c["page"]} for c in chunks],  # Seitennummer pro Chunk
    collection_name=f"user_{user_id}",    # Pro-User-Isolation
    connection=_get_connection(),
    pre_delete_collection=True,           # alten Index löschen bei neuem Upload
)
```

**PostgreSQL-Tabellen danach:**

| Tabelle | Inhalt |
|---------|--------|
| `langchain_pg_collection` | Index-Name (`user_42`) und UUID |
| `langchain_pg_embedding` | Vektoren, Original-Texte, `cmetadata: {"page": 3}` |

---

## Phase 6 — Backend antwortet

**Datei:** `backend/routers/tutor.py`, Zeile 66

```python
return UploadResponse(status="ok", chunks=len(chunks))
```

---

## Phase 7 — Wie die Suche beim Chat funktioniert

**Dateien:** `backend/routers/tutor.py`, `backend/agent/rag/vectorstore.py`

### 7.1 Semantische Suche: `query_with_pages()`

**Datei:** `vectorstore.py`, Zeile 71–86

> **`🟡 LangChain`** — `PGVector.similarity_search()` intern
> Kein LLM-Aufruf — nur Vektor-Vergleich in PostgreSQL

```python
docs = store.similarity_search(message, k=top_k)
```

### 7.2 Seitenzahl-Suche: `get_page()`

**Datei:** `vectorstore.py`, Zeile 89–101
**Regex:** `tutor.py`, Zeile 114 `_PAGE_PATTERN`

```python
# Erkennt: "Seite 5", "page 5", "s. 5"
docs = store.similarity_search(" ", k=50, filter={"page": page_num})
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
[Backend] Validierung: PDF? Nicht leer?          ← kein LLM (tutor.py:45)
        │
        ▼
[Backend] extract_pages(pdf_bytes)               ← kein LLM (loader.py)
        │  pypdf → [(1, "Text..."), (2, "Text...")]
        ▼
[Backend] split_pages(pages)                     ← kein LLM (splitter.py)
        │  → [{"text": "...", "page": 1}, ...]
        ▼
[Backend] build_and_save(chunks, user_id)
        │
        ├─► get_embeddings()                     ← 🟡 LangChain (config.py)
        │     OpenAI? → OpenAIEmbeddings
        │     sonst   → OllamaEmbeddings
        │
        └─► PGVector.from_texts()                ← ⚡ LLM-AUFRUF + 🟡 LangChain (vectorstore.py:40)
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
[Ab jetzt] jede Chat-Frage sucht im pgvector-Index   ← 🟡 LangChain, kein LLM (vectorstore.py:71)
           → Kontext gefunden: run_chat_with_context() ← ⚡ LLM-Aufruf (tutor_agent.py:227)
           → kein PDF:         run_chat() ReAct-Agent  ← ⚡ LLM-Aufruf (tutor_agent.py:184)
```

---

## LLM-Aufrufe

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
| `PGVector.from_texts()` | **🟡 LangChain** | `vectorstore.py:40` |
| `PGVector.similarity_search()` | **🟡 LangChain** | `vectorstore.py:77` |
| `OpenAIEmbeddings`, `OllamaEmbeddings` | **🟡 LangChain** | `config.py` |
| `get_embeddings()` | **🟡 LangChain** abstrahiert | `config.py` |
| `PdfReader`, `extract_text()` | normaler Code (pypdf) | `loader.py` |
| `split_pages()` | normaler Code | `splitter.py` |
| `_extract_page_number()` | normaler Code (Regex) | `tutor.py:117` |
| `db.query(...)`, `HTTPException` | normaler Code | `tutor.py` |

---

## Wichtige Einschränkungen

1. **Per-User-Index** — jeder User hat seine eigene pgvector-Collection `user_{id}`. Ein neuer Upload überschreibt nur seine eigene Collection (`pre_delete_collection=True`).
2. **Eingescannte PDFs** ohne Text-Layer funktionieren nicht — pypdf braucht einen Text-Layer (kein OCR).
3. **RAM-Limit** — die gesamte PDF wird beim Upload in den RAM geladen (Server-RAM, nicht Browser).
4. **Render-Persistenz** — Vektoren überleben Redeploys, da sie in PostgreSQL gespeichert sind.
