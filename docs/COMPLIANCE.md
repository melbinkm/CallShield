# CallShield Compliance Reference

**Version:** v1.0.0
**Effective date:** 2026-03-01

This document maps CallShield's architectural decisions to GDPR and CCPA obligations. It is
intended for operators evaluating CallShield for production deployment in regulated environments.

For the full data flow and threat model, see [docs/THREAT_MODEL.md](THREAT_MODEL.md).

---

## 1. Compliance by Design

CallShield's primary compliance mechanism is **architectural elimination of data**. Because the
system stores no audio, no transcripts, and no personal data of any kind, the majority of data
subject rights are satisfied automatically — there is nothing to erase, port, access, or correct.

**Zero-storage properties:**
- Audio bytes are held only in function-local variables for the duration of a single request (~1–3s)
- No database, no file system writes, no object storage, no caches
- No verbatim transcripts are generated or persisted
- Results (score, verdict, signals) exist only in the browser's React state and are lost on page reload
- Server logs contain only exception types, HTTP status codes, and request metadata — no audio content, no PII

> This design means CallShield operators face **no data retention obligations** for call audio
> processed through the system. The only data that may require governance is the score/verdict
> output if it is stored downstream by the operator's own systems.

---

## 2. GDPR Article Mapping

| GDPR Article | Requirement | How CallShield Satisfies It | Evidence |
|--------------|-------------|----------------------------|---------|
| **Art. 5(1)(c)** — Data minimisation | Collect only what is necessary | Audio is processed and immediately discarded; no personal identifiers collected | [THREAT_MODEL.md §3](THREAT_MODEL.md) |
| **Art. 5(1)(e)** — Storage limitation | Do not retain data longer than necessary | Retention period = duration of a single API call (~1–3s); no persistence layer exists | [THREAT_MODEL.md §3](THREAT_MODEL.md) |
| **Art. 17** — Right to erasure | Data subjects can request deletion | Nothing to erase; zero-storage architecture satisfies this by design | [THREAT_MODEL.md §7](THREAT_MODEL.md) |
| **Art. 20** — Right to data portability | Data subjects can receive their data | No stored data to port | [THREAT_MODEL.md §7](THREAT_MODEL.md) |
| **Art. 25** — Privacy by design and default | Build privacy protections into the system | Zero-storage is the default; no opt-out needed; audio discarded without configuration | Architecture design decision |
| **Art. 32** — Security of processing | Implement appropriate technical measures | HTTPS transport to Mistral API; injection-hardened output parsing; score clamping; enum validation | [THREAT_MODEL.md §6](THREAT_MODEL.md), [SECURITY.md](../SECURITY.md) |
| **Art. 28** — Processor contracts | Controllers must have DPAs with processors | Mistral AI acts as data processor; operators must review Mistral's DPA before production use | [THREAT_MODEL.md §7](THREAT_MODEL.md) |
| **Art. 13/14** — Transparency | Inform data subjects about processing | Consent banner required before microphone activation (see §5 below) | [THREAT_MODEL.md §7](THREAT_MODEL.md) |

---

## 3. CCPA

CallShield does not sell, share, or monetize personal data. Because no personal data is retained,
the CCPA's core rights (Right to Know, Right to Delete, Right to Opt-Out of Sale) are satisfied
by the zero-retention architecture.

**Operator obligations under CCPA:**
- Include disclosure of the CallShield processing pipeline in your privacy policy
- Do not log or store the score/verdict output in a way that could be linked to a specific
  California consumer without providing appropriate CCPA disclosures
- If downstream score storage is implemented, apply CCPA deletion rights to those records

---

## 4. Data Processor Relationship

Under GDPR, when CallShield is deployed by an operator:

| Role | Party | Obligations |
|------|-------|-------------|
| **Data Controller** | The operator (carrier, enterprise, SaaS provider) | Establish lawful basis; provide privacy notices; manage DPAs |
| **Data Processor** | Mistral AI (processes audio on behalf of the operator) | Mistral's DPA and ToS govern this relationship |
| **Sub-processor** | None within CallShield itself | CallShield adds no sub-processors beyond Mistral |

**Required steps for operators:**
1. Review [Mistral AI's Data Processing Agreement](https://mistral.ai/terms) and confirm it meets
   your GDPR obligations
2. Confirm Mistral's current API data retention policy (at time of writing, Mistral does not retain
   API inputs for model training on paid tiers — verify against current terms)
3. Establish a lawful basis for processing (typically **legitimate interest** in fraud prevention
   or **explicit consent** from call participants)
4. Ensure any downstream storage of CallShield output (scores, verdicts) is governed by your own
   data retention and deletion policies

---

## 5. Deployment Compliance Checklist

Before deploying CallShield in a production environment:

- [ ] **Consent banner** — Display a clear, prominent notice before activating the microphone,
  explaining that audio will be sent to an external AI service (Mistral) for analysis
- [ ] **Opt-in only** — The consent mechanism must be affirmative (not pre-checked), and users
  must be able to decline without loss of service
- [ ] **Privacy policy** — Publish a privacy policy referencing the CallShield data flow
  (see [THREAT_MODEL.md §2](THREAT_MODEL.md) for the data flow diagram to adapt)
- [ ] **EU adequacy** — If processing EU residents' data, confirm the legal mechanism for
  transferring audio to Mistral AI's infrastructure (Standard Contractual Clauses or adequacy
  decision)
- [ ] **Wiretapping law** — Comply with applicable call-recording consent laws (e.g., two-party
  consent in some US states, GDPR Art. 6 lawful basis in the EU, PECR in the UK)
- [ ] **Mistral DPA** — Sign or accept Mistral's Data Processing Agreement before production use
- [ ] **Downstream audit trail** — If you store CallShield verdicts for fraud investigation
  purposes, ensure your own retention and deletion policies are documented and compliant

---

## 6. What Is NOT in Scope

| Item | Status |
|------|--------|
| Biometric data (voiceprints, speaker ID) | Not collected — CallShield does not create voiceprints |
| Call content retention | Not applicable — no verbatim transcripts stored |
| Cross-border data transfer within CallShield | Not applicable — CallShield has no persistent storage to transfer |
| Data subject access requests | Not applicable — no stored data to provide |

---

*Cross-reference: [docs/THREAT_MODEL.md](THREAT_MODEL.md) · [SECURITY.md](../SECURITY.md) · [docs/DETECTION_POLICY.md](DETECTION_POLICY.md)*
*Last updated: 2026-03-01*
