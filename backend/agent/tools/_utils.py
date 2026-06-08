"""Gemeinsame Hilfsfunktionen für alle Tool-Module."""
import json
import re


def _parse_json(text: str) -> dict:
    """Entfernt Markdown-Code-Block-Marker und parst den Text als JSON.

    Wird von allen Tools verwendet die JSON-Antworten vom LLM parsen müssen.
    Wirft json.JSONDecodeError wenn kein gültiges JSON gefunden wird.
    """
    # ```json ... ``` oder ``` ... ``` Marker entfernen
    text = re.sub(r"```json\s*|\s*```", "", text).strip()
    return json.loads(text)
