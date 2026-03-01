#!/usr/bin/env python3
"""
CallShield Evaluation Runner
============================
Runs the full 20-scenario evaluation suite against the CallShield transcript API
and prints a results table + metrics that match docs/EVALUATION.md Section 9.

Usage:
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --url https://callshield.onrender.com
    python scripts/run_evaluation.py --url http://localhost:8000 --api-key MY_KEY
    python scripts/run_evaluation.py --delay 0.5   # seconds between requests

Exit code: 0 if binary accuracy is 100%, 1 otherwise.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Evaluation scenarios — mirrors docs/EVALUATION.md sections 2 and 3
# ---------------------------------------------------------------------------
SCENARIOS = [
    # (id, category, expected_verdict, transcript)
    ("S01", "IRS Arrest Threat", "SCAM",
     "This is Officer Daniel Reynolds with the Internal Revenue Service Criminal Division. "
     "We have filed a lawsuit against you for tax fraud totaling fourteen thousand six hundred dollars. "
     "If you do not settle this matter immediately by purchasing retail gift cards, a warrant will be "
     "issued for your arrest within the next forty-five minutes."),

    ("S02", "Tech Support Virus Alert", "SCAM",
     "Hello, this is the Windows Security Center. We have detected that your computer is sending out "
     "virus signals and your personal banking credentials have been compromised. I need you to go to "
     "your computer right now and download our secure remote access tool so our certified technician "
     "can remove the threat before your files are permanently deleted."),

    ("S03", "Medicare Robocall", "LIKELY_SCAM",
     "Attention Medicare recipients. Due to recent changes in federal healthcare policy, you may be "
     "eligible for additional benefits at no cost to you. Your current Medicare plan could be upgraded "
     "immediately. Press 1 now to speak with a licensed enrollment specialist, or press 2 to be removed "
     "from our list. This is a time-sensitive offer and your benefits window closes at the end of this week."),

    ("S04", "Auto Warranty Robocall", "LIKELY_SCAM",
     "We are calling regarding your vehicle extended warranty, which is about to expire. This is your "
     "final notice. Once your coverage lapses, you will be responsible for all repair costs out of pocket. "
     "Press 1 to speak with a representative and renew your protection plan today before it is too late."),

    ("S05", "Grandparent Scam", "SCAM",
     "Grandma? It is me, please do not hang up. I got into a car accident and they arrested me. I am "
     "calling from the county jail. My lawyer says I need thirty-five hundred dollars for bail posted by "
     "tonight or I will be transferred to state lockup. Please do not tell Mom and Dad, I am so embarrassed. "
     "Can you wire the money through Western Union right now?"),

    ("S06", "Romance Scam", "LIKELY_SCAM",
     "Baby, I know we have not met in person yet, but you mean everything to me. I am stuck at this job "
     "site overseas and my wallet was stolen. I cannot even afford a flight home. If you could just send "
     "two thousand dollars through a wire transfer, I will pay you back the moment I land. I have never "
     "asked anyone for help like this, but I trust you with my life."),

    ("S07", "Fake Bank Fraud Dept", "SCAM",
     "Good afternoon, this is the fraud prevention department at First National Bank. We have flagged a "
     "suspicious purchase of eight hundred and twelve dollars on your debit card at an electronics store "
     "in another state. To verify your identity and block further transactions, I will need you to confirm "
     "your full sixteen-digit card number, the expiration date, and the three-digit security code on the back."),

    ("S08", "Lottery Winner", "SCAM",
     "Congratulations! You have been selected as the grand prize winner of the International Mega Lottery, "
     "and your winnings total two point five million dollars. To process your claim, we require a one-time "
     "tax and processing fee of four hundred and ninety-nine dollars, payable by prepaid debit card or "
     "cryptocurrency. We will also need your full name, date of birth, and bank routing number to deposit "
     "your winnings."),

    ("S09", "Debt Threats Arrest", "LIKELY_SCAM",
     "This message is for the individual residing at your address. You are being notified of a legal action "
     "filed against you for an outstanding debt of six thousand two hundred dollars. If payment is not "
     "received by five PM today, we will proceed with wage garnishment and a deputy will be dispatched to "
     "serve you at your home or place of employment."),

    ("S10", "Crypto Guaranteed Returns", "LIKELY_SCAM",
     "Hi there, I was given your number by a mutual friend. I have been making incredible returns with a "
     "new AI-powered crypto trading platform. We are talking three hundred percent gains in just six weeks, "
     "completely guaranteed. They only have fifty spots left in the current investment round, so if you want "
     "in, you need to deposit at least five thousand dollars in Bitcoin by midnight tonight."),

    ("L01", "Friend Call", "SAFE",
     "Hey, it is Sarah! I just wanted to check in. I have not heard from you in ages. How is the new job "
     "going? We should grab coffee sometime this week if you are free. Let me know what works for you."),

    ("L02", "Meeting Scheduling", "SAFE",
     "Hi, this is Karen from the marketing team. I wanted to see if you are available Thursday at two PM "
     "for the quarterly review. We will be going over the campaign metrics in conference room B. Let me "
     "know if that time works or if we need to reschedule."),

    ("L03", "Doctor Reminder IVR", "SAFE",
     "This is an automated reminder from Riverside Family Medical Center. You have an appointment scheduled "
     "with Doctor Patel on Wednesday, March fourth, at ten thirty AM. Press 1 to confirm your appointment, "
     "press 2 to reschedule, or press 3 to cancel. If you have questions, please call our office at "
     "555-0142 during business hours."),

    ("L04", "BBQ Invitation", "SAFE",
     "Hey! So Marcus and I are throwing a barbecue this Saturday afternoon around three. Nothing fancy, "
     "burgers, hot dogs, maybe some corn on the cob. Bring whoever you want. If you could grab a bag of "
     "ice on the way over, that would be awesome. Let me know if you can make it!"),

    ("L05", "Customer Service Callback", "SAFE",
     "Hi, this is James from Northstar Internet customer support. I am returning your call from earlier "
     "today about the intermittent connection drops you have been experiencing. I have reviewed your ticket, "
     "number 4417, and I would like to walk you through a few troubleshooting steps. Is now a good time "
     "to go over that?"),

    ("L06", "Angry Customer Complaint", "SAFE",
     "I have been waiting three weeks for my refund and nobody at your company will give me a straight "
     "answer. This is completely unacceptable. I paid four hundred dollars for a product that arrived "
     "broken, and I want my money back today. If this is not resolved by the end of this call, I am "
     "filing a complaint with the Better Business Bureau and leaving reviews everywhere."),

    ("L07", "Parent Dinner Plans", "SAFE",
     "Hi sweetheart, it is Mom. Dad and I were thinking about doing dinner at that Italian place on "
     "Franklin Street this Sunday, the one with the good pasta. Would six o clock work for you and the "
     "kids? Let us know so we can make a reservation."),

    ("L08", "Job Interview Scheduling", "SAFE",
     "Hello, this is David Chen from the talent acquisition team at Meridian Technologies. I am reaching "
     "out because we reviewed your application for the senior software engineer position and we would love "
     "to schedule a first-round interview. Are you available next Tuesday or Wednesday afternoon? We can "
     "do it over video call or in person at our downtown office."),

    ("L09", "Legit Bank Fraud Alert", "SAFE",
     "This is an automated security alert from First National Bank. We detected unusual activity on your "
     "account. A transaction of three hundred and twenty dollars at an online retailer was flagged. If you "
     "authorized this transaction, no action is needed. If you did not, please call the number on the back "
     "of your debit card or visit your nearest branch. Do not share your card number or PIN with anyone "
     "who calls you."),

    ("L10", "Friend Voicemail", "SAFE",
     "Hey, it is Mike. Just leaving a quick message. I finished that book you lent me and it was honestly "
     "so good. Anyway, I will swing by tomorrow to drop it off if you are around. Give me a call back when "
     "you get a chance. Talk to you later."),
]

SCAM_VERDICTS = {"SCAM", "LIKELY_SCAM", "SUSPICIOUS"}


def is_positive(verdict: str) -> bool:
    """Binary: any non-SAFE verdict counts as a scam detection."""
    return verdict != "SAFE"


def run(base_url: str, api_key: str, delay: float) -> List[Dict]:
    url = f"{base_url}/api/analyze/transcript?api_key={urllib.parse.quote(api_key)}"
    results = []

    for sid, category, expected, transcript in SCENARIOS:
        payload = json.dumps({"transcript": transcript}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
            analysis = data.get("text_analysis") or data.get("audio_analysis") or {}
            score = round(data.get("combined_score", 0.0), 2)
            verdict = analysis.get("verdict", "ERROR")
            error = None
        except urllib.error.HTTPError as e:
            score, verdict, error = None, "ERROR", f"HTTP {e.code}: {e.read()[:120]}"
        except Exception as e:
            score, verdict, error = None, "ERROR", str(e)

        binary_match = (is_positive(verdict) == is_positive(expected)) if verdict != "ERROR" else False
        exact_match = verdict == expected

        results.append({
            "id": sid,
            "category": category,
            "expected": expected,
            "score": score,
            "verdict": verdict,
            "binary_match": binary_match,
            "exact_match": exact_match,
            "error": error,
        })

        status = "OK  " if binary_match else "MISS"
        score_str = f"{score:.2f}" if score is not None else " ERR"
        print(f"{status} {sid:<4} | {score_str} | {verdict:<12} | expected {expected}")

        if delay > 0:
            time.sleep(delay)

    return results


def print_summary(results: List[Dict]) -> int:
    total = len(results)
    binary_correct = sum(1 for r in results if r["binary_match"])
    exact_correct = sum(1 for r in results if r["exact_match"])
    errors = [r for r in results if r["error"]]

    scam_results = [r for r in results if r["expected"] != "SAFE"]
    safe_results = [r for r in results if r["expected"] == "SAFE"]

    tp = sum(1 for r in scam_results if r["binary_match"])
    fn = len(scam_results) - tp
    tn = sum(1 for r in safe_results if r["binary_match"])
    fp = len(safe_results) - tn

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    hard_cases = ["L03", "L06", "L09"]
    hard_correct = sum(1 for r in results if r["id"] in hard_cases and r["binary_match"])

    print()
    print("=" * 60)
    print("RESULTS TABLE")
    print("=" * 60)
    print(f"{'ID':<4} {'Category':<26} {'Expected':<14} {'Score':>5} {'Actual':<14} {'Bin':>4} {'Exact':>5}")
    print("-" * 75)
    for r in results:
        score_str = f"{r['score']:.2f}" if r["score"] is not None else "  ERR"
        bin_mark   = "✓" if r["binary_match"] else "✗"
        exact_mark = "✓" if r["exact_match"]  else "✗"
        print(f"{r['id']:<4} {r['category']:<26} {r['expected']:<14} {score_str:>5} "
              f"{r['verdict']:<14} {bin_mark:>4} {exact_mark:>5}")

    print()
    print("=" * 60)
    print("METRICS")
    print("=" * 60)
    print(f"  Binary accuracy    : {binary_correct}/{total} = {binary_correct/total:.2%}")
    print(f"  Precision          : {tp}/{tp+fp} = {precision:.2f}")
    print(f"  Recall             : {tp}/{tp+fn} = {recall:.2f}")
    print(f"  Specificity        : {tn}/{tn+fp} = {specificity:.2f}")
    print(f"  F1 score           : {f1:.2f}")
    print(f"  4-class exact match: {exact_correct}/{total} = {exact_correct/total:.2%}")
    print(f"  Hard cases correct : {hard_correct}/3")
    print()
    print(f"  Confusion matrix (binary)")
    print(f"    TP={tp}  FN={fn}")
    print(f"    FP={fp}  TN={tn}")

    if errors:
        print()
        print(f"  ERRORS ({len(errors)}):")
        for r in errors:
            print(f"    {r['id']} — {r['error']}")

    return 0 if binary_correct == total else 1


def main() -> int:

    parser = argparse.ArgumentParser(description="CallShield evaluation runner")
    parser.add_argument("--url", default="http://localhost:8000",
                        help="Backend base URL (default: http://localhost:8000)")
    parser.add_argument("--api-key", default="", dest="api_key",
                        help="API key (leave empty when auth is disabled)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between requests (default: 1.0)")
    args = parser.parse_args()

    print(f"CallShield Evaluation — {args.url}")
    print(f"Running {len(SCENARIOS)} scenarios...\n")

    results = run(args.url, args.api_key, args.delay)
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
