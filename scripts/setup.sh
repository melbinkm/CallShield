#!/usr/bin/env bash
set -euo pipefail

# CallShield — Cross-platform setup script (Linux / macOS)
# Usage: ./scripts/setup.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Dependency checks ────────────────────────────────────────────────────────

info "Checking dependencies..."

# Python 3.11+
PYTHON=""
for cmd in python3.11 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    # Fall back to any python3 if 3.11+ not found
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON="$cmd"
            warn "Found $cmd but version may be < 3.11. Recommended: Python 3.11+"
            break
        fi
    done
fi

[ -z "$PYTHON" ] && error "Python 3 not found. Install Python 3.11+ from https://python.org"
info "Using Python: $PYTHON ($($PYTHON --version 2>&1))"

# Node 18+
if ! command -v node &>/dev/null; then
    error "Node.js not found. Install Node 18+ from https://nodejs.org"
fi

NODE_VERSION=$(node --version | grep -oP '\d+' | head -1)
if [ "$NODE_VERSION" -lt 18 ]; then
    error "Node.js $NODE_VERSION found, but 18+ is required"
fi
info "Using Node: $(node --version)"

# ── Backend setup ─────────────────────────────────────────────────────────────

info "Setting up backend..."

cd "$ROOT_DIR/backend"

if [ ! -d "venv" ]; then
    info "Creating virtual environment..."
    $PYTHON -m venv venv
fi

source venv/bin/activate
info "Installing Python dependencies..."
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
    cp .env.example .env
    warn ".env created from .env.example — please add your MISTRAL_API_KEY"
    read -rp "Enter your Mistral API key (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        sed -i "s/your_mistral_api_key_here/$api_key/" .env 2>/dev/null || \
        sed -i '' "s/your_mistral_api_key_here/$api_key/" .env 2>/dev/null
        info "API key saved to .env"
    fi
fi

# ── Frontend setup ────────────────────────────────────────────────────────────

info "Setting up frontend..."

cd "$ROOT_DIR/frontend"
npm install --silent

if [ ! -f ".env" ]; then
    cp .env.example .env
    info ".env created for frontend (defaults to localhost:8000)"
fi

# ── Start services ────────────────────────────────────────────────────────────

cleanup() {
    info "Shutting down..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

info "Starting backend..."
cd "$ROOT_DIR/backend"
source venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

info "Starting frontend..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
info "========================================="
info "  CallShield is running!"
info "  Frontend: http://localhost:5173"
info "  Backend:  http://localhost:8000"
info "  API docs: http://localhost:8000/docs"
info "========================================="
info "Press Ctrl+C to stop both services"
echo ""

wait
