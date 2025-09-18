import json, random, re, argparse
from pathlib import Path

def parse_number(s: str):
    m = list(re.finditer(r"-?\d+(?:\.\d+)?", s or ""))
    return float(m[-1].group()) if m else None

def inject_off_by_one(x: float):
    return x + (1 if random.random() < 0.5 else -1), "off_by_one"

def inject_sign_flip(x: float):
    return -x, "sign_flip"

def inject_small_perturb(x: float):
    delta = random.choice([2, -2, 3, -3])
    return x + delta, "small_perturb"

INJECTORS = [inject_off_by_one, inject_sign_flip, inject_small_perturb]

def format_answer(num):
    return str(int(num)) if float(num).is_integer() else str(num)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_path", default="data/processed/gsm8k/pilot.jsonl")
    p.add_argument("--out", dest="out_path", default="results/gsm8k_injected.jsonl")
    p.add_argument("--k", type=int, default=5, help="number of corrupted variants per problem")
    p.add_argument("--limit", type=int, default=1000, help="max problems to read")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)

    in_path  = Path(args.in_path)
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_prob = n_out = 0
    with in_path.open() as fin, out_path.open("w") as fout:
        for line in fin:
            rec = json.loads(line)
            rid = rec.get("id")
            q   = rec.get("question")
            ref = rec.get("reference_answer")
            y = parse_number(ref)
            if y is None:
                continue

            n_prob += 1
            for j in range(args.k):
                inj_fn = random.choice(INJECTORS)
                y_bad, etype = inj_fn(y)
                corr = format_answer(y_bad)
                out = {
                    "id": f"{rid}::v{j+1}",
                    "question": q,
                    "reference_answer": format_answer(y),
                    "corrupted_answer": corr,
                    "error_injected": 1,
                    "error_type": etype
                }
                fout.write(json.dumps(out) + "\n")
                n_out += 1

            if n_prob >= args.limit:
                break

    print(f"Read {n_prob} base problems from {in_path}")
    print(f"Wrote {n_out} corrupted items to {out_path}")

if __name__ == "__main__":
    main()
