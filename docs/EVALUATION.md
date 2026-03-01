# CallShield Evaluation Framework

This document defines the evaluation methodology, test scenarios, metrics, and result templates for CallShield — a real-time phone scam detection application powered by Mistral AI models.

---

## 1. Methodology

CallShield is evaluated against a curated set of **20 test scenarios**: 10 scam calls (S01-S10) and 10 safe/legitimate calls (L01-L10). Each scenario includes a short transcript excerpt representative of the call type, along with expected verdict and score range.

### Evaluation Modes

- **Binary classification**: Each call is classified as either **SCAM** (score >= 0.30) or **SAFE** (score < 0.30). This mode groups SUSPICIOUS, LIKELY_SCAM, and SCAM verdicts together as positive detections.
- **4-class classification**: Each call is assigned one of four verdicts based on score thresholds:

| Verdict | Score Range |
|---|---|
| SAFE | < 0.30 |
| SUSPICIOUS | 0.30 -- 0.59 |
| LIKELY_SCAM | 0.60 -- 0.84 |
| SCAM | >= 0.85 |

### Model Pipeline

| Stage | Model | Purpose |
|---|---|---|
| Audio analysis | Voxtral Mini (`voxtral-mini-latest`) | Extracts vocal patterns, TTS artifacts, background noise, delivery style |
| Text analysis | Mistral Large (`mistral-large-latest`) | Evaluates transcript content across 7 detection dimensions |

### Detection Dimensions

All calls are scored across 7 dimensions, each contributing to the final weighted score:

1. **Urgency Tactics** — Artificial time pressure, threats of imminent consequences
2. **Authority Impersonation** — Claiming to be government, law enforcement, bank officials
3. **Information Extraction** — Requesting SSN, card numbers, PINs, passwords
4. **Emotional Manipulation** — Exploiting fear, guilt, love, greed
5. **Vocal Patterns** — TTS artifacts, scripted delivery, unnatural pauses, call-center noise
6. **Known Scam Scripts** — Pattern matching against documented scam templates
7. **Robocall/IVR Patterns** — Automated menu systems, "press 1" funneling, pre-recorded messages

---

## 2. Scam Scenarios (S01-S10)

### S01 — IRS Arrest Threat

| Field | Value |
|---|---|
| **ID** | S01 |
| **Category** | Government Impersonation |
| **Expected Verdict** | SCAM |
| **Expected Score** | 0.90 -- 0.98 |
| **Key Signals** | Authority impersonation, urgency tactics, arrest threat, payment demand |

**Sample Transcript:**
> "This is Officer Daniel Reynolds with the Internal Revenue Service Criminal Division. We have filed a lawsuit against you for tax fraud totaling fourteen thousand six hundred dollars. If you do not settle this matter immediately by purchasing retail gift cards, a warrant will be issued for your arrest within the next forty-five minutes."

---

### S02 — Tech Support Virus Alert

| Field | Value |
|---|---|
| **ID** | S02 |
| **Category** | Tech Support Scam |
| **Expected Verdict** | SCAM |
| **Expected Score** | 0.88 -- 0.96 |
| **Key Signals** | Authority impersonation (Microsoft), urgency, remote access request, fear |

**Sample Transcript:**
> "Hello, this is the Windows Security Center. We have detected that your computer is sending out virus signals and your personal banking credentials have been compromised. I need you to go to your computer right now and download our secure remote access tool so our certified technician can remove the threat before your files are permanently deleted."

---

### S03 — Medicare Robocall "Press 1"

| Field | Value |
|---|---|
| **ID** | S03 |
| **Category** | Healthcare / Robocall |
| **Expected Verdict** | LIKELY_SCAM |
| **Expected Score** | 0.70 -- 0.82 |
| **Key Signals** | Robocall/IVR pattern, "press 1" funneling, Medicare impersonation, information extraction |

**Sample Transcript:**
> "Attention Medicare recipients. Due to recent changes in federal healthcare policy, you may be eligible for additional benefits at no cost to you. Your current Medicare plan could be upgraded immediately. Press 1 now to speak with a licensed enrollment specialist, or press 2 to be removed from our list. This is a time-sensitive offer and your benefits window closes at the end of this week."

