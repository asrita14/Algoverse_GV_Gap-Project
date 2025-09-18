# found these through 3 different papers.
# Li et al. 2024 — math (GSM8K)
MATH_TAXONOMY = {
    "calc_error": "Calculation error",
    "count_error": "Counting error",
    "hallucination": "Hallucination / fictitious statement",
    "missing_step": "Missing step",
    "contradiction": "Contradictory step",
    "wrong_formula": "Wrong formula / concept",
    "misread": "Problem misread / misparse",
    "format_violation": "Answer format violation",
    "other_reasoning": "Other reasoning error",
}

# Dou et al. 2024 — code (MBPP)
CODE_TAXONOMY = {
    "syntax": "Syntax bug",
    "runtime": "Runtime/exception bug",
    "functional_wrong": "Functional logic wrong",
    "io_mismatch": "I/O format mismatch",
    "edge_case": "Edge-case not handled",
    "api_misuse": "API/library misuse",
    "type_error": "Type mismatch/annotation",
    "off_by_one": "Off-by-one / indexing",
    "state_mutation": "State/side-effect bug",
    "perf_timeout": "Performance/time limit",
    "test_leak": "Test leakage / cheating",
    "other_code": "Other code bug",
}

#Xu et al. 2025 = multi-domain (TruthfulQA)
ATTR_TAXONOMY = {
    "factuality": "Factual inaccuracy",
    "reasoning": "Reasoning flaw",
    "relevance": "Irrelevant / off-topic",
    "completeness": "Incomplete answer",
    "instruction_miss": "Instruction not followed",
    "style_register": "Stylistic/hedged reply instead of facts",
    "unsupported": "Unsupported claim / no evidence",
    "ambiguity": "Ambiguity handling issue",
    "other_attr": "Other attribution",
}
