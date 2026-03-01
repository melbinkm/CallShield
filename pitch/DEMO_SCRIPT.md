# CallShield — Demo Script

A scripted walkthrough for presenting CallShield in ~2 minutes.

---

## Setup (30 seconds)

1. Open browser to [http://localhost:5173](http://localhost:5173) (or live URL)
2. Ensure the app is loaded — you should see the CallShield interface with three input modes

**Talking point**: "CallShield detects phone scams in real-time using Mistral's Voxtral Mini — it analyzes raw audio natively, no transcription step needed."

---

## Demo 1: IRS Scam Transcript (45 seconds)

1. Click the **"Transcript"** tab
2. Paste the following IRS scam text:

> "This is Officer James Wilson from the Internal Revenue Service. Your Social Security number has been suspended due to suspicious activity. There is a federal arrest warrant issued under your name. To resolve this matter immediately, you must purchase $5,000 in Apple gift cards and read me the redemption codes. If you do not comply within the next 45 minutes, local law enforcement will be dispatched to your location."

3. Click **"Analyze"**
4. Watch the verdict appear: **SCAM** (score ~0.95-1.0)
5. Point out the detected signals:
   - Authority impersonation (IRS)
   - Urgency tactics (45 minutes)
   - Unusual payment method (gift cards)
   - Known scam script

**Talking point**: "Mistral Large identified 4 scam dimensions — authority impersonation, urgency, unusual payment, and a known scam script. Score: nearly 1.0."

---

## Demo 2: Safe Conversation (30 seconds)

1. Clear the previous result
2. Paste a safe conversation:

> "Hey! Are you free this Saturday? We're having a BBQ at our place around 4pm. Sarah and Mike are coming too. Bring whatever you want to drink — I've got burgers and hot dogs covered. Let me know!"

3. Click **"Analyze"**
4. Watch the verdict: **SAFE** (score 0.0)

**Talking point**: "Zero false positives — a normal conversation scores exactly 0.0. The model was calibrated with few-shot examples to avoid over-flagging."

---

## Demo 3: Try Sample Button (15 seconds)

1. Click the **"Try Sample"** button
2. A pre-loaded scam transcript is analyzed instantly
3. Verdict appears with signals

**Talking point**: "One click to see CallShield in action — no setup needed for evaluators."

---

## Key Talking Points

Use these to fill Q&A or transition between demos:

- **Native audio analysis**: Voxtral Mini processes raw audio bytes in a single API call — no transcription step. This preserves vocal cues like aggressive tone, scripted delivery, and call-center background noise.
- **7 scam dimensions**: Every call is evaluated across urgency, authority impersonation, information extraction, emotional manipulation, vocal patterns, known scam scripts, and robocall/IVR patterns.
- **Zero storage**: No audio, transcripts, or PII are ever persisted. All processing is in-memory.
- **Exponential scoring**: During live streaming, recent chunks are weighted 70% — a scam escalation late in a call raises the score quickly.
- **Real-world tested**: 8/8 samples correctly classified against real robocall recordings from the FTC dataset.

---

## If Asked About...

- **Accuracy**: "8/8 in our evaluation — 5 real robocalls + 3 transcripts. See docs/EVALUATION.md for the full 20-scenario framework."
- **Latency**: "2-4 seconds for audio analysis vs 5-8s for traditional STT+LLM pipelines."
- **Privacy**: "Zero storage. See docs/THREAT_MODEL.md for GDPR/CCPA analysis."
- **Why not use the Mistral SDK?**: "The Python SDK doesn't support `input_audio` content blocks yet, so we use raw HTTP for the Voxtral endpoint."