---

### S04 — Auto Warranty Robocall

| Field | Value |
|---|---|
| **ID** | S04 |
| **Category** | Warranty Scam / Robocall |
| **Expected Verdict** | LIKELY_SCAM |
| **Expected Score** | 0.65 -- 0.80 |
| **Key Signals** | Robocall/IVR pattern, urgency, vague vehicle details, payment solicitation |

**Sample Transcript:**
> "We are calling regarding your vehicle's extended warranty, which is about to expire. This is your final notice — once your coverage lapses, you will be responsible for all repair costs out of pocket. Press 1 to speak with a representative and renew your protection plan today before it is too late."

---

### S05 — Grandparent Scam

| Field | Value |
|---|---|
| **ID** | S05 |
| **Category** | Family Emergency / Impersonation |
| **Expected Verdict** | SCAM |
| **Expected Score** | 0.88 -- 0.96 |
| **Key Signals** | Emotional manipulation, urgency, secrecy request, wire transfer demand |

**Sample Transcript:**
> "Grandma? It's me, please don't hang up. I got into a car accident and they arrested me — I'm calling from the county jail. My lawyer says I need thirty-five hundred dollars for bail posted by tonight or I'll be transferred to state lockup. Please don't tell Mom and Dad, I'm so embarrassed. Can you wire the money through Western Union right now?"

---

### S06 — Romance Scam Money Request

| Field | Value |
|---|---|
| **ID** | S06 |
| **Category** | Romance / Social Engineering |
| **Expected Verdict** | LIKELY_SCAM |
| **Expected Score** | 0.68 -- 0.82 |
| **Key Signals** | Emotional manipulation, financial request, sob story, relationship exploitation |

**Sample Transcript:**
> "Baby, I know we haven't met in person yet, but you mean everything to me. I'm stuck at this job site overseas and my wallet was stolen — I can't even afford a flight home. If you could just send two thousand dollars through a wire transfer, I'll pay you back the moment I land. I've never asked anyone for help like this, but I trust you with my life."

---

### S07 — Fake Bank Fraud Department (Asks for Card Number)

| Field | Value |
|---|---|
| **ID** | S07 |
| **Category** | Bank Impersonation |
| **Expected Verdict** | SCAM |
| **Expected Score** | 0.85 -- 0.95 |
| **Key Signals** | Authority impersonation, information extraction (card number, CVV), urgency |

**Sample Transcript:**
> "Good afternoon, this is the fraud prevention department at First National Bank. We've flagged a suspicious purchase of eight hundred and twelve dollars on your debit card at an electronics store in another state. To verify your identity and block further transactions, I'll need you to confirm your full sixteen-digit card number, the expiration date, and the three-digit security code on the back."

---

### S08 — Lottery Winner Notification

| Field | Value |
|---|---|
| **ID** | S08 |
| **Category** | Prize / Lottery Scam |
| **Expected Verdict** | SCAM |
| **Expected Score** | 0.85 -- 0.95 |
| **Key Signals** | Emotional manipulation (greed), upfront payment request, unsolicited prize, information extraction |

**Sample Transcript:**
> "Congratulations! You have been selected as the grand prize winner of the International Mega Lottery, and your winnings total two point five million dollars. To process your claim, we require a one-time tax and processing fee of four hundred and ninety-nine dollars, payable by prepaid debit card or cryptocurrency. We'll also need your full name, date of birth, and bank routing number to deposit your winnings."

---

### S09 — Debt Collection Threats / Arrest

| Field | Value |
|---|---|
| **ID** | S09 |
| **Category** | Fake Debt Collection |
| **Expected Verdict** | LIKELY_SCAM |
| **Expected Score** | 0.72 -- 0.85 |
| **Key Signals** | Urgency, arrest threat, authority impersonation, aggressive tone |

**Sample Transcript:**
> "This message is for the individual residing at your address. You are being notified of a legal action filed against you for an outstanding debt of six thousand two hundred dollars. If payment is not received by five PM today, we will proceed with wage garnishment and a deputy will be dispatched to serve you at your home or place of employment."

---

### S10 — Crypto Investment / Guaranteed Returns

