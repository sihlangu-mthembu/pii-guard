"""Detect and redact personal information (PII) in text. Pure Python, no dependencies.

Detectors, run in this order so longer numbers are claimed first:
    SA_ID   13-digit South African ID number: valid YYMMDD birth date and Luhn check digit
    CARD    15-16 digit payment card number with a valid Luhn check digit
    PHONE   South African phone number: +27 or 0, then 9 digits (spaces or dashes allowed)
    EMAIL   email address
    NAME    first names from a supplied list (whole words, case-sensitive)
"""

import datetime
import re
from typing import Any

DEFAULT_NAMES = ["Thabo", "Lerato", "Sipho", "Naledi", "Johan", "Priya", "Ayesha", "Pieter",
                 "Zanele", "Grace", "Bongani", "Fatima"]


def luhn_valid(digits: str) -> bool:
    """Standard Luhn checksum, used by SA ID numbers and payment cards."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def valid_sa_id(digits: str) -> bool:
    if len(digits) != 13 or not luhn_valid(digits):
        return False
    yy, mm, dd = int(digits[0:2]), int(digits[2:4]), int(digits[4:6])
    for century in (1900, 2000):
        try:
            datetime.date(century + yy, mm, dd)
            return True
        except ValueError:
            continue
    return False


PATTERNS = [
    ("SA_ID", re.compile(r"(?<!\d)\d{6}[ ]?\d{4}[ ]?\d{3}(?!\d)"),
     lambda m: valid_sa_id(re.sub(r"\D", "", m))),
    ("CARD", re.compile(r"(?<!\d)(?:\d[ -]?){14,15}\d(?!\d)"),
     lambda m: len(re.sub(r"\D", "", m)) in (15, 16) and luhn_valid(re.sub(r"\D", "", m))),
    ("PHONE", re.compile(r"(?<![\d+])(?:\+27[ -]?|0)\d{2}[ -]?\d{3}[ -]?\d{4}(?!\d)"), None),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), None),
]


def detect(text: str, names: list[str]=DEFAULT_NAMES) -> list[tuple[str, int, int, str] | Any]:
    """Return a list of (type, start, end, value) found in the text, without overlaps."""
    found = []
    taken = [False] * len(text)

    def claim(kind: str, start: int, end: int) -> None:
        if any(taken[start:end]):
            return
        for i in range(start, end):
            taken[i] = True
        found.append((kind, start, end, text[start:end]))

    for kind, pattern, check in PATTERNS:
        for m in pattern.finditer(text):
            if check is None or check(m.group()):
                claim(kind, m.start(), m.end())
    if names:
        name_re = re.compile(r"\b(?:" + "|".join(map(re.escape, names)) + r")\b")
        for m in name_re.finditer(text):
            claim("NAME", m.start(), m.end())
    return sorted(found, key=lambda f: f[1])


def redact(text: str, names: list[str]=DEFAULT_NAMES) -> tuple[str, list[tuple[str, int, int, str]]]:
    """Replace every detected item with a [TYPE] placeholder. Returns (redacted_text, findings)."""
    findings = detect(text, names)
    out, last = [], 0
    for kind, start, end, _ in findings:
        out.append(text[last:start])
        out.append(f"[{kind}]")
        last = end
    out.append(text[last:])
    return "".join(out), findings


def residual_risks(text: str) -> list[str | Any]:
    """Things a reviewer should look at after redaction: long digit runs and '@' signs."""
    risks = [m.group() for m in re.finditer(r"\d[\d -]{7,}\d", text)]
    if "@" in text:
        risks.append("@")
    return risks
