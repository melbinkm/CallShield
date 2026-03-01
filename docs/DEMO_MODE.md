# CallShield — Demo Mode

## What Is Demo Mode?

Demo mode lets you run and explore CallShield **without a Mistral API key**. Instead of calling the real Voxtral/Mistral models, the backend returns pre-built canned responses from `demo/expected_outputs/`.

No API costs. No network calls to Mistral. Perfect for local development, CI, and testing the UI flow.

---

## How It's Triggered

Demo mode activates automatically in `backend/config.py` when no API key is found:

```python
DEMO_MODE = False
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    # Try reading from .secrets/mistral_api_key
    try:
        with open(secrets_path, "r") as f:
            MISTRAL_API_KEY = f.read().strip()
    except FileNotFoundError:
        DEMO_MODE = True          # ← activates here
        MISTRAL_API_KEY = "demo"

if MISTRAL_API_KEY == "demo":
    DEMO_MODE = True              # ← or here
```

---

## How to Force Demo Mode On/Off

**Force ON** — remove or omit `MISTRAL_API_KEY` from `backend/.env`:
```bash
# backend/.env
# MISTRAL_API_KEY=   ← commented out or deleted
```

**Force ON explicitly** — set the key to the literal string `"demo"`:
```bash
# backend/.env
MISTRAL_API_KEY=demo
```

**Force OFF** — set a real API key:
```bash
# backend/.env
MISTRAL_API_KEY=your_real_mistral_api_key_here
```

---

## Endpoint Behavior in Demo Mode

### GET /api/health

Returns `"demo_mode": true` so clients can display a banner.

```json
{
  "status": "ok",
  "model": "voxtral-mini-latest",
  "version": "1.0.0",
  "demo_mode": true
}
```

---

### POST /api/analyze/transcript

Input validation (empty transcript, 10,000-character limit) still runs **before** the demo short-circuit. After validation, the transcript is matched against keywords to pick a canned response:

| Keywords matched (any) | Response file |
|------------------------|---------------|
| `irs`, `tax`, `arrest` | `irs_scam.json` |
| `medicare`, `benefits`, `press 1` | `medicare_robocall.json` |
| `amazon`, `suspicious`, `charge` | `amazon_scam_robocall.json` |
| `warranty`, `vehicle`, `car` | `warranty_robocall.json` |
| `social security`, `ssn` | `ssn_fraud_robocall.json` |
| *(no match)* | `safe_call.json` |

Simulated delay: **1.0 second** (mimics real model latency).

Each response gets a fresh UUID and randomized `processing_time_ms` (800–3000ms).

---

### POST /api/analyze/audio

File validation (`.wav` extension, 25MB limit, RIFF/WAVE magic bytes) still runs **before** the demo short-circuit. After validation, one of the following canned responses is returned at random:

- `ssn_fraud_robocall.json`
- `legal_threat_robocall.json`
- `amazon_scam_robocall.json`
- `warranty_robocall.json`
- `medicare_robocall_audio.json`

Simulated delay: **1.5 seconds**.

---

### WS /ws/stream

Returns 4 escalating `partial_result` chunks (one per binary audio frame received), then a `final_result` on `end_stream`. Each chunk has a 0.5s simulated delay.

**Partial results (chunks 0–3):**

| Chunk | `scam_score` | `cumulative_score` | New signal added |
|-------|--------------|---------------------|-----------------|
| 0 | 0.15 | 0.15 | *(none)* |
| 1 | 0.45 | 0.30 | `AUTHORITY_IMPERSONATION` (medium) |
| 2 | 0.75 | 0.50 | + `URGENCY_TACTICS` (high) |
| 3 | 0.90 | 0.65 | + `UNUSUAL_PAYMENT` (high) |

**Final result** (after `end_stream`):

```json
{
  "type": "final_result",
  "combined_score": 0.65,
  "verdict": "LIKELY_SCAM",
  "total_chunks": 4,
  "max_score": 0.90,
  "signals": [
    {"category": "AUTHORITY_IMPERSONATION", "detail": "Caller claims to represent a government agency", "severity": "medium"},
    {"category": "URGENCY_TACTICS", "detail": "Threatens immediate action if you don't comply", "severity": "high"},
    {"category": "UNUSUAL_PAYMENT", "detail": "Requests payment via gift cards", "severity": "high"}
  ],
  "recommendation": "Hang up immediately. Do not provide personal information or make any payments. Report this call to the FTC."
}
```

---

## Where Canned Data Lives

| Location | Contents |
|----------|----------|
| `demo/expected_outputs/*.json` | Pre-built `ScamReport` responses for each scenario |
| `backend/services/demo_responses.py` | Keyword matching, random audio pick, stream chunk logic |

The JSON files are loaded once at startup (`_RESPONSES` dict). `_TRANSCRIPT_KEYWORDS` maps keyword lists to file keys. `_AUDIO_KEYS` lists the 5 audio-mode files used for random selection.
