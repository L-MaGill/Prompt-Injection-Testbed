"""
Reads logs/multi_turn_conversations.json and plays each conversation
turn by turn against the running target app, carrying the real
conversation history forward exactly as a live user session would.

Unlike run_attacks.py (one isolated prompt per row), this is what
actually tests "gradual erosion" -- each turn sees everything the bot
said in prior turns, so trust-building/reframing across turns can have
a real effect on the model's behavior.

Usage:
    python app/run_multi_turn_attacks.py --out logs/results_multiturn_unhardened.csv
    # flip HARDENED = True in main.py, restart server, then:
    python app/run_multi_turn_attacks.py --out logs/results_multiturn_hardened.csv
"""

import argparse
import csv
import datetime
import json
import requests

from detection import detect_leak, REQUIRES_MANUAL_REVIEW

API_URL = "http://127.0.0.1:8000/chat"


def run(input_json: str, output_csv: str):
    with open(input_json, encoding="utf-8") as f:
        conversations = json.load(f)

    rows = []
    for convo in conversations:
        history = []  # reset for each new conversation -- these are independent sessions
        needs_review = convo.get("technique", "") in REQUIRES_MANUAL_REVIEW

        for turn_number, prompt in enumerate(convo["turns"], start=1):
            try:
                resp = requests.post(
                    API_URL,
                    json={"message": prompt, "history": history},
                    timeout=30,
                )
                data = resp.json()
                reply = data.get("reply", "")
                history = data.get("history", history)  # carry forward for the next turn
            except Exception as e:
                reply = f"ERROR: {e}"

            succeeded, how = detect_leak(reply)

            row = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "conversation_id": convo["conversation_id"],
                "category": convo.get("category", ""),
                "technique": convo.get("technique", ""),
                "turn_number": turn_number,
                "prompt": prompt,
                "response": reply,
                "succeeded": succeeded,
                "detection_method": how,
                "needs_manual_review": needs_review,
                "notes": convo.get("notes", ""),
            }
            rows.append(row)

            flag = " [NEEDS MANUAL REVIEW]" if needs_review else ""
            print(
                f"[{row['conversation_id']} turn {turn_number}] "
                f"succeeded={succeeded} ({how}){flag} -> {reply[:80]}"
            )

            # Once a leak succeeds, later turns in the same conversation are
            # still worth logging (e.g. does the model keep leaking, or
            # backpedal?) so we deliberately do NOT break out of the loop here.

    fieldnames = [
        "timestamp", "conversation_id", "category", "technique", "turn_number",
        "prompt", "response", "succeeded", "detection_method",
        "needs_manual_review", "notes",
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
    parser.add_argument("--input", default="logs/multi_turn_conversations.json")
    parser.add_argument("--out", default="logs/results_multiturn.csv")
    args = parser.parse_args()
    run(args.input, args.out)