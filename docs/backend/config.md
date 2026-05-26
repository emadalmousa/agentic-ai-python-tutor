# agent/config.py

**Pfad:** `backend/agent/config.py`
**Zweck:** Einzige Stelle im Code wo der LLM-Provider gewählt wird. Alle Tools und der Agent rufen diese Funktionen auf — sie wissen selbst nicht welchen Provider sie nutzen.

## Strategie: OpenAI primär, Ollama als Fallback

Jede Funktion prüft in dieser Reihenfolge:

1. Ist `OPENAI_API_KEY` gesetzt und kein Platzhalter (`sk-...`)?
2. Ist die OpenAI-API erreichbar? (`client.models.list()`)
3. Wenn beides ja → OpenAI nutzen
4. Sonst → Ollama-Fallback

## Funktionen

### `get_llm()`

```python
def get_llm() -> ChatOpenAI | ChatOllama
```

Gibt das Haupt-LLM zurück. Wird von allen drei Analyse-Tools (`explain_tool`, `debug_tool`, `exercise_tool`) und vom Chat-Endpunkt aufgerufen.

| Provider | Modell | Bedingung |
|----------|--------|-----------|
| OpenAI | `gpt-4o` (oder `LLM_MODEL` aus `.env`) | `OPENAI_API_KEY` gültig und API erreichbar |
| Ollama | `llama3.2` (oder `OLLAMA_MODEL`) | Fallback wenn OpenAI nicht verfügbar |

Beide Varianten werden mit `temperature=0` erstellt (deterministische Ausgabe).

---

### `get_classifier_llm()`

```python
def get_classifier_llm() -> ChatOpenAI | ChatOllama
```

Gibt ein günstiges/schnelles Modell für Ja/Nein-Klassifikation zurück. Wird vom Off-Topic-Filter im Chat-Endpunkt genutzt.

| Provider | Modell | Bedingung |
|----------|--------|-----------|
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` gültig (ca. 15× günstiger als gpt-4o) |
| Ollama | `llama3.2` | Fallback |

---

### `get_embeddings()`

```python
def get_embeddings() -> OpenAIEmbeddings | OllamaEmbeddings
```

Gibt ein Embedding-Modell zurück. Wird ausschließlich von `agent/rag/vectorstore.py` aufgerufen, um Text-Chunks und Suchanfragen in Vektoren umzuwandeln.

| Provider | Modell | Bedingung |
|----------|--------|-----------|
| OpenAI | `text-embedding-ada-002` (Standard) | `OPENAI_API_KEY` gültig |
| Ollama | `llama3.2` | Fallback |

## Umgebungsvariablen

| Variable | Default | Wirkung |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Wenn gesetzt und gültig: OpenAI-Pfad aktiv |
| `LLM_MODEL` | `gpt-4o` | OpenAI-Modell für `get_llm()` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama-Server-URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama-Modell für alle drei Funktionen |

## Warum dieser Aufbau?

Ein einzelner Aufruf wie `get_llm()` in jedem Tool bedeutet: der Provider kann jederzeit gewechselt werden ohne eine einzige Tool-Datei zu ändern. Die `.env`-Datei ist die einzige Schaltstelle.
