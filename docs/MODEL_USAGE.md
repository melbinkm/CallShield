# CallShield -- Model Usage Guide

How CallShield uses Mistral AI models for real-time phone scam detection.

---

## 1. Models Overview

| | Voxtral Mini | Mistral Large |
|---|---|---|
| **Model ID** | `voxtral-mini-latest` | `mistral-large-latest` |
| **Purpose** | Native audio analysis | Text transcript analysis |
| **Input type** | Raw audio bytes (base64-encoded) | Transcript text |
| **API method** | Raw `urllib` POST to `https://api.mistral.ai/v1/chat/completions` | Mistral SDK (`mistralai` Python package) |
| **Unique detections** | Vocal stress patterns, background noise anomalies, robocall/IVR audio signatures, speech cadence irregularities, silence gaps | Semantic intent analysis, social engineering language patterns, known scam script matching, information extraction requests |

Both models return structured JSON and contribute to a combined scam score: **60% audio weight (Voxtral Mini) + 40% text weight (Mistral Large)**.

---

## 2. Voxtral Mini -- Native Audio Analysis

### When It Is Called

| Mode | Calls per interaction |
|---|---|
| **Audio upload** | 1 Voxtral call per uploaded file |
| **Streaming** | 1 Voxtral call per chunk (chunks arrive via WebSocket, max 512 KB each, max 60 chunks per session) |

### API Call Pattern

Voxtral Mini is called via a **raw `urllib` POST** request executed through `asyncio`'s thread-pool executor (`loop.run_in_executor`). This avoids SDK limitations with multimodal audio payloads.

```
POST https://api.mistral.ai/v1/chat/completions
Authorization: Bearer {MISTRAL_API_KEY}
Content-Type: application/json
```

### Parameters

| Parameter | Value |
|---|---|
| `model` | `voxtral-mini-latest` |
| `temperature` | `0.3` |
| `top_p` | `0.9` |
| `response_format` | `{"type": "json_object"}` |
| `timeout` | 120 seconds |

### Streaming Exponential Weighting

During live streaming analysis, chunk scores are combined using exponential weighting to prioritize the most recent audio while retaining context:

```
combined = 0.7 * current_chunk_score + 0.3 * previous_cumulative_score
```

This ensures the score responds quickly to new scam indicators without being thrown off by a single anomalous chunk.

### Latency Estimates

| Scenario | Expected latency |
|---|---|
| Single chunk (streaming) | 3--8 seconds |
| Full file upload (short clip) | 4--10 seconds |

### Cost Estimates

| Scenario | Approximate cost |
|---|---|
| 1 chunk (~5s of audio) | ~$0.002--$0.004 |
| 1 minute of streaming (~12 chunks) | ~$0.024--$0.048 |
| Single file upload (1 min) | ~$0.004--$0.008 |

*Costs are approximate and depend on Mistral AI pricing at time of use.*

---

## 3. Mistral Large -- Text Transcript Analysis

### When It Is Called

Mistral Large is called **once per transcript** when the user submits a text transcript via the Paste Transcript tab. It analyzes the textual content of the conversation for social engineering patterns, known scam scripts, and semantic red flags that complement the audio-level analysis from Voxtral Mini.

### API Call Pattern

Mistral Large is called via the **official Mistral SDK** (`mistralai` Python package):

```python
from mistralai import Mistral

client = Mistral(api_key=MISTRAL_API_KEY)
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[...],
    response_format={"type": "json_object"},
)
```

### Parameters

| Parameter | Value |
|---|---|
| `model` | `mistral-large-latest` |
| `response_format` | `{"type": "json_object"}` |

### Cost Estimates

| Scenario | Approximate cost |
|---|---|
| Single transcript (short call, ~1 min) | ~$0.003--$0.006 |
| Single transcript (longer call, ~5 min) | ~$0.010--$0.020 |

---

## 4. One Call vs Two Calls -- Why Native Audio Matters

A traditional scam-detection pipeline requires two separate API calls: first a speech-to-text service, then an LLM for analysis. Voxtral Mini collapses this into a single call with native audio understanding.

| | Traditional STT + LLM Pipeline | Voxtral Native Audio (CallShield) |
|---|---|---|
| **API calls required** | 2 (STT service + LLM) | 1 (Voxtral Mini) |
| **Audio signal** | Vocal cues **lost** after transcription | Full audio signal **preserved** and analyzed |
| **Detectable signals** | Text semantics only | Text semantics + vocal stress, pace, background noise, robocall audio signatures |
| **Typical latency** | ~5--8 seconds (STT latency + LLM latency) | ~2--4 seconds (single model inference) |
| **Pipeline complexity** | Higher -- must orchestrate two services, handle intermediate transcript format | Lower -- single request, single response |
| **Cost** | Two billable API calls | One billable API call |
| **Failure modes** | Transcription errors cascade into incorrect analysis | No transcription step to introduce errors |

The native audio approach is strictly superior for scam detection because vocal patterns (urgency in tone, robotic cadence, background call-center noise) are first-class signals rather than artifacts lost in transcription.

---

## 5. Prompt Engineering Techniques

CallShield uses seven specific prompt engineering techniques to maximize detection accuracy while minimizing false positives.

### 5.1 Anti-False-Positive Preamble

Every prompt begins with an explicit instruction to avoid over-flagging legitimate calls:

> "You are a phone scam detection expert. Be precise and conservative in your assessments. Legitimate calls from banks, doctors, family members, and businesses are common -- do NOT flag normal conversations as scams. Only raise the scam score when concrete indicators are present."

This preamble significantly reduces false positives on benign calls such as appointment reminders, family check-ins, and routine business calls.

### 5.2 Seven-Dimension Scoring Framework

The model scores each call across seven independent dimensions, each on a 0.0--1.0 scale:

| Dimension | What it measures |
|---|---|
| **Urgency** | Artificial time pressure ("act now", "limited time", "your account will be closed") |
| **Authority Impersonation** | Claims to be IRS, police, bank, government, tech support |
| **Information Extraction** | Requests for SSN, credit card, bank account, passwords, PINs |
| **Emotional Manipulation** | Fear, guilt, excitement, or romantic manipulation tactics |
| **Vocal Patterns** | Robotic speech, pre-recorded audio, unnatural cadence, call-center background noise |
| **Known Scam Scripts** | Matches to known scam templates (IRS, tech support, grandparent, romance, lottery) |
| **Robocall/IVR** | Automated phone tree systems, "press 1" prompts, pre-recorded menu-driven flows |

The seven dimension scores are aggregated into a single overall scam score.

### 5.3 Scoring Calibration Guidelines

The prompt includes explicit calibration ranges so the model produces consistent, interpretable scores:

| Score range | Classification | Description |
|---|---|---|
| **0.0 -- 0.2** | Normal | Routine conversation with no suspicious indicators |
| **0.2 -- 0.4** | Minor suspicious elements | One or two mild indicators that could be coincidental |
| **0.4 -- 0.6** | Concerning | Multiple indicators present; warrants caution |
| **0.6 -- 0.8** | Strong scam indicators | Clear pattern of manipulation or impersonation |
| **0.8 -- 1.0** | Clear scam | Textbook scam with multiple strong indicators |

### 5.4 Severity Definitions

Each analysis returns a severity level tied to the overall score:

| Severity | Triggered when | User-facing meaning |
|---|---|---|
| **low** | Score < 0.4 | Call appears normal or has only minor oddities |
| **medium** | Score 0.4 -- 0.7 | Caution advised; some scam indicators detected |
| **high** | Score > 0.7 | Likely scam; user should consider ending the call |

### 5.5 Silence Handling

Audio chunks that are effectively silent are detected before being sent to Voxtral Mini:

- **RMS threshold**: An RMS amplitude value below **500** classifies the chunk as silence.
- Silent chunks are **skipped** rather than sent to the model, saving cost and avoiding meaningless analysis.
- This prevents dead air or hold music from being misinterpreted as suspicious.

### 5.6 Few-Shot Calibration Examples

The prompt includes three calibration examples so the model understands the expected scoring scale:

| Example scenario | Expected score | Rationale |
|---|---|---|
| **IRS impersonation scam** -- "This is the IRS. You owe back taxes and a warrant has been issued for your arrest. Press 1 to speak to an agent immediately." | **0.95** | Authority impersonation (IRS) + urgency (arrest warrant) + known scam script + robocall/IVR pattern |
| **Love letter from a partner** -- "Hey babe, just wanted to say I love you and I hope you have a great day at work. Call me tonight!" | **0.0** | No scam indicators whatsoever; entirely normal personal call |
| **Medicare robocall** -- "Hello, this is an important message about your Medicare benefits. Your coverage may be changing. Press 1 to speak with a benefits coordinator." | **0.75** | Authority impersonation (Medicare) + robocall/IVR pattern + known scam script, but lower urgency than the IRS example |

### 5.7 Structured JSON Output Format

Both models are required to return responses in a strict JSON schema via the `json_object` response format. This ensures deterministic parsing and consistent downstream processing:

```json
{
  "scam_score": 0.72,
  "severity": "high",
  "confidence": 0.85,
  "indicators": [
    "Authority impersonation: caller claims to be from the IRS",
    "Urgency: threatens immediate arrest",
    "Information extraction: requests Social Security number"
  ],
  "recommendation": "This call shows strong indicators of a scam. Do not provide personal information.",
  "dimensions": {
    "urgency": 0.9,
    "authority_impersonation": 0.95,
    "information_extraction": 0.8,
    "emotional_manipulation": 0.6,
    "vocal_patterns": 0.5,
    "known_scam_scripts": 0.9,
    "robocall_ivr": 0.3
  }
}
```

---

## 6. Token Usage Summary

Estimated token consumption per operation:

| Operation | Approximate tokens |
|---|---|
| Audio upload (single file) | ~2,400 tokens |
| Stream chunk (single) | ~2,000 tokens |
| 1-minute stream (~12 chunks) | ~25,000 tokens |
| Transcript analysis (Mistral Large) | ~1,500 tokens |

**Typical full analysis** (1-minute streaming call with transcript):
~25,000 tokens (Voxtral streaming) + ~1,500 tokens (Mistral Large transcript) = **~26,500 tokens total**.

---

## Summary

CallShield combines two Mistral AI models to provide layered scam detection:

1. **Voxtral Mini** analyzes raw audio natively -- capturing vocal cues, robocall signatures, and speech patterns that would be lost in transcription.
2. **Mistral Large** analyzes the text transcript -- catching semantic manipulation, known scam scripts, and social engineering language.
3. The two scores are combined with **60/40 audio/text weighting** to produce a final verdict that is more accurate than either model alone.
