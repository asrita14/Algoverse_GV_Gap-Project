#!/usr/bin/env python3
"""
run_verifier.py - Verifies AI-generated answers using another AI model

WHAT THIS SCRIPT DOES:
1. Reads AI-generated answers from a JSONL file (created by generate_cot.py)
2. For each answer, asks a "judge" AI model to check if it's correct
3. The judge returns: accept/reject, confidence level, and explanation
4. Saves verification results to a new JSONL file

NEW FEATURE: Can verify multiple candidate answers per question (from multi-sample generation)
#him - MULTI-SAMPLE VERIFICATION: Line 11 - Added support for verifying multiple candidates per question
"""
import os, time, json, argparse, requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables (API keys) from .env file
load_dotenv(find_dotenv(usecwd=True) or ".env")

# Instruction for the judge model on how to format its response
INSTR = 'Return JSON: {"label":"accept|reject","confidence":0.xx,"rationale":"..."}'

def judge_messages(q, ans, cot):
    """
    Creates the prompt messages for the judge model
    
    Args:
        q: The original question
        ans: The AI's final answer to verify
        cot: The AI's reasoning steps (chain of thought)
        
    Returns:
        List of message dictionaries for the API call
    """
    return [
        {"role": "system", "content": "You judge if a final answer is correct."},
        {"role": "user", "content": f"Question: {q}\nFinal answer: {ans}\nSteps (may be empty):\n{cot or ''}\n{INSTR}"}
    ]