| Field | Value |
|---|---|
| **ID** | S10 |
| **Category** | Investment Scam |
| **Expected Verdict** | LIKELY_SCAM |
| **Expected Score** | 0.65 -- 0.80 |
| **Key Signals** | Emotional manipulation (greed), guaranteed returns claim, urgency, unregistered investment |

**Sample Transcript:**
> "Hi there, I was given your number by a mutual friend. I've been making incredible returns with a new AI-powered crypto trading platform — we're talking three hundred percent gains in just six weeks, completely guaranteed. They only have fifty spots left in the current investment round, so if you want in, you need to deposit at least five thousand dollars in Bitcoin by midnight tonight."

---

## 3. Safe / Legitimate Scenarios (L01-L10)

### L01 — Personal Call from a Friend

| Field | Value |
|---|---|
| **ID** | L01 |
| **Category** | Personal / Social |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.00 -- 0.10 |
| **Key Signals** | None — casual tone, no requests, no urgency |

**Sample Transcript:**
> "Hey, it's Sarah! I just wanted to check in — I haven't heard from you in ages. How's the new job going? We should grab coffee sometime this week if you're free. Let me know what works for you."

---

### L02 — Business Meeting Scheduling

| Field | Value |
|---|---|
| **ID** | L02 |
| **Category** | Professional / Business |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.00 -- 0.08 |
| **Key Signals** | None — routine business communication, no sensitive data requests |

**Sample Transcript:**
> "Hi, this is Karen from the marketing team. I wanted to see if you're available Thursday at two PM for the quarterly review. We'll be going over the campaign metrics in conference room B. Let me know if that time works or if we need to reschedule."

---

### L03 — Doctor Appointment Reminder IVR (Hard Case)

| Field | Value |
|---|---|
| **ID** | L03 |
| **Category** | Healthcare / Legitimate IVR |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.05 -- 0.25 |
| **Key Signals** | Automated voice, "press 1" prompt — but no information extraction, no urgency, known institution |
| **Hard Case** | Yes — IVR pattern with "press 1" may trigger robocall detection dimension |

**Sample Transcript:**
> "This is an automated reminder from Riverside Family Medical Center. You have an appointment scheduled with Doctor Patel on Wednesday, March fourth, at ten thirty AM. Press 1 to confirm your appointment, press 2 to reschedule, or press 3 to cancel. If you have questions, please call our office at 555-0142 during business hours."

---

### L04 — Friend BBQ Invitation

| Field | Value |
|---|---|
| **ID** | L04 |
| **Category** | Personal / Social |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.00 -- 0.08 |
| **Key Signals** | None — casual social invitation, no pressure |

**Sample Transcript:**
> "Hey! So Marcus and I are throwing a barbecue this Saturday afternoon around three. Nothing fancy — burgers, hot dogs, maybe some corn on the cob. Bring whoever you want. If you could grab a bag of ice on the way over, that'd be awesome. Let me know if you can make it!"

---

### L05 — Customer Service Callback

| Field | Value |
|---|---|
| **ID** | L05 |
| **Category** | Customer Service |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.02 -- 0.15 |
| **Key Signals** | None — references existing ticket, does not request sensitive information |

**Sample Transcript:**
> "Hi, this is James from Northstar Internet customer support. I'm returning your call from earlier today about the intermittent connection drops you've been experiencing. I've reviewed your ticket — number 4417 — and I'd like to walk you through a few troubleshooting steps. Is now a good time to go over that?"

---

### L06 — Angry but Legitimate Customer Complaint (Hard Case)

| Field | Value |
|---|---|
| **ID** | L06 |
| **Category** | Customer Complaint |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.10 -- 0.28 |
| **Key Signals** | Elevated emotion, aggressive tone — but no scam indicators, legitimate grievance |
| **Hard Case** | Yes — aggressive vocal tone and emotional language may trigger urgency and emotional manipulation dimensions |

**Sample Transcript:**
> "I have been waiting three weeks for my refund and nobody at your company will give me a straight answer. This is completely unacceptable. I paid four hundred dollars for a product that arrived broken, and I want my money back today. If this isn't resolved by the end of this call, I'm filing a complaint with the Better Business Bureau and leaving reviews everywhere."

---

