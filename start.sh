#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ollama starten falls nicht läuft
if ! pgrep -x ollama > /dev/null; then
  echo "Starte Ollama..."
  ollama serve &
  OLLAMA_PID=$!
  echo "Ollama gestartet (PID $OLLAMA_PID)"
  sleep 2
else
  echo "Ollama läuft bereits"
  OLLAMA_PID=""
fi

# Backend starten
cd "$SCRIPT_DIR/backend"

if [ ! -f "venv/bin/activate" ]; then
  echo "Erstelle venv..."
  rm -rf venv
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt -q
else
  source venv/bin/activate
  pip install -r requirements.txt -q --quiet 2>/dev/null
fi

uvicorn main:app --reload &
BACKEND_PID=$!
echo "Backend gestartet (PID $BACKEND_PID) → http://localhost:8000"

# Frontend starten
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "Frontend gestartet (PID $FRONTEND_PID) → http://localhost:3000"

echo ""
echo "Alles läuft. Ctrl+C zum Beenden."

cleanup() {
  echo ""
  echo "Beende alle Prozesse..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  if [ -n "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID 2>/dev/null
  fi
  exit
}

trap cleanup INT TERM EXIT

wait
