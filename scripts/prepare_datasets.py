#!/usr/bin/env python3
import argparse, json, os, random, re
from pathlib import Path
from typing import Iterable, Dict, Any
from datasets import load_dataset

RNG = random.Random()
GSM_FINAL_RE = re.compile(r"####\s*([^\n]+)")

def norm(s: str) -> str: return " ".join((s or "").strip().split())

def sample_indices(n_total: int, n_want: int, seed: int):
    idxs = list(range(n_total)); RNG.seed(seed); RNG.shuffle(idxs)
    return idxs[:min(n_want, n_total)]

def iter_gsm8k(split: str, n: int, seed: int) -> Iterable[Dict[str, Any]]:
    ds = load_dataset("gsm8k", "main", split="train" if split!="test" else "test")
    for i in sample_indices(len(ds), n, seed):
        ex = ds[i]; q = norm(ex["question"]); raw = ex["answer"] or ""
        m = GSM_FINAL_RE.search(raw); final = m.group(1).strip() if m else raw.strip()
        yield {"id": f"gsm8k/{split}/{i}","domain":"math","dataset":"GSM8K","split":split,
               "question": q,"reference_answer": final,"gold_cot": raw}

def iter_mbpp(split: str, n: int, seed: int):
    ds = load_dataset("mbpp", split="train")
    for i in sample_indices(len(ds), n, seed):
        ex = ds[i]; q = norm(ex.get("text", ex.get("prompt",""))); code = ex.get("code","")
        yield {"id": f"mbpp/{split}/{i}","domain":"code","dataset":"MBPP","split":split,
               "question": q,"reference_answer": code,"gold_cot": None}

def iter_truthfulqa(split: str, n: int, seed: int):
    ds = load_dataset("truthful_qa", "generation", split="validation")
    for i in sample_indices(len(ds), n, seed):
        ex = ds[i]; q = norm(ex["question"])
        best = ex.get("best_answer") or (ex.get("correct_answers") or [""])[0]
        yield {"id": f"truthfulqa/{split}/{i}","domain":"factual","dataset":"TruthfulQA","split":split,
               "question": q,"reference_answer": norm(best),"gold_cot": None}

LOADERS = {"gsm8k":iter_gsm8k,"mbpp":iter_mbpp,"truthfulqa":iter_truthfulqa}
REQ = ["id","domain","dataset","split","question","reference_answer"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=LOADERS.keys())
    ap.add_argument("--split", required=True, help="pilot|dev|main")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    Path(os.path.dirname(args.out)).mkdir(parents=True, exist_ok=True)
    it = LOADERS[args.dataset](args.split, args.n, args.seed)

    n_written = 0
    with open(args.out, "w", encoding="utf-8") as f:
        for rec in it:
            for k in REQ:
                if k not in rec: raise ValueError(f"missing key {k} in {rec}")
            f.write(json.dumps(rec, ensure_ascii=False)+"\n"); n_written += 1
    print(f"Wrote {n_written} → {args.out}")

if __name__ == "__main__": main()
