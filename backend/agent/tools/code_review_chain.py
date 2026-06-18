"""Code-Review Chain: 3-stufige RunnableSequence für strukturiertes Code-Feedback.

Schritt 1 — Syntax:       Syntaxfehler, fehlende Doppelpunkte, falsche Einrückung
Schritt 2 — Stil/PEP8:    Namenskonventionen, Zeilenlänge, Leerzeichen, Docstrings
Schritt 3 — Best Practices: Pythonische Muster, unnötige Komplexität, Sicherheit

Jeder Schritt ist ein eigener LLM-Aufruf. Das Ergebnis des vorherigen Schritts
wird dem nächsten als Kontext übergeben (echte Chain-Semantik).
"""
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda

from agent.config import get_llm

# ---------------------------------------------------------------------------
# System-Prompts je Stufe
# ---------------------------------------------------------------------------

_SYNTAX_SYSTEM = """Du bist ein Python-Code-Reviewer. Analysiere NUR Syntaxfehler.
Prüfe: fehlende Doppelpunkte, falsche Einrückung, nicht geschlossene Klammern/Strings,
ungültige Schlüsselwörter, fehlende return-Statements in Funktionen.

Antworte NUR mit validem JSON:
{
  "issues": [
    { "line": 3, "severity": "error", "message": "Fehlender Doppelpunkt nach if-Bedingung" }
  ],
  "summary": "1 Syntaxfehler gefunden."
}
severity: "error" (Fehler) oder "warning" (Warnung).
Wenn keine Probleme: issues=[], summary="Keine Syntaxfehler gefunden."
Kein Markdown, nur JSON."""

_STYLE_SYSTEM = """Du bist ein Python-Code-Reviewer. Analysiere NUR Stil- und PEP8-Probleme.
Prüfe: Variablennamen (snake_case), Zeilenlänge (>79 Zeichen), fehlende Leerzeichen um Operatoren,
fehlende Leerzeilen zwischen Funktionen, Magic Numbers, fehlende Docstrings bei Funktionen.

Kontext aus Syntax-Analyse: {syntax_summary}

Antworte NUR mit validem JSON:
{
  "issues": [
    { "line": 5, "severity": "warning", "message": "Variablenname 'X' sollte klein geschrieben sein (snake_case)" }
  ],
  "summary": "2 Stil-Probleme gefunden."
}
Wenn keine Probleme: issues=[], summary="PEP8-konform. Kein Handlungsbedarf."
Kein Markdown, nur JSON."""

_BESTPRACTICES_SYSTEM = """Du bist ein Python-Code-Reviewer. Analysiere NUR Best-Practice-Verstöße.
Prüfe: nicht-pythonische Muster (range(len()) statt enumerate), mutable Default-Argumente,
bare except, unnötige Typ-Konvertierungen, String-Konkatenation in Schleifen,
global-Variablen, redundante Vergleiche (== True/False/None statt is).

Kontext aus vorherigen Schritten: {syntax_summary} | {style_summary}

Antworte NUR mit validem JSON:
{
  "issues": [
    { "line": 8, "severity": "info", "message": "Verwende enumerate() statt range(len(...))" }
  ],
  "summary": "1 Best-Practice-Hinweis."
}
severity: "info" (Verbesserungsvorschlag) oder "warning" (sollte geändert werden).
Wenn keine Probleme: issues=[], summary="Gute Python-Praxis. Keine Verbesserungen nötig."
Kein Markdown, nur JSON."""


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"issues": [], "summary": text[:200]}


# ---------------------------------------------------------------------------
# Chain-Stufen als Runnables
# ---------------------------------------------------------------------------

def _make_syntax_step():
    def run(inputs: dict) -> dict:
        llm = get_llm()
        result = llm.invoke([
            SystemMessage(content=_SYNTAX_SYSTEM),
            HumanMessage(content=f"Python-Code:\n```python\n{inputs['code']}\n```"),
        ])
        parsed = _parse_json(str(result.content))
        return {**inputs, "syntax": parsed}
    return RunnableLambda(run)


def _make_style_step():
    def run(inputs: dict) -> dict:
        llm = get_llm()
        system = _STYLE_SYSTEM.format(
            syntax_summary=inputs["syntax"].get("summary", "")
        )
        result = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=f"Python-Code:\n```python\n{inputs['code']}\n```"),
        ])
        parsed = _parse_json(str(result.content))
        return {**inputs, "style": parsed}
    return RunnableLambda(run)


def _make_bestpractices_step():
    def run(inputs: dict) -> dict:
        llm = get_llm()
        system = _BESTPRACTICES_SYSTEM.format(
            syntax_summary=inputs["syntax"].get("summary", ""),
            style_summary=inputs["style"].get("summary", ""),
        )
        result = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=f"Python-Code:\n```python\n{inputs['code']}\n```"),
        ])
        parsed = _parse_json(str(result.content))
        return {**inputs, "best_practices": parsed}
    return RunnableLambda(run)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_code_review(code: str) -> dict:
    """Führt die 3-stufige Code-Review-Chain aus und gibt strukturiertes Ergebnis zurück.

    Gibt dict zurück:
    {
      "syntax":         { "issues": [...], "summary": "..." },
      "style":          { "issues": [...], "summary": "..." },
      "best_practices": { "issues": [...], "summary": "..." },
      "total_issues":   int
    }
    Bei Fehler in einer Stufe → leere Issues, Fehlermeldung als Summary.
    """
    chain = _make_syntax_step() | _make_style_step() | _make_bestpractices_step()

    try:
        result = chain.invoke({"code": code})
    except Exception as e:
        empty = {"issues": [], "summary": f"Fehler: {e}"}
        return {"syntax": empty, "style": empty, "best_practices": empty, "total_issues": 0}

    syntax         = result.get("syntax",         {"issues": [], "summary": ""})
    style          = result.get("style",          {"issues": [], "summary": ""})
    best_practices = result.get("best_practices", {"issues": [], "summary": ""})

    total = (
        len(syntax.get("issues", []))
        + len(style.get("issues", []))
        + len(best_practices.get("issues", []))
    )

    return {
        "syntax":         syntax,
        "style":          style,
        "best_practices": best_practices,
        "total_issues":   total,
    }
