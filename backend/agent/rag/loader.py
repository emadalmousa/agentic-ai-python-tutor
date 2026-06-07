import io
from pypdf import PdfReader


def extract_pages(pdf_bytes: bytes) -> list[tuple[str, int]]:
    """Liest jede Seite eines PDFs und gibt [(text, seitennummer), ...] zurück.

    Seitennummern beginnen bei 1.
    Wirft ValueError bei leerem Input, Exception bei ungültigem PDF.
    """
    if not pdf_bytes:
        raise ValueError("PDF-Bytes sind leer.")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ValueError(f"Ungültiges PDF: {e}") from e

    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append((text, i))

    return pages
