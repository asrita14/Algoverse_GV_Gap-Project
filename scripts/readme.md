# scripts/ — Pipeline overview (Asrita GV-Gap)

This folder contains small, script-only pieces that form a repeatable pipeline:

data/processed/<dataset>/<split>.jsonl
└─ generate_cot.py → results/<dataset>/<model>/<split>/01_gen.jsonl
(model’s answer + brief chain-of-thought, latency, token usage)
└─ run_verifier.py → .../02_verify.jsonl
(judge verdict: {"label":"accept|reject","confidence":0.xx,"rationale":"..."})
└─ compute_metrics.py → .../03_metrics.csv (+ 03_summary.txt)
(Generation acc, Verifier acc, GV-Gap = Verifier − Generation)


## Input data contract (for all scripts)

Each line in `data/processed/<dataset>/<split>.jsonl` is one example:

- `id` (string) — e.g., `"gsm8k/pilot/3146"`
- `domain` (string) — `"math" | "code" | "factual"`
- `dataset` (string) — e.g., `"GSM8K" | "MBPP" | "TruthfulQA"`
- `split` (string) — `"pilot" | "dev" | "main"`
- `question` (string)
- `reference_answer` (string)
- `gold_cot` (string or null; optional worked solution if available)

**Example line**
```json
{"id":"gsm8k/pilot/3146","domain":"math","dataset":"GSM8K","split":"pilot","question":"George and Harry ...","reference_answer":"22","gold_cot":"..."}
Files in this folder
prepare_datasets.py ✅
Make unified JSONL splits from public benchmarks.
CLI
python scripts/prepare_datasets.py --dataset gsm8k --split pilot --n 200 --out data/processed/gsm8k/pilot.jsonl
generate_cot.py ✅
Call a provider model (OpenAI/Together) to solve each question with a short chain-of-thought; extract a single-line Final: <answer>.
Inputs
--in processed JSONL
--out results/<dataset>/<model>/<split>/01_gen.jsonl
--provider openai | together
--model model id (e.g., gpt-4o-mini, or meta-llama/Meta-Llama-3-8B-Instruct)
Output (per line) adds:
"gen": {
  "cot": "...steps... Final: 22",
  "answer": "22",
  "latency_s": 0.73,
  "tokens_in": 123,
  "tokens_out": 45
}
run_verifier.py ✅
Ask a judge model to accept/reject each generated final answer with a strict JSON response.
Inputs
--in 01_gen.jsonl
--out 02_verify.jsonl
--ref processed JSONL (for metrics later)
--provider openai | together
--model judge model id
Output (per line) adds:
"verify": {
  "label": "accept",
  "confidence": 0.83,
  "rationale": "...",
  "latency_s": 0.51
}
compute_metrics.py ✅ / (planned)
Compute Generation accuracy, Verifier accuracy, and GV-Gap (= Verifier − Generation).
Writes a CSV and prints the 3 headline numbers (tee to 03_summary.txt).
CLI
python scripts/compute_metrics.py \
  --in  results/<dataset>/<model>/<split>/02_verify.jsonl \
  --ref data/processed/<dataset>/<split>.jsonl \
  --out results/<dataset>/<model>/<split>/03_metrics.csv | tee results/<dataset>/<model>/<split>/03_summary.txt
Environment & models
Put keys in a local .env at repo root (not committed):
OPENAI_API_KEY=...
TOGETHER_API_KEY=...
PROVIDER=openai
MODEL_SMALL=gpt-4o-mini
MODEL_LARGE=gpt-4o
Choose provider/model per run with CLI flags.
Results are organized by benchmark / model / split:
results/<dataset>/<model>/<split>/{01_gen.jsonl,02_verify.jsonl,03_metrics.csv,03_summary.txt}
Note: Together model ids often include slashes. For folder names, replace / with _ when creating results/<dataset>/<model>/....
