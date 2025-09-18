# GV-Gap Project Pipeline Guide

## What This Project Does

This project studies how well AI models can **check their own work**. We measure the **Generation-Verification Gap (GV-Gap)**:

- **Generation**: How often does the AI get questions right?
- **Verification**: How often does the AI correctly identify right/wrong answers?
- **GV-Gap**: The difference between these two (Verification - Generation)

## Quick Start

1. **Set up your environment**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Create .env file with your API keys
   echo "OPENAI_API_KEY=your_key_here" > .env
   echo "TOGETHER_API_KEY=your_key_here" >> .env
   ```

2. **Run the complete pipeline**:
   ```bash
   # See example commands
   python scripts/run_example_pipeline.py
   
   # Or run manually (example for GSM8K with 5 samples):
   python scripts/generate_cot.py --in data/processed/gsm8k/pilot.jsonl --out results/gsm8k/gpt-4o-mini/pilot/01_gen.jsonl --provider openai --model gpt-4o-mini --n_samples 5
   
   python scripts/run_verifier.py --in results/gsm8k/gpt-4o-mini/pilot/01_gen.jsonl --out results/gsm8k/gpt-4o-mini/pilot/02_verify.jsonl --ref data/processed/gsm8k/pilot.jsonl --provider openai --model gpt-4o-mini
   
   python scripts/tag_errors.py --in results/gsm8k/gpt-4o-mini/pilot/02_verify.jsonl --out results/gsm8k/gpt-4o-mini/pilot/02_tagged.jsonl
   
   python scripts/compute_gv_gap.py --in results/gsm8k/gpt-4o-mini/pilot/02_verify.jsonl --ref data/processed/gsm8k/pilot.jsonl --out results/gsm8k/gpt-4o-mini/pilot/03_metrics.csv --summary results/gsm8k/gpt-4o-mini/pilot/03_summary.txt
   
   python scripts/update_taxonomy.py
   ```

## What Each Script Does

### 1. `generate_cot.py` - Generate AI Answers
- **Input**: Questions from `data/processed/<dataset>/<split>.jsonl`
- **Output**: AI's reasoning + answers in `results/<dataset>/<model>/<split>/01_gen.jsonl`
- **New**: Can generate multiple samples per question (`--n_samples 5`)

### 2. `run_verifier.py` - Verify AI Answers  
- **Input**: Generated answers from step 1
- **Output**: Judge's verdict (accept/reject) + confidence + explanation
- **New**: Handles multiple candidates per question

### 3. `tag_errors.py` - Categorize Errors
- **Input**: Verified answers from step 2
- **Output**: Error categories (math errors, code bugs, etc.)
- **Categories**: Based on taxonomies from recent research papers

### 4. `compute_gv_gap.py` - Calculate Metrics
- **Input**: Verified answers + reference answers
- **Output**: Generation accuracy, Verification accuracy, GV-Gap
- **New**: Detailed analysis of verification patterns

### 5. `update_taxonomy.py` - Update Summary Table
- **Input**: Tagged errors from step 3
- **Output**: Updates the table in `taxonomy.md`
- **Fixed**: Now works with the correct field names

## File Structure

```
data/processed/           # Input questions and correct answers
├── gsm8k/
│   ├── pilot.jsonl      # Math problems
│   └── val.jsonl
├── mbpp/
│   ├── pilot.jsonl      # Code problems  
│   └── val.jsonl
└── truthfulqa/
    ├── pilot.jsonl      # Factual questions
    └── val.jsonl

results/                  # Output files (created when you run scripts)
├── <dataset>/
│   └── <model>/
│       └── <split>/
│           ├── 01_gen.jsonl      # Generated answers
│           ├── 02_verify.jsonl   # Verification results
│           ├── 02_tagged.jsonl   # Error categories
│           ├── 03_metrics.csv    # Detailed metrics
│           └── 03_summary.txt    # Summary report
```

## Understanding the Results

### GV-Gap Interpretation
- **Positive GV-Gap**: Verifier is better than generator (good self-verification)
- **Negative GV-Gap**: Generator is better than verifier (poor self-verification)  
- **Zero GV-Gap**: Generator and verifier perform equally

### Example Output
```
Generation Accuracy: 0.750 (75/100)
Verification Accuracy: 0.820 (82/100)  
GV-Gap: 0.070
✓ Positive GV-Gap: Verifier outperforms generator (good self-verification)
```

## Error Categories

The project uses taxonomies from recent research:

### Math (GSM8K)
- `calc_error`: Calculation mistakes
- `reasoning_gap`: Wrong logic steps
- `format_mismatch`: Wrong answer format
- `instruction_miss`: Solved wrong problem

### Code (MBPP)  
- `syntax_error`: Code doesn't run
- `logic_bug`: Runs but wrong output
- `edge_case_fail`: Breaks on special inputs
- `spec_misread`: Misunderstood requirements

### Facts (TruthfulQA)
- `factual_hallucination`: Confidently false claims
- `misleading_generalization`: Partly true but misleading
- `ambiguous_misread`: Misunderstood question
- `hedged_nonanswer`: Vague instead of factual

## Troubleshooting

### Common Issues
1. **Missing .env file**: Create it with your API keys
2. **Missing input data**: Run `prepare_datasets.py` first
3. **API errors**: Check your API keys and rate limits
4. **File not found**: Make sure you're in the project root directory

### Getting Help
- Check the comments in each script - they explain what each part does
- Run `python scripts/run_example_pipeline.py` to see example commands
- Look at the output files to understand the data format

## Next Steps

1. **Run on your data**: Use the pipeline with your own questions
2. **Experiment with models**: Try different AI models and compare results
3. **Analyze patterns**: Look at which types of errors are most common
4. **Improve verification**: Use the insights to build better self-verification systems
