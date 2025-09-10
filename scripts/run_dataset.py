import os, json, time, argparse
from pathlib import Path
import requests

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
URL = "https://api.together.xyz/v1/chat/completions"
MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"  # serverless

def ask_model(question: str) -> str:
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a careful reasoning assistant. Answer concisely."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 256,
        "temperature": 0
    }
    r = requests.post(URL, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    j = r.json()
    return j["choices"][0]["message"]["content"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("dataset", choices=["gsm8k","mbpp","truthfulqa"])
    p.add_argument("--limit", type=int, default=5)
    args = p.parse_args()

    in_path  = Path(f"data/processed/{args.dataset}/pilot.jsonl")
    out_path = Path(f"results/{args.dataset}_outputs.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        raise FileNotFoundError(f"Missing {in_path}")

    print(f"Reading from {in_path} → writing to {out_path}")
    n = 0
    with in_path.open() as fin, out_path.open("w") as fout:
        for line in fin:
            rec = json.loads(line)
            q = rec.get("question") or rec.get("prompt") or rec.get("input")
            rid = rec.get("id", f"{args.dataset}/{n}")

            try:
                ans = ask_model(q)
            except Exception as e:
                ans = f"[ERROR] {type(e).__name__}: {e}"

            out = {
                "id": rid,
                "dataset": args.dataset,
                "question": q,
                "reference_answer": rec.get("reference_answer") or rec.get("target") or rec.get("label"),
                "model_answer": ans,
                "meta": {"model": MODEL}
            }
            fout.write(json.dumps(out) + "\n")
            n += 1
            print(f"[{n}] {rid} ✓")
            if n >= args.limit:
                break
            time.sleep(0.2)

    print(f"\nSaved {n} outputs to {out_path}")

if __name__ == "__main__":
    main()