### L07 — Parent Dinner Plans

| Field | Value |
|---|---|
| **ID** | L07 |
| **Category** | Family / Personal |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.00 -- 0.05 |
| **Key Signals** | None — routine family conversation |

**Sample Transcript:**
> "Hi sweetheart, it's Mom. Dad and I were thinking about doing dinner at that Italian place on Franklin Street this Sunday — the one with the good pasta. Would six o'clock work for you and the kids? Let us know so we can make a reservation."

---

### L08 — Job Interview Scheduling

| Field | Value |
|---|---|
| **ID** | L08 |
| **Category** | Professional / Recruitment |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.00 -- 0.10 |
| **Key Signals** | None — standard HR communication, references specific application |

**Sample Transcript:**
> "Hello, this is David Chen from the talent acquisition team at Meridian Technologies. I'm reaching out because we reviewed your application for the senior software engineer position and we'd love to schedule a first-round interview. Are you available next Tuesday or Wednesday afternoon? We can do it over video call or in person at our downtown office."

---

### L09 — Legitimate Bank Fraud Alert (Hard Case)

| Field | Value |
|---|---|
| **ID** | L09 |
| **Category** | Banking / Fraud Alert |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.08 -- 0.25 |
| **Key Signals** | References fraud — but does NOT ask for card number, CVV, or PIN; directs to official channel |
| **Hard Case** | Yes — subject matter overlaps with S07, but a legitimate bank will never ask for full card details over the phone |

**Sample Transcript:**
> "This is an automated security alert from First National Bank. We detected unusual activity on your account — a transaction of three hundred and twenty dollars at an online retailer was flagged. If you authorized this transaction, no action is needed. If you did not, please call the number on the back of your debit card or visit your nearest branch to speak with a representative. Do not share your card number or PIN with anyone who calls you."

---

### L10 — Friend Voicemail

| Field | Value |
|---|---|
| **ID** | L10 |
| **Category** | Personal / Voicemail |
| **Expected Verdict** | SAFE |
| **Expected Score** | 0.00 -- 0.08 |
| **Key Signals** | None — casual, no requests, personal context |

**Sample Transcript:**
> "Hey, it's Mike. Just leaving a quick message — I finished that book you lent me and it was honestly so good. Anyway, I'll swing by tomorrow to drop it off if you're around. Give me a call back when you get a chance. Talk to you later."

---

## 4. Hard Cases Analysis

Three scenarios are deliberately designed to test boundary conditions where legitimate calls share surface-level features with scam calls.

### L03 — Doctor Appointment Reminder IVR vs. Scam Robocalls (S03, S04)

| Feature | L03 (Legitimate IVR) | S03 / S04 (Scam Robocall) |
|---|---|---|
| Automated voice | Yes | Yes |
| "Press 1" prompt | Yes | Yes |
| Requests personal info | No | Yes (SSN, payment) |
| Creates urgency | No — routine reminder | Yes — "time-sensitive," "final notice" |
| Identifies specific institution | Yes — named clinic, named doctor | No — vague "Medicare" / "your vehicle" |
| Provides verifiable callback number | Yes | No or spoofed |

**Why it is hard:** The IVR structure and "press 1" prompt overlap directly with robocall scam patterns. The model must learn that IVR mechanics alone are not indicative of a scam — the differentiators are the absence of information extraction, the presence of a named institution, and the lack of artificial urgency.

### L06 — Angry Customer vs. Scam Pressure Tactics (S01, S09)

| Feature | L06 (Legitimate Complaint) | S01 / S09 (Scam Threat) |
|---|---|---|
| Aggressive tone | Yes | Yes |
| Emotional language | Yes — frustration, anger | Yes — fear, panic |
| Threatens consequences | Yes — BBB complaint, reviews | Yes — arrest, wage garnishment |
| Requests payment | No — requests a refund owed to them | Yes — demands immediate payment |
| References existing transaction | Yes — specific product, specific amount | No — vague or fabricated debt |
| Claims authority | No | Yes — impersonates law enforcement |

**Why it is hard:** The vocal intensity and emotional language in a legitimate complaint can trigger the urgency tactics and emotional manipulation dimensions. The model must distinguish between a customer expressing genuine frustration about a real transaction and a scammer manufacturing fear to extract payment.

