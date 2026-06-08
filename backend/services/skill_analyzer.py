"""Skill-Analyse-Service: erkennt Python-Skills im Code und bewertet den Wissensstand.

LLM-Pfad (OpenAI / Ollama): strukturierte JSON-Ausgabe.
Fallback-Pfad (kein LLM): regelbasierte Keyword-Erkennung.
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

# Die einzigen gültigen Skill-Keys — das LLM darf nur diese zurückgeben
VALID_SKILLS = {
    # Beginner
    "variables", "datatypes", "input_output", "string_methods", "type_conversion",
    "if_else", "for_loop", "while_loop", "lists", "tuples", "sets", "dictionaries",
    "functions",
    # Intermediate
    "list_comprehension", "error_handling", "file_io", "classes_basic",
    "instance_methods", "instance_variables", "static_methods", "class_methods",
    "magic_methods", "modules_imports", "lambda_functions", "map_filter_reduce",
    # Advanced
    "inheritance", "polymorphism", "abstract_classes", "interfaces", "decorators",
    "generators", "context_managers", "recursion", "algorithms", "design_patterns",
    "async_await", "testing",
}

# Grenzwerte für Status-Berechnung
THRESHOLD_UNDERSTOOD = 75
THRESHOLD_PARTIAL    = 40


def _status_from_score(score: int) -> str:
    if score >= THRESHOLD_UNDERSTOOD:
        return "understood"
    if score >= THRESHOLD_PARTIAL:
        return "partial"
    return "not_understood"


# ---------------------------------------------------------------------------
# Regelbasierter Fallback
# ---------------------------------------------------------------------------

_KEYWORD_MAP: dict[str, list[str]] = {
    # Beginner
    "variables":          ["=", "int(", "float(", "str(", "bool("],
    "datatypes":          ["int", "float", "str", "bool", "type("],
    "input_output":       ["input(", "print("],
    "string_methods":     [".upper(", ".lower(", ".split(", ".strip(", ".replace(", ".format("],
    "type_conversion":    ["int(", "float(", "str(", "bool(", "list(", "tuple("],
    "if_else":            ["if ", "elif ", "else:"],
    "for_loop":           ["for ", " in ", "range("],
    "while_loop":         ["while "],
    "lists":              ["[", "]", ".append(", ".extend(", ".pop("],
    "tuples":             ["(", ",)", "tuple(", ".count(", ".index("],
    "sets":               ["set(", ".add(", ".union(", ".intersection(", ".discard("],
    "dictionaries":       ["{", ".keys(", ".values(", ".items(", ".get("],
    "functions":          ["def ", "return "],
    # Intermediate
    "list_comprehension": ["[x for", "[ x for", "for x in", "if x"],
    "error_handling":     ["try:", "except", "finally:", "raise ", "Exception("],
    "file_io":            ["open(", ".read(", ".write(", ".close(", "with open("],
    "classes_basic":      ["class ", "def __init__"],
    "instance_methods":   ["self.", "def ", "class "],
    "instance_variables": ["self.", "__init__"],
    "static_methods":     ["@staticmethod", "staticmethod("],
    "class_methods":      ["@classmethod", "cls."],
    "magic_methods":      ["__str__", "__repr__", "__len__", "__add__", "__eq__"],
    "modules_imports":    ["import ", "from ", "as "],
    "lambda_functions":   ["lambda ", "lambda:"],
    "map_filter_reduce":  ["map(", "filter(", "reduce(", "from functools"],
    # Advanced
    "inheritance":        ["class ", "(", "):", "super("],
    "polymorphism":       ["super(", "isinstance(", "override"],
    "abstract_classes":   ["from abc", "ABC", "@abstractmethod"],
    "interfaces":         ["from abc", "ABC", "@abstractmethod"],
    "decorators":         ["@", "def decorator", "functools.wraps"],
    "generators":         ["yield ", "yield from", "next(", "iter("],
    "context_managers":   ["with ", "__enter__", "__exit__", "contextmanager"],
    "recursion":          ["def ", "return ", "factorial", "fibonacci"],
    "algorithms":         ["sort", "search", "binary", "bubble", "merge"],
    "design_patterns":    ["class ", "singleton", "factory", "observer"],
    "async_await":        ["async def", "await ", "asyncio"],
    "testing":            ["import unittest", "def test_", "assert ", "pytest"],
}

_COMMON_MISTAKES: dict[str, list[str]] = {
    "for_loop":    ["Doppelpunkt am Ende fehlt", "Einrückung fehlt"],
    "while_loop":  ["Endlosschleife möglich", "Abbruchbedingung fehlt"],
    "functions":   ["return-Wert fehlt", "Einrückung fehlt"],
    "if_else":     ["Doppelpunkt fehlt", "Vergleich mit = statt =="],
    "variables":   ["Typ-Fehler", "Variablenname nicht definiert"],
    "input_output":["Typ-Konvertierung fehlt", "print-Syntax falsch"],
    "lists":       ["Index außerhalb des Bereichs", "Falsche Methode verwendet"],
}


def _rule_based_analysis(code: str, question: str) -> dict:
    """Keyword-Matching — wird verwendet, wenn kein LLM verfügbar ist.

    Kombiniert Code und Frage zu einem einzigen Text für die Keyword-Suche.
    Score-Heuristik: Syntaxfehler-Indikator im Text → 35, sonst 60 (niedrig genug
    um LLM-Ergebnis zu unterscheiden).
    """
    text = (code + " " + question).lower()  # kombiniert für einfache Keyword-Suche

    detected: list[str] = []
    for skill, keywords in _KEYWORD_MAP.items():
        if any(kw.lower() in text for kw in keywords):
            detected.append(skill)

    main_skill = detected[0] if detected else "variables"  # Fallback: variables ist der Einstiegs-Skill

    # Syntaxfehler-Erkennung: "SyntaxError" im Text ODER def ohne Doppelpunkt
    has_syntax_error = (
        re.search(r"\bsyntaxerror\b", text) is not None
        or (code and not code.strip().endswith(":") and "def " in code and ":" not in code)
    )
    score = 35 if has_syntax_error else 60
    mistakes = _COMMON_MISTAKES.get(main_skill, [])

    return {
        "detected_skills": detected or ["variables"],
        "main_skill":      main_skill,
        "score":           score,
        "status":          _status_from_score(score),
        "mistakes":        mistakes[:2],  # max. 2 Fehler zurückgeben
        "feedback":        "Regelbasierte Analyse (kein LLM verfügbar).",
        "recommended_next_exercise": f"Übe das Thema '{main_skill}' mit einem einfachen Beispiel.",
    }


# ---------------------------------------------------------------------------
# LLM-basierte Analyse
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Du bist ein Python-Tutor-Analyst. Analysiere den Code oder die Frage des Studenten.

Gib NUR gültiges JSON zurück — kein Markdown, keine Erklärungen drumherum.

Erlaubte skill_keys (AUSSCHLIESSLICH diese):
  variables, datatypes, input_output, string_methods, type_conversion,
  if_else, for_loop, while_loop, lists, tuples, sets, dictionaries, functions,
  list_comprehension, error_handling, file_io, classes_basic,
  instance_methods, instance_variables, static_methods, class_methods,
  magic_methods, modules_imports, lambda_functions, map_filter_reduce,
  inheritance, polymorphism, abstract_classes, interfaces, decorators,
  generators, context_managers, recursion, algorithms, design_patterns,
  async_await, testing

JSON-Schema:
{
  "detected_skills": ["<skill_key>", ...],
  "main_skill": "<skill_key>",
  "score": <0-100>,
  "status": "understood" | "partial" | "not_understood",
  "mistakes": ["<Fehlerbeschreibung>", ...],
  "feedback": "<Kurzes, konstruktives Feedback auf Deutsch>",
  "recommended_next_exercise": "<Konkrete Übungsaufgabe auf Deutsch>"
}

Score-Regeln:
- 75–100: Student zeigt klares Verständnis
- 40–74:  Teilweises Verständnis, kleinere Fehler
- 0–39:   Grundlegende Missverständnisse oder Syntaxfehler

Antworte AUSSCHLIESSLICH mit dem JSON-Objekt."""


