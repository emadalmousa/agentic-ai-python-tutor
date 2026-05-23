"""
Phase 3 integration tests: tutor_agent orchestrator, service wiring, and FastAPI endpoint.

Validates:
- run_analysis returns a dict with the correct keys and delegates to both tools
- question is forwarded to explain_code_tool.invoke
- ServiceUnavailableError is raised on connection/timeout errors
- Other exceptions (e.g. ValueError) are not wrapped as ServiceUnavailableError
- explain_code delegates to run_analysis and returns the explanation string
- debug_code delegates to run_analysis and returns a (bool, str) tuple
- POST /tutor/analyze returns 200 with all TutorResponse fields
- POST /tutor/analyze forwards question into run_analysis
- POST /tutor/analyze returns 503 when ServiceUnavailableError is raised

No running Ollama instance is required — all LLM calls are mocked.

Mocking strategy
----------------
explain_code_tool and debug_code_tool are LangChain StructuredTool (Pydantic) objects.
patch.object on their .invoke attribute fails at teardown because Pydantic's frozen model
blocks delattr.  Instead we replace the entire tool objects in the agent.tutor_agent
module namespace with MagicMock instances.  monkeypatch handles cleanup automatically.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_explain_tool(response: str = "Erklärung des Codes.") -> MagicMock:
    """Return a mock that behaves like explain_code_tool: mock.invoke({...}) -> str."""
    mock = MagicMock()
    mock.invoke.return_value = response
    return mock


def _make_mock_debug_tool(error_found: bool = False, suggestion: str = "Kein Fehler.") -> MagicMock:
    """Return a mock that behaves like debug_code_tool: mock.invoke({...}) -> dict."""
    mock = MagicMock()
    mock.invoke.return_value = {"error_found": error_found, "suggestion": suggestion}
    return mock


def _make_analysis_result(
    explanation: str = "Erklärung des Codes.",
    error_found: bool = False,
    suggestion: str = "Kein Fehler gefunden.",
) -> dict:
    """Return a minimal valid run_analysis result dict."""
    return {
        "explanation": explanation,
        "error_found": error_found,
        "suggestion": suggestion,
    }


# ---------------------------------------------------------------------------
# tutor_agent.run_analysis
# ---------------------------------------------------------------------------


class TestRunAnalysis:
    def test_run_analysis_returns_correct_keys(self, monkeypatch):
        """run_analysis must return a dict with exactly explanation, error_found, suggestion."""
        import agent.tutor_agent as agent_module

        monkeypatch.setattr(agent_module, "explain_code_tool", _make_mock_explain_tool("Eine Erklärung."))
        monkeypatch.setattr(agent_module, "debug_code_tool", _make_mock_debug_tool(False, "Kein Fehler."))

        result = agent_module.run_analysis("print('hallo')")

        assert isinstance(result, dict)
        assert set(result.keys()) == {"explanation", "error_found", "suggestion"}
        assert result["explanation"] == "Eine Erklärung."
        assert result["error_found"] is False
        assert result["suggestion"] == "Kein Fehler."

    def test_run_analysis_passes_question(self, monkeypatch):
        """run_analysis must forward the question argument to explain_code_tool.invoke."""
        import agent.tutor_agent as agent_module

        mock_explain = _make_mock_explain_tool("Antwort mit Frage.")
        monkeypatch.setattr(agent_module, "explain_code_tool", mock_explain)
        monkeypatch.setattr(agent_module, "debug_code_tool", _make_mock_debug_tool())

        agent_module.run_analysis("x = 1", question="Was macht x?")

        mock_explain.invoke.assert_called_once()
        call_input = mock_explain.invoke.call_args[0][0]  # first positional arg is the input dict
        assert call_input.get("question") == "Was macht x?"
        assert call_input.get("code") == "x = 1"

    def test_run_analysis_raises_service_unavailable_on_connection_error(self, monkeypatch):
        """ConnectionError from explain_code_tool must be wrapped as ServiceUnavailableError."""
        import agent.tutor_agent as agent_module
        from agent.tutor_agent import ServiceUnavailableError

        mock_explain = MagicMock()
        mock_explain.invoke.side_effect = ConnectionError("Connection refused")
        monkeypatch.setattr(agent_module, "explain_code_tool", mock_explain)
        monkeypatch.setattr(agent_module, "debug_code_tool", _make_mock_debug_tool())

        with pytest.raises(ServiceUnavailableError):
            agent_module.run_analysis("print('hallo')")

    def test_run_analysis_raises_service_unavailable_on_timeout(self, monkeypatch):
        """An exception whose class name contains 'timeout' must be wrapped as ServiceUnavailableError."""
        import agent.tutor_agent as agent_module
        from agent.tutor_agent import ServiceUnavailableError

        class SimulatedReadTimeout(Exception):
            """Simulates httpx.ReadTimeout — class name contains 'timeout'."""
            pass

        mock_explain = MagicMock()
        mock_explain.invoke.side_effect = SimulatedReadTimeout("timed out")
        monkeypatch.setattr(agent_module, "explain_code_tool", mock_explain)
        monkeypatch.setattr(agent_module, "debug_code_tool", _make_mock_debug_tool())

        with pytest.raises(ServiceUnavailableError):
            agent_module.run_analysis("x = 1")

    def test_run_analysis_reraises_other_exceptions(self, monkeypatch):
        """A ValueError raised by a tool must not be wrapped as ServiceUnavailableError."""
        import agent.tutor_agent as agent_module
        from agent.tutor_agent import ServiceUnavailableError

        mock_explain = MagicMock()
        mock_explain.invoke.side_effect = ValueError("unexpected value")
        monkeypatch.setattr(agent_module, "explain_code_tool", mock_explain)
        monkeypatch.setattr(agent_module, "debug_code_tool", _make_mock_debug_tool())

        with pytest.raises(ValueError):
            agent_module.run_analysis("bad_input")

        # Sanity check: same setup must NOT raise ServiceUnavailableError
        mock_explain2 = MagicMock()
        mock_explain2.invoke.side_effect = ValueError("x")
        monkeypatch.setattr(agent_module, "explain_code_tool", mock_explain2)

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
        """explain_code(code, question) must call run_analysis(code, question) and return explanation."""
        import services.code_explainer as explainer_module

        fake_result = _make_analysis_result(explanation="Delegierte Erklärung.")
        mock_run = MagicMock(return_value=fake_result)
        monkeypatch.setattr(explainer_module, "run_analysis", mock_run)

        result = explainer_module.explain_code("print('test')", "Warum print?")

        mock_run.assert_called_once_with("print('test')", "Warum print?")
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
# FastAPI endpoint — TestClient with mocked run_analysis
# ---------------------------------------------------------------------------


class TestAnalyzeEndpoint:
    def _get_client_with_mocked_tools(self, monkeypatch, explain_response: str, debug_response: dict):
        """Return a TestClient with explain and debug tools replaced by mocks."""
        import agent.tutor_agent as agent_module

        mock_explain = MagicMock()
        mock_explain.invoke.return_value = explain_response
        mock_debug = MagicMock()
        mock_debug.invoke.return_value = debug_response

        monkeypatch.setattr(agent_module, "explain_code_tool", mock_explain)
        monkeypatch.setattr(agent_module, "debug_code_tool", mock_debug)

        from main import app
        return TestClient(app), mock_explain, mock_debug

    def test_analyze_endpoint_returns_200(self, monkeypatch):
        """POST /tutor/analyze with valid code returns 200 and all TutorResponse fields."""
        client, _, _ = self._get_client_with_mocked_tools(
            monkeypatch,
            explain_response="Der Code gibt 'hi' aus.",
            debug_response={"error_found": False, "suggestion": "Kein Fehler gefunden."},
        )

        response = client.post("/tutor/analyze", json={"code": "print('hi')"})

        assert response.status_code == 200
        body = response.json()
        assert "explanation" in body
        assert "error_found" in body
        assert "suggestion" in body

    def test_analyze_endpoint_passes_question(self, monkeypatch):
        """question from the request must arrive in at least one explain_code_tool.invoke call.

        The router calls both explain_code and debug_code, each of which calls run_analysis,
        so explain_code_tool.invoke may be called twice per request.  We only care that
        the call originating from explain_code forwards the question correctly.
        """
        client, mock_explain, _ = self._get_client_with_mocked_tools(
            monkeypatch,
            explain_response="Erklärung mit Frage.",
            debug_response={"error_found": False, "suggestion": "ok"},
        )

        response = client.post(
            "/tutor/analyze",
            json={"code": "x = 42", "question": "Was ist 42?"},
        )

        assert response.status_code == 200
        assert mock_explain.invoke.call_count >= 1
        # The first invocation comes from explain_code, which forwards the question
        first_call_input = mock_explain.invoke.call_args_list[0][0][0]
        assert first_call_input.get("question") == "Was ist 42?"
        assert first_call_input.get("code") == "x = 42"

    def test_analyze_endpoint_returns_503_when_ollama_down(self, monkeypatch):
        """When a connection error is raised, the endpoint must return HTTP 503."""
        import agent.tutor_agent as agent_module

        mock_explain = MagicMock()
        mock_explain.invoke.side_effect = ConnectionError("Connection refused")
        mock_debug = MagicMock()

        monkeypatch.setattr(agent_module, "explain_code_tool", mock_explain)
        monkeypatch.setattr(agent_module, "debug_code_tool", mock_debug)

        from main import app
        client = TestClient(app)
        response = client.post("/tutor/analyze", json={"code": "print('hi')"})

        assert response.status_code == 503
        body = response.json()
        assert "detail" in body
