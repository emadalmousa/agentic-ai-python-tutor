# Backend — Übersicht

Das Backend ist eine FastAPI-Anwendung (`backend/main.py`) mit drei HTTP-Endpunkten. Die KI-Logik liegt vollständig im `agent/`-Paket; der Rest sind Routing, Schemas und kleine Service-Adapter.

## Verzeichnisstruktur

```
backend/
├── main.py                     Einstiegspunkt, CORS, Exception-Handler
├── requirements.txt            Abhängigkeiten
├── .env                        Konfiguration (OPENAI_API_KEY, OLLAMA_*)
│
├── models/
│   └── schemas.py              Pydantic-Modelle für alle Requests und Responses
│
├── agent/
│   ├── config.py               LLM-Factory (Provider-Auswahl)
│   ├── tutor_agent.py          ReAct-Agent-Orchestrator (run_analysis)
│   └── tools/
│       ├── explain_tool.py     Tool: Code erklären
│       ├── debug_tool.py       Tool: Fehler analysieren
│       └── exercise_tool.py    Tool: Übung generieren
│
├── routers/
│   └── tutor.py                Alle HTTP-Endpunkte
│
├── services/
│   ├── code_explainer.py       Thin Adapter → run_analysis (Legacy)
│   └── debugger.py             Thin Adapter → run_analysis (Legacy)
│
└── tests/
    ├── conftest.py             sys.path-Setup für pytest
    ├── test_config.py          Tests: LLM-Factory
    ├── test_tools.py           Tests: explain_tool, debug_tool
    └── test_integration.py     Tests: run_analysis, Service-Wiring, Endpoint
```

## Endpunkte

| Methode | URL | Beschreibung |
|---------|-----|--------------|
| GET | `/` | Health-Check |
| POST | `/tutor/analyze` | Code analysieren (ReAct-Agent) |
| POST | `/tutor/run` | Code direkt ausführen (subprocess, kein LLM) |
| POST | `/tutor/chat` | Chat mit History + Off-Topic-Filter |

## Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `OPENAI_API_KEY` | — | Wenn gesetzt und gültig: OpenAI wird genutzt |
| `LLM_MODEL` | `gpt-4o` | OpenAI-Modell für Analyse und Chat |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama-Server-URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama-Modell |

## Dateien im Detail

- [main.py](main.md)
- [models/schemas.py](schemas.md)
- [agent/config.py](config.md)
- [agent/tutor_agent.py](tutor_agent.md)
- [agent/tools/](tools.md)
- [routers/tutor.py](router.md)
- [services/](services.md)
- [tests/](tests.md)
