"""PDF-Loader: extrahiert Text seitenweise aus einem PDF-Bytes-Objekt."""
import io
from pypdf import PdfReader


def extract_pages(pdf_bytes: bytes) -> list[tuple[str, int]]:
    """Liest jede Seite eines PDFs und gibt [(text, seitennummer), ...] zurück.

    Seitennummern beginnen bei 1 (nicht 0) für benutzerfreundliche Anzeige.
    Wirft ValueError bei leerem Input oder ungültigem PDF-Format.
    Leere Seiten (z.B. reine Bild-Seiten ohne Text) werden als ('', n) zurückgegeben.
    """
    if not pdf_bytes:
        raise ValueError("PDF-Bytes sind leer.")

    try:
        # BytesIO wrappt die Bytes als dateiähnliches Objekt für pypdf
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ValueError(f"Ungültiges PDF: {e}") from e

    pages = []
    for i, page in enumerate(reader.pages, start=1):
        # extract_text() gibt None zurück wenn keine Textschicht vorhanden — None → leerer String
        text = page.extract_text() or ""
        pages.append((text, i))

    return pages
