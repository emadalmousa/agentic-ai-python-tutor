# Phase 1: Dummy-Erklärung — wird in Phase 2 durch OpenAI API ersetzt
def explain_code(code: str) -> str:
    # Code in einzelne Zeilen aufteilen und zählen
    lines = code.strip().splitlines()
    line_count = len(lines)

    # Dummy-Antwort mit Zeilenanzahl — Phase 2 ersetzt diese Rückgabe
    return (
        f"Dein Code hat {line_count} Zeile(n). "
        "Ich analysiere ihn Schritt für Schritt: "
        "Zunächst lese ich die Struktur, prüfe Einrückungen und Syntax. "
        "In Phase 2 übernimmt ein OpenAI/LangChain-Agent diese Erklärung "
        "und gibt dir eine detaillierte, personalisierte Antwort."
    )
