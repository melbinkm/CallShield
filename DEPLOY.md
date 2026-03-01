# CallShield — Deployment Guide

## 1. Docker Compose (Local Development)

The fastest way to run everything:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — add your MISTRAL_API_KEY
make dev
```

This builds and starts both containers:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173

To stop: `Ctrl+C` then `make clean` to remove containers.

---

## 2. Docker Compose (Production)

For production, set the real backend URL so the frontend can reach it:

```bash
# In frontend/.env or docker-compose.yml environment
VITE_API_URL=https://your-domain.com

# In backend/.env
MISTRAL_API_KEY=your-production-key
```

Build and start:
```bash
docker compose up --build -d
```

The frontend container serves via nginx on port 80. Place a reverse proxy (Caddy, nginx, Traefik) in front for TLS.

---

## 3. Render (One-Click Cloud)

CallShield includes a `render.yaml` Blueprint for [Render](https://render.com):

1. Fork the repository to your GitHub account
2. Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
3. Connect your forked repo
4. Render reads `render.yaml` and creates:
   - **Backend** web service (Python, port 8000)
   - **Frontend** static site (built with Vite)
5. Set the environment variable in the Render dashboard:
   - `MISTRAL_API_KEY` → your Mistral API key
6. Set `VITE_API_URL` to the backend service URL Render assigns

Render auto-deploys on every push to `main`.

---

## 4. Manual Deployment

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your MISTRAL_API_KEY

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

For production, use a process manager like `systemd` or `supervisord`.

### Frontend

```bash
cd frontend
npm install
VITE_API_URL=https://your-backend-url npm run build
```

The `dist/` directory contains static files. Serve with any static host:
- nginx, Caddy, Apache
- Netlify, Vercel, Cloudflare Pages
- S3 + CloudFront

Example nginx config is provided in `frontend/nginx.conf`.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISTRAL_API_KEY` | **Yes** | — | Your Mistral AI API key |
| `VITE_API_URL` | No | `http://localhost:8000` | Backend URL for the frontend to call |

---

## Health Check

After deployment, verify the backend is running:

```bash
curl https://your-domain.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "models": {
    "audio": "voxtral-mini-latest",
    "text": "mistral-large-latest"
  }
}
```
