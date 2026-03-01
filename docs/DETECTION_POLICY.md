# CallShield Detection Policy

**Version:** v1.0.0
**Effective date:** 2026-03-01
**Status:** Active

---

## 1. Policy Statement

CallShield detects real-time telephone scam patterns using native audio analysis (Voxtral Mini) and optional semantic confirmation (Mistral Large). The system produces a calibrated scam score and verdict for each analysis request.

**In scope:**
- Phone-based social engineering (IVR robocalls, authority impersonation, urgency tactics)
- Financial fraud patterns (gift card demands, wire transfer requests, fake prize claims)
- Vocal and acoustic indicators (scripted delivery, TTS/robocall fingerprints, stress patterns)
- Known scam script templates (IRS impersonation, tech support fraud, grandparent scams)

**Out of scope:**
- Legal determinations of fraud — CallShield produces a probability estimate, not a legal finding
- Speaker identification or diarization — the system does not identify who is speaking
- Content moderation beyond scam patterns — hateful speech, misinformation, and other harmful content categories are not scored
- Real-time call interception — CallShield analyzes audio submitted via API; it does not tap live carrier infrastructure

---

## 2. Verdict Thresholds

Thresholds are defined in `backend/config.py` and applied in `backend/audio_analyzer.py`.

| Score Range | Verdict | Recommended Action |
|-------------|---------|-------------------|
| 0.00 – 0.29 | **SAFE** | No action required; call appears legitimate |
| 0.30 – 0.59 | **SUSPICIOUS** | Monitor call; consider alerting subscriber |
| 0.60 – 0.84 | **LIKELY_SCAM** | Warn subscriber immediately; log for review |
| 0.85 – 1.00 | **SCAM** | Block or intercept; escalate to fraud team |

> These thresholds were calibrated against the 25-scenario evaluation set documented in
> [docs/EVALUATION.md](EVALUATION.md). Operators may adjust thresholds via environment variables
> to tune sensitivity for their subscriber base.

---

## 3. Scoring Algorithm

CallShield uses a **peak-weighted composite score** to prevent a friendly call opener from diluting a later scam demand.

```
effective_score = 0.6 × peak_score + 0.4 × cumulative_avg_score
```

Where:
- `peak_score` = the highest `scam_score` across all analyzed chunks in the session
- `cumulative_avg_score` = the running mean of all chunk scores

**Rationale:** A scammer will frequently open with benign rapport-building ("Hi, how are you today?") before escalating to the demand. A purely cumulative average would under-weight this escalation. The 60/40 peak weighting ensures that the worst moment in a call dominates the final verdict.

**Score clamping:** All raw model outputs are clamped to `[0.0, 1.0]` server-side, regardless of the model's raw response. The verdict is then validated against a fixed enum (`SAFE`, `SUSPICIOUS`, `LIKELY_SCAM`, `SCAM`) to prevent prompt injection from producing unexpected output.

---

## 4. Human Review Trigger

The `review_required` flag is set to `true` and a `review_reason` string is populated when any of the following conditions are met:

| Condition | Threshold | Reason |
|-----------|-----------|--------|
| Ambiguous score band | `0.35 ≤ effective_score ≤ 0.65` | Score falls in uncertain range between SAFE and SUSPICIOUS |
| Audio/text disagreement | `\|audio_score − text_score\| > 0.3` | Voxtral and Mistral Large models disagree substantially |
| Low model confidence | `confidence < 0.55` | Model returned a low-confidence result |

When `review_required` is set, the UI displays a **"Needs Human Review"** badge alongside the verdict. In production deployments, this flag should trigger an escalation workflow (e.g., route to a fraud analyst queue, flag for supervisor listen-in, or notify the subscriber with a "we're checking this call" message).

---

## 5. Model Assignment

| Input Type | Primary Model | Secondary Model | Trigger |
|------------|---------------|----------------|---------|
| Raw audio (WAV/PCM) | Voxtral Mini (`voxtral-mini-latest`) | Mistral Large (`mistral-large-latest`) | Audio score > 0.5 |
| Text transcript | Mistral Large (`mistral-large-latest`) | — | Always (text path) |

**Voxtral Mini** performs native audio reasoning — it processes raw audio bytes without a transcription step. This preserves acoustic signals (vocal stress, robocall fingerprints, scripted delivery cadence) that would be lost after speech-to-text conversion.

**Mistral Large** is conditionally invoked as a second-opinion semantic analysis when the audio score exceeds 0.5. It receives a text summary (not verbatim transcript) and returns an independent score, which is combined with the audio score for the final verdict. On the text transcript path, Mistral Large is the sole model.

Both models are configured with:
- `temperature: 0.3` — low randomness for consistent, reproducible scores
- `response_format: json_object` — structured output guarantees; model cannot return free text

---

## 6. Changelog

| Version | Date | Summary |
|---------|------|---------|
| v1.0.0 | 2026-03-01 | Initial policy release; thresholds and algorithm documented from codebase |

---

*Policy questions or threshold adjustment requests: open a GitHub issue with the `policy` label.*
*Cross-reference: [docs/THREAT_MODEL.md](THREAT_MODEL.md) · [docs/EVALUATION.md](EVALUATION.md) · `backend/config.py`*
