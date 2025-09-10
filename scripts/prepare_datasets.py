import json
import requests
import random
from pathlib import Path

def download_gsm8k_sample():
    """Download a small sample of GSM8K for testing"""
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    print("Downloading GSM8K sample...")

    sample_problems = [
        {
            "question": "Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?",
            "answer": "Natalia sold 48/2 = 24 clips in May.\nNatalia sold 48+24 = 72 clips altogether in April and May.\n#### 72"
        },
        {
            "question": "Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of babysitting. How much did she earn?",
            "answer": "Weng earns 12/60 = $0.2 per minute.\nWorking 50 minutes, she earned 0.2 x 50 = $10.\n#### 10"
        },
        {
            "question": "Betty is saving money for a new wallet which costs $100. Betty has only half of the money she needs. Her parents decided to give her $15 for that purpose, and her grandparents twice as much as her parents. How much more money does Betty need to buy the wallet?",
            "answer": "In the beginning, Betty has only 100/2 = $50.\nBetty's grandparents gave her 15 * 2 = $30.\nThis means, Betty needs 100 - 50 - 15 - 30 = $5 more.\n#### 5"
        }
    ]

    with open("data/raw/gsm8k_sample.json", "w") as f:
        json.dump(sample_problems, f, indent=2)

    print(f"Downloaded {len(sample_problems)} sample problems to data/raw/gsm8k_sample.json")
    return sample_problems

def convert_to_standard_format(problems, dataset_name="GSM8K", split="pilot"):
    """Convert to the standard JSONL format from your roadmap"""
    Path("data/processed/gsm8k").mkdir(parents=True, exist_ok=True)
    converted = []

    for i, problem in enumerate(problems):
        answer_text = problem["answer"]
        if "####" in answer_text:
            final_answer = answer_text.split("####")[-1].strip()
        else:
            final_answer = "Unknown"

        record = {
            "id": f"gsm8k/{split}/{i}",
            "domain": "math",
            "dataset": dataset_name,
            "split": split,
            "question": problem["question"],
            "reference_answer": final_answer,
            "gold_cot": answer_text.split("####")[0].strip() if "####" in answer_text else answer_text,
            "metadata": {"source": "sample", "difficulty": "easy"}
        }
        converted.append(record)

    output_file = f"data/processed/gsm8k/{split}.jsonl"
    with open(output_file, "w") as f:
        for record in converted:
            f.write(json.dumps(record) + "\n")

    print(f"Converted {len(converted)} problems to {output_file}")
    return converted

if __name__ == "__main__":
    problems = download_gsm8k_sample()
    converted = convert_to_standard_format(problems)
    print("\nFirst converted record:")
    print(json.dumps(converted[0], indent=2))
