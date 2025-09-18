import os, re, json, math, collections
from pathlib import Path
import requests

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
URL   = "https://api.together.xyz/v1/chat/completions"
MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"  # serverless

IN_PATH  = Path("results/gsm8k_injected.jsonl")       # from inject_errors.py
OUT_PATH = Path("results/gsm8k_verifications.jsonl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

def as_num(s):
    if s is None: return None
    m = re.findall(r"-?\d+(?:\.\d+)?", str(s))
    return float(m[-1]) if m else None

def llm_verify(question, candidate_answer, reference_answer):
    """Ask the model to judge correctness. Return ('correct'|'incorrect', confidence_float)."""
    sys = (
        "You are a strict math verifier. "
        "Decide if the candidate answer matches the correct final answer. "
        "Output exactly one line in the form: Verdict: <correct|incorrect>; Confidence: <0.0-1.0>."
    )
    user = f"""Question: {question}

Reference (ground truth) final answer: {reference_answer}
Candidate answer to verify: {candidate_answer}

Decide if the candidate equals the reference (numerically)."""
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": sys},
            {"role": "user", "content": user}
        ],
        "max_tokens": 64,
        "temperature": 0
    }
    r = requests.post(URL, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"]
    # Parse: Verdict: incorrect; Confidence: 0.87
    verdict = "unknown"; conf = 0.5
    v = re.search(r"Verdict:\s*(correct|incorrect)", txt, re.I)
    c = re.search(r"Confidence:\s*([01](?:\.\d+)?)", txt)
    if v: verdict = v.group(1).lower()
    if c:
        try: conf = float(c.group(1))
        except: pass
    return verdict, conf, txt

def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing {IN_PATH}. Run inject_errors.py first.")
    totals = collections.Counter()
    caught  = collections.Counter()

    with IN_PATH.open() as fin, OUT_PATH.open("w") as fout:
        for line in fin:
            rec = json.loads(line)
            q    = rec["question"]
            ref  = rec["reference_answer"]
            cand = rec["corrupted_answer"]
            et   = rec["error_type"]

            # ground truth correctness by numeric compare
            ref_n  = as_num(ref)
            cand_n = as_num(cand)
            gt_correct = (ref_n is not None and cand_n is not None and math.isclose(ref_n, cand_n, rel_tol=1e-9, abs_tol=1e-9))

            verdict, conf, raw = llm_verify(q, cand, ref)
            predicted_incorrect = (verdict == "incorrect")

            totals[et] += 1
            if (not gt_correct) and predicted_incorrect:
                caught[et] += 1

            out = {
                **rec,
                "verdict": verdict,
                "confidence": conf,
                "raw_model_output": raw
            }
            fout.write(json.dumps(out) + "\n")

    print(f"Saved verifications to {OUT_PATH}\n")
    # Quick micro-metrics per error type
    for et in totals:
        c = caught[et]
        t = totals[et]
        fnr = 1 - (c / t)  # miss rate on actually-wrong items
        print(f"{et:14s}  caught: {c:>2}/{t:<2}  miss_rate(FNR): {fnr:.2f}")

if __name__ == "__main__":
    main()
