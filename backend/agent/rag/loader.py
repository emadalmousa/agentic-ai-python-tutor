import io
import logging

logger = logging.getLogger(__name__)


def extract_text(source: bytes | str) -> str:
    """Extrahiert den gesamten Text aus einer PDF-Datei."""
    pages = extract_pages(source)
    if not pages:
        raise ValueError("Kein Text aus der PDF extrahiert — Datei ist leer oder nicht lesbar.")
    full_text = "\n".join(text for _, text in pages)
    logger.info("PDF-Text extrahiert: %d Zeichen aus %d Seiten", len(full_text), len(pages))
    return full_text


def extract_pages(source: bytes | str) -> list[tuple[int, str]]:
    """Extrahiert Text seitenweise aus einer PDF-Datei.

    Returns:
        Liste von (page_number, text) Tupeln (1-basiert).

    Raises:
        ValueError: Wenn die PDF leer ist oder kein Text extrahiert werden konnte.
    """
    from pypdf import PdfReader

    if isinstance(source, bytes):
        reader = PdfReader(io.BytesIO(source))
    else:
        reader = PdfReader(source)

    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append((i + 1, text))

    if not pages:
        raise ValueError("Kein Text aus der PDF extrahiert — Datei ist leer oder nicht lesbar.")

    logger.info("PDF-Seiten extrahiert: %d Seiten aus %d total", len(pages), len(reader.pages))
    return pages
