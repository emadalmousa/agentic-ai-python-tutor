# tests/

**Pfad:** `backend/tests/`
**Zweck:** Automatisierte Tests für die gesamte Backend-Logik. Kein laufendes LLM erforderlich — alle LLM-Aufrufe werden gemockt.

## Ausführen

```bash
cd backend
python3 -m pytest tests/ -v
```

Erwartetes Ergebnis: **32 Tests, alle grün.**

## conftest.py

Stellt sicher dass `import agent` und `import services` funktionieren, egal von welchem Verzeichnis pytest gestartet wird. Fügt das Backend-Root und die venv-Site-Packages in `sys.path` ein.

---

## test_config.py

Testet `get_llm()` aus `agent/config.py`.

**Klasse `TestPackageImports`**
- Prüft dass `agent`, `agent.tools` und `agent.config` importierbar sind

**Klasse `TestGetLlmOpenAI`**
- `test_get_llm_returns_openai_when_key_valid` — Mock: `openai.OpenAI` gibt gültige Client-Instanz zurück → `get_llm()` gibt `ChatOpenAI` zurück
- `test_get_llm_uses_llm_model_env` — `LLM_MODEL=gpt-4-turbo` in Umgebung → `llm.model_name == "gpt-4-turbo"`

**Klasse `TestGetLlmOllamaFallback`**
- `test_get_llm_falls_back_to_ollama_when_no_key` — kein `OPENAI_API_KEY` → `ChatOllama`
- `test_get_llm_falls_back_to_ollama_when_key_is_placeholder` — `OPENAI_API_KEY=sk-...` → `ChatOllama`
- `test_get_llm_uses_ollama_model_env` — `OLLAMA_MODEL=llama3.1` → `llm.model == "llama3.1"`
- `test_get_llm_uses_ollama_base_url_env` — `OLLAMA_BASE_URL=http://remote:11434` → `llm.base_url == "http://remote:11434"`
- `test_get_llm_default_ollama_model` — kein `OLLAMA_MODEL` gesetzt → Default `"llama3.2"`

---

## test_tools.py

Testet `explain_code_tool` und `debug_code_tool` aus `agent/tools/`.

**Klasse `TestExplainCodeTool`**
- `test_explain_tool_returns_string` — Mock-LLM → `invoke()` gibt String zurück
- `test_explain_tool_invokes_llm_once` — LLM wird genau einmal aufgerufen
- `test_explain_tool_includes_code_in_human_message` — Code erscheint in der HumanMessage
- `test_explain_tool_uses_get_llm` — `get_llm` aus `agent.config` wird aufgerufen

**Klasse `TestDebugCodeTool`**
- `test_debug_tool_returns_dict` — Tool gibt Dict zurück (nicht String)
- `test_debug_tool_error_found_true` — bei Fehler-JSON: `error_found == True`

**Klasse `TestParseDebugResponse`**
- `test_parse_clean_json` — sauberes JSON wird direkt geparsed
- `test_parse_fenced_json` — ` ```json ... ``` ` wird korrekt entfernt
- `test_parse_fenced_json_with_braces_in_suggestion` — geschweifte Klammern im suggestion-Text führen nicht zu Fehlern
- `test_parse_fallback_on_garbage` — bei ungültigem JSON: Safe-Default-Dict
- `test_parse_various_fence_styles` — parametrisiert: clean / generic-fence / json-fence

---

## test_integration.py

Testet `run_analysis()`, Service-Wiring und den FastAPI-Endpunkt.

**Mock-Strategie:** `create_agent` aus `agent.tutor_agent` wird durch eine Factory ersetzt die einen Mock-Agenten zurückgibt. Der Mock-Agent gibt einen vorformulierten Text im erwarteten Format zurück. Dadurch wird `_parse_agent_output()` mitgetestet.

**Klasse `TestRunAnalysis`**
- `test_run_analysis_returns_correct_keys` — alle 5 Schlüssel im Ergebnis-Dict
- `test_run_analysis_calls_agent_once` — Agent wird genau einmal aufgerufen
- `test_run_analysis_raises_service_unavailable_on_connection_error` — `ConnectionError` → `ServiceUnavailableError`
- `test_run_analysis_raises_service_unavailable_on_timeout` — Exception mit "timeout" im Klassennamen → `ServiceUnavailableError`
- `test_run_analysis_reraises_other_exceptions` — `ValueError` wird NICHT in `ServiceUnavailableError` umgewandelt

**Klasse `TestServiceWiring`**
- `test_explain_code_delegates_to_run_analysis` — `explain_code(code)` ruft `run_analysis(code)` auf und gibt `explanation` zurück
- `test_debug_code_returns_tuple` — `debug_code(code)` gibt `(bool, str)`-Tupel zurück

**Klasse `TestAnalyzeEndpoint`**
- `test_analyze_endpoint_returns_200` — valider Code → HTTP 200 mit allen TutorResponse-Feldern
- `test_analyze_endpoint_returns_503_when_llm_down` — `ConnectionError` im Agent → HTTP 503
