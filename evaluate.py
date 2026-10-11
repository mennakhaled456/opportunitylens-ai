"""Run labelled test cases through the pipeline and save accuracy results.

Usage:
    python evaluate.py                       # main set, resume
    python evaluate.py --fresh               # main set, start over
    python evaluate.py --cases eval_holdout.json --out eval_holdout_results.json
"""
import json
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from src.pipeline import analyze_opportunity

CASES_FILE = "eval_cases.json"
RESULTS_FILE = "eval_results.json"
PAUSE_SECONDS = 3  # avoids free-tier rate limits

if "--cases" in sys.argv:
    CASES_FILE = sys.argv[sys.argv.index("--cases") + 1]
if "--out" in sys.argv:
    RESULTS_FILE = sys.argv[sys.argv.index("--out") + 1]


def summarize(rows):
    done = [r for r in rows if r["predicted"] is not None]
    correct = sum(r["correct"] for r in done)
    risk = [r for r in done if r["expected"] == "High Risk"]
    risk_hit = sum(r["predicted"] == "High Risk" for r in risk)
    return {
        "n": len(rows),
        "answered": len(done),
        "accuracy": round(correct / len(done), 3) if done else 0,
        "high_risk_recall": round(risk_hit / len(risk), 3) if risk else None,
        "rows": rows,
    }


def save(rows):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summarize(rows), f, indent=2, ensure_ascii=False)


def main():
    with open(CASES_FILE, encoding="utf-8") as f:
        cases = json.load(f)

    rows = []
    if "--fresh" not in sys.argv and os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, encoding="utf-8") as f:
            rows = json.load(f)["rows"]
    finished = {r["id"] for r in rows if r["predicted"] is not None}
    rows = [r for r in rows if r["id"] in finished]

    for case in cases:
        if case["id"] in finished:
            continue
        print(f"Running {case['id']} ...", end=" ", flush=True)
        try:
            res = analyze_opportunity(case["text"])
            row = {
                "id": case["id"],
                "expected": case["expected"],
                "predicted": res.verdict,
                "score": res.score,
                "correct": res.verdict == case["expected"],
                "error": None,
            }
            print(f"{res.verdict} ({res.score})")
        except Exception as e:
            row = {
                "id": case["id"],
                "expected": case["expected"],
                "predicted": None,
                "score": None,
                "correct": False,
                "error": str(e)[:200],
            }
            print(f"ERROR: {row['error']}")
        rows.append(row)
        save(rows)
        time.sleep(PAUSE_SECONDS)

    summary = summarize(rows)
    print(f"\nAccuracy: {summary['accuracy']:.0%} on {summary['answered']}/{summary['n']} cases")
    if summary["high_risk_recall"] is not None:
        print(f"High Risk recall: {summary['high_risk_recall']:.0%}")


if __name__ == "__main__":
    main()