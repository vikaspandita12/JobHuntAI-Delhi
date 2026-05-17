#!/usr/bin/env bash
# One-time setup — run this once before starting the app
set -e

echo "==> JobHuntAI Delhi — Setup"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "==> Creating Python virtual environment..."
  python3 -m venv .venv
fi

# Activate and install
source .venv/bin/activate
echo "==> Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Create .env from example if not present
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "==> .env file created. Please fill in your keys:"
  echo "    ANTHROPIC_API_KEY  — for cover letter generation"
  echo "    SMTP_USER / SMTP_PASS  — Gmail + App Password for daily emails"
  echo ""
fi

mkdir -p data

echo "==> Setup complete! Run: bash start.sh"
