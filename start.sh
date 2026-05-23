#!/bin/bash

# Start Ollama before backend and frontend
# Check if Ollama is already running
if ! pgrep -x ollama > /dev/null; then
  echo "Starte Ollama..."
  ollama serve &
  OLLAMA_PID=$!
  echo "Ollama gestartet (PID $OLLAMA_PID)"
  # Give Ollama time to start and listen on port 11434
  sleep 2
else
  echo "Ollama läuft bereits"
  OLLAMA_PID=""
fi

# Backend starten
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
  echo "Erstelle venv..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt -q
else
  source venv/bin/activate
fi

uvicorn main:app --reload &
BACKEND_PID=$!
echo "Backend gestartet (PID $BACKEND_PID) → http://127.0.0.1:8000"

# Frontend starten
cd "$(dirname "$0")/../frontend"
npm run dev &
FRONTEND_PID=$!
echo "Frontend gestartet (PID $FRONTEND_PID) → http://localhost:3000"

# Alle Prozesse stoppen wenn Ctrl+C gedrückt wird
cleanup() {
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  if [ -n "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID 2>/dev/null
  fi
  exit
}

trap cleanup INT TERM EXIT

wait
