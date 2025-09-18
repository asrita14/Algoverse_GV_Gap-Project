#!/usr/bin/env python3
"""
run_example_pipeline.py - Example script showing how to run the complete pipeline

WHAT THIS SCRIPT DOES:
Shows you exactly how to run the complete pipeline from start to finish.
This is a template - you can copy these commands and run them manually.

PIPELINE STEPS:
1. Generate 5 CoT samples per question
2. Verify each answer using a judge model
3. Tag errors with taxonomy categories
4. Calculate GV-Gap metrics
5. Update taxonomy summary table
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print what it does"""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"COMMAND: {cmd}")
    print('='*60)
    
    # Uncomment the next line to actually run the command
    # subprocess.run(cmd, shell=True, check=True)
    print("(Command not executed - uncomment subprocess.run to execute)")

def main():
    print("GV-GAP PROJECT PIPELINE EXAMPLE")
    print("="*60)
    print("This script shows you the exact commands to run the complete pipeline.")
    print("Copy these commands and run them in your terminal.")
    
    # Configuration - CHANGE THESE TO MATCH YOUR SETUP
    DATASET = "gsm8k"  # or "mbpp" or "truthfulqa"
    SPLIT = "pilot"    # or "val"
    MODEL = "gpt-4o-mini"  # or "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    PROVIDER = "openai"  # or "together"
    N_SAMPLES = 5  # Number of samples per question
    
    # Create safe model name for file paths (replace / with _)
    MODEL_SAFE = MODEL.replace("/", "_")
    
    # File paths
    INPUT_FILE = f"data/processed/{DATASET}/{SPLIT}.jsonl"
    GEN_OUTPUT = f"results/{DATASET}/{MODEL_SAFE}/{SPLIT}/01_gen.jsonl"
    VERIFY_OUTPUT = f"results/{DATASET}/{MODEL_SAFE}/{SPLIT}/02_verify.jsonl"
    TAGGED_OUTPUT = f"results/{DATASET}/{MODEL_SAFE}/{SPLIT}/02_tagged.jsonl"
    METRICS_OUTPUT = f"results/{DATASET}/{MODEL_SAFE}/{SPLIT}/03_metrics.csv"
    SUMMARY_OUTPUT = f"results/{DATASET}/{MODEL_SAFE}/{SPLIT}/03_summary.txt"
    
    print(f"\nConfiguration:")
    print(f"  Dataset: {DATASET}")
    print(f"  Split: {SPLIT}")
    print(f"  Model: {MODEL}")
    print(f"  Provider: {PROVIDER}")
    print(f"  Samples per question: {N_SAMPLES}")
    
    # Step 1: Generate Chain of Thought answers
    cmd1 = f"""python scripts/generate_cot.py \\
    --in {INPUT_FILE} \\
    --out {GEN_OUTPUT} \\
    --provider {PROVIDER} \\
    --model {MODEL} \\
    --n_samples {N_SAMPLES}"""
    
    run_command(cmd1, "Generate 5 CoT samples per question")
    
    # Step 2: Verify the answers
    cmd2 = f"""python scripts/run_verifier.py \\
    --in {GEN_OUTPUT} \\
    --out {VERIFY_OUTPUT} \\
    --ref {INPUT_FILE} \\
    --provider {PROVIDER} \\
    --model {MODEL}"""
    
    run_command(cmd2, "Verify each answer using judge model")
    
    # Step 3: Tag errors with taxonomy
    cmd3 = f"""python scripts/tag_errors.py \\
    --in {VERIFY_OUTPUT} \\
    --out {TAGGED_OUTPUT}"""
    
    run_command(cmd3, "Tag errors with taxonomy categories")
    
    # Step 4: Calculate GV-Gap metrics
    cmd4 = f"""python scripts/compute_gv_gap.py \\
    --in {VERIFY_OUTPUT} \\
    --ref {INPUT_FILE} \\
    --out {METRICS_OUTPUT} \\
    --summary {SUMMARY_OUTPUT}"""
    
    run_command(cmd4, "Calculate Generation-Verification Gap metrics")
    
    # Step 5: Update taxonomy summary table
    cmd5 = "python scripts/update_taxonomy.py"
    
    run_command(cmd5, "Update taxonomy summary table in taxonomy.md")
    
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE!")
    print('='*60)
    print(f"Results saved to: results/{DATASET}/{MODEL_SAFE}/{SPLIT}/")
    print(f"Check {SUMMARY_OUTPUT} for GV-Gap summary")
    print(f"Check {METRICS_OUTPUT} for detailed results")
    print(f"Check taxonomy.md for updated error counts")
    
    print(f"\nTo run this pipeline:")
    print(f"1. Make sure you have a .env file with your API keys")
    print(f"2. Make sure {INPUT_FILE} exists")
    print(f"3. Copy and run each command above in your terminal")
    print(f"4. Or uncomment the subprocess.run lines in this script")

if __name__ == "__main__":
    main()
