# CallShield API Reference

## Overview

The CallShield backend exposes a REST API and WebSocket endpoint for scam detection.

**Base URL:** `http://localhost:8000` (local) or your deployed domain

**Authentication:** API key via `X-API-Key` header (REST) or `?api_key=` query param (WebSocket). When no `api_keys.json` exists, all endpoints are open (dev mode).

---

## Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/health` | Health check + model info | None |
| `POST` | `/api/analyze/audio` | Analyze a WAV file | `X-API-Key` |
| `POST` | `/api/analyze/transcript` | Analyze a text transcript | `X-API-Key` |
| `WS` | `/ws/stream` | Stream live audio chunks | `?api_key=` |

---

## GET /api/health

Returns server status, model name, version, and whether demo mode is active.

**Response:**
```json
{
  "status": "ok",
  "model": "voxtral-mini-latest",
  "version": "1.0.0",
  "demo_mode": false
}
```

---

## POST /api/analyze/audio

Upload a WAV file for scam detection using Voxtral Mini.

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | `UploadFile` | Yes | Must be `.wav`, max 25MB |

**Headers:**
```
Content-Type: multipart/form-data
X-API-Key: cs_YOUR_KEY_HERE
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/analyze/audio \
  -H "X-API-Key: cs_YOUR_KEY_HERE" \
  -F "file=@recording.wav"
```

**Response:** `ScamReport` JSON (see [Response Format](#response-format--scamreport))

**Errors:**

| Status | `error` | Cause |
|--------|---------|-------|
| 400 | `invalid_file_type` | Not a `.wav` file or invalid WAV header |
| 400 | `file_too_large` | File exceeds 25MB |
| 502 | `model_error` | Voxtral API call failed |
| 502 | `parse_error` | Could not parse model response |

---

## POST /api/analyze/transcript

Analyze a text transcript using Mistral Large.

**Request:** `application/json`

```json
{
  "transcript": "Hello, this is the IRS. You owe $5000 in back taxes."
}
```

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `transcript` | `string` | Yes | Max 10,000 characters |

**Headers:**
```
Content-Type: application/json
X-API-Key: cs_YOUR_KEY_HERE
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/analyze/transcript \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cs_YOUR_KEY_HERE" \
  -d '{"transcript": "Hello, this is the IRS. You owe $5000 in back taxes."}'
```

**Response:** `ScamReport` JSON (see [Response Format](#response-format--scamreport))

**Errors:**

| Status | `error` | Cause |
|--------|---------|-------|
| 400 | `transcript_empty` | Transcript is blank after trimming |
| 400 | `transcript_too_long` | Transcript exceeds 10,000 characters |
| 502 | `model_error` | Mistral API call failed |
| 502 | `parse_error` | Could not parse model response |

---

## WS /ws/stream

Stream live audio chunks for real-time scam detection.

**URL:** `ws://localhost:8000/ws/stream?api_key=cs_YOUR_KEY_HERE`

### Protocol

1. **Connect** — server sends `{"type": "connected"}`
2. **Send binary WAV chunks** — max 512KB each, up to 60 chunks — server replies with `partial_result` per chunk
3. **Send** `{"type": "end_stream"}` — server replies with `final_result` then closes

### Messages (server → client)

**Connected:**
```json
{"type": "connected"}
```

**Partial result** (per audio chunk):
```json
{
  "type": "partial_result",
  "chunk_index": 2,
  "scam_score": 0.75,
  "cumulative_score": 0.50,
  "signals": [
    {"category": "AUTHORITY_IMPERSONATION", "detail": "Caller claims government agency", "severity": "medium"},
    {"category": "URGENCY_TACTICS", "detail": "Threatens immediate action", "severity": "high"}
  ],
  "recommendation": "High risk — caller using urgency tactics and authority impersonation."
}
```

**Final result** (after `end_stream`):
```json
{
  "type": "final_result",
  "combined_score": 0.65,
  "verdict": "LIKELY_SCAM",
  "total_chunks": 4,
  "max_score": 0.90,
  "signals": [...],
  "transcript_summary": "Caller impersonated a government agency, used urgency and threats, demanded gift cards.",
  "recommendation": "Hang up immediately. Do not provide personal information or make any payments."
}
```

**Error:**
```json
{"type": "error", "detail": "Invalid or missing API key."}
```

### wscat Example

```bash
wscat -c "ws://localhost:8000/ws/stream?api_key=cs_YOUR_KEY_HERE"
# Send binary audio frames, then:
# > {"type": "end_stream"}
```

---

## Response Format — ScamReport

All REST endpoints return a `ScamReport` object:

```json
{
  "id": "analysis_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "mode": "audio",
  "audio_analysis": {
    "scam_score": 0.92,
    "confidence": 0.95,
    "verdict": "SCAM",
    "signals": [
      {"category": "AUTHORITY_IMPERSONATION", "detail": "Claims to be IRS officer", "severity": "high"},
      {"category": "URGENCY_TACTICS", "detail": "Threatens arrest within 45 minutes", "severity": "high"},
      {"category": "KNOWN_SCAM_SCRIPTS", "detail": "Gift card payment demand", "severity": "high"}
    ],
    "transcript_summary": "Caller impersonates IRS, threatens arrest, demands gift cards",
    "recommendation": "Hang up immediately. The IRS never demands payment via gift cards."
  },
  "text_analysis": null,
  "combined_score": 0.92,
  "processing_time_ms": 3420.5
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique ID for this analysis |
| `mode` | `"audio"` \| `"text"` | Input type |
| `audio_analysis` | object \| null | Present for audio/stream mode |
| `text_analysis` | object \| null | Present for transcript mode |
| `combined_score` | `float` [0–1] | Final scam score |
| `processing_time_ms` | `float` | End-to-end latency in milliseconds |

### Analysis Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `scam_score` | `float` [0–1] | Raw model score |
| `confidence` | `float` [0–1] | Model confidence |
| `verdict` | `string` | `SAFE` / `SUSPICIOUS` / `LIKELY_SCAM` / `SCAM` |
| `signals` | `array` | Detected scam indicators |
| `transcript_summary` | `string` | Brief summary of call content |
| `recommendation` | `string` | User-facing action advice |

### Signal Object

```json
{"category": "URGENCY_TACTICS", "detail": "Threatens arrest", "severity": "high"}
```

| `severity` | Meaning |
|------------|---------|
| `low` | Worth noting |
| `medium` | Concerning |
| `high` | Strong scam indicator |

### Verdict Thresholds

| Score Range | Verdict |
|-------------|---------|
| 0.00 – 0.29 | `SAFE` |
| 0.30 – 0.59 | `SUSPICIOUS` |
| 0.60 – 0.84 | `LIKELY_SCAM` |
| 0.85 – 1.00 | `SCAM` |

---

## Error Response Format

All errors return JSON with this shape:

```json
{
  "error": "invalid_file_type",
  "detail": "Only WAV files are accepted."
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `POST /api/analyze/audio` | 10 requests / minute |
| `POST /api/analyze/transcript` | 20 requests / minute |
| `WS /ws/stream` | No rate limit |

---

## Developer API Key

When no `api_keys.json` exists, all endpoints are open (dev mode). To enable authentication:

```bash
cd backend
python scripts/generate_api_key.py --name "my-app"
```

This creates `api_keys.json` with a hashed key. Pass the key via:
- REST: `X-API-Key: cs_YOUR_KEY_HERE` header
- WebSocket: `?api_key=cs_YOUR_KEY_HERE` query param

---

## Interactive Documentation

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs) — click **Authorize** to set your API key
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
