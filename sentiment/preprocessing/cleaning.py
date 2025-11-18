import re
from typing import Final


WHITESPACE_RE: Final = re.compile(r"\s+")
PII_REPLACEMENTS: Final = [
    (re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b"), "[SSN]"), 
    (re.compile(r"\b\d{10,16}\b"), "[CARD]"),  
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[EMAIL]"),
]


def preprocess_text_for_sentiment(text: str) -> str:
    cleaned = text.strip()
    for pattern, replacement in PII_REPLACEMENTS:
        cleaned = pattern.sub(replacement, cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    return cleaned


