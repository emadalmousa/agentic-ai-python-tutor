# Gibt immer zwei Werte zurück: (Fehler gefunden?, Nachricht)
def debug_code(code: str) -> tuple[bool, str]:

    # Jede Zeile einzeln prüfen — nicht den ganzen Code auf einmal
    # (wichtig: ein Doppelpunkt in einer anderen Zeile soll die Prüfung nicht stören)
    for line in code.splitlines():
        stripped = line.strip()  # Einrückungen (Spaces/Tabs) entfernen

        # Regel 1: for-Schleife ohne Doppelpunkt am Ende
        if stripped.startswith("for ") and not stripped.endswith(":"):
            return True, "Möglicher Syntaxfehler: Bei einer for-Schleife fehlt ein Doppelpunkt ':' am Ende."

        # Regel 2: if-Bedingung ohne Doppelpunkt am Ende
        if stripped.startswith("if ") and not stripped.endswith(":"):
            return True, "Möglicher Syntaxfehler: Bei einer if-Bedingung fehlt ein Doppelpunkt ':' am Ende."

    # Regel 3: kein print() im Code — nur ein Hinweis, kein Fehler
    if "print" not in code:
        return False, "Hinweis: Dein Code enthält keine Ausgabe mit print()."

    # Kein Problem gefunden
    return False, "Kein offensichtlicher Fehler gefunden."
