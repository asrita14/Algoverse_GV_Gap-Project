#!/usr/bin/env python3
"""
compute_gv_gap.py - Calculates the Generation-Verification Gap (GV-Gap)

WHAT THIS SCRIPT DOES:
1. Reads AI-generated answers and their verifications
2. Compares AI answers against ground truth to calculate Generation accuracy
3. Compares verifier decisions against ground truth to calculate Verification accuracy  
4. Computes the GV-Gap = Verification accuracy - Generation accuracy
5. Reports detailed metrics and saves results to CSV

THE GV-GAP MEASURES:
- Positive GV-Gap: Verifier is better than generator (good self-verification)
- Negative GV-Gap: Generator is better than verifier (poor self-verification)
- Zero GV-Gap: Generator and verifier perform equally
"""
import json
import argparse
import pandas as pd
from pathlib import Path
from collections import defaultdict

def load_reference_answers(ref_file):
    """
    Loads the reference (correct) answers from the original dataset
    
    Args:
        ref_file: Path to the reference JSONL file
        
    Returns:
        Dictionary mapping question IDs to correct answers
    """
    ref_answers = {}
    with open(ref_file, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line.strip())
            ref_answers[record['id']] = record['reference_answer']
    return ref_answers

def is_answer_correct(generated_answer, reference_answer):
    """
    Checks if a generated answer matches the reference answer
    
    Args:
        generated_answer: The AI's answer
        reference_answer: The correct answer
        
    Returns:
        Boolean: True if correct, False otherwise
    """
    # Simple string comparison (can be enhanced for different answer types)
    return str(generated_answer).strip().lower() == str(reference_answer).strip().lower()

def extract_verification_decision(verify_data):
    """
    Extracts the verification decision from the verify field
    
    Args:
        verify_data: The verify field from the record
        
    Returns:
        Tuple of (label, confidence) where label is "accept" or "reject"
    """
    if isinstance(verify_data, dict):
        # Check if it's multi-sample format
        if "aggregate" in verify_data:
            return verify_data["aggregate"]["label"], verify_data["aggregate"]["confidence"]
        else:
            # Single sample format
            return verify_data.get("label", "reject"), verify_data.get("confidence", 0.0)
    return "reject", 0.0

def calculate_metrics(verified_file, ref_answers):
    """
    Calculates generation and verification metrics
    
    Args:
        verified_file: Path to the verified JSONL file
        ref_answers: Dictionary of reference answers
        
    Returns:
        Dictionary with calculated metrics
    """
    total_questions = 0
    generation_correct = 0
    verification_correct = 0
    
    # Detailed tracking
    generation_details = []
    verification_details = []
    
    with open(verified_file, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line.strip())
            question_id = record['id']
            total_questions += 1
            
            # Get the generated answer
            generated_answer = record['gen']['answer']
            reference_answer = ref_answers.get(question_id, "")
            
            # Check if generation is correct
            gen_correct = is_answer_correct(generated_answer, reference_answer)
            if gen_correct:
                generation_correct += 1
            
            # Get verification decision
            verify_label, verify_confidence = extract_verification_decision(record.get('verify', {}))
            
            # Check if verification is correct
            # Verification is correct if:
            # - It accepts a correct answer, OR
            # - It rejects an incorrect answer
            verify_correct = (verify_label == "accept" and gen_correct) or (verify_label == "reject" and not gen_correct)
            if verify_correct:
                verification_correct += 1
            
            # Store details for analysis
            generation_details.append({
                'id': question_id,
                'generated': generated_answer,
                'reference': reference_answer,
                'correct': gen_correct
            })
            
            verification_details.append({
                'id': question_id,
                'verify_label': verify_label,
                'verify_confidence': verify_confidence,
                'gen_correct': gen_correct,
                'verify_correct': verify_correct
            })
    
    # Calculate accuracies
    generation_accuracy = generation_correct / total_questions if total_questions > 0 else 0
    verification_accuracy = verification_correct / total_questions if total_questions > 0 else 0
    gv_gap = verification_accuracy - generation_accuracy
    
    return {
        'total_questions': total_questions,
        'generation_correct': generation_correct,
        'verification_correct': verification_correct,
        'generation_accuracy': generation_accuracy,
        'verification_accuracy': verification_accuracy,
        'gv_gap': gv_gap,
        'generation_details': generation_details,
        'verification_details': verification_details
    }

def analyze_verification_patterns(verification_details):
    """
    Analyzes patterns in verification behavior
    
    Args:
        verification_details: List of verification detail records
        
    Returns:
        Dictionary with pattern analysis
    """
    # Count different verification scenarios
    true_positives = 0  # Accept correct answers
    true_negatives = 0  # Reject incorrect answers  
    false_positives = 0  # Accept incorrect answers
    false_negatives = 0  # Reject correct answers
    
    confidence_by_scenario = defaultdict(list)
    
    for detail in verification_details:
        gen_correct = detail['gen_correct']
        verify_label = detail['verify_label']
        confidence = detail['verify_confidence']
        
        if gen_correct and verify_label == "accept":
            true_positives += 1
            confidence_by_scenario['true_positives'].append(confidence)
        elif not gen_correct and verify_label == "reject":
            true_negatives += 1
            confidence_by_scenario['true_negatives'].append(confidence)
        elif not gen_correct and verify_label == "accept":
            false_positives += 1
            confidence_by_scenario['false_positives'].append(confidence)
        elif gen_correct and verify_label == "reject":
            false_negatives += 1
            confidence_by_scenario['false_negatives'].append(confidence)
    
    # Calculate average confidence for each scenario
    avg_confidence = {}
    for scenario, confidences in confidence_by_scenario.items():
        avg_confidence[scenario] = sum(confidences) / len(confidences) if confidences else 0
    
    return {
        'true_positives': true_positives,
        'true_negatives': true_negatives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'avg_confidence': avg_confidence
    }

def main():
    # Set up command line arguments
    ap = argparse.ArgumentParser(description="Calculate Generation-Verification Gap metrics")
    ap.add_argument("--in", dest="inp", required=True, 
                   help="Input JSONL file with verified answers (from run_verifier.py)")
    ap.add_argument("--ref", required=True, 
                   help="Reference JSONL file with correct answers")
    ap.add_argument("--out", required=True, 
                   help="Output CSV file for detailed results")
    ap.add_argument("--summary", 
                   help="Optional: Output text file for summary metrics")
    args = ap.parse_args()
    
    print("Loading reference answers...")
    ref_answers = load_reference_answers(args.ref)
    print(f"Loaded {len(ref_answers)} reference answers")
    
    print("Calculating metrics...")
    metrics = calculate_metrics(args.inp, ref_answers)
    
    print("Analyzing verification patterns...")
    patterns = analyze_verification_patterns(metrics['verification_details'])
    
    # Print summary to console
    print("\n" + "="*60)
    print("GENERATION-VERIFICATION GAP ANALYSIS")
    print("="*60)
    print(f"Total Questions: {metrics['total_questions']}")
    print(f"Generation Accuracy: {metrics['generation_accuracy']:.3f} ({metrics['generation_correct']}/{metrics['total_questions']})")
    print(f"Verification Accuracy: {metrics['verification_accuracy']:.3f} ({metrics['verification_correct']}/{metrics['total_questions']})")
    print(f"GV-Gap: {metrics['gv_gap']:.3f}")
    
    if metrics['gv_gap'] > 0:
        print("✓ Positive GV-Gap: Verifier outperforms generator (good self-verification)")
    elif metrics['gv_gap'] < 0:
        print("✗ Negative GV-Gap: Generator outperforms verifier (poor self-verification)")
    else:
        print("= Zero GV-Gap: Generator and verifier perform equally")
    
    print("\nVerification Pattern Analysis:")
    print(f"True Positives (Accept correct): {patterns['true_positives']}")
    print(f"True Negatives (Reject incorrect): {patterns['true_negatives']}")
    print(f"False Positives (Accept incorrect): {patterns['false_positives']}")
    print(f"False Negatives (Reject correct): {patterns['false_negatives']}")
    
    # Save detailed results to CSV
    print(f"\nSaving detailed results to {args.out}...")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    
    # Combine generation and verification details
    detailed_results = []
    for gen_detail, ver_detail in zip(metrics['generation_details'], metrics['verification_details']):
        detailed_results.append({
            'id': gen_detail['id'],
            'generated_answer': gen_detail['generated'],
            'reference_answer': gen_detail['reference'],
            'generation_correct': gen_detail['correct'],
            'verify_label': ver_detail['verify_label'],
            'verify_confidence': ver_detail['verify_confidence'],
            'verification_correct': ver_detail['verify_correct']
        })
    
    df = pd.DataFrame(detailed_results)
    df.to_csv(args.out, index=False)
    
    # Save summary if requested
    if args.summary:
        with open(args.summary, 'w') as f:
            f.write("Generation-Verification Gap Analysis\n")
            f.write("="*40 + "\n\n")
            f.write(f"Total Questions: {metrics['total_questions']}\n")
            f.write(f"Generation Accuracy: {metrics['generation_accuracy']:.3f}\n")
            f.write(f"Verification Accuracy: {metrics['verification_accuracy']:.3f}\n")
            f.write(f"GV-Gap: {metrics['gv_gap']:.3f}\n\n")
            f.write("Verification Patterns:\n")
            f.write(f"True Positives: {patterns['true_positives']}\n")
            f.write(f"True Negatives: {patterns['true_negatives']}\n")
            f.write(f"False Positives: {patterns['false_positives']}\n")
            f.write(f"False Negatives: {patterns['false_negatives']}\n")
        print(f"Saved summary to {args.summary}")
    
    print(f"Analysis complete! GV-Gap = {metrics['gv_gap']:.3f}")

if __name__ == "__main__":
    main()
