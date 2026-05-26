import os
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def rag_tool(query: str) -> str:
    """Sucht in den hochgeladenen Lernmaterialien nach relevanten Textstellen.

    Nutze dieses Tool, wenn der Schüler Fragen stellt, die durch Kursinhalt
    beantwortet werden könnten, oder wenn eine Erklärung aus dem Lernmaterial
    hilfreich wäre. Das Tool gibt die relevantesten Textpassagen zurück.

    Args:
        query: Eine natürlichsprachige Suchanfrage auf Deutsch.

    Returns:
        Die relevantesten Textpassagen aus den Lernmaterialien, oder eine
        Meldung, dass noch kein Material hochgeladen wurde.
    """
    from agent.rag.vectorstore import load, query as vs_query

    index_data = load()
    if index_data is None:
        return "Es wurden noch keine Lernmaterialien hochgeladen."

    top_k = int(os.getenv("RAG_TOP_K", "3"))
    passages = vs_query(index_data, query, top_k=top_k)

    if not passages:
        return "Keine relevanten Textstellen gefunden."

    return "\n\n---\n\n".join(passages)
