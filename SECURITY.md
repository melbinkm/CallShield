# Security Policy

## Supported Versions

CallShield is an active hackathon project. Security fixes are applied to the latest version on `master`.

| Version | Supported |
|---------|-----------|
| Latest (`master`) | ✅ |
| Older commits | ❌ |

---

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report security issues by opening a [GitHub Issue](https://github.com/melbinkm/callshield/issues) with the label **`security`** and a brief description. For sensitive disclosures, prefix the title with `[SECURITY]` — maintainers will respond within 48 hours and coordinate a fix before any public disclosure.

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce (or a proof-of-concept if safe to share)
- Any suggested mitigations

---

## Security Design Principles

CallShield is built with security and privacy by default:

| Property | Implementation |
|----------|---------------|
| **Zero audio retention** | Audio bytes exist only in function-local variables; never written to disk, database, or object storage |
| **No verbatim transcripts** | Only scores, signals, and summaries are returned to the client; raw speech is never exposed |
| **Score clamping** | `scam_score` is always clamped to `[0.0, 1.0]` server-side regardless of model output |
| **Verdict enum validation** | Verdict is validated against a fixed 4-value enum; unexpected values fall back to `SAFE` |
| **Prompt injection hardening** | `response_format: json_object` enforces structured output; injected instructions cannot override clamping or enum validation |
| **No PII logging** | Logs contain only exception types and HTTP status codes — no audio content, transcripts, or IP addresses |
| **Input size limits** | 25 MB max upload, 512 KB max WebSocket chunk, 60 chunks per session, 10 000 char max transcript |

→ Full threat model, data flow diagram, abuse scenarios, and GDPR/CCPA analysis: [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)

---

## Known Limitations

- **No authentication on the hosted demo** — The public demo at `callshield-ui.onrender.com` has no API key requirement. It is rate-limited and intended for evaluation only; do not send sensitive call recordings to it.
- **Model output is probabilistic** — Scores and verdicts are model outputs, not cryptographic guarantees. See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) Section 1 (Disclaimer).
- **Third-party data processing** — Audio sent to the hosted demo is forwarded to the Mistral API. Review [Mistral's privacy policy](https://mistral.ai/privacy-policy) before sending sensitive recordings.
