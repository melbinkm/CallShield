# CallShield Frontend

React 19 + TypeScript + Vite frontend for the CallShield real-time phone scam detector.

## Development

```bash
npm install
cp .env.example .env   # set VITE_API_URL if backend runs on a different port
npm run dev            # http://localhost:5173
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend base URL |
| `VITE_API_KEY` | _(empty)_ | API key — leave empty when backend auth is disabled |

## Build

```bash
npm run build   # output → dist/
npm run preview # serve the production build locally
```

## Key Source Files

| Path | Purpose |
|---|---|
| `src/App.tsx` | Root component, tab routing, recording state |
| `src/api/client.ts` | REST + WebSocket helpers, auth headers |
| `src/hooks/useStream.ts` | Live audio streaming via WebSocket + AudioWorklet |
| `src/components/InputPanel/` | Transcript paste and mic-record tabs |
| `src/components/AnalysisPanel/` | Score gauge, verdict badge, signals list |
| `public/pcm-processor.js` | AudioWorklet processor — PCM → WAV chunks |

## Lint & Type-check

```bash
npm run lint
npx tsc --noEmit
```
