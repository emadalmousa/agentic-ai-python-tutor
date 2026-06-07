import os
import pickle
from pathlib import Path

from langchain_community.vectorstores import FAISS

from agent.config import get_embeddings

_DEFAULT_BASE = str(Path(__file__).parent.parent.parent / "rag_stores")


def _store_path(user_id: int) -> Path:
    base = Path(os.getenv("RAG_VECTORSTORE_PATH", _DEFAULT_BASE))
    path = base / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_and_save(chunks: list[dict], user_id: int) -> None:
    """Erstellt einen FAISS-Index für einen User und speichert ihn auf Disk."""
    texts = [c["text"] for c in chunks]
    embeddings = get_embeddings()
    store = FAISS.from_texts(texts, embeddings)

    path = _store_path(user_id)
    store.save_local(str(path))

    with open(path / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)


def load(user_id: int) -> dict | None:
    """Lädt den FAISS-Index des Users. Gibt None zurück wenn kein Index vorhanden."""
    path = _store_path(user_id)
    index_file = path / "index.faiss"
    chunks_file = path / "chunks.pkl"

    if not index_file.exists() or not chunks_file.exists():
        return None

    embeddings = get_embeddings()
    store = FAISS.load_local(str(path), embeddings, allow_dangerous_deserialization=True)

    with open(chunks_file, "rb") as f:
        chunks = pickle.load(f)

    return {"store": store, "chunks": chunks}


def query_with_pages(index_data: dict, message: str, top_k: int = 3) -> list[tuple[str, int]]:
    """Semantische Suche im FAISS-Index. Gibt [(text, seitennummer), ...] zurück."""
    store: FAISS = index_data["store"]
    docs = store.similarity_search(message, k=top_k)

    chunks: list[dict] = index_data["chunks"]
    text_to_page = {c["text"]: c["page"] for c in chunks}

    results = []
    for doc in docs:
        text = doc.page_content
        page = text_to_page.get(text, 0)
        results.append((text, page))

    return results


def get_page(index_data: dict, page_num: int) -> list[tuple[str, int]]:
    """Gibt alle Chunks einer bestimmten Seite zurück."""
    chunks: list[dict] = index_data["chunks"]
    return [(c["text"], c["page"]) for c in chunks if c["page"] == page_num]
