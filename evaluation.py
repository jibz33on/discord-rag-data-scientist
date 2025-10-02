"""
evaluation.py - Very simple 6-step evaluator for your RAG pipeline.

Place at project root (same level as `backend/`). Run:

    # using built-in tests
    python evaluation.py

    # or with your own tests file
    python evaluation.py --tests tests/eval_tests.json --out_dir reports

Outputs:
- reports/results.json
- reports/evaluation_report.md
"""

# Step 1 : import your RAG pipeline function

import json
import os
import re
import argparse
from datetime import datetime

# Try importing the project's pipeline function
try:
    from backend.RAG_pipeline import run_rag_pipeline
except Exception as _import_err:
    run_rag_pipeline = None
    IMPORT_ERROR = _import_err

# Step 2: Safe pipeline runner

def safe_run_pipeline(query, top_k=None):
    """
    Call run_rag_pipeline in a defensive way.

    - If the import (Step 1) failed, raise a clear RuntimeError with the original import error.
    - Try calling run_rag_pipeline(query, top_k=top_k) first (many pipelines accept top_k).
    - If the pipeline doesn't accept top_k (TypeError), call it as run_rag_pipeline(query).
    - Propagate other exceptions so the caller can decide how to handle them.
    """
    if run_rag_pipeline is None:
        # Clear, actionable error if import failed
        raise RuntimeError(f"Cannot import run_rag_pipeline: {IMPORT_ERROR}")

    try:
        # Prefer calling with top_k if provided
        if top_k is None:
            return run_rag_pipeline(query)
        return run_rag_pipeline(query, top_k=top_k)
    except TypeError:
        # Pipeline signature doesn't accept top_k — call without it
        return run_rag_pipeline(query)
    
    #step 3: Extract answer plus documents

def extract_answer_and_docs(result):
    """
        Normalize pipeline output into (answer_text, docs_list).

        Handles common return shapes:
      - dict with keys like "answer", "text", "docs", "retrieved"
      - tuple/list where result[0] is answer and result[1] may be docs/hits
      - plain string (treated as answer)
      - anything else -> stringified answer

        Returns:
            (answer: str, docs: List[str])
    """
    answer = ""
    docs = []

    # If pipeline returned a dict, check common keys
    if isinstance(result, dict):
        for key in ("answer", "text", "response", "output", "final"):
            if key in result and result[key]:
                answer = str(result[key])
                break

        for key in ("retrieved", "docs", "chunks", "context", "hits", "sources"):
            if key in result and result[key]:
                vals = result[key]
                # normalize list-like or single value
                if isinstance(vals, list):
                    for v in vals:
                        if isinstance(v, dict):
                            docs.append(v.get("text") or v.get("content") or "")
                        else:
                            docs.append(str(v))
                else:
                    docs.append(str(vals))

        # sometimes retrieved docs are nested in an 'info' or 'meta' field
        for meta_key in ("info", "meta"):
            if meta_key in result and isinstance(result[meta_key], dict):
                maybe_hits = result[meta_key].get("hits") or result[meta_key].get("results")
                if isinstance(maybe_hits, list):
                    for h in maybe_hits:
                        if isinstance(h, dict):
                            docs.append(h.get("text") or h.get("content") or "")
                        else:
                            docs.append(str(h))

    # If tuple/list: assume (answer, docs/hits, ...)
    elif isinstance(result, (list, tuple)):
        if len(result) >= 1:
            answer = str(result[0] or "")
        if len(result) >= 2:
            second = result[1]
            if isinstance(second, list):
                for v in second:
                    if isinstance(v, dict):
                        docs.append(v.get("text") or v.get("content") or "")
                    else:
                        docs.append(str(v))

    # If string, use as answer
    elif isinstance(result, str):
        answer = result

    else:
        # fallback: stringify whatever it is
        answer = str(result)

    # cleanup/normalize
    answer = (answer or "").strip()
    docs = [d.strip() for d in docs if isinstance(d, str) and d.strip()]

    return answer, docs

# -----------------------
# Step 4: Tokenization & metrics

import re
_word_rx = re.compile(r"\w+")

def tokenize(text):
    """
    Simple tokenizer: returns lowercase word tokens from text.
    Example: "Hello, world!" -> ["hello", "world"]
    """
    if not text:
        return []
    return _word_rx.findall(text.lower())

def token_overlap_fraction(answer, docs):
    """
    Compute the fraction of answer tokens that appear in any retrieved doc tokens.
    - If answer is empty -> return 0.0
    - If no docs -> return 0.0
    - Otherwise return matched_tokens / total_answer_tokens (0.0 .. 1.0)
    This is a simple proxy for whether the answer is grounded in retrieved docs.
    """
    if not answer:
        return 0.0

    ans_tokens = tokenize(answer)
    if not ans_tokens:
        return 0.0

    doc_tokens = set()
    for d in docs:
        doc_tokens.update(tokenize(d))

    if not doc_tokens:
        return 0.0

    matched = sum(1 for t in ans_tokens if t in doc_tokens)
    return matched / len(ans_tokens)

