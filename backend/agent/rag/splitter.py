import os
import logging

logger = logging.getLogger(__name__)


def split_text(text: str) -> list[str]:
    """Teilt einen Text in überlappende Chunks auf."""
    return [chunk for chunk, _ in split_pages([(1, text)])]


def split_pages(pages: list[tuple[int, str]]) -> list[tuple[str, int]]:
    """Teilt seitenweisen Text in Chunks mit Seitenreferenz auf.

    Args:
        pages: Liste von (page_number, text) Tupeln.

    Returns:
        Liste von (chunk_text, page_number) Tupeln.
    """
    chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

    result: list[tuple[str, int]] = []
    for page_num, text in pages:
        chunks = _recursive_split(text, chunk_size, chunk_overlap)
        for chunk in chunks:
            result.append((chunk, page_num))

    logger.info(
        "Text in %d Chunks aufgeteilt (chunk_size=%d, overlap=%d)",
        len(result),
        chunk_size,
        chunk_overlap,
    )
    return result


def _recursive_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Teilt Text rekursiv an Absätzen, Zeilenumbrüchen, Leerzeichen und Zeichen auf."""
    separators = ["\n\n", "\n", " ", ""]

    for separator in separators:
        if separator == "":
            # Letzter Ausweg: zeichenweise aufteilen
            return _split_by_size(text, chunk_size, chunk_overlap, separator)

        if separator in text:
            return _split_by_size(text, chunk_size, chunk_overlap, separator)

    return [text]


def _split_by_size(text: str, chunk_size: int, chunk_overlap: int, separator: str) -> list[str]:
    """Baut Chunks der Zielgröße aus Teilen auf, die an `separator` gespalten wurden."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    parts = text.split(separator) if separator else list(text)
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for part in parts:
        part_length = len(part) + (len(separator) if current_chunk else 0)

        if current_length + part_length > chunk_size and current_chunk:
            # Chunk abschließen
            chunk_text = separator.join(current_chunk)
            if chunk_text.strip():
                chunks.append(chunk_text)

            # Überlapp berechnen: letzte Teile beibehalten
            overlap_parts: list[str] = []
            overlap_length = 0
            for p in reversed(current_chunk):
                p_len = len(p) + (len(separator) if overlap_parts else 0)
                if overlap_length + p_len > chunk_overlap:
                    break
                overlap_parts.insert(0, p)
                overlap_length += p_len

            current_chunk = overlap_parts
            current_length = overlap_length

        current_chunk.append(part)
        current_length += part_length

    # Letzten Chunk hinzufügen
    if current_chunk:
        chunk_text = separator.join(current_chunk)
        if chunk_text.strip():
            chunks.append(chunk_text)

    return chunks
