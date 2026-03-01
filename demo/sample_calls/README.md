# Sample Call Data

This directory contains sample transcripts and real robocall audio recordings for testing CallShield's scam detection capabilities.

## Transcript Samples

| File | Type | Actual Verdict | Actual Score |
|------|------|----------------|--------------|
| `irs_scam_transcript.txt` | IRS arrest threat + gift card demand | **SCAM** | 1.0 |
| `medicare_robocall_transcript.txt` | "Press 1" Medicare benefits robocall | **LIKELY_SCAM** | 0.70 |
| `safe_call_transcript.txt` | Personal friendly call | **SAFE** | 0.0 |

## Audio Samples (Real Robocalls)

Real-world robocall recordings from the FTC's Project Point of No Entry, analyzed by Voxtral Mini's native audio intelligence.

| File | Scam Type | Verdict | Score | Signals |
|------|-----------|---------|-------|---------|
| `audio/ssn_fraud_robocall.wav` | SSN suspension threat | **LIKELY_SCAM** | 0.70 | Robocall IVR, authority impersonation, urgency |
| `audio/legal_threat_robocall.wav` | SSA legal threat + criminal charges | **LIKELY_SCAM** | 0.85 | Authority impersonation, urgency, known scam script, robocall IVR |
| `audio/amazon_scam_robocall.wav` | Fake Amazon suspicious charge | **SUSPICIOUS** | 0.65 | Authority impersonation, urgency, known scam script |
| `audio/warranty_robocall.wav` | Vehicle warranty expiration | **LIKELY_SCAM** | 0.60 | Urgency, authority impersonation, known scam script |
| `audio/medicare_robocall.wav` | Medicare health advisor | **SUSPICIOUS** | 0.40 | Authority impersonation, low urgency |

### Key Observations

- **All 5 real robocalls were correctly identified** as suspicious or scam (scores 0.40 - 0.85)
- **Legal threat robocall scored highest** (0.85) — multiple high-severity signals including authority impersonation, urgency, and known scam scripts
- **Medicare audio scored lowest** (0.40) — the recording was short and conversational, with fewer overt scam signals
- **Voxtral detected robocall/IVR patterns** from audio characteristics alone (pre-recorded voice, "press 1" prompts)

## Using These Samples

### Transcript via the API

```bash
curl -X POST http://localhost:8000/api/analyze/transcript \
  -H "Content-Type: application/json" \
  -d "{\"transcript\": \"$(cat irs_scam_transcript.txt)\"}"
```

### Audio via the API

```bash
curl -X POST http://localhost:8000/api/analyze/audio \
  -F "file=@audio/legal_threat_robocall.wav"
```

### Via the UI

1. Open http://localhost:5173
2. Select "Upload Audio" and choose any `.wav` file from `audio/`
3. Or select "Paste Transcript" and copy-paste any `.txt` file
4. Click "Analyze"

### Audio Format Requirements

CallShield expects:
- **Format**: WAV (RIFF header)
- **Sample Rate**: 16kHz recommended
- **Channels**: Mono
- **Max Size**: 25MB for uploads, 512KB per streaming chunk

## Expected Outputs

See `../expected_outputs/` for the actual JSON responses from the API for each sample.

## Audio Dataset Attribution

The audio samples in `audio/` are sourced from the **Robocall Audio Dataset** — a collection of real-world robocall recordings made available by the FTC through the Project Point of No Entry initiative.

- **Repository**: [wspr-ncsu/robocall-audio-dataset](https://github.com/wspr-ncsu/robocall-audio-dataset)
- **Paper**: [Robocall Audio from the FTC's Project Point of No Entry](https://www.csc2.ncsu.edu/techreports/tech/2023/TR-2023-1.pdf)
- **Website**: [robocall.science](https://robocall.science)
- **License**: Public domain (data), Creative Commons BY-ND (documentation)

```bibtex
@techreport{robocallDatasetTechReport,
  author      = {{Sathvik Prasad and Bradley Reaves}},
  title       = {{Robocall Audio from the FTC's Project Point of No Entry}},
  institution = {{North Carolina State University}},
  year        = {2023},
  month       = {Nov},
  number      = {TR-2023-1}
}
```

The dataset consists of 1,432 real robocall recordings collected from FTC cease-and-desist cases, converted to 16kHz WAV mono format. We selected 5 representative samples spanning SSN fraud, legal threats, Amazon impersonation, warranty scams, and Medicare scams.
