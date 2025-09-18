import json
import collections
from pathlib import Path

IN_PATH = Path("results/gsm8k_verifications.jsonl")

def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing {IN_PATH}. Run verify_answers.py first.")

    totals = collections.Counter()
    caught = collections.Counter()
    wrong_predictions = collections.Counter()

    with IN_PATH.open() as fin:
        for line in fin:
            rec = json.loads(line)
            et = rec.get("error_type", "unknown")
            verdict = rec.get("verdict")
            ref = rec.get("reference_answer")
            cand = rec.get("corrupted_answer")

            # ground truth: these injected items are always wrong
            gt_wrong = True

            totals[et] += 1
            if verdict == "incorrect":
                caught[et] += 1
            else:
                wrong_predictions[et] += 1

    print(f"Metrics from {IN_PATH}\n")
    print(f"{'ErrorType':14s} | {'Total':^5s} | {'Caught':^6s} | {'MissRate(FNR)':^12s}")
    print("-"*45)
    for et in totals:
        t = totals[et]
        c = caught[et]
        fnr = 1 - (c / t)
        print(f"{et:14s} | {t:^5d} | {c:^6d} | {fnr:^12.2f}")

if __name__ == "__main__":
    main()
