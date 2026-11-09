"""Redact PII from a CSV, scan the result for leftovers, and draw a spot-check sample.

Usage:
    python run.py                                   # redacts data/tickets.csv
    python run.py --input my.csv --column message   # your own file and text column
    python run.py --sample 10                       # spot-check sample size

Writes output/<name>_redacted.csv, reports/redaction_summary.md and reports/spot_check.csv.
"""

import argparse
import csv
import pathlib
import random
from collections import Counter

from pii_guard import redact, residual_risks

ROOT = pathlib.Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=ROOT / "data" / "tickets.csv")
    parser.add_argument("--column", default="message")
    parser.add_argument("--sample", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    src = pathlib.Path(args.input)
    with open(src, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    counts: Counter[str] = Counter()
    flagged = []
    for row in rows:
        clean, findings = redact(row[args.column])
        counts.update(kind for kind, *_ in findings)
        row[args.column] = clean
        risks = residual_risks(clean)
        if risks:
            flagged.append((row, risks))

    (ROOT / "output").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    out_csv = ROOT / "output" / f"{src.stem}_redacted.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    sample = random.Random(args.seed).sample(rows, min(args.sample, len(rows)))
    with open(ROOT / "reports" / "spot_check.csv", "w", newline="", encoding="utf-8") as fh:
        sheet = csv.writer(fh)
        sheet.writerow([*rows[0].keys(), "reviewer_ok (Y/N)", "reviewer_note"])
        for row in sample:
            sheet.writerow([*row.values(), "", ""])

    lines = ["# Redaction summary", "",
             f"Redacted {sum(counts.values())} items across {len(rows)} rows of `{src.name}`.", "",
             "| Type | Items redacted |", "| --- | --- |"]
    lines += [f"| {kind} | {n} |" for kind, n in counts.most_common()]
    lines += ["", f"## Residual risk scan: {len(flagged)} rows need a human look", "",
              "These rows still contain long digit runs or an '@' after redaction. "
              "Most will be harmless (order references), but each must be checked before the data is shared.", ""]
    for row, risks in flagged:
        lines.append(f"- `{row.get('ticket_id', '?')}`: {', '.join(risks)}")
    lines += ["", "## Spot check", "",
              f"A random sample of {len(sample)} redacted rows is in `spot_check.csv`, with columns for a reviewer "
              "to mark each row OK or not. Sampling is how QA teams estimate the miss rate on data too large "
              "to review in full."]
    (ROOT / "reports" / "redaction_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:8]))
    print(f"Redacted file: {out_csv}")


if __name__ == "__main__":
    main()