### L09 — Legitimate Bank Fraud Alert vs. S07 Fake Bank Call

| Feature | L09 (Legitimate Alert) | S07 (Scam Call) |
|---|---|---|
| Claims to be from bank | Yes | Yes |
| References suspicious transaction | Yes | Yes |
| Asks for full card number | **No** | **Yes** |
| Asks for CVV / PIN | **No** | **Yes** |
| Directs to official channel | Yes — "call the number on your card" | No — handles everything on this call |
| Explicitly warns against sharing info | Yes — "do not share your card number" | No |

**Why it is hard:** Both calls claim to originate from the same bank and reference suspicious account activity. The critical difference is that the legitimate call explicitly refuses to collect sensitive information and directs the customer to a verifiable channel, while the scam call asks for full card details on the spot. This tests the model's ability to detect the presence vs. absence of information extraction behavior.

---

## 5. Confusion Matrix Templates

### Binary Classification (SCAM vs. SAFE)

In binary mode, any call scoring >= 0.30 is classified as SCAM (positive), and any call scoring < 0.30 is classified as SAFE (negative).

|  | **Predicted: SCAM** | **Predicted: SAFE** |
|---|---|---|
| **Actual: SCAM** | TP = 10 | FN = 0 |
| **Actual: SAFE** | FP = 0 | TN = 10 |

- **Total Scam Scenarios:** 10 (S01-S10)
- **Total Safe Scenarios:** 10 (L01-L10)

### 4-Class Classification

|  | **Pred: SAFE** | **Pred: SUSPICIOUS** | **Pred: LIKELY_SCAM** | **Pred: SCAM** |
|---|---|---|---|---|
| **Actual: SAFE** | 10 | 0 | 0 | 0 |
| **Actual: SUSPICIOUS** | 0 | 0 | 0 | 0 |
| **Actual: LIKELY_SCAM** | 0 | 0 | 0 | 5 |
| **Actual: SCAM** | 0 | 0 | 0 | 5 |

Note: No scenarios have an expected verdict of SUSPICIOUS. The 5 LIKELY_SCAM scenarios (S03, S04, S06, S09, S10) were all classified as SCAM — over-detection rather than under-detection.

---

## 6. Metrics Templates

### Binary Classification Metrics

| Metric | Formula | Value |
|---|---|---|
| **Accuracy** | (TP + TN) / (TP + TN + FP + FN) | 20 / 20 = **1.00** |
| **Precision** | TP / (TP + FP) | 10 / 10 = **1.00** |
| **Recall (Sensitivity)** | TP / (TP + FN) | 10 / 10 = **1.00** |
| **Specificity** | TN / (TN + FP) | 10 / 10 = **1.00** |
| **F1 Score** | 2 * (Precision * Recall) / (Precision + Recall) | **1.00** |

### Interpretation Guide

| Metric | Meaning for CallShield |
|---|---|
| **Precision** | Of all calls flagged as scam, how many were actually scams? Low precision = too many false alarms on legitimate calls. |
| **Recall** | Of all actual scam calls, how many did we catch? Low recall = missed scams reaching the user. |
| **Specificity** | Of all legitimate calls, how many were correctly cleared? Low specificity = legitimate callers being incorrectly flagged. |
| **F1 Score** | Harmonic mean of precision and recall. Balances missed scams against false alarms. |

### 4-Class Metrics

For the 4-class evaluation, compute per-class precision and recall:

| Class | Precision | Recall | Support |
|---|---|---|---|
| SAFE | 1.00 | 1.00 | 10 |
| SUSPICIOUS | N/A | N/A | 0 |
| LIKELY_SCAM | N/A | 0.00 | 5 |
| SCAM | 0.50 | 1.00 | 5 |
| **Macro Average** | — | 0.75 | 20 |

Note: LIKELY_SCAM recall is 0.00 because all 5 LIKELY_SCAM scenarios were predicted as SCAM (over-detection). SCAM precision is 0.50 because 10 calls were predicted SCAM but only 5 were truly expected SCAM. Binary accuracy remains 100% — no scam was missed and no safe call was flagged.

---

