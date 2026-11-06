"""
Reads logs/attack_log.csv, sends each prompt to the running target app,
and writes results (response + timestamp) back to a results file.

This lets you re-run the exact same attack set before and after hardening
and diff the two result files for your before/after comparison.

Usage:
    python app/run_attacks.py --out logs/results_unhardened.csv
    # flip HARDENED = True in main.py, restart server, then:
    python app/run_attacks.py --out logs/results_hardened.csv
"""

import argparse
import csv
import datetime
import requests

from detection import detect_leak, REQUIRES_MANUAL_REVIEW

API_URL = "http://127.0.0.1:8000/chat"


def run(input_csv: str, output_csv: str):
    rows = []
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompt = row["prompt"]
            if not prompt.strip():
                continue
            try:
                resp = requests.post(API_URL, json={"message": prompt}, timeout=30)
                reply = resp.json().get("reply", "")
            except Exception as e:
                reply = f"ERROR: {e}"

            succeeded, how = detect_leak(reply)
            needs_review = row.get("technique", "") in REQUIRES_MANUAL_REVIEW

            row["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            row["response"] = reply
            row["succeeded"] = succeeded
            row["detection_method"] = how
            row["needs_manual_review"] = needs_review
            rows.append(row)

            flag = " [NEEDS MANUAL REVIEW]" if needs_review else ""
            print(f"[{row['category']}] succeeded={succeeded} ({how}){flag} -> {reply[:80]}")

    fieldnames = [
        "timestamp", "category", "technique", "prompt", "response",
        "succeeded", "detection_method", "needs_manual_review", "notes",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Results written to {output_csv}")
    print("Reminder: rows marked needs_manual_review=True were NOT reliably")
    print("auto-scored -- read those responses yourself before trusting the count.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="logs/attack_log.csv")
    parser.add_argument("--out", default="logs/results.csv")
    args = parser.parse_args()
    run(args.input, args.out)