"""Deterministic scoring: Python does the math, the LLM only rates each category."""
from .redflags import detect_red_flags

WEIGHTS = {
    "career_relevance": 0.20,
    "learning_potential": 0.20,
    "mentorship": 0.15,
    "company_credibility": 0.15,
    "compensation": 0.10,
    "workload": 0.10,
    "transparency": 0.10,
}

HARD_FLAG_CAP = 35


def compute_score(breakdown) -> int:
    total = sum(getattr(breakdown, name) * weight for name, weight in WEIGHTS.items())
    return max(0, min(100, round(total)))


def verdict_for(score: int) -> str:
    if score >= 80:
        return "Recommended"
    if score >= 40:
        return "Consider with Caution"
    return "High Risk"


def apply_deterministic_score(result, text: str = ""):
    """Overwrite the model's own score/verdict with the exact weighted result,
    then apply the rule-based red-flag cap."""
    result.score = compute_score(result.score_breakdown)

    flags = detect_red_flags(text) if text else {"hard": [], "soft": []}

    if flags["hard"]:
        result.score = min(result.score, HARD_FLAG_CAP)
        result.strengths = []

    result.verdict = verdict_for(result.score)

    for label in flags["hard"] + flags["soft"]:
        msg = f"Red flag detected: {label}"
        if msg not in result.risks:
            result.risks.insert(0, msg)

    return result