def call_openai(model, messages):
    """
    Calls OpenAI API to get judge's verdict
    
    Args:
        model: Model name (e.g., "gpt-4o-mini")
        messages: List of message dictionaries
        
    Returns:
        Tuple of (response_text, latency_seconds)
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    t0 = time.time()
    r = client.chat.completions.create(model=model, messages=messages, temperature=0.0)
    return r.choices[0].message.content, time.time() - t0

def call_together(model, messages):
    """
    Calls Together API to get judge's verdict
    
    Args:
        model: Model name (e.g., "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
        messages: List of message dictionaries
        
    Returns:
        Tuple of (response_text, latency_seconds)
    """
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}", 
        "Content-Type": "application/json"
    }
    t0 = time.time()
    r = requests.post(
        url, 
        json={"model": model, "messages": messages, "temperature": 0.0}, 
        headers=headers
    )
    r.raise_for_status()
    d = r.json()
    return d["choices"][0]["message"]["content"], time.time() - t0

def safe_parse(s: str):
    """
    Safely parses the judge's JSON response
    
    Args:
        s: Raw response text from the judge model
        
    Returns:
        Dictionary with label, confidence, and rationale
    """
    try:
        j = json.loads(s)
        lab = j.get("label", "").strip().lower()
        conf = float(j.get("confidence", 0))
        rat = j.get("rationale", "")
        
        # Validate label is either "accept" or "reject"
        if lab not in {"accept", "reject"}: 
            raise ValueError(f"Invalid label: {lab}")
        
        # Clamp confidence to [0, 1] range
        return {
            "label": lab,
            "confidence": max(0, min(1, conf)),
            "rationale": rat
        }
    except Exception as e:
        # If parsing fails, return a safe default
        return {
            "label": "reject",
            "confidence": 0.0,
            "rationale": f"invalid JSON: {str(e)}"
        }

def verify_single_candidate(question, candidate, provider, model):
    """
    Verifies a single candidate answer
    
    Args:
        question: The original question
        candidate: Dictionary with 'answer' and 'cot' fields
        provider: API provider ("openai" or "together")
        model: Model name
        
    Returns:
        Dictionary with verification results
    """
    ans = candidate["answer"]
    cot = candidate["cot"]
    
    # Create messages for the judge
    msgs = judge_messages(question, ans, cot)
    
    # Call the appropriate API
    if provider == "openai":
        txt, dt = call_openai(model, msgs)
    else:
        txt, dt = call_together(model, msgs)
    
    # Parse the response
    v = safe_parse(txt)
    
    return {
        "label": v["label"],
        "confidence": v["confidence"],
        "rationale": v["rationale"],
        "latency_s": round(dt, 3)
    }

def aggregate_verification_results(candidate_verifications):
    """
    Combines multiple verification results into a single decision
    
    Args:
        candidate_verifications: List of verification results for each candidate
        
    Returns:
        Dictionary with aggregated decision
    """
    if not candidate_verifications:
        return {"label": "reject", "confidence": 0.0, "rationale": "no candidates"}
    
    # Count accepts vs rejects
    accepts = sum(1 for v in candidate_verifications if v["label"] == "accept")
    rejects = len(candidate_verifications) - accepts
    
    # Majority vote
    if accepts > rejects:
        aggregate_label = "accept"
    elif rejects > accepts:
        aggregate_label = "reject"
    else:
        # Tie - use highest confidence to break tie
        max_conf = max(v["confidence"] for v in candidate_verifications)
        tie_breaker = next(v for v in candidate_verifications if v["confidence"] == max_conf)
        aggregate_label = tie_breaker["label"]
    
    # Average confidence
    avg_confidence = sum(v["confidence"] for v in candidate_verifications) / len(candidate_verifications)
    
    # Combine rationales
    rationales = [v["rationale"] for v in candidate_verifications]
    combined_rationale = f"Majority vote ({accepts}A/{rejects}R): " + "; ".join(rationales[:2])  # Limit length
    
    return {
        "label": aggregate_label,
        "confidence": round(avg_confidence, 3),
        "rationale": combined_rationale,
        "candidate_count": len(candidate_verifications),
        "accept_count": accepts,
        "reject_count": rejects
    }

def main():
    # Set up command line arguments
    ap = argparse.ArgumentParser(description="Verify AI-generated answers using a judge model")
    ap.add_argument("--in", dest="inp", required=True, help="Input JSONL file with generated answers")
    ap.add_argument("--out", required=True, help="Output JSONL file for verification results")
    ap.add_argument("--ref", required=True, help="Reference JSONL file (for future use)")
    ap.add_argument("--provider", choices=["openai","together"], 
                   default=os.getenv("PROVIDER","openai"), help="API provider to use")
    ap.add_argument("--model", default=os.getenv("MODEL_SMALL","gpt-4o-mini"), 
                   help="Judge model name to use")
    args = ap.parse_args()

    # Create output directory if it doesn't exist
    Path(Path(args.out).parent).mkdir(parents=True, exist_ok=True)
    
    # Process each record in the input file
    with open(args.inp, "r", encoding="utf-8") as fin, open(args.out, "w", encoding="utf-8") as fout:
        for line_num, line in enumerate(fin, 1):
            print(f"Verifying question {line_num}...")
            
            # Parse the input record
            rec = json.loads(line)
            question = rec.get("question", "")
            
            # Check if we have multiple candidates or just one
            if "candidates" in rec["gen"] and len(rec["gen"]["candidates"]) > 1:  #him - MULTI-SAMPLE VERIFICATION: Line 221 - Detect if we have multiple candidates to verify
                # Multi-sample case: verify each candidate
                candidates = rec["gen"]["candidates"]
                candidate_verifications = []
                
                for i, candidate in enumerate(candidates):
                    print(f"  Verifying candidate {i+1}/{len(candidates)}...")
                    verification = verify_single_candidate(question, candidate, args.provider, args.model)
                    candidate_verifications.append(verification)
                
                # Aggregate the results
                aggregate = aggregate_verification_results(candidate_verifications)
                
                # Store both individual and aggregated results
                rec["verify"] = {
                    "aggregate": aggregate,  #him - MULTI-SAMPLE VERIFICATION: Line 236 - Store aggregated decision from majority vote
                    "candidates": candidate_verifications  #him - MULTI-SAMPLE VERIFICATION: Line 237 - Store individual verification results for each candidate
                }
            else:
                # Single sample case: verify the main answer
                ans = rec["gen"]["answer"]
                cot = rec["gen"]["cot"]
                
                msgs = judge_messages(question, ans, cot)
                txt, dt = (call_openai if args.provider == "openai" else call_together)(args.model, msgs)
                v = safe_parse(txt)
                
                rec["verify"] = {
                    "label": v["label"],
                    "confidence": v["confidence"],
                    "rationale": v["rationale"],
                    "latency_s": round(dt, 3)
                }
            
            # Write to output file
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    
    print(f"Wrote verification results to → {args.out}")

if __name__ == "__main__": 
    main()
