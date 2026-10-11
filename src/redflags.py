"""Rule-based red-flag detection. Deterministic, runs before the verdict is final."""
import re

_F = re.IGNORECASE
_NEG = re.compile(r"\b(no|not|without|never|zero|free of)\b|n't", _F)

# (label, pattern, check_negation)
HARD_FLAGS = [
    ("Asks you to pay a fee or deposit",
     re.compile(r"\b(registration|training|application|processing|admin|enrol?lment)\s+(fee|deposit)"
                r"|\bpay\b[^.]{0,40}\b(fee|deposit)\b"
                r"|\byou (must|need to|have to|will need to)\b[^.]{0,40}\bpay\b", _F), True),
    ("Asks for ID, passport or bank details up front",
     re.compile(r"\b(send|share|provide|give|submit)\b[^.]{0,40}"
                r"\b(national id|id card|passport|bank account|bank details|credit card|card number)\b", _F), True),
    ("Cheque or money-forwarding scheme",
     re.compile(r"\bcheque\b[^.]{0,60}\b(deposit|forward|send)\b"
                r"|\bcheck\b[^.]{0,30}\$\s?\d[^.]{0,40}\b(deposit|forward|send)\b", _F), False),
    ("Guaranteed job or no interview",
     re.compile(r"\bguaranteed\b[^.]{0,20}\b(job|income|salary|offer)\b|\bno interview\b", _F), False),
]

SOFT_FLAGS = [
    ("Applications only through WhatsApp or Telegram",
     re.compile(r"\b(whatsapp|telegram)\b", _F)),
    ("Unrealistic earnings promised",
     re.compile(r"\bearn\b[^.]{0,25}\$\s?\d{3,}", _F)),
    ("Pressure tactics (urgent, limited spots)",
     re.compile(r"\burgent\b|\blimited spots\b|\breply today\b", _F)),
]


def _matches(rx, text, check_negation):
    for m in rx.finditer(text):
        if check_negation:
            before = re.split(r"[.!?\n,;]", text[:m.start()])[-1][-30:]
            if _NEG.search(before):
                continue
        return True
    return False


def detect_red_flags(text: str) -> dict:
    hard = [label for label, rx, neg in HARD_FLAGS if _matches(rx, text, neg)]
    soft = [label for label, rx in SOFT_FLAGS if rx.search(text)]
    return {"hard": hard, "soft": soft}