def _parse_llm_json(raw: str) -> dict | None:
    """Extrahiert JSON aus LLM-Antwort (tolerant gegenüber Markdown-Wrapping).

    Gibt None zurück wenn kein gültiges JSON gefunden oder Skill-Keys alle ungültig.
    Skill-Keys werden gegen VALID_SKILLS geprüft — verhindert halluzinierte Skills.
    Score wird auf 0-100 geclampt um Grenzwertprobleme zu vermeiden.
    """
    # Markdown-Code-Block-Marker entfernen (LLM gibt manchmal ```json ... ``` zurück)
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    # Erstes {...} herausschneiden — ignoriert Text vor/nach dem JSON-Objekt
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None

    # Skill-Keys gegen Whitelist filtern — LLM darf nur definierte Keys zurückgeben
    detected = [s for s in data.get("detected_skills", []) if s in VALID_SKILLS]
    main = data.get("main_skill", "")
    if main not in VALID_SKILLS:
        # ungültiger main_skill → ersten erkannten nehmen oder Fallback
        main = detected[0] if detected else "variables"

    # Score auf gültigen Bereich begrenzen
    score = max(0, min(100, int(data.get("score", 0))))

    return {
        "detected_skills":        detected or ["variables"],
        "main_skill":             main,
        "score":                  score,
        "status":                 _status_from_score(score),
        "mistakes":               data.get("mistakes", []),
        "feedback":               data.get("feedback", ""),
        "recommended_next_exercise": data.get("recommended_next_exercise", ""),
    }


def analyze_skill(code: str, question: str = "") -> dict:
    """Analysiert Code / Frage und gibt ein strukturiertes Skill-Ergebnis zurück.

    Versucht LLM-Analyse mit strukturierter JSON-Ausgabe.
    Fallback auf regelbasierte Keyword-Analyse wenn LLM nicht verfügbar oder JSON-Parse fehlschlägt.

    Lazy-Import von get_llm um zirkuläre Imports zu vermeiden (services ↔ agent).
    """
    prompt_content = f"Code:\n```python\n{code}\n```\n\nFrage: {question}" if code else f"Frage: {question}"

    try:
        from agent.config import get_llm
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt_content),
        ])
        raw = str(response.content) if hasattr(response, "content") else str(response)
        result = _parse_llm_json(raw)
        if result:
            logger.info("LLM-Skill-Analyse erfolgreich: main_skill=%s score=%d", result["main_skill"], result["score"])
            return result
        # JSON-Parse fehlgeschlagen → Regellogik (LLM hat kein gültiges JSON zurückgegeben)
        logger.warning("LLM-JSON-Parse fehlgeschlagen — Fallback auf Regellogik")
    except Exception as e:
        logger.warning("LLM nicht verfügbar (%s) — Fallback auf Regellogik", e)

    return _rule_based_analysis(code, question)
