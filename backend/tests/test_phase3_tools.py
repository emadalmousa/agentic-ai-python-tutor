"""
Tests: Phase 3 — Five new LangChain tools.

Covers:
1. _utils._parse_json  — plain JSON, markdown-fenced JSON, invalid input
2. exercise_evaluator_tool (evaluate_exercise) — richtig/teilweise/falsch branches,
   exception fallback, empty-stdout branch
3. hint_tool (get_hint) — returns non-empty string, exception fallback
4. skill_test_evaluator_tool scoring logic — MC arithmetic, code_reading, mini_task,
   total_score and passed flag
5. Import smoke tests — all five tools import without error

No running LLM instance is required — all llm.invoke() calls are mocked.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_llm(response_content: str) -> MagicMock:
    """Return a mock LLM whose .invoke() returns an object with .content set."""
    mock_response = MagicMock()
    mock_response.content = response_content

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response

    return mock_llm


def _make_raising_llm(exc: Exception) -> MagicMock:
    """Return a mock LLM whose .invoke() raises the given exception."""
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = exc
    return mock_llm


# ---------------------------------------------------------------------------
# 1. _utils._parse_json
# ---------------------------------------------------------------------------


class TestParseJson:
    def _parse(self, text: str) -> dict:
        import agent.tools._utils as utils_module

        return utils_module._parse_json(text)

    def test_parses_plain_json_string(self):
        """A plain JSON object string is parsed into a dict."""
        result = self._parse('{"result": "richtig", "hint": "Gut gemacht!"}')

        assert result == {"result": "richtig", "hint": "Gut gemacht!"}

    def test_parses_json_wrapped_in_json_fence(self):
        """JSON wrapped in ```json ... ``` fences is stripped and parsed correctly."""
        fenced = '```json\n{"result": "falsch", "what_went_wrong": "Fehler"}\n```'

        result = self._parse(fenced)

        assert result["result"] == "falsch"
        assert result["what_went_wrong"] == "Fehler"

    def test_parses_json_wrapped_in_plain_fence(self):
        """JSON wrapped in plain ``` ... ``` fences (no language tag) is parsed."""
        fenced = '```\n{"key": "value"}\n```'

        result = self._parse(fenced)

        assert result == {"key": "value"}

    def test_raises_json_decode_error_on_invalid_input(self):
        """Completely invalid input raises json.JSONDecodeError (not swallowed)."""
        with pytest.raises(json.JSONDecodeError):
            self._parse("this is not json at all!!")

    def test_raises_on_empty_string(self):
        """An empty string raises json.JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            self._parse("")

    def test_raises_on_fence_containing_garbage(self):
        """Fenced but non-JSON content still raises json.JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            self._parse("```json\nnot valid json\n```")


# ---------------------------------------------------------------------------
# 2. evaluate_exercise
# ---------------------------------------------------------------------------


class TestEvaluateExercise:
    """Tests for the evaluate_exercise LangChain tool.

    The tool returns a JSON *string* when called via .invoke().
    We parse that string and inspect the dict.
    """

    _VALID_INPUT = {
        "code": "print('Hallo')",
        "exercise_description": "Gib Hallo aus.",
        "expected_output": "Hallo",
        "stdout": "Hallo",
    }

    def _invoke(self, llm_response: str, input_override: dict | None = None) -> dict:
        import agent.tools.exercise_evaluator_tool as mod

        mock_llm = _make_mock_llm(llm_response)
        tool_input = {**self._VALID_INPUT, **(input_override or {})}

        with patch.object(mod, "get_llm", return_value=mock_llm):
            raw = mod.evaluate_exercise.invoke(tool_input)

        return json.loads(raw)

    # --- result = "richtig" ---

    def test_result_richtig_returned(self):
        """LLM returning result='richtig' → tool result dict has result='richtig'."""
        llm_json = json.dumps({
            "result": "richtig",
            "what_was_good": "Super Lösung!",
            "what_went_wrong": "",
            "hint": "Versuche die nächste Aufgabe.",
        })

        result = self._invoke(llm_json)

        assert result["result"] == "richtig"
        assert result["what_was_good"] != ""

    # --- result = "teilweise" ---

    def test_result_teilweise_returned(self):
        """LLM returning result='teilweise' → tool result dict has result='teilweise'."""
        llm_json = json.dumps({
            "result": "teilweise",
            "what_was_good": "Guter Ansatz.",
            "what_went_wrong": "Kleiner Fehler.",
            "hint": "Schau nochmal hin.",
        })
        # Stdout differs from expected_output to hit the "mismatch" branch
        result = self._invoke(llm_json, {"stdout": "Hallo Welt", "expected_output": "Hallo"})

        assert result["result"] == "teilweise"

    # --- result = "falsch" ---

    def test_result_falsch_returned(self):
        """LLM returning result='falsch' → tool result dict has result='falsch'."""
        llm_json = json.dumps({
            "result": "falsch",
            "what_was_good": "Du hast Code geschrieben.",
            "what_went_wrong": "Falsches Konzept.",
            "hint": "Nutze eine for-Schleife.",
        })
        result = self._invoke(llm_json, {"stdout": "falsch output", "expected_output": "Hallo"})

        assert result["result"] == "falsch"

    # --- empty stdout branch always returns "falsch" ---

    def test_empty_stdout_forces_falsch(self):
        """When stdout is empty the tool must return result='falsch' regardless of LLM."""
        llm_json = json.dumps({
            "result": "falsch",
            "what_was_good": "Guter Versuch.",
            "what_went_wrong": "Keine Ausgabe.",
            "hint": "Füge print() hinzu.",
        })
        result = self._invoke(llm_json, {"stdout": ""})

        assert result["result"] == "falsch"

    def test_whitespace_only_stdout_forces_falsch(self):
        """stdout containing only whitespace is treated as empty → result='falsch'."""
        llm_json = json.dumps({
            "result": "falsch",
            "what_was_good": "Guter Versuch.",
            "what_went_wrong": "Keine Ausgabe.",
            "hint": "Prüfe print().",
        })
        result = self._invoke(llm_json, {"stdout": "   \n  "})

        assert result["result"] == "falsch"

    # --- exception fallback ---

    @pytest.mark.parametrize("stdout,expected_output", [
        ("", "5"),            # empty-stdout branch
        ("wrong output", "5"),  # mismatch branch
        ("Hallo", "Hallo"),   # exact-match branch
    ], ids=["empty-stdout", "mismatch", "exact-match"])
    def test_llm_exception_propagates_from_all_branches(self, stdout, expected_output):
        """In all three evaluation branches llm.invoke() is called outside the try/except
        that only guards _parse_json.  A raw LLM exception therefore propagates through
        the LangChain tool layer.

        This test documents the current behaviour so regressions are caught.
        """
        import agent.tools.exercise_evaluator_tool as mod

        mock_llm = _make_raising_llm(RuntimeError("LLM unavailable"))

        tool_input = {
            "code": "x = 1",
            "exercise_description": "Test",
            "expected_output": expected_output,
            "stdout": stdout,
        }

        with patch.object(mod, "get_llm", return_value=mock_llm):
            with pytest.raises(RuntimeError, match="LLM unavailable"):
                mod.evaluate_exercise.invoke(tool_input)

    def test_llm_invalid_json_returns_fallback(self):
        """When the LLM returns invalid JSON the tool returns a fallback dict (no exception)."""
        result = self._invoke("this is not json", {"stdout": "wrong", "expected_output": "right"})

        assert result["result"] == "falsch"
        assert "what_was_good" in result

    # --- required output fields always present ---

    def test_result_dict_has_all_required_fields(self):
        """The returned dict must always contain result, what_was_good, what_went_wrong, hint."""
        llm_json = json.dumps({
            "result": "richtig",
            "what_was_good": "Toll!",
            "what_went_wrong": "",
            "hint": "Weiter so!",
        })
        result = self._invoke(llm_json)

        for field in ("result", "what_was_good", "what_went_wrong", "hint"):
            assert field in result, f"Missing field: {field}"

    def test_exact_stdout_match_normalises_invalid_result_value(self):
        """If the LLM returns the placeholder string 'richtig_oder_teilweise' it is normalised
        to 'richtig'."""
        # The tool sends a prompt asking for 'richtig_oder_teilweise' and normalises it
        llm_json = json.dumps({
            "result": "richtig_oder_teilweise",
            "what_was_good": "Gut!",
            "what_went_wrong": "",
            "hint": "Weiter!",
        })
        result = self._invoke(llm_json)

        assert result["result"] == "richtig"

    def test_exact_stdout_match_fills_empty_what_was_good(self):
        """If the LLM returns empty what_was_good on an exact match, the tool fills it."""
        llm_json = json.dumps({
            "result": "richtig",
            "what_was_good": "",
            "what_went_wrong": "",
            "hint": "Weiter so!",
        })
        result = self._invoke(llm_json)

        assert result["what_was_good"] != ""

    def test_mismatch_branch_fills_empty_what_was_good(self):
        """On the mismatch branch, if LLM returns empty what_was_good, the tool fills it."""
        llm_json = json.dumps({
            "result": "falsch",
            "what_was_good": "",
            "what_went_wrong": "Falsche Ausgabe.",
            "hint": "Schau nochmal.",
        })
        result = self._invoke(
            llm_json, {"stdout": "wrong output", "expected_output": "Hallo"}
        )

        assert result["what_was_good"] != ""


# ---------------------------------------------------------------------------
# 3. get_hint
# ---------------------------------------------------------------------------


class TestGetHint:
    _BASE_INPUT = {
        "code": "for i in range(5):\n    pass",
        "exercise_description": "Gib die Zahlen 0 bis 4 aus.",
        "hint_level": 1,
    }

    def _invoke(self, llm_response: str, input_override: dict | None = None) -> str:
        import agent.tools.hint_tool as mod

        mock_llm = _make_mock_llm(llm_response)
        tool_input = {**self._BASE_INPUT, **(input_override or {})}

        with patch.object(mod, "get_llm", return_value=mock_llm):
            return mod.get_hint.invoke(tool_input)

    def test_returns_non_empty_string(self):
        """get_hint returns a non-empty string from the LLM."""
        result = self._invoke("Denke an eine Schleife mit print().")

        assert isinstance(result, str)
        assert result.strip() != ""

    def test_returns_exact_llm_content(self):
        """get_hint returns the LLM response content verbatim."""
        hint_text = "Verwende eine for-Schleife mit range()."
        result = self._invoke(hint_text)

        assert result == hint_text

    def test_exception_returns_german_fallback(self):
        """When the LLM raises an exception the tool returns the German fallback string."""
        import agent.tools.hint_tool as mod

        mock_llm = _make_raising_llm(ConnectionError("LLM not reachable"))

        with patch.object(mod, "get_llm", return_value=mock_llm):
            result = mod.get_hint.invoke(self._BASE_INPUT)

        assert "Tipp" in result or "verfügbar" in result
        assert isinstance(result, str)
        assert result.strip() != ""

    def test_hint_level_clamped_to_1_for_zero(self):
        """hint_level=0 is clamped to 1 — the tool must not raise."""
        result = self._invoke("Ein Tipp.", {"hint_level": 0})

        assert isinstance(result, str)

    def test_hint_level_clamped_to_3_for_large_value(self):
        """hint_level=99 is clamped to 3 — the tool must not raise."""
        result = self._invoke("Detaillierter Tipp.", {"hint_level": 99})

        assert isinstance(result, str)

    @pytest.mark.parametrize("level", [1, 2, 3])
    def test_valid_hint_levels_return_string(self, level: int):
        """All three valid hint levels return a string result."""
        result = self._invoke(f"Tipp Stufe {level}.", {"hint_level": level})

        assert isinstance(result, str)
        assert result.strip() != ""


# ---------------------------------------------------------------------------
# 4. evaluate_skill_test scoring logic
# ---------------------------------------------------------------------------


class TestEvaluateSkillTestScoring:
    """Tests for the scoring arithmetic in evaluate_skill_test.

    The MC section is pure Python (no LLM). The code_reading and mini_task
    sections call the LLM — we mock it to test score accumulation.
    """

    _BASE_INPUT = {
        "skill_key": "for_loop",
        "mini_task_description": "Gib 1 bis 3 aus.",
        "mini_task_expected": "1\n2\n3",
        "mini_task_code": "for i in range(1, 4):\n    print(i)",
        "code_reading_answer": "8",
        "code_reading_correct": "8",
    }

    def _make_llm_correct(self) -> MagicMock:
        return _make_mock_llm('{"correct": true, "explanation": "Richtig!"}')

    def _make_llm_incorrect(self) -> MagicMock:
        return _make_mock_llm('{"correct": false, "explanation": "Falsch."}')

    def _invoke(self, mc_answers: str, mc_correct: str, llm: MagicMock) -> dict:
        import agent.tools.skill_test_evaluator_tool as mod

        tool_input = {
            **self._BASE_INPUT,
            "mc_answers": mc_answers,
            "mc_correct": mc_correct,
        }

        with patch.object(mod, "get_llm", return_value=llm):
            raw = mod.evaluate_skill_test.invoke(tool_input)

        return json.loads(raw)

    # --- MC scoring ---

    def test_mc_3_correct_answers_gives_30_points(self):
        """3 correct MC answers → mc_score = 30."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_correct())

        assert result["mc_score"] == 30

    def test_mc_2_correct_answers_gives_20_points(self):
        """2 correct MC answers → mc_score = 20."""
        result = self._invoke("A,B,D", "A,B,C", self._make_llm_correct())

        assert result["mc_score"] == 20

    def test_mc_0_correct_answers_gives_0_points(self):
        """0 correct MC answers → mc_score = 0."""
        result = self._invoke("D,D,D", "A,B,C", self._make_llm_correct())

        assert result["mc_score"] == 0

    def test_mc_1_correct_answer_gives_10_points(self):
        """1 correct MC answer → mc_score = 10."""
        result = self._invoke("A,D,D", "A,B,C", self._make_llm_correct())

        assert result["mc_score"] == 10

    # --- code_reading scoring ---

    def test_code_reading_correct_gives_30_points(self):
        """LLM returning correct=true for code reading → code_reading_score = 30."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_correct())

        assert result["code_reading_score"] == 30

    def test_code_reading_incorrect_gives_0_points(self):
        """LLM returning correct=false for code reading → code_reading_score = 0."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_incorrect())

        assert result["code_reading_score"] == 0

    # --- mini_task scoring ---

    def test_mini_task_correct_gives_40_points(self):
        """LLM returning correct=true for mini_task → mini_task_score = 40."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_correct())

        assert result["mini_task_score"] == 40

    def test_mini_task_incorrect_gives_0_points(self):
        """LLM returning correct=false for mini_task → mini_task_score = 0."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_incorrect())

        assert result["mini_task_score"] == 0

    # --- total_score and passed ---

    def test_total_score_is_sum_of_all_parts(self):
        """total_score = mc_score + code_reading_score + mini_task_score."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_correct())

        expected = result["mc_score"] + result["code_reading_score"] + result["mini_task_score"]
        assert result["total_score"] == expected

    def test_passed_true_when_total_score_at_least_60(self):
        """passed=True when total_score >= 60 (all correct → 100 points)."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_correct())

        assert result["total_score"] == 100
        assert result["passed"] is True

    def test_passed_false_when_total_score_below_60(self):
        """passed=False when total_score < 60 (all wrong → 0 points)."""
        result = self._invoke("D,D,D", "A,B,C", self._make_llm_incorrect())

        assert result["total_score"] == 0
        assert result["passed"] is False

    def test_boundary_exactly_60_is_passed(self):
        """total_score == 60 must be passed=True (boundary condition)."""
        # MC=0 (all wrong), code_reading=20? Not achievable with fixed weights.
        # MC=30 correct + code_reading=30 correct + mini_task=0 wrong = 60 → passed
        # mc_answers all correct, LLM correct for code_reading, incorrect for mini_task
        # We need the LLM to return correct=true for code_reading and correct=false for mini_task.
        # Since both LLM calls share the same mock, we use side_effect to alternate responses.
        import agent.tools.skill_test_evaluator_tool as mod

        mock_response_correct = MagicMock()
        mock_response_correct.content = '{"correct": true, "explanation": "Richtig!"}'
        mock_response_incorrect = MagicMock()
        mock_response_incorrect.content = '{"correct": false, "explanation": "Falsch."}'

        mock_llm = MagicMock()
        # First LLM call is code_reading (correct=true → 30), second is mini_task (correct=false → 0)
        mock_llm.invoke.side_effect = [mock_response_correct, mock_response_incorrect]

        tool_input = {
            **self._BASE_INPUT,
            "mc_answers": "A,B,C",
            "mc_correct": "A,B,C",
        }

        with patch.object(mod, "get_llm", return_value=mock_llm):
            raw = mod.evaluate_skill_test.invoke(tool_input)

        result = json.loads(raw)

        assert result["mc_score"] == 30
        assert result["code_reading_score"] == 30
        assert result["mini_task_score"] == 0
        assert result["total_score"] == 60
        assert result["passed"] is True

    def test_59_points_is_not_passed(self):
        """total_score == 59 must be passed=False (one below boundary)."""
        # MC=20 (2 correct), code_reading=30 correct, mini_task=0 incorrect → 50 points (not 59)
        # Closest achievable: MC=20 + code_reading=30 + mini_task=0 = 50 → False
        # or MC=30 + code_reading=0 + mini_task=0 = 30 → False
        # 59 is not achievable with fixed weights (10+10+10 / 30 / 40).
        # Use 50 as a "below 60" case: MC=20 + code=30 + mini=0.
        import agent.tools.skill_test_evaluator_tool as mod

        mock_response_correct = MagicMock()
        mock_response_correct.content = '{"correct": true, "explanation": "Richtig!"}'
        mock_response_incorrect = MagicMock()
        mock_response_incorrect.content = '{"correct": false, "explanation": "Falsch."}'

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = [mock_response_correct, mock_response_incorrect]

        tool_input = {
            **self._BASE_INPUT,
            "mc_answers": "A,B,D",
            "mc_correct": "A,B,C",
        }

        with patch.object(mod, "get_llm", return_value=mock_llm):
            raw = mod.evaluate_skill_test.invoke(tool_input)

        result = json.loads(raw)

        assert result["mc_score"] == 20
        assert result["code_reading_score"] == 30
        assert result["mini_task_score"] == 0
        assert result["total_score"] == 50
        assert result["passed"] is False

    # --- per_question_feedback structure ---

    def test_per_question_feedback_has_5_entries(self):
        """per_question_feedback must contain exactly 5 items: 3 MC + code_reading + mini_task."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_correct())

        assert len(result["per_question_feedback"]) == 5

    def test_result_dict_has_all_required_keys(self):
        """The result dict must contain total_score, passed, mc_score, code_reading_score,
        mini_task_score, per_question_feedback."""
        result = self._invoke("A,B,C", "A,B,C", self._make_llm_correct())

        for key in ("total_score", "passed", "mc_score", "code_reading_score",
                    "mini_task_score", "per_question_feedback"):
            assert key in result, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# 5. Import smoke tests
# ---------------------------------------------------------------------------


class TestToolImports:
    """Verify that each tool module can be imported without error.

    These tests confirm that _utils is accessible from all tools and that
    there are no import-time errors in any module.
    """

    def test_import_exercise_evaluator_tool(self):
        """exercise_evaluator_tool imports without error."""
        import agent.tools.exercise_evaluator_tool as mod  # noqa: F401

        assert hasattr(mod, "evaluate_exercise")

    def test_import_hint_tool(self):
        """hint_tool imports without error."""
        import agent.tools.hint_tool as mod  # noqa: F401

        assert hasattr(mod, "get_hint")

    def test_import_exercise_generator_tool(self):
        """exercise_generator_tool imports without error."""
        import agent.tools.exercise_generator_tool as mod  # noqa: F401

        assert hasattr(mod, "generate_exercise")

    def test_import_skill_test_generator_tool(self):
        """skill_test_generator_tool imports without error."""
        import agent.tools.skill_test_generator_tool as mod  # noqa: F401

        assert hasattr(mod, "generate_skill_test")

    def test_import_skill_test_evaluator_tool(self):
        """skill_test_evaluator_tool imports without error."""
        import agent.tools.skill_test_evaluator_tool as mod  # noqa: F401

        assert hasattr(mod, "evaluate_skill_test")

    def test_import_utils(self):
        """_utils imports without error and exposes _parse_json."""
        import agent.tools._utils as utils_module  # noqa: F401

        assert callable(utils_module._parse_json)

    def test_utils_accessible_from_exercise_evaluator(self):
        """_parse_json imported by exercise_evaluator_tool refers to the correct function."""
        import agent.tools.exercise_evaluator_tool as mod

        # The module must have imported _parse_json at module level
        assert hasattr(mod, "_parse_json")
        assert callable(mod._parse_json)

    def test_utils_accessible_from_exercise_generator(self):
        """_parse_json imported by exercise_generator_tool refers to the correct function."""
        import agent.tools.exercise_generator_tool as mod

        assert hasattr(mod, "_parse_json")
        assert callable(mod._parse_json)

    def test_utils_accessible_from_skill_test_generator(self):
        """_parse_json imported by skill_test_generator_tool refers to the correct function."""
        import agent.tools.skill_test_generator_tool as mod

        assert hasattr(mod, "_parse_json")
        assert callable(mod._parse_json)

    def test_utils_accessible_from_skill_test_evaluator(self):
        """_parse_json imported by skill_test_evaluator_tool refers to the correct function."""
        import agent.tools.skill_test_evaluator_tool as mod

        assert hasattr(mod, "_parse_json")
        assert callable(mod._parse_json)
