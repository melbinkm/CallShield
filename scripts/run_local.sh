#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "Shutting down..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    wait 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# Check for API key
if [ -z "${MISTRAL_API_KEY:-}" ]; then
    if [ -f "$ROOT_DIR/.secrets/mistral_api_key" ]; then
        export MISTRAL_API_KEY="$(cat "$ROOT_DIR/.secrets/mistral_api_key")"
        echo "Loaded API key from .secrets/mistral_api_key"
    elif [ -f "$ROOT_DIR/backend/.env" ]; then
        echo "Using backend/.env for API key"
    else
        echo "ERROR: MISTRAL_API_KEY not set."
        echo "  Option 1: export MISTRAL_API_KEY=your-key"
        echo "  Option 2: cp backend/.env.example backend/.env and edit it"
        echo "  Option 3: echo your-key > .secrets/mistral_api_key"
        exit 1
    fi
fi

echo "Starting CallShield locally..."

# Backend
echo "Starting backend on :8000..."
cd "$ROOT_DIR/backend"
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi
pip install -q -r requirements.txt 2>/dev/null
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd "$ROOT_DIR"

# Wait for backend
echo "Waiting for backend..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "Backend ready."
        break
    fi
    sleep 1
done

# Frontend
echo "Starting frontend on :5173..."
cd "$ROOT_DIR/frontend"
npm install --silent 2>/dev/null
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

echo ""
echo "CallShield is running!"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  Health:   http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop."

wait
