# scripts/tag_errors.py
import json, re, argparse
from taxonomies import MATH_TAXONOMY, CODE_TAXONOMY, ATTR_TAXONOMY

def pick_tax(ds: str):
    s = (ds or "").lower()
    if s.startswith("gsm8k"): return "math", MATH_TAXONOMY
    if s.startswith("mbpp"):  return "code", CODE_TAXONOMY
    return "attr", ATTR_TAXONOMY  # truthfulqa / default

# ---------- heuristics v1 (quick + editable) ----------
def tag_math(r):
    rat = (r.get("rationale") or "").lower()
    ans = (r.get("model_answer") or "").lower()
    q   = (r.get("question") or "").lower()
    if "format" in rat:                                              return "format_violation"
    if re.search(r"[-+*/]", ans) and r.get("label")=="reject":       return "calc_error"
    if "count" in q and r.get("label")=="reject":                    return "count_error"
    if "step" in q and "therefore" not in ans and r.get("label")=="reject": return "missing_step"
    if "contradict" in rat:                                          return "contradiction"
    if "misread" in rat or "mis-parse" in rat or "misparse" in rat:  return "misread"
    return "other_reasoning"

def tag_code(r):
    rat = (r.get("rationale") or "").lower()
    if "syntax" in rat or "parse" in rat:                            return "syntax"
    if "exception" in rat or "traceback" in rat:                     return "runtime"
    if "wrong output" in rat or "failed test" in rat:                return "functional_wrong"
    if "stdin" in rat or "stdout" in rat or "format" in rat:         return "io_mismatch"
    if "edge case" in rat:                                           return "edge_case"
    if "api" in rat or "library" in rat:                             return "api_misuse"
    if "type" in rat:                                                return "type_error"
    if "index" in rat or "off-by-one" in rat:                        return "off_by_one"
    if "state" in rat or "side effect" in rat:                       return "state_mutation"
    if "timeout" in rat or "time limit" in rat or "performance" in rat: return "perf_timeout"
    if "leak" in rat:                                                return "test_leak"
    return "other_code"

def tag_attr(r):
    rat = (r.get("rationale") or "").lower()
    if "factual" in rat or "incorrect fact" in rat:                  return "factuality"
    if "instruction" in rat or "did not follow" in rat or "format" in rat: return "instruction_miss"
    if "incomplete" in rat or "missing" in rat:                      return "completeness"
    if "irrelevant" in rat or "off-topic" in rat:                    return "relevance"
    if "reasoning" in rat or "logic" in rat:                         return "reasoning"
    if "style" in rat or "stylistic" in rat or "weak reply" in rat:  return "style_register"
    if "unsupported" in rat or "no evidence" in rat:                 return "unsupported"
    if "ambiguous" in rat:                                           return "ambiguity"
    return "other_attr"
# ------------------------------------------------------

DISPATCH = {"math": tag_math, "code": tag_code, "attr": tag_attr}

def main(inp, outp):
    with open(inp) as f, open(outp, "w") as g:
        for line in f:
            r = json.loads(line)

            # Only tag actual errors; accepts get "No error"
            if r.get("label") == "reject":
                kind, taxonomy = pick_tax(r.get("dataset", ""))
                code = DISPATCH[kind](r)
                r["taxonomy_code"] = code
                r["taxonomy_name"] = taxonomy.get(code, code)
            else:
                r["taxonomy_code"] = "none"
                r["taxonomy_name"] = "No error"

            g.write(json.dumps(r) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="inp",  required=True)
    ap.add_argument("--out", dest="outp", required=True)
    args = ap.parse_args()
    main(args.inp, args.outp)