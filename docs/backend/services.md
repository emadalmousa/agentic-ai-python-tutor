# services/

**Pfad:** `backend/services/`
**Zweck:** Dünne Adapter die `run_analysis()` aufrufen und nur einen Teil des Ergebnisses zurückgeben. Diese Schicht existiert aus historischen Gründen; der Router ruft `run_analysis()` direkt auf.

## code_explainer.py

```python
def explain_code(code: str) -> str:
    result = run_analysis(code)
    return result["explanation"]
```

Ruft `run_analysis(code)` auf und gibt nur das `explanation`-Feld zurück.

## debugger.py

```python
def debug_code(code: str) -> tuple[bool, str]:
    result = run_analysis(code)
    return result["error_found"], result["suggestion"]
```

Ruft `run_analysis(code)` auf und gibt `(error_found, suggestion)` als Tupel zurück.

## Nutzung

Diese Funktionen werden aktuell nicht direkt vom Router aufgerufen. Der Router ruft `run_analysis()` direkt auf und baut daraus die vollständige `TutorResponse`.

Die Services werden in `tests/test_integration.py` getestet um sicherzustellen dass das Delegations-Verhalten korrekt ist.
