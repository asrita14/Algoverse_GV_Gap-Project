#!/usr/bin/env python3
"""
generate_cot.py - Generates Chain of Thought (CoT) reasoning for questions

WHAT THIS SCRIPT DOES:
1. Reads questions from a JSONL file (like data/processed/gsm8k/pilot.jsonl)
2. For each question, asks an AI model to solve it step-by-step
3. Extracts the final answer from the AI's reasoning
4. Saves the results to a new JSONL file

NEW FEATURE: Can generate multiple samples (k=5) per question for better analysis
#him - MULTI-SAMPLE FEATURE: Line 11 - Added support for generating multiple CoT samples per question
"""
import os, time, json, argparse, re, requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables (API keys) from .env file
load_dotenv(find_dotenv(usecwd=True) or ".env")

# Regular expression to find "Final: <answer>" in AI responses
FINAL_RE = re.compile(r"Final:\s*(.+)")

def messages_for(q: str):
    """
    Creates the prompt messages to send to the AI model
    
    Args:
        q: The question to ask
        
    Returns:
        List of message dictionaries for the API call
    """
    sys = "You are a careful problem solver. Show steps briefly and end with 'Final: <answer>'."
    usr = f"Question: {q}\nSolve step by step. Conclude with 'Final: <answer>'."
    return [{"role":"system","content":sys},{"role":"user","content":usr}]

def call_openai(model, messages, n_samples=1):
    """
    Calls OpenAI API to get AI responses
    
    Args:
        model: Model name (e.g., "gpt-4o-mini")
        messages: List of message dictionaries
        n_samples: Number of different responses to generate
        
    Returns:
        List of (response_text, latency, usage_info) tuples
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    results = []
    for _ in range(n_samples):
        t0 = time.time()
        # For OpenAI, we can request multiple responses in one call if n_samples > 1
        if n_samples > 1:
            r = client.chat.completions.create(
                model=model, 
                messages=messages, 
                temperature=0.7,  # Add some randomness for diversity
                n=n_samples
            )
            # Process all responses
            for choice in r.choices:
                results.append((
                    choice.message.content, 
                    time.time()-t0, 
                    getattr(r,"usage",{}) or {}
                ))
            break  # We got all samples in one call
        else:
            r = client.chat.completions.create(
                model=model, 
                messages=messages, 
                temperature=0.0
            )
            results.append((
                r.choices[0].message.content, 
                time.time()-t0, 
                getattr(r,"usage",{}) or {}
            ))
    
    return results

def call_together(model, messages, n_samples=1):
    """
    Calls Together API to get AI responses
    
    Args:
        model: Model name (e.g., "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
        messages: List of message dictionaries  
        n_samples: Number of different responses to generate
        
    Returns:
        List of (response_text, latency, usage_info) tuples
    """
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}", 
        "Content-Type": "application/json"
    }
    
    results = []
    for _ in range(n_samples):
        t0 = time.time()
        r = requests.post(
            url,
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7 if n_samples > 1 else 0.0  # Add randomness for diversity
            },
            headers=headers
        )
        r.raise_for_status()
        d = r.json()
        results.append((
            d["choices"][0]["message"]["content"], 
            time.time()-t0, 
            d.get("usage",{})
        ))
    
    return results

def parse_final(text: str):
    """
    Extracts the final answer from AI response text
    
    Args:
        text: The full AI response
        
    Returns:
        Just the final answer part
    """
    m = FINAL_RE.search(text or "")
    return (m.group(1).strip() if m else text.strip()) or ""

def main():
    # Set up command line arguments
    ap = argparse.ArgumentParser(description="Generate Chain of Thought reasoning for questions")
    ap.add_argument("--in", dest="inp", required=True, help="Input JSONL file with questions")
    ap.add_argument("--out", required=True, help="Output JSONL file for results")
    ap.add_argument("--provider", choices=["openai","together"], 
                   default=os.getenv("PROVIDER","openai"), help="API provider to use")
    ap.add_argument("--model", default=os.getenv("MODEL_SMALL","gpt-4o-mini"), 
                   help="Model name to use")
    ap.add_argument("--n_samples", type=int, default=1, 
                   help="Number of different responses to generate per question (default: 1)")  #him - MULTI-SAMPLE FEATURE: Line 147 - Added command line argument for number of samples
    args = ap.parse_args()

    # Create output directory if it doesn't exist
    Path(Path(args.out).parent).mkdir(parents=True, exist_ok=True)
    
    # Process each question in the input file
    with open(args.inp, "r", encoding="utf-8") as fin, open(args.out, "w", encoding="utf-8") as fout:
        for line_num, line in enumerate(fin, 1):
            print(f"Processing question {line_num}...")
            
            # Parse the input record
            ex = json.loads(line)
            msgs = messages_for(ex["question"])
            
            # Get AI responses
            if args.provider == "openai": 
                responses = call_openai(args.model, msgs, args.n_samples)
            else:                       
                responses = call_together(args.model, msgs, args.n_samples)
            
            # Process each response
            candidates = []
            for i, (text, dt, usage) in enumerate(responses):
                candidate = {
                    "cot": text,
                    "answer": parse_final(text),
                    "latency_s": round(dt, 3),
                    "tokens_in": usage.get("prompt_tokens") or usage.get("prompt_tokens_total"),
                    "tokens_out": usage.get("completion_tokens") or usage.get("generation_tokens"),
                    "cost_usd": None
                }
                candidates.append(candidate)
            
            # Create output record
            rec = {
                "id": ex["id"],
                "domain": ex["domain"], 
                "dataset": ex["dataset"],
                "split": ex["split"],
                "question": ex["question"],
                "generator": {
                    "provider": args.provider,
                    "model": args.model,
                    "temperature": 0.7 if args.n_samples > 1 else 0.0,
                    "n_samples": args.n_samples
                },
                "gen": {
                    "candidates": candidates,  #him - MULTI-SAMPLE FEATURE: Line 196 - Store all candidates in an array
                    # Keep the first candidate as the "main" answer for backward compatibility
                    "cot": candidates[0]["cot"],  #him - BACKWARD COMPATIBILITY: Line 198 - Keep first candidate as main answer so old scripts still work
                    "answer": candidates[0]["answer"],
                    "latency_s": candidates[0]["latency_s"],
                    "tokens_in": candidates[0]["tokens_in"],
                    "tokens_out": candidates[0]["tokens_out"],
                    "cost_usd": None
                }
            }
            
            # Write to output file
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    
    print(f"Generated {args.n_samples} samples per question")
    print(f"Wrote results to → {args.out}")

if __name__ == "__main__": 
    main()