def expected_keywords_match(answer, expected_keywords):
    """
    Check whether all expected keywords appear in the answer (case-insensitive).
    Returns True if expected_keywords is empty (no expectation specified).
    """
    if not expected_keywords:
        return True
    ans_lower = (answer or "").lower()
    return all(kw.lower() in ans_lower for kw in expected_keywords)

# -----------------------
# Step 5: Run tests
# -----------------------
def run_single_test(query, expected_keywords=None, top_k=3):
    """
    Run one query through the pipeline and compute metrics.
    Returns a dictionary with query, answer, docs preview, and evaluation results.
    """
    expected_keywords = expected_keywords or []

    # Call pipeline safely
    raw = safe_run_pipeline(query, top_k=top_k)

    # Extract answer and docs
    answer, docs = extract_answer_and_docs(raw)

    # Metric 1: expected keywords match
    expected_ok = expected_keywords_match(answer, expected_keywords)

    # Metric 2: token overlap
    overlap = token_overlap_fraction(answer, docs)

    return {
        "query": query,
        "answer": answer,
        "docs_preview": [d[:300] for d in docs],
        "expected_keywords": expected_keywords,
        "expected_match": expected_ok,
        "token_overlap": round(overlap, 4),
    }

def run_all_tests(test_cases, top_k=3):
    """
    Run all test cases and collect results.
    Each test_case is a dict: {"query": str, "expected_keywords": [list of str]}.
    """
    results = []
    for case in test_cases:
        q = case.get("query")
        expected = case.get("expected_keywords", [])
        try:
            res = run_single_test(q, expected, top_k=top_k)
        except Exception as e:
            res = {"query": q, "error": str(e)}
        results.append(res)
    return results


# -----------------------
# Step 6: Write outputs + CLI
# -----------------------
import json
import os
from datetime import datetime
import argparse

def write_reports(results, out_dir="reports"):
    """
    Save raw results (results.json) and a human-friendly markdown report
    (evaluation_report.md) into out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    results_path = os.path.join(out_dir, "results.json")
    report_path = os.path.join(out_dir, "evaluation_report.md")

    # 1) Write raw JSON
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 2) Compose a simple markdown report
    total = len(results)
    passed = sum(1 for r in results if r.get("expected_match"))
    # average token overlap (skip items without numeric token_overlap)
    overlaps = [r.get("token_overlap") for r in results if isinstance(r.get("token_overlap"), (int, float))]
    avg_overlap = (sum(overlaps) / len(overlaps)) if overlaps else 0.0

    md_lines = []
    md_lines.append(f"# RAG Evaluation Report\n\nGenerated: {ts}\n\n")
    md_lines.append(f"- Tests run: **{total}**\n")
    md_lines.append(f"- Passed (expected keywords): **{passed}**\n")
    md_lines.append(f"- Avg token overlap (proxy): **{avg_overlap:.3f}**\n\n---\n\n")
    md_lines.append("## Details\n\n")

    for i, r in enumerate(results, start=1):
        md_lines.append(f"### {i}. `{r.get('query')}`\n\n")
        if r.get("error"):
            md_lines.append(f"**Error:** {r.get('error')}\n\n---\n\n")
            continue
        md_lines.append("**Answer (truncated):**\n\n```\n")
        md_lines.append((r.get("answer") or "")[:800] + "\n```\n\n")
        md_lines.append(f"- Expected keywords: {r.get('expected_keywords')}\n")
        md_lines.append(f"- Expected match: {r.get('expected_match')}\n")
        md_lines.append(f"- Token overlap: {r.get('token_overlap')}\n")
        if r.get("docs_preview"):
            md_lines.append("- Top retrieved previews:\n")
            for j, p in enumerate(r.get("docs_preview")[:3], 1):
                clean_preview = p.replace("\n", " ")[:300]
                md_lines.append(f"  - {j}. {clean_preview}\n")
        md_lines.append("\n---\n\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(md_lines)

    return results_path, report_path

# -----------------------
# Simple CLI to run everything
# -----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Very simple RAG evaluator (Step 6 CLI)")
    parser.add_argument("--tests", type=str, default=None, help="Path to JSON tests file")
    parser.add_argument("--out_dir", type=str, default="reports", help="Output folder for reports")
    parser.add_argument("--top_k", type=int, default=3, help="Optional top_k to pass to pipeline")
    args = parser.parse_args()

    # default test cases (used if --tests not provided)
    default_tests = [
        {"query": "Who created Python?", "expected_keywords": ["Guido", "1991"]},
        {"query": "What is machine learning?", "expected_keywords": ["data", "learn"]},
        {"query": "What are Discord bots?", "expected_keywords": ["Discord", "bot"]},
        {"query": "Who is Elon Musk?", "expected_keywords": []}
    ]

    if args.tests:
        with open(args.tests, "r", encoding="utf-8") as f:
            test_cases = json.load(f)
    else:
        test_cases = default_tests

    print(f"Running {len(test_cases)} tests...")
    results = run_all_tests(test_cases, top_k=args.top_k)
    results_path, report_path = write_reports(results, out_dir=args.out_dir)
    print(f"Saved raw results: {results_path}")
    print(f"Saved markdown report: {report_path}")

