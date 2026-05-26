# agent/rag/

**Pfad:** `backend/agent/rag/`
**Zweck:** Gesamte RAG-Pipeline (Retrieval-Augmented Generation). Verantwortlich für das Einlesen von PDFs, das Aufteilen in Chunks, das Erstellen eines FAISS-Vektorindex und die Ähnlichkeitssuche.

## Was ist RAG?

Ohne RAG kennt der Agent nur was das LLM während des Trainings gelernt hat. Mit RAG kann ein Schüler (oder Lehrer) ein Python-Lehrbuch als PDF hochladen. Ab diesem Moment kann der Agent bei jeder Analyse konkrete Stellen aus dem Buch zitieren.

## Ablauf

```
PDF hochladen (POST /tutor/upload-material)
    │
    ├── loader.py: extract_text(pdf_bytes)     → Text als String
    ├── splitter.py: split_text(text)          → Liste von Chunks
    └── vectorstore.py: build_and_save(chunks) → FAISS-Index auf Disk

Bei jeder Analyse (run_analysis):
    └── vectorstore.py: load() + query()       → relevante Chunks
```

---

## loader.py

**Funktion:** `extract_text(source: bytes | str) -> str`

Liest alle Seiten einer PDF-Datei mit `pypdf` und gibt den vollständigen Text zurück.

```python
extract_text(pdf_bytes)   # bytes-Objekt
extract_text("/pfad/zu/datei.pdf")  # oder Dateipfad
```

Wirft `ValueError` wenn kein Text extrahiert werden konnte (leere oder nicht lesbare PDF).

---

## splitter.py

**Funktion:** `split_text(text: str) -> list[str]`

Teilt einen langen Text in überlappende Chunks auf. Implementiert denselben Algorithmus wie LangChains `RecursiveCharacterTextSplitter`:

- Trennt zuerst an Absätzen (`\n\n`)
- Dann an Zeilenumbrüchen (`\n`)
- Dann an Leerzeichen (` `)
- Als letzter Ausweg zeichenweise

Chunk-Größe und Überlapp sind über Umgebungsvariablen konfigurierbar:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `RAG_CHUNK_SIZE` | `500` | Zeichen pro Chunk |
| `RAG_CHUNK_OVERLAP` | `50` | Überlapp zwischen benachbarten Chunks |

Der Überlapp verhindert dass wichtige Informationen an Chunk-Grenzen abgeschnitten werden.

---

## vectorstore.py

Verwaltet den FAISS-Vektorindex auf der Festplatte.

**Speicherort:** `backend/vectorstore/` (konfigurierbar über `RAG_VECTORSTORE_PATH`)

Zwei Dateien werden gespeichert:
- `index.faiss` — der eigentliche FAISS-Index mit Vektoren
- `chunks.pkl` — die Original-Textstücke als Python-Pickle

### `build_and_save(chunks: list[str]) -> None`

Erstellt einen neuen FAISS-Index und speichert ihn auf Disk:

1. `get_embeddings()` holt das Embedding-Modell (OpenAI oder Ollama)
2. Alle Chunks werden in Vektoren umgewandelt (`embed_documents`)
3. Ein `faiss.IndexFlatL2`-Index wird erstellt (exakte L2-Distanzsuche)
4. Index und Chunks werden auf Disk gespeichert

Wirft `ValueError` wenn `chunks` leer ist.

### `load() -> tuple | None`

Lädt den gespeicherten Index von Disk. Gibt `(index, chunks)` zurück oder `None` wenn kein Index vorhanden.

### `query(index_data, question: str, top_k: int = 3) -> list[str]`

Sucht die ähnlichsten Chunks für eine natürlichsprachige Frage:

1. Die Frage wird in einen Vektor umgewandelt (`embed_query`)
2. FAISS sucht die `top_k` Vektoren mit kleinster L2-Distanz
3. Die zugehörigen Text-Chunks werden zurückgegeben

```python
index_data = load()
results = query(index_data, "Was ist eine Schleife?", top_k=3)
# → ["Eine for-Schleife ...", "Schleifen werden verwendet ...", ...]
```

## Warum FAISS?

FAISS ist eine reine Python-Bibliothek (`faiss-cpu`) ohne Server-Abhängigkeit. Für einen lokalen Lern-Prototypen ist das einfacher als ChromaDB oder Qdrant, die eigene Server-Prozesse benötigen.
