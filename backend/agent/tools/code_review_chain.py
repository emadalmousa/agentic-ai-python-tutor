"""Code-Review Chain: 3-stufige RunnableSequence für strukturiertes Code-Feedback.

Schritt 1 — Syntax:       Syntaxfehler, fehlende Doppelpunkte, falsche Einrückung
Schritt 2 — Stil/PEP8:    Namenskonventionen, Zeilenlänge, Leerzeichen, Docstrings
Schritt 3 — Best Practices: Pythonische Muster, unnötige Komplexität, Sicherheit

Jeder Schritt ist ein eigener LLM-Aufruf. Das Ergebnis des vorherigen Schritts
wird dem nächsten als Kontext übergeben (echte Chain-Semantik).
"""
import ast
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda

from agent.config import get_llm


# ---------------------------------------------------------------------------
# Statische Syntax-Analyse (kein LLM nötig)
# ---------------------------------------------------------------------------

def _static_syntax_check(code: str) -> dict:
    """Prüft Syntaxfehler und undefinierte Variablen mit Python selbst."""
    issues = []

    # 1. Compile-Check: echte SyntaxErrors
    try:
        tree = compile(code, "<string>", "exec", ast.PyCF_ONLY_AST)
    except SyntaxError as e:
        return {
            "issues": [{"line": e.lineno or 1, "severity": "error", "message": f"SyntaxError: {e.msg}"}],
            "summary": f"Syntaxfehler in Zeile {e.lineno}: {e.msg}",
        }

    # 2. AST-Walk: undefinierte Variablen (Namen die benutzt aber nie zugewiesen werden)
    assigned: set[str] = set()
    used: dict[str, int] = {}  # name -> first line used

    for node in ast.walk(tree):
        # Zuweisungen: x = ..., for x in ..., def x, class x, import x
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assigned.add(node.name)
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                assigned.add(arg.arg)
            if node.args.vararg:
                assigned.add(node.args.vararg.arg)
            if node.args.kwarg:
                assigned.add(node.args.kwarg.arg)
        elif isinstance(node, ast.ClassDef):
            assigned.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                assigned.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                assigned.add(node.target.id)
        elif isinstance(node, ast.NamedExpr):
            assigned.add(node.target.id)
        elif isinstance(node, ast.Global):
            for name in node.names:
                assigned.add(name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in used:
                used[node.id] = getattr(node, "lineno", 1)

    # Builtins + häufige Namen die immer verfügbar sind
    import builtins as _builtins_module
    builtins = set(dir(_builtins_module))
    builtins.update({"__name__", "__file__", "__doc__", "__package__", "__spec__", "__builtins__"})

    for name, lineno in sorted(used.items(), key=lambda x: x[1]):
        if name not in assigned and name not in builtins:
            issues.append({
                "line": lineno,
                "severity": "error",
                "message": f"Name '{name}' wird benutzt aber wurde nicht definiert.",
            })

    if issues:
        summary = f"{len(issues)} Fehler gefunden."
    else:
        summary = "Alles korrekt."

    return {"issues": issues, "summary": summary}

# ---------------------------------------------------------------------------
# System-Prompts je Stufe
# ---------------------------------------------------------------------------

_SYNTAX_SYSTEM = """Du bist ein Python-Code-Reviewer. Analysiere NUR Syntaxfehler.
Behandle den Code als vollständiges, eigenständiges Skript — es gibt keinen äußeren Scope.
Variablen die benutzt aber nirgendwo im Snippet zugewiesen oder als Parameter definiert werden, sind undefiniert und müssen als Fehler gemeldet werden.
Prüfe: fehlende Doppelpunkte, falsche Einrückung, nicht geschlossene Klammern/Strings,
ungültige Schlüsselwörter, fehlende return-Statements in Funktionen, undefinierte Variablen.

Antworte NUR mit validem JSON:
{
  "issues": [
    { "line": 3, "severity": "error", "message": "Fehlender Doppelpunkt nach if-Bedingung" }
  ],
  "summary": "1 Fehler gefunden."
}
severity: "error" oder "warning". summary: maximal 1 kurzer Satz.
Wenn keine Probleme: issues=[], summary="Alles korrekt."
Kein Markdown, nur JSON."""

_STYLE_SYSTEM = """Du bist ein Python-Code-Reviewer. Analysiere NUR Stil- und PEP8-Probleme.
Prüfe: Variablennamen (snake_case), Zeilenlänge (>79 Zeichen), fehlende Leerzeichen um Operatoren,
fehlende Leerzeilen zwischen Funktionen, Magic Numbers, fehlende Docstrings bei Funktionen.

Kontext aus Syntax-Analyse: {syntax_summary}

Antworte NUR mit validem JSON:
{
  "issues": [
    { "line": 5, "severity": "warning", "message": "Variablenname sollte snake_case sein" }
  ],
  "summary": "2 Stil-Probleme gefunden."
}
severity: "warning". summary: maximal 1 kurzer Satz.
Wenn keine Probleme: issues=[], summary="Stil einwandfrei."
Kein Markdown, nur JSON."""

_BESTPRACTICES_SYSTEM = """Du bist ein Python-Code-Reviewer. Analysiere NUR Best-Practice-Verstöße.
Prüfe: nicht-pythonische Muster (range(len()) statt enumerate), mutable Default-Argumente,
bare except, unnötige Typ-Konvertierungen, String-Konkatenation in Schleifen,
global-Variablen, redundante Vergleiche (== True/False/None statt is).

Kontext aus vorherigen Schritten: {syntax_summary} | {style_summary}

Antworte NUR mit validem JSON:
{
  "issues": [
    {
      "line": 3,
      "severity": "info",
      "message": "Redundanter Vergleich mit True — verwende direkt den Ausdruck",
      "suggestion": "if x > 4:"
    }
  ],
  "summary": "1 Verbesserungsvorschlag."
}
WICHTIG: Jedes Issue MUSS ein "suggestion" Feld haben — den verbesserten Code-Ausschnitt (nur die betroffene Zeile, kein ganzer Block).
severity: "info" oder "warning". summary: maximal 1 kurzer Satz.
Wenn keine Probleme: issues=[], summary="Professioneller Code."
Kein Markdown, nur JSON."""


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_json(text: str) -> dict:
    # Always extract the first {...} block — handles markdown fences, leading/trailing text
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if not match:
        # No JSON object found at all
        return {"issues": [], "summary": "Keine Probleme gefunden."}
    # Use greedy match to get the full outermost object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"issues": [], "summary": "Keine Probleme gefunden."}


# ---------------------------------------------------------------------------
# Chain-Stufen als Runnables
# ---------------------------------------------------------------------------

def _make_syntax_step():
    def run(inputs: dict) -> dict:
        parsed = _static_syntax_check(inputs["code"])
        return {**inputs, "syntax": parsed}
    return RunnableLambda(run)


def _make_style_step():
    def run(inputs: dict) -> dict:
        llm = get_llm()
        syntax_summary = inputs["syntax"].get("summary", "")
        system = _STYLE_SYSTEM.replace("{syntax_summary}", syntax_summary)
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
        syntax_summary = inputs["syntax"].get("summary", "")
        style_summary = inputs["style"].get("summary", "")
        system = _BESTPRACTICES_SYSTEM.replace("{syntax_summary}", syntax_summary).replace("{style_summary}", style_summary)
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
