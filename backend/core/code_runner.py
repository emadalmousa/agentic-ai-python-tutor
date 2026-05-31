"""Shared utility for running user-submitted Python code in a subprocess."""
import subprocess
import sys


def run_user_code(code: str) -> tuple[str, str]:
    """Runs user code in a subprocess and returns (stdout, stderr)."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "Timeout: Code hat zu lange gebraucht (max 10 Sekunden)."
    except Exception as e:
        return "", str(e)
