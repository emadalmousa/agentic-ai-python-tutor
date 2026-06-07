_CHUNK_SIZE = 500
_OVERLAP = 50


def split_pages(pages: list[tuple[str, int]]) -> list[dict]:
    """Teilt Seiten-Texte in Chunks von ~500 Zeichen auf.

    Gibt eine Liste von {"text": str, "page": int} zurück.
    Leere oder nur-Whitespace-Seiten werden übersprungen.
    """
    chunks = []
    for text, page_num in pages:
        text = text.strip()
        if not text:
            continue

        if len(text) <= _CHUNK_SIZE:
            chunks.append({"text": text, "page": page_num})
            continue

        start = 0
        while start < len(text):
            end = start + _CHUNK_SIZE
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page_num})
            start = end - _OVERLAP

    return chunks
