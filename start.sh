#!/usr/bin/env bash
# Start JobHuntAI Delhi — runs on http://localhost:8000
set -e

# Activate virtual environment
if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo "Run setup first: bash setup.sh"
  exit 1
fi

# Load .env
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "==> Starting JobHuntAI Delhi on http://localhost:8000"
echo "==> Dashboard: http://localhost:8000"
echo "==> API docs:  http://localhost:8000/docs"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
