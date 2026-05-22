#!/bin/bash

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

# Beide stoppen wenn Ctrl+C gedrückt wird
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