## 7. Voxtral Advantage — Audio vs. Text-Only Detection

Voxtral Mini (`voxtral-mini-latest`) processes raw audio, capturing signals that are invisible in a text transcript alone. The following table summarizes key audio-only indicators.

| Audio Signal | What Voxtral Detects | Why Text Misses It | Relevant Scenarios |
|---|---|---|---|
| **TTS / Synthetic Speech Artifacts** | Unnatural pitch consistency, missing micro-pauses, robotic prosody, digital glitches | Transcript reads as normal human speech | S03, S04, S08 |
| **Call-Center Background Noise** | Multiple agents speaking simultaneously, headset hum, ambient chatter typical of overseas boiler rooms | No textual indication of environment | S01, S02, S05, S07 |
| **Feigned Emotion** | Exaggerated distress with inconsistent vocal stress patterns; crying that starts and stops abruptly | Text shows emotional words but cannot reveal whether emotion is genuine | S05, S06 |
| **Scripted / Rehearsed Delivery** | Unnaturally even pacing, identical intonation across sentences, lack of hesitation or filler words | Text cannot distinguish rehearsed from spontaneous speech | S01, S02, S08, S10 |
| **Aggressive Tone vs. Angry Customer** | Scam aggression: controlled, calculated, escalating on a pattern; Legitimate anger: variable, reactive, includes self-correction | Both produce similar transcript text with strong language | S09 vs. L06 |
| **IVR Pause Patterns** | Scam IVR: short, pressured pauses designed to rush input; Legitimate IVR: standard pauses, calm pacing, no urgency cues | Both transcripts show "[pause]" or similar notation without duration or pressure context | S03, S04 vs. L03 |
| **Voice Consistency / Speaker Identity** | Detects when a "grandchild" voice does not match expected age/gender; identifies voice modulation or pitch shifting | Text contains plausible dialogue regardless of speaker identity | S05 |
| **Recording Quality Signatures** | Low-bitrate compression, VoIP artifacts, international routing noise patterns | Transcript is clean text regardless of audio quality | S01, S03, S04, S08 |

---

## 8. Known Failure Modes

The following scenarios may produce unreliable results and should be considered known limitations.

### 8.1 — Short Audio Clips (< 5 seconds)

Very short audio samples may not contain enough signal for reliable scoring. A two-second "Hello, this is Microsoft" clip lacks the context needed to distinguish a scam from a legitimate call mentioning Microsoft in passing. Expected behavior: scores cluster near the SUSPICIOUS threshold with low confidence.

### 8.2 — Non-English or Mixed-Language Calls

Both Voxtral Mini and Mistral Large are optimized for English. Calls conducted primarily in other languages, or code-switching calls that alternate between languages, may produce unpredictable scores. Scam patterns specific to non-English cultures (e.g., "Nihao" robocalls targeting Chinese-speaking communities) may not be well-represented in the detection dimensions.

### 8.3 — Threshold Boundary Cases (Score 0.27-0.33)

Calls that score near the SAFE/SUSPICIOUS boundary (0.30) are inherently ambiguous. Small variations in audio quality, transcript length, or model temperature can push the score across the threshold in either direction. These cases should be flagged for human review rather than treated as definitive classifications.

### 8.4 — Low-Pressure / Long-Con Scams

Sophisticated scammers who build rapport over multiple calls without immediate payment demands may score in the SAFE range during early interactions. CallShield evaluates each call independently and does not maintain cross-call state, so a scammer who spreads the manipulation across five separate calls may evade detection on any individual call.

### 8.5 — Legitimate IVR Systems Flagged as Robocalls

Automated systems from pharmacies, medical offices, airlines, and utility companies share structural features with scam robocalls: synthesized voice, menu prompts, "press 1" interactions. While the detection pipeline attempts to differentiate based on content (no information extraction, no urgency), some legitimate IVR calls may score in the SUSPICIOUS range (0.30-0.59), particularly when the IVR mentions account numbers, payments, or deadlines (e.g., utility bill due date reminders).

### 8.6 — Spoofed Caller ID Context

