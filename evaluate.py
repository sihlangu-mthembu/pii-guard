"""Measure detection quality on the labelled test cases.

Usage:  python evaluate.py      -> reports/evaluation.md
"""

import datetime
import json
import pathlib
import re
from collections import defaultdict

from pii_guard import detect

ROOT = pathlib.Path(__file__).resolve().parent
TYPES = ["SA_ID", "CARD", "PHONE", "EMAIL", "NAME"]


def key(kind: str, value: str) -> tuple[str, str]:
    """Compare numbers by digits only, everything else exactly."""
    return (kind, re.sub(r"\D", "", value) if kind in ("SA_ID", "CARD", "PHONE") else value)


def main() -> None:
    cases = [json.loads(line) for line in open(ROOT / "data" / "test_cases.jsonl", encoding="utf-8")]
    tp: defaultdict[str, int] = defaultdict(int)
    fp: defaultdict[str, int] = defaultdict(int)
    fn: defaultdict[str, int] = defaultdict(int)
    errors = []
    for case in cases:
        expected = {key(k, v) for k, v in case["expected"]}
        predicted = {key(k, v) for k, _, _, v in detect(case["text"])}
        for k, _ in expected & predicted:
            tp[k] += 1
        for item in predicted - expected:
            fp[item[0]] += 1
            errors.append((case["id"], "false positive", item, case["text"]))
        for item in expected - predicted:
            fn[item[0]] += 1
            errors.append((case["id"], "missed", item, case["text"]))

    def ratio(a: int, b: int) -> float | None:
        return a / b if b else None

    def pct(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.0%}"

    total_tp, total_fp, total_fn = sum(tp.values()), sum(fp.values()), sum(fn.values())
    lines = ["# PII detection evaluation", "",
             f"{len(cases)} labelled test sentences, including deliberate traps. "
             f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M}.", "",
             f"**Overall:** precision {pct(ratio(total_tp, total_tp + total_fp))}, "
             f"recall {pct(ratio(total_tp, total_tp + total_fn))} "
             f"({total_tp} found, {total_fp} false alarms, {total_fn} missed).", "",
             "| Type | Found | False alarms | Missed | Precision | Recall |",
             "| --- | --- | --- | --- | --- | --- |"]
    for t in TYPES:
        lines.append(f"| {t} | {tp[t]} | {fp[t]} | {fn[t]} | {pct(ratio(tp[t], tp[t] + fp[t]))} | "
                     f"{pct(ratio(tp[t], tp[t] + fn[t]))} |")
    lines += ["", "Precision: of the things flagged, how many were really PII. "
              "Recall: of the real PII, how much was caught. For redaction, **recall matters more**: "
              "a missed ID number is a privacy breach, a false alarm is just an over-redacted word.", "",
              "## Every error", ""]
    if not errors:
        lines.append("None.")
    for cid, kind, (t, _value), text in errors:
        lines.append(f"- **{cid}, {kind} `{t}`:** \"{text}\"")
    lines += ["", "## Why these errors happen", "",
              "- **Names outside the list are missed.** Rule-based name matching only knows the names it is given. "
              "A production system would add a named-entity recognition model.",
              "- **Common words that are also names cause false alarms** (\"grace period\"), and the matcher is "
              "case-sensitive, so a lowercase name would be missed.",
              "- **Unusually spaced numbers are missed** when they don't follow the expected grouping."]
    out = ROOT / "reports" / "evaluation.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:5]))
    print(f"Full report: {out}")


if __name__ == "__main__":
    main()
