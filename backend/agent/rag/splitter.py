"""Teilt PDF-Seiten in überlappende Chunks für den pgvector-Vektorstore."""
_CHUNK_SIZE = 500  # Zeichenanzahl pro Chunk
_OVERLAP = 50      # Überlappung zwischen Chunks — verhindert Kontext-Verlust an Grenzen


def split_pages(pages: list[tuple[str, int]]) -> list[dict]:
    """Teilt Seiten-Texte in Chunks von ~500 Zeichen auf.

    Gibt eine Liste von {"text": str, "page": int} zurück.
    Leere oder nur-Whitespace-Seiten werden übersprungen.
    Kurze Seiten (< CHUNK_SIZE) bleiben als ein Chunk.
    Lange Seiten werden mit OVERLAP gesplittet damit kein Kontext verloren geht.
    """
    chunks = []
    for text, page_num in pages:
        text = text.strip()
        if not text:
            continue  # Leere Seiten (z.B. Bilder ohne Text) überspringen

        # Kurze Seite: kein Splitting nötig
        if len(text) <= _CHUNK_SIZE:
            chunks.append({"text": text, "page": page_num})
            continue

        # Lange Seite: mit Überlappung splitten
        start = 0
        while start < len(text):
            end = start + _CHUNK_SIZE
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page_num})
            # start - OVERLAP: nächster Chunk beginnt leicht früher → Kontext-Kontinuität
            start = end - _OVERLAP

    return chunks
