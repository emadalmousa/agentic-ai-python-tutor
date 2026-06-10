"""RAG-Tool: sucht im pgvector-Index des Users nach relevanten PDF-Passagen.

Wird vom ReAct-Agenten aufgerufen wenn der Student eine Frage zum hochgeladenen PDF stellt.
Das Tool ist nur verfügbar wenn ein pgvector-Index für den User existiert
(wird in _build_chat_tools geprüft bevor das Tool gebunden wird).
"""
from langchain_core.tools import tool


@tool
def rag_tool(query: str) -> str:
    """Sucht relevante Passagen aus dem hochgeladenen Lernmaterial (PDF).

    Verwende dieses Tool wenn der Student eine Frage zum hochgeladenen PDF stellt.
    Gibt die relevanten Textstellen zurück, oder einen Hinweis wenn kein Material verfügbar ist.
    """
    try:
        # Lazy-Import: vectorstore wird nur bei Bedarf geladen, nicht beim Server-Start
        from agent.rag.vectorstore import load, query_with_pages

        index_data = load()
        if index_data is None:
            return "Kein Lernmaterial verfügbar. Bitte lade zuerst ein PDF über 'Material hochladen' hoch."

        results = query_with_pages(index_data, query, top_k=3)
        if not results:
            return "Keine relevanten Passagen im Lernmaterial gefunden."

        # Ergebnisse mit Seitenreferenzen formatieren — z.B. "[Seite 5]\nText..."
        parts = []
        for text, page in results:
            ref = f"[Seite {page}]" if page > 0 else ""
            parts.append(f"{ref}\n{text}" if ref else text)

        # Trennlinie zwischen Passagen für bessere Lesbarkeit
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        return f"Fehler beim Zugriff auf das Lernmaterial: {e}"