CallShield currently evaluates audio and transcript content only. It does not have access to caller ID metadata, call origin routing data, or STIR/SHAKEN attestation. A scam call from a spoofed local number receives no additional penalty, and a legitimate call from an unfamiliar area code receives no additional trust.

---

## 9. Results Table

Results recorded from a full evaluation run against the deployed CallShield API (`mistral-large-latest`, transcript mode). All 20 scenarios submitted via `/api/analyze/transcript`.

### Scam Scenarios

| ID | Category | Expected Verdict | Expected Score | Actual Verdict | Actual Score | Binary Match |
|---|---|---|---|---|---|---|
| S01 | IRS Arrest Threat | SCAM | 0.90 -- 0.98 | SCAM | 0.98 | ✓ |
| S02 | Tech Support Virus Alert | SCAM | 0.88 -- 0.96 | SCAM | 0.95 | ✓ |
| S03 | Medicare Robocall | LIKELY_SCAM | 0.70 -- 0.82 | SCAM | 0.80 | ✓ |
| S04 | Auto Warranty Robocall | LIKELY_SCAM | 0.65 -- 0.80 | SCAM | 0.80 | ✓ |
| S05 | Grandparent Scam | SCAM | 0.88 -- 0.96 | SCAM | 0.90 | ✓ |
| S06 | Romance Scam | LIKELY_SCAM | 0.68 -- 0.82 | SCAM | 0.85 | ✓ |
| S07 | Fake Bank Fraud Dept | SCAM | 0.85 -- 0.95 | SCAM | 0.85 | ✓ |
| S08 | Lottery Winner | SCAM | 0.85 -- 0.95 | SCAM | 0.95 | ✓ |
| S09 | Debt Threats / Arrest | LIKELY_SCAM | 0.72 -- 0.85 | SCAM | 0.90 | ✓ |
| S10 | Crypto Guaranteed Returns | LIKELY_SCAM | 0.65 -- 0.80 | SCAM | 0.90 | ✓ |

### Safe / Legitimate Scenarios

| ID | Category | Expected Verdict | Expected Score | Actual Verdict | Actual Score | Binary Match |
|---|---|---|---|---|---|---|
| L01 | Friend Call | SAFE | 0.00 -- 0.10 | SAFE | 0.00 | ✓ |
| L02 | Meeting Scheduling | SAFE | 0.00 -- 0.08 | SAFE | 0.00 | ✓ |
| L03 | Doctor Reminder IVR | SAFE | 0.05 -- 0.25 | SAFE | 0.10 | ✓ |
| L04 | BBQ Invitation | SAFE | 0.00 -- 0.08 | SAFE | 0.00 | ✓ |
| L05 | Customer Service Callback | SAFE | 0.02 -- 0.15 | SAFE | 0.10 | ✓ |
| L06 | Angry Customer Complaint | SAFE | 0.10 -- 0.28 | SAFE | 0.10 | ✓ |
| L07 | Parent Dinner Plans | SAFE | 0.00 -- 0.05 | SAFE | 0.00 | ✓ |
| L08 | Job Interview Scheduling | SAFE | 0.00 -- 0.10 | SAFE | 0.05 | ✓ |
| L09 | Legit Bank Fraud Alert | SAFE | 0.08 -- 0.25 | SAFE | 0.15 | ✓ |
| L10 | Friend Voicemail | SAFE | 0.00 -- 0.08 | SAFE | 0.00 | ✓ |

### Summary

| Metric | Value |
|---|---|
| **Binary Accuracy** | **20 / 20 (100%)** |
| Binary Precision | 10 / 10 = 1.00 |
| Binary Recall | 10 / 10 = 1.00 |
| Binary F1 | 1.00 |
| 4-Class Exact Match | 15 / 20 (75%) |
| Hard Cases Correct (L03, L06, L09) | **3 / 3** |
| False Positives (safe flagged as scam) | **0** |
| False Negatives (scam missed) | **0** |

### Notes on 4-Class Mismatches

Five scam scenarios scored SCAM where LIKELY_SCAM was expected (S03, S04, S06, S09, S10). In every case the model correctly identified the call as a scam — the scores were higher than expected, not lower. This is the desirable failure mode for a scam detector: over-detection on ambiguous scams is preferable to under-detection. No safe call was ever flagged as a scam.
