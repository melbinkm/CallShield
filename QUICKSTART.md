# CallShield — Quick Start

Get CallShield running in under 2 minutes.

## Prerequisites

- **Mistral API key** — get one at [console.mistral.ai](https://console.mistral.ai/)
- **Option A** requires: Docker + Docker Compose
- **Option B** requires: Python 3.11+, Node 18+
- **Option C** requires: Python 3.11+, Node 18+ (automated setup)

---

## Option A: Docker (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/callshield.git
cd callshield
cp backend/.env.example backend/.env
# Edit backend/.env — paste your MISTRAL_API_KEY
make dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Option B: Manual

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Edit with your API key
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Option C: One-Line Setup Script

**Linux / macOS:**
```bash
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\setup.bat
```

The script checks dependencies, creates a virtual environment, installs packages, and starts both services.

---

## Try It

1. Open [http://localhost:5173](http://localhost:5173)
2. Click **"Try Sample"** — a pre-loaded IRS scam transcript is analyzed instantly
3. Or paste your own transcript, upload a WAV file, or record from your microphone

---

## Next Steps

- [README.md](README.md) — full documentation, API reference, scoring details
- [DEPLOY.md](DEPLOY.md) — production deployment guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture
