# GV-Gap Project: Practical Diagnostics for LLM Self-Verification

A comprehensive research pipeline for studying the Generation-Verification Gap (GV-Gap) in Large Language Models across multiple domains.

## 🎯 Project Overview

This project investigates when and how AI models can effectively verify their own outputs. We measure the **Generation-Verification Gap (GV-Gap)** - the difference between how well a model generates answers versus how well it can verify the correctness of those answers.

### Research Questions
- **RQ1**: How does the GV-Gap vary across domains (math, code, factual QA)?
- **RQ2**: What are the failure modes of self-verification?
- **RQ3**: Which methods best close the GV-Gap?
- **RQ4**: Do multi-agent verification setups outperform single-agent approaches?

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Set up API keys
echo "OPENAI_API_KEY=your_key_here" > .env
echo "TOGETHER_API_KEY=your_key_here" >> .env
```

### 2. Run Complete Pipeline
```bash
# Generate 5 samples per question
python scripts/generate_cot.py \
  --in data/processed/gsm8k/pilot.jsonl \
  --out results/gsm8k/gpt-4o-mini/pilot/01_gen.jsonl \
  --provider openai \
  --model gpt-4o-mini \
  --n_samples 5

# Verify each sample
python scripts/run_verifier.py \
  --in results/gsm8k/gpt-4o-mini/pilot/01_gen.jsonl \
  --out results/gsm8k/gpt-4o-mini/pilot/02_verify.jsonl \
  --ref data/processed/gsm8k/pilot.jsonl \
  --provider openai \
  --model gpt-4o-mini

# Calculate GV-Gap metrics
python scripts/compute_gv_gap.py \
  --in results/gsm8k/gpt-4o-mini/pilot/02_verify.jsonl \
  --ref data/processed/gsm8k/pilot.jsonl \
  --out results/gsm8k/gpt-4o-mini/pilot/03_metrics.csv \
  --summary results/gsm8k/gpt-4o-mini/pilot/03_summary.txt

# Update taxonomy summary
python scripts/update_taxonomy.py
```

## 📁 Project Structure

```
├── data/processed/           # Input datasets
│   ├── gsm8k/               # Math reasoning problems
│   ├── mbpp/                # Code generation tasks
│   └── truthfulqa/          # Factual QA questions
├── scripts/                 # Pipeline components
│   ├── generate_cot.py      # Generate Chain of Thought answers
│   ├── run_verifier.py      # Verify answers with judge model
│   ├── tag_errors.py        # Categorize errors by taxonomy
│   ├── compute_gv_gap.py    # Calculate research metrics
│   └── update_taxonomy.py   # Update error summary tables
├── results/                 # Output files (created when running)
└── docs/                    # Documentation
    ├── PIPELINE_GUIDE.md    # Detailed usage guide
    ├── ISSUES_FIXED.md      # Technical issue analysis
    └── CHECKIN_UPDATE.md    # Progress updates
```

## 🔧 Pipeline Components

### 1. **generate_cot.py** - Answer Generation
- **Purpose**: Generate Chain of Thought reasoning for questions
- **Input**: Questions from `data/processed/<dataset>/<split>.jsonl`
- **Output**: AI's reasoning + answers in `results/<dataset>/<model>/<split>/01_gen.jsonl`
- **Features**: 
  - Single or multi-sample generation (`--n_samples`)
  - Support for OpenAI and Together APIs
  - Temperature variation for diversity

### 2. **run_verifier.py** - Answer Verification
- **Purpose**: Verify AI-generated answers using a judge model
- **Input**: Generated answers from step 1
- **Output**: Judge's verdict (accept/reject) + confidence + explanation
- **Features**:
  - Handles single or multiple candidates per question
  - Majority voting for multi-sample aggregation
  - Detailed confidence scoring

### 3. **tag_errors.py** - Error Categorization
- **Purpose**: Categorize errors using research-backed taxonomies
- **Input**: Verified answers from step 2
- **Output**: Error categories (math errors, code bugs, factual mistakes)
- **Taxonomies**:
  - **Math (GSM8K)**: calc_error, reasoning_gap, format_mismatch, instruction_miss
  - **Code (MBPP)**: syntax_error, logic_bug, edge_case_fail, spec_misread
  - **Facts (TruthfulQA)**: factual_hallucination, misleading_generalization, ambiguous_misread, hedged_nonanswer

### 4. **compute_gv_gap.py** - Metrics Calculation
- **Purpose**: Calculate the core research metric (GV-Gap)
- **Input**: Verified answers + reference answers
- **Output**: Generation accuracy, Verification accuracy, GV-Gap
- **Metrics**:
  - **Generation Accuracy**: How often AI gets questions right
  - **Verification Accuracy**: How often verifier correctly identifies right/wrong
  - **GV-Gap**: Difference between verification and generation performance
  - **Pattern Analysis**: True positives, false negatives, confidence distributions

### 5. **update_taxonomy.py** - Summary Updates
- **Purpose**: Update the taxonomy summary table in `taxonomy.md`
- **Input**: Tagged errors from step 3
- **Output**: Updated markdown table with error counts by category

## 📊 Understanding Results

### GV-Gap Interpretation
- **Positive GV-Gap**: Verifier outperforms generator (good self-verification)
- **Negative GV-Gap**: Generator outperforms verifier (poor self-verification)
- **Zero GV-Gap**: Generator and verifier perform equally

### Example Output
```
Generation-Verification Gap Analysis
====================================
Total Questions: 100
Generation Accuracy: 0.750 (75/100)
Verification Accuracy: 0.820 (82/100)
GV-Gap: 0.070

✓ Positive GV-Gap: Verifier outperforms generator (good self-verification)

Verification Patterns:
True Positives: 70    (Accept correct answers)
True Negatives: 12    (Reject incorrect answers)
False Positives: 5    (Accept incorrect answers)
False Negatives: 13   (Reject correct answers)
```

## 🎯 Research Applications

### Multi-Sample Analysis
Generate multiple answers per question to study:
- **Consistency**: How often does the AI give the same answer?
- **Diversity**: What types of errors occur across different attempts?
- **Verification Patterns**: How does the verifier handle multiple candidates?

### Cross-Domain Comparison
Compare GV-Gap across:
- **Math Reasoning** (GSM8K): Step-by-step problem solving
- **Code Generation** (MBPP): Programming task completion
- **Factual QA** (TruthfulQA): Knowledge-based question answering

### Model Comparison
Test different AI models:
- **OpenAI**: GPT-4o, GPT-4o-mini
- **Together**: Llama, Mistral, Qwen models
- **Size Analysis**: Compare 1B-20B parameter models

## 🔬 Research Methodology

### Data Flow
```
Raw Questions → AI Generation → AI Verification → Error Tagging → Metrics Calculation
```

### Key Metrics
1. **Generation Accuracy**: Percentage of correct answers
2. **Verification Accuracy**: Percentage of correct accept/reject decisions
3. **GV-Gap**: Verification accuracy - Generation accuracy
4. **Error Distribution**: Breakdown by taxonomy categories
5. **Confidence Calibration**: How well does confidence predict correctness?

### Experimental Design
- **Multi-sample generation**: 5+ answers per question for consistency analysis
- **Cross-validation**: Test on multiple datasets and model sizes
- **Ablation studies**: Compare different verification strategies
- **Error analysis**: Deep dive into failure modes by category

## 📚 Documentation

- **[PIPELINE_GUIDE.md](PIPELINE_GUIDE.md)**: Detailed usage instructions
- **[ISSUES_FIXED.md](ISSUES_FIXED.md)**: Technical issue analysis and solutions
- **[CHECKIN_UPDATE.md](CHECKIN_UPDATE.md)**: Progress updates and milestones
- **[taxonomy.md](taxonomy.md)**: Error categorization system

## 🛠️ Development

### Adding New Datasets
1. Create `data/processed/<dataset>/<split>.jsonl` with standard format
2. Add dataset-specific error taxonomy in `scripts/taxonomies.py`
3. Update `scripts/update_taxonomy.py` to include new dataset
4. Test pipeline with new dataset

### Adding New Models
1. Add model support in `scripts/generate_cot.py` and `scripts/run_verifier.py`
2. Update model configuration in `.env` file
3. Test with new model and compare results

### Customizing Taxonomies
1. Modify error categories in `scripts/taxonomies.py`
2. Update tagging logic in `scripts/tag_errors.py`
3. Regenerate taxonomy summary with `scripts/update_taxonomy.py`

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes with clear comments
4. **Test** the pipeline end-to-end
5. **Submit** a pull request with detailed description

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📞 Support

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join team discussions for research questions
- **Documentation**: Check the docs/ folder for detailed guides

## 🎉 Acknowledgments

- **Research Team**: Leo Hilti, Asrita Bobba, Shlok Channawar, Himavanth Karpurapu
- **Datasets**: GSM8K, MBPP, TruthfulQA communities
- **Models**: OpenAI, Together AI, and open-source model providers

---

**Ready to start your GV-Gap research?** Check out [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) for step-by-step instructions!