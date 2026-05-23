"""
Phase 2 tests: LangChain explain_code_tool and debug_code_tool.

Validates:
- explain_code_tool returns a string, forwards question into the prompt,
  and delegates LLM instantiation to get_llm()
- debug_code_tool returns a dict with the expected keys and delegates to get_llm()
- _parse_debug_response handles clean JSON, markdown-fenced JSON, braces inside
  the suggestion value, and completely unparseable output

No running Ollama instance is required — all llm.invoke() calls are mocked.
"""

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


# ---------------------------------------------------------------------------
# explain_code_tool
# ---------------------------------------------------------------------------


class TestExplainCodeTool:
    def test_explain_tool_returns_string(self):
        """explain_code_tool.invoke() must return the LLM's response as a plain str."""
        import agent.tools.explain_tool as explain_module

        mock_llm = _make_mock_llm("Erklärung: Diese Funktion gibt 'Hallo' aus.")

        with patch.object(explain_module, "get_llm", return_value=mock_llm):
            result = explain_module.explain_code_tool.invoke({"code": "print('Hallo')"})

        assert isinstance(result, str)
        assert result == "Erklärung: Diese Funktion gibt 'Hallo' aus."

    def test_explain_tool_without_question(self):
        """explain_code_tool.invoke() works when question is omitted."""
        import agent.tools.explain_tool as explain_module

        mock_llm = _make_mock_llm("Schritt 1: …")

        with patch.object(explain_module, "get_llm", return_value=mock_llm):
            result = explain_module.explain_code_tool.invoke({"code": "x = 1"})

        # No exception raised; a string is returned
        assert isinstance(result, str)
        # llm.invoke was called exactly once
        mock_llm.invoke.assert_called_once()

    def test_explain_tool_with_question(self):
        """When question is provided it must appear in the HumanMessage content."""
        import agent.tools.explain_tool as explain_module
        from langchain_core.messages import HumanMessage

        mock_llm = _make_mock_llm("Antwort auf die Frage …")

        with patch.object(explain_module, "get_llm", return_value=mock_llm):
            explain_module.explain_code_tool.invoke(
                {"code": "x = 1", "question": "Was ist eine Variable?"}
            )

        # Inspect the messages list passed to llm.invoke
        call_args = mock_llm.invoke.call_args
        messages = call_args[0][0]  # first positional argument

        human_messages = [m for m in messages if isinstance(m, HumanMessage)]
        assert human_messages, "No HumanMessage found in llm.invoke call"

        human_content = human_messages[0].content
        assert "Was ist eine Variable?" in human_content

    def test_explain_tool_uses_get_llm(self):
        """explain_code_tool must call get_llm() — it must not instantiate ChatOllama directly."""
        import agent.tools.explain_tool as explain_module

        mock_llm = _make_mock_llm("OK")

        with patch.object(explain_module, "get_llm", return_value=mock_llm) as mock_get_llm:
            explain_module.explain_code_tool.invoke({"code": "pass"})

        mock_get_llm.assert_called_once()


# ---------------------------------------------------------------------------
# debug_code_tool
# ---------------------------------------------------------------------------


class TestDebugCodeTool:
    def test_debug_tool_returns_dict(self):
        """debug_code_tool.invoke() must return a dict."""
        import agent.tools.debug_tool as debug_module

        llm_json = '{"error_found": false, "suggestion": "Kein Fehler gefunden."}'
        mock_llm = _make_mock_llm(llm_json)

        with patch.object(debug_module, "get_llm", return_value=mock_llm):
            result = debug_module.debug_code_tool.invoke({"code": "x = 1"})

        assert isinstance(result, dict)
        assert "error_found" in result
        assert "suggestion" in result

    def test_debug_tool_error_found_true(self):
        """When the LLM reports an error, error_found must be True and suggestion non-empty."""
        import agent.tools.debug_tool as debug_module

        llm_json = '{"error_found": true, "suggestion": "Fehlender Doppelpunkt nach for-Schleife."}'
        mock_llm = _make_mock_llm(llm_json)

        with patch.object(debug_module, "get_llm", return_value=mock_llm):
            result = debug_module.debug_code_tool.invoke(
                {"code": "for i in range(5)\n    print(i)"}
            )

        assert result["error_found"] is True
        assert result["suggestion"] == "Fehlender Doppelpunkt nach for-Schleife."


# ---------------------------------------------------------------------------
# _parse_debug_response — pure function, no mocking required
# ---------------------------------------------------------------------------


class TestParseDebugResponse:
    def _parse(self, content: str) -> dict:
        from agent.tools.debug_tool import _parse_debug_response

        return _parse_debug_response(content)

    def test_parse_clean_json(self):
        """Clean JSON string is parsed directly into the expected dict."""
        result = self._parse('{"error_found": true, "suggestion": "test"}')

        assert result == {"error_found": True, "suggestion": "test"}

    def test_parse_fenced_json(self):
        """JSON wrapped in ```json ... ``` markdown fences is parsed correctly."""
        fenced = "```json\n{\"error_found\": false, \"suggestion\": \"ok\"}\n```"

        result = self._parse(fenced)

        assert result == {"error_found": False, "suggestion": "ok"}

    def test_parse_fenced_json_with_braces_in_suggestion(self):
        """Braces inside the suggestion value must not confuse the fence-stripping logic."""
        fenced = '```json\n{"error_found": true, "suggestion": "Fehler {liegt hier}"}\n```'

        result = self._parse(fenced)

        assert result == {"error_found": True, "suggestion": "Fehler {liegt hier}"}

    def test_parse_fallback_on_garbage(self):
        """Completely unparseable LLM output must fall back to the safe default dict."""
        result = self._parse("komplett unleserlich!!")

        assert result == {"error_found": False, "suggestion": "Analyse nicht möglich."}

    @pytest.mark.parametrize(
        "content",
        [
            '{"error_found": false, "suggestion": "alles ok"}',
            "```\n{\"error_found\": false, \"suggestion\": \"alles ok\"}\n```",
            "```json\n{\"error_found\": false, \"suggestion\": \"alles ok\"}\n```",
        ],
        ids=["clean", "generic-fence", "json-fence"],
    )
    def test_parse_various_fence_styles(self, content: str):
        """Both plain and json-labelled code fences are stripped successfully."""
        result = self._parse(content)

        assert result["error_found"] is False
        assert result["suggestion"] == "alles ok"
