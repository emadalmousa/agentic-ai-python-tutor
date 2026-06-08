"""pgvector-Vektorstore für user-spezifische RAG-Indizes.

Ersetzt FAISS-auf-Disk durch PostgreSQL mit pgvector-Extension.
Vorteil: Vektoren bleiben bei Render-Deploys erhalten — kein Disk-Verlust.

Jeder User bekommt eine eigene Collection: "user_<user_id>".
"""
import os

from langchain_postgres.vectorstores import PGVector

from agent.config import get_embeddings

# Datenbankverbindung — gleiche URL wie SQLAlchemy, aber psycopg3-Format
def _get_connection() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://app:app@localhost:5432/ki_tutor")
    # PGVector braucht psycopg3-Format: postgresql+psycopg://...
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _collection_name(user_id: int) -> str:
    """Gibt den Collection-Namen für einen User zurück — isoliert pro User."""
    return f"user_{user_id}"


def build_and_save(chunks: list[dict], user_id: int) -> None:
    """Erstellt einen pgvector-Index für einen User und speichert ihn in PostgreSQL.

    pre_delete_collection=True: altes PDF des Users wird überschrieben wenn er neu hochlädt.
    metadatas enthält die Seitennummer — direkt in PostgreSQL gespeichert, kein chunks.pkl nötig.
    """
    texts = [c["text"] for c in chunks]
    # Seitennummern als Metadaten mitspeichern — pgvector speichert sie als JSON
    metadatas = [{"page": c["page"]} for c in chunks]

    embeddings = get_embeddings()

    PGVector.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        collection_name=_collection_name(user_id),
        connection=_get_connection(),
        pre_delete_collection=True,  # alten Index des Users löschen vor neuem Upload
    )


def load(user_id: int) -> dict | None:
    """Lädt den pgvector-Store des Users. Gibt None zurück wenn kein Index vorhanden.

    Prüft ob der User schon ein PDF hochgeladen hat indem eine leere Suche gemacht wird.
    """
    try:
        embeddings = get_embeddings()
        store = PGVector(
            embeddings=embeddings,
            collection_name=_collection_name(user_id),
            connection=_get_connection(),
        )
        # Prüfen ob Collection Daten enthält — leere Collection = kein PDF hochgeladen
        results = store.similarity_search("test", k=1)
        if not results:
            return None
        return {"store": store}
    except Exception:
        return None


def query_with_pages(index_data: dict, message: str, top_k: int = 3) -> list[tuple[str, int]]:
    """Semantische Suche im pgvector-Store. Gibt [(text, seitennummer), ...] zurück.

    Seitennummern kommen aus den Metadaten — direkt aus PostgreSQL, kein chunks.pkl nötig.
    """
    store: PGVector = index_data["store"]
    docs = store.similarity_search(message, k=top_k)

    results = []
    for doc in docs:
        text = doc.page_content
        # Seitennummer aus Metadaten lesen — wurde beim Upload als {"page": int} gespeichert
        page = doc.metadata.get("page", 0)
        results.append((text, page))

    return results


def get_page(index_data: dict, page_num: int) -> list[tuple[str, int]]:
    """Gibt alle Chunks einer bestimmten Seite zurück.

    Filtert über Metadaten in PostgreSQL — kein FAISS-Disk-Lookup nötig.
    """
    store: PGVector = index_data["store"]
    # pgvector unterstützt Metadaten-Filter direkt in der Suche
    docs = store.similarity_search(
        " ",  # leere Suche — nur Filter zählt
        k=50,  # großzügig — eine Seite hat selten mehr als 50 Chunks
        filter={"page": page_num},
    )
    return [(doc.page_content, page_num) for doc in docs]
