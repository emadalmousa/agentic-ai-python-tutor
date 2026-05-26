"""
Integration tests: tutor_agent orchestrator, service wiring, and FastAPI endpoint.

Validates:
- run_analysis returns a dict with the correct keys and values from agent output
- ServiceUnavailableError is raised on connection/timeout errors
- Other exceptions (e.g. ValueError) are not wrapped as ServiceUnavailableError
- explain_code delegates to run_analysis and returns the explanation string
- debug_code delegates to run_analysis and returns a (bool, str) tuple
- POST /tutor/analyze returns 200 with all TutorResponse fields
- POST /tutor/analyze returns 503 when ServiceUnavailableError is raised

No running LLM instance is required — all LLM/agent calls are mocked.

Mocking strategy
----------------
run_analysis delegates to a LangGraph agent created with create_agent().
We mock the agent at the create_agent boundary: monkeypatch replaces
agent.tutor_agent.create_agent with a factory that returns a mock graph
whose .invoke() returns a pre-formatted output message.

For service-layer and endpoint tests, run_analysis itself is patched at
the module level (services.code_explainer.run_analysis and
services.debugger.run_analysis), which is independent of the agent internals.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AGENT_OUTPUT_TEMPLATE = """\
Erklärung: {explanation}
Fehler gefunden: {error_found_str}
Fehlertyp: {error_type}
Verbesserungsvorschlag: {suggestion}
Nächste Übung: {next_exercise}
"""


def _make_agent_output(
    explanation: str = "Erklärung des Codes.",
    error_found: bool = False,
    error_type: str = "Kein Fehler",
    suggestion: str = "Kein Fehler gefunden.",
    next_exercise: str = "🎯 Aufgabe: Schreibe eine Schleife.",
) -> str:
    return _AGENT_OUTPUT_TEMPLATE.format(
        explanation=explanation,
        error_found_str="ja" if error_found else "nein",
        error_type=error_type,
        suggestion=suggestion,
        next_exercise=next_exercise,
    )


def _make_mock_agent(output_text: str) -> MagicMock:
    """Return a mock that behaves like the compiled LangGraph agent."""
    ai_message = MagicMock()
    ai_message.content = output_text
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"messages": [ai_message]}
    return mock_agent


def _patch_agent(monkeypatch, output_text: str | None = None, side_effect=None) -> MagicMock:
    """Replace create_agent in tutor_agent module; returns the mock agent."""
    import agent.tutor_agent as agent_module

    if output_text is None:
        output_text = _make_agent_output()
    mock_agent = _make_mock_agent(output_text)
    if side_effect is not None:
        mock_agent.invoke.side_effect = side_effect

    mock_create = MagicMock(return_value=mock_agent)
    monkeypatch.setattr(agent_module, "create_agent", mock_create)
    return mock_agent


def _make_analysis_result(
    explanation: str = "Erklärung des Codes.",
    error_found: bool = False,
    error_type: str = "Kein Fehler",
    suggestion: str = "Kein Fehler gefunden.",
    next_exercise: str = "🎯 Aufgabe: Schreibe eine Schleife.",
) -> dict:
    return {
        "explanation": explanation,
        "error_found": error_found,
        "error_type": error_type,
        "suggestion": suggestion,
        "next_exercise": next_exercise,
    }


# ---------------------------------------------------------------------------
# tutor_agent.run_analysis
# ---------------------------------------------------------------------------


class TestRunAnalysis:
    def test_run_analysis_returns_correct_keys(self, monkeypatch):
        """run_analysis must return a dict with explanation, error_found, error_type, suggestion, next_exercise."""
        output = _make_agent_output(explanation="Eine Erklärung.", suggestion="Kein Fehler.")
        _patch_agent(monkeypatch, output)

        import agent.tutor_agent as agent_module
        result = agent_module.run_analysis("print('hallo')")

        assert isinstance(result, dict)
        assert "explanation" in result
        assert "error_found" in result
        assert "error_type" in result
        assert "suggestion" in result
        assert "next_exercise" in result
        assert result["explanation"] == "Eine Erklärung."
        assert result["error_found"] is False
        assert result["suggestion"] == "Kein Fehler."

    def test_run_analysis_calls_agent_once(self, monkeypatch):
        """run_analysis must invoke the agent exactly once."""
        mock_agent = _patch_agent(monkeypatch)

        import agent.tutor_agent as agent_module
        agent_module.run_analysis("print('hallo')")

        mock_agent.invoke.assert_called_once()

    def test_run_analysis_raises_service_unavailable_on_connection_error(self, monkeypatch):
        """ConnectionError from agent.invoke must be wrapped as ServiceUnavailableError."""
        import agent.tutor_agent as agent_module
        from agent.tutor_agent import ServiceUnavailableError

        _patch_agent(monkeypatch, side_effect=ConnectionError("Connection refused"))

        with pytest.raises(ServiceUnavailableError):
            agent_module.run_analysis("print('hallo')")

    def test_run_analysis_raises_service_unavailable_on_timeout(self, monkeypatch):
        """An exception whose class name contains 'timeout' must be wrapped as ServiceUnavailableError."""
        import agent.tutor_agent as agent_module
        from agent.tutor_agent import ServiceUnavailableError

        class SimulatedReadTimeout(Exception):
            """Simulates httpx.ReadTimeout — class name contains 'timeout'."""
            pass

        _patch_agent(monkeypatch, side_effect=SimulatedReadTimeout("timed out"))

        with pytest.raises(ServiceUnavailableError):
            agent_module.run_analysis("x = 1")

    def test_run_analysis_reraises_other_exceptions(self, monkeypatch):
        """A ValueError raised by the agent must not be wrapped as ServiceUnavailableError."""
        import agent.tutor_agent as agent_module
        from agent.tutor_agent import ServiceUnavailableError

        _patch_agent(monkeypatch, side_effect=ValueError("unexpected value"))

        with pytest.raises(ValueError):
            agent_module.run_analysis("bad_input")

        _patch_agent(monkeypatch, side_effect=ValueError("x"))
        try:
            agent_module.run_analysis("code")
        except ServiceUnavailableError:
            pytest.fail("ValueError must not be re-raised as ServiceUnavailableError")
        except ValueError:
            pass  # expected


# ---------------------------------------------------------------------------
# Service wiring — mock run_analysis
# ---------------------------------------------------------------------------


class TestServiceWiring:
    def test_explain_code_delegates_to_run_analysis(self, monkeypatch):
        """explain_code(code) must call run_analysis(code) and return explanation."""
        import services.code_explainer as explainer_module

        fake_result = _make_analysis_result(explanation="Delegierte Erklärung.")
        mock_run = MagicMock(return_value=fake_result)
        monkeypatch.setattr(explainer_module, "run_analysis", mock_run)

        result = explainer_module.explain_code("print('test')")

        mock_run.assert_called_once_with("print('test')")
        assert result == "Delegierte Erklärung."

    def test_debug_code_returns_tuple(self, monkeypatch):
        """debug_code(code) must return a (bool, str) tuple extracted from run_analysis result."""
        import services.debugger as debugger_module

        fake_result = _make_analysis_result(error_found=True, suggestion="Fehlender Doppelpunkt.")
        mock_run = MagicMock(return_value=fake_result)
        monkeypatch.setattr(debugger_module, "run_analysis", mock_run)

        error_found, suggestion = debugger_module.debug_code("for i in range(5)\n    print(i)")

        mock_run.assert_called_once_with("for i in range(5)\n    print(i)")
        assert isinstance(error_found, bool)
        assert isinstance(suggestion, str)
        assert error_found is True
        assert suggestion == "Fehlender Doppelpunkt."


# ---------------------------------------------------------------------------
# FastAPI endpoint — TestClient with mocked agent
# ---------------------------------------------------------------------------


class TestAnalyzeEndpoint:
    def _get_client(self, monkeypatch, **kwargs) -> tuple:
        output = _make_agent_output(**kwargs)
        mock_agent = _patch_agent(monkeypatch, output)
        from main import app
        return TestClient(app), mock_agent

    def test_analyze_endpoint_returns_200(self, monkeypatch):
        """POST /tutor/analyze with valid code returns 200 and all TutorResponse fields."""
        client, _ = self._get_client(monkeypatch, explanation="Der Code gibt 'hi' aus.")

        response = client.post("/tutor/analyze", json={"code": "print('hi')"})

        assert response.status_code == 200
        body = response.json()
        assert "explanation" in body
        assert "error_found" in body
        assert "suggestion" in body
        assert "next_exercise" in body

    def test_analyze_endpoint_returns_503_when_llm_down(self, monkeypatch):
        """When a connection error is raised, the endpoint must return HTTP 503."""
        import agent.tutor_agent as agent_module

        _patch_agent(monkeypatch, side_effect=ConnectionError("Connection refused"))

        from main import app
        client = TestClient(app)
        response = client.post("/tutor/analyze", json={"code": "print('hi')"})

        assert response.status_code == 503
        body = response.json()
        assert "detail" in body
