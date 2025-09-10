#!/usr/bin/env python3
import pandas as pd
import subprocess

# Fixed columns
cols = ["calc_error", "format_mismatch", "hedged_nonanswer",
        "instruction_miss", "logic_bug", "spec_misread"]

# Hardcode dataset → file mapping
datasets = {
    "GSM8K": "results/gsm8k_tagged_val.jsonl",
    "MBPP": "results/mbpp_tagged_val.jsonl",
    "TruthfulQA": "results/truthfulqa_tagged_val.jsonl",
}

rows = []
for ds, file in datasets.items():
    out = subprocess.check_output(
        ["jq", "-r", 'select(.label=="reject") | .taxonomy_error', file]
    ).decode().splitlines()

    counts = {c: 0 for c in cols}
    for x in out:
        if x in counts:
            counts[x] += 1

    row = [ds] + [counts[c] for c in cols]
    rows.append(row)

df = pd.DataFrame(rows, columns=["Dataset"] + cols)
print(df.to_markdown(index=False))

