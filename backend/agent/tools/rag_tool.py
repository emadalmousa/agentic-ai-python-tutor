from langchain_core.tools import tool


@tool
def rag_tool(query: str) -> str:
    """Sucht relevante Passagen aus dem hochgeladenen Lernmaterial (PDF).

    Verwende dieses Tool wenn der Student eine Frage zum hochgeladenen PDF stellt.
    Gibt die relevanten Textstellen zurück, oder einen Hinweis wenn kein Material verfügbar ist.
    """
    try:
        from agent.rag.vectorstore import load, query_with_pages

        index_data = load()
        if index_data is None:
            return "Kein Lernmaterial verfügbar. Bitte lade zuerst ein PDF über 'Material hochladen' hoch."

        results = query_with_pages(index_data, query, top_k=3)
        if not results:
            return "Keine relevanten Passagen im Lernmaterial gefunden."

        parts = []
        for text, page in results:
            ref = f"[Seite {page}]" if page > 0 else ""
            parts.append(f"{ref}\n{text}" if ref else text)

        return "\n\n---\n\n".join(parts)
    except Exception as e:
        return f"Fehler beim Zugriff auf das Lernmaterial: {e}"
