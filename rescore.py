"""Recompute verdicts in eval_results.json from saved scores (no API calls)."""
import json
import os
import shutil

from src.scoring import verdict_for

SRC = "eval_results.json"
BACKUP = "eval_results_v1.json"

if not os.path.exists(BACKUP):
    shutil.copy(SRC, BACKUP)  # keep the original thresholds' results

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)

for r in data["rows"]:
    if r["score"] is not None:
        r["predicted"] = verdict_for(r["score"])
        r["correct"] = r["predicted"] == r["expected"]

done = [r for r in data["rows"] if r["predicted"] is not None]
risk = [r for r in done if r["expected"] == "High Risk"]
data["accuracy"] = round(sum(r["correct"] for r in done) / len(done), 3)
data["high_risk_recall"] = round(sum(r["predicted"] == "High Risk" for r in risk) / len(risk), 3)

with open(SRC, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Accuracy: {data['accuracy']:.0%} | High Risk recall: {data['high_risk_recall']:.0%}")