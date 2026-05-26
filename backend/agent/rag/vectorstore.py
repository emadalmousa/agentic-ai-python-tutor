import os
import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_VECTORSTORE_PATH = str(Path(__file__).parent / "vectorstore")

_INDEX_FILE = "index.faiss"
_CHUNKS_FILE = "chunks.pkl"


def _get_vectorstore_path() -> str:
    return os.getenv("RAG_VECTORSTORE_PATH", _DEFAULT_VECTORSTORE_PATH)


def build_and_save(chunks: list[str] | list[tuple[str, int]]) -> None:
    """Erstellt einen FAISS-Index aus den Chunks und speichert ihn auf Disk.

    Args:
        chunks: Liste von Text-Chunks (str) oder (chunk_text, page_number) Tupeln.

    Raises:
        ValueError: Wenn die Chunk-Liste leer ist.
    """
    import faiss
    import numpy as np
    from agent.config import get_embeddings

    if not chunks:
        raise ValueError("Keine Chunks übergeben — FAISS-Index kann nicht erstellt werden.")

    # Normalisiere zu (text, page) Tupeln
    if isinstance(chunks[0], str):
        normalized: list[tuple[str, int]] = [(c, 0) for c in chunks]  # type: ignore[arg-type]
    else:
        normalized = list(chunks)  # type: ignore[arg-type]

    texts = [c for c, _ in normalized]
    embeddings_model = get_embeddings()
    vectors = embeddings_model.embed_documents(texts)
    vectors_array = np.array(vectors, dtype="float32")

    dimension = vectors_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors_array)

    vectorstore_path = Path(_get_vectorstore_path())
    vectorstore_path.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(vectorstore_path / _INDEX_FILE))
    with open(vectorstore_path / _CHUNKS_FILE, "wb") as f:
        pickle.dump(normalized, f)

    logger.info("FAISS-Index mit %d Chunks gespeichert unter: %s", len(normalized), vectorstore_path)


def load():
    """Lädt den FAISS-Index von Disk.

    Returns:
        Ein Tuple (index, chunks) oder None, wenn kein Index vorhanden ist.
        chunks ist eine Liste von (text, page_number) Tupeln.
    """
    import faiss

    vectorstore_path = Path(_get_vectorstore_path())
    index_file = vectorstore_path / _INDEX_FILE
    chunks_file = vectorstore_path / _CHUNKS_FILE

    if not index_file.exists() or not chunks_file.exists():
        logger.info("Kein FAISS-Index gefunden unter: %s", vectorstore_path)
        return None

    index = faiss.read_index(str(index_file))
    with open(chunks_file, "rb") as f:
        raw = pickle.load(f)

    # Rückwärtskompatibilität: alte Indizes hatten nur Strings
    if raw and isinstance(raw[0], str):
        chunks: list[tuple[str, int]] = [(c, 0) for c in raw]
    else:
        chunks = raw

    logger.info("FAISS-Index geladen von: %s (%d Chunks)", vectorstore_path, len(chunks))
    return index, chunks


def query(index_data, question: str, top_k: int = 3) -> list[str]:
    """Führt eine Ähnlichkeitssuche durch und gibt Chunks mit Seitenreferenz zurück."""
    results = query_with_pages(index_data, question, top_k)
    return [text for text, _ in results]


def query_with_pages(index_data, question: str, top_k: int = 3) -> list[tuple[str, int]]:
    """Ähnlichkeitssuche — gibt (chunk_text, page_number) Tupeln zurück."""
    import numpy as np
    from agent.config import get_embeddings

    index, chunks = index_data
    embeddings_model = get_embeddings()
    query_vector = embeddings_model.embed_query(question)
    query_array = np.array([query_vector], dtype="float32")

    actual_k = min(top_k, len(chunks))
    _, indices = index.search(query_array, actual_k)

    return [chunks[i] for i in indices[0] if i < len(chunks)]


def get_page(index_data, page_number: int) -> list[tuple[str, int]]:
    """Gibt alle Chunks einer bestimmten Seite zurück (direkte Seitensuche, kein FAISS)."""
    _, chunks = index_data
    return [(text, page) for text, page in chunks if page == page_number]
