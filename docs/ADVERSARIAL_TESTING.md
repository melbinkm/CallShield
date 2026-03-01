# CallShield Adversarial Testing

This document describes the adversarial test cases we used to challenge CallShield's detection logic — including deliberate attempts to trick the model with polite scammers, angry-but-innocent callers, and synthesized evasion tactics.

The goal: confirm that the audio-native Voxtral pipeline catches what text-only models miss.

---

## The Core Challenge

Text-only scam detection can be fooled by word choice. A scammer who says *"I understand your concern"* instead of *"You must pay NOW"* can drop their text-score significantly. Voxtral doesn't have this weakness — it listens to the acoustic delivery, not just the words.

We tested this systematically.

---

## Adversarial Scenario Results

### 1. The Polite IRS Agent
**Attack:** A scammer using calm, professional language — "I'd like to help you resolve this" instead of threatening arrest.
**Text-only vulnerability:** Politeness reduces urgency signal weight.
**Result:** Score **0.95 SCAM** — Voxtral detected the scripted call-center delivery cadence and IRS authority claim regardless of polite framing.

### 2. The Hedged Crypto Pitch
**Attack:** Softened language — "some people have seen returns" instead of "guaranteed profits."
**Text-only vulnerability:** Hedging removes the "too good to be true" signal.
**Result:** Score **0.80 LIKELY_SCAM** — Voxtral caught the rehearsed sales delivery pattern and financial solicitation structure.

### 3. The Angry Legitimate Customer
**Attack:** A genuinely upset customer complaining about a billing error — aggressive tone, emotional language, demand for resolution.
**Risk:** Could be misclassified due to emotional intensity and urgency.
**Result:** Score **0.10 SAFE** — No payment demand, no authority impersonation, no information extraction. Anger alone is not a scam signal.

### 4. The "Certified" Tech Support
**Attack:** Scammer claims to be from a "Microsoft Certified Partner" with a legitimate-sounding business name.
**Text-only vulnerability:** "Certified" and business-name legitimacy signals can lower suspicion.
**Result:** Score **0.90 SCAM** — Remote access request + unsolicited outbound call pattern flagged regardless of claimed credentials.

### 5. The FDIC Bank Examiner
**Attack:** Highly convincing authority impersonation of a federal banking regulator — formal language, regulation citations.
**Text-only vulnerability:** Formal institutional language can suppress scam scores.
**Result:** Score **0.92 SCAM** — Voxtral detected the combination of authority impersonation + account information request, which legitimate FDIC examiners never do by phone.

### 6. The Legitimate Doctor IVR
**Attack:** A real automated appointment reminder — robotic voice, pre-recorded, mentions a patient name.
**Risk:** Automated voice + patient data mention could trip false positive.
**Result:** Score **0.10 SAFE** — No financial request, no urgency pressure, recognisable healthcare IVR pattern. Correctly cleared.

### 7. The Legitimate Bank Fraud Alert
**Attack:** Real bank automated alert — uses authority language ("This is First National Bank"), urgency ("possible unauthorized transaction"), and asks for callback.
**Risk:** Authority + urgency is the classic scam combination.
**Result:** Score **0.15 SAFE** — Critically, the call does NOT request credentials or payment. CallShield distinguishes "call us back" from "give us your PIN now."

---

## Automated Adversarial Suite

All adversarial scenarios are implemented as automated tests in `backend/tests/test_adversarial.py`:

| Test | What it probes | Expected result |
|------|---------------|-----------------|
| Prompt injection in recommendation field | Model output manipulation | Score clamped, valid result |
| Score out of range (1.5, -0.5) | Clamping enforcement | Clamped to [0.0, 1.0] |
| Missing fields in model response | Default value safety | No crash, safe defaults applied |
| Silence (zero-byte PCM buffer) | Edge case handling | is_silent() → True |
| Long-con script (friendly opener → wire transfer) | Multi-phase scam detection | score ≥ 0.6 |
| Pharmacy IVR (benign robocall) | False positive prevention | verdict ≠ SCAM |

Run: `cd backend && pytest tests/test_adversarial.py -v`

---

## Why Native Audio Matters for Adversarial Robustness

The key finding across all adversarial tests: **acoustic delivery is harder to fake than word choice.**

A scammer can rewrite their script to sound polite. They cannot easily:
- Suppress the call-center background noise of a boiler room
- Remove the flat, rehearsed cadence of a scripted pitch
- Eliminate the TTS artifacts of a synthesized robocall voice
- Change the rhythm of a pre-recorded IVR message

Text-based models see only the words. Voxtral hears the room.

---

*Full evaluation results: [docs/EVALUATION.md](docs/EVALUATION.md)*
*Threat model and red-team mitigations: [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)*
