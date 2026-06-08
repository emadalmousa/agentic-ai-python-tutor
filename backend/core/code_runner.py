"""Gemeinsames Hilfsmittel zum Ausführen von Schüler-Code in einem Subprocess."""
import subprocess
import sys


def run_user_code(code: str) -> tuple[str, str]:
    """Führt Schüler-Code in einem isolierten Subprocess aus und gibt (stdout, stderr) zurück.

    Der Code wird über -c übergeben, nicht als Datei, um Filesystem-Interaktion zu minimieren.
    Timeout: 10 Sekunden — verhindert Endlosschleifen im Schüler-Code.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],  # sys.executable = gleiche Python-Version wie Backend
            capture_output=True,  # stdout und stderr separat abfangen
            text=True,            # Bytes automatisch als UTF-8 dekodieren
            timeout=10,           # Schutz gegen Endlosschleifen
        )
        # strip() entfernt führende/nachfolgende Leerzeichen für sauberen Vergleich
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        # Kein stdout wenn Timeout — Schüler bekommt klare Fehlermeldung
        return "", "Timeout: Code hat zu lange gebraucht (max 10 Sekunden)."
    except Exception as e:
        return "", str(e)
