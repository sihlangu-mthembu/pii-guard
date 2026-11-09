"""Generate the SYNTHETIC sample data (fixed seed, so results are repeatable).

data/tickets.csv        50 fake customer-support tickets containing fake PII
data/test_cases.jsonl   29 hand-designed sentences with the PII each one should contain,
                        including traps (invoice numbers, amounts, dates, "grace period")

All emails use example.com or example.org, domains reserved for examples.
ID, card and phone numbers are randomly generated to pass format checks;
any match with a real person's number would be coincidental.
"""

import csv
import json
import pathlib
import random
from typing import Any

from pii_guard import DEFAULT_NAMES, luhn_valid

ROOT = pathlib.Path(__file__).resolve().parent
rng = random.Random(7)


def luhn_complete(prefix: str) -> str:
    for check in "0123456789":
        if luhn_valid(prefix + check):
            return prefix + check
    raise ValueError(prefix)


def fake_sa_id() -> str:
    yy, mm, dd = rng.randint(60, 99), rng.randint(1, 12), rng.randint(1, 28)
    return luhn_complete(f"{yy:02d}{mm:02d}{dd:02d}{rng.randint(0, 9999):04d}08")


def fake_card() -> str:
    return luhn_complete("4" + "".join(str(rng.randint(0, 9)) for _ in range(14)))


def fake_phone(style: str) -> str:
    digits = f"{rng.choice(['72', '82', '83', '61', '11', '21'])}{rng.randint(0, 999):03d}{rng.randint(0, 9999):04d}"
    return {
        "spaced": f"0{digits[:2]} {digits[2:5]} {digits[5:]}",
        "plain": f"0{digits}",
        "intl": f"+27 {digits[:2]} {digits[2:5]} {digits[5:]}",
        "dashed": f"0{digits[:2]}-{digits[2:5]}-{digits[5:]}",
    }[style]


def not_luhn(n_digits: int) -> str:
    while True:
        s = "".join(str(rng.randint(0, 9)) for _ in range(n_digits))
        if not luhn_valid(s):
            return s


def email(name: str) -> str:
    return f"{name.lower()}.{rng.randint(10, 99)}@{rng.choice(['example.com', 'example.org'])}"


def build_test_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def add(text: str, expected: list[list[str]]) -> None:
        cases.append({"id": f"t{len(cases) + 1:02d}", "text": text, "expected": expected})

    for _ in range(4):
        i = fake_sa_id()
        add(f"Customer ID number is {i}, please verify.", [["SA_ID", i]])
    i = fake_sa_id()
    spaced = f"{i[:6]} {i[6:10]} {i[10:]}"
    add(f"ID: {spaced}", [["SA_ID", spaced]])
    for style in ["spaced", "plain", "intl", "dashed"]:
        p = fake_phone(style)
        add(f"Call me back on {p} after 5pm.", [["PHONE", p]])
    for name in ["Thabo", "Priya", "Johan"]:
        e = email(name)
        add(f"Send the statement to {e} thanks", [["EMAIL", e]])
    c = fake_card()
    add(f"Card ending in {c[-4:]}: full number {c}", [["CARD", c]])
    c = fake_card()
    grouped = " ".join(c[k:k + 4] for k in range(0, 16, 4))
    add(f"Paid with {grouped} yesterday", [["CARD", grouped]])
    add("Hi, this is Lerato from the Durban branch.", [["NAME", "Lerato"]])
    add("Sipho and Naledi both asked about the refund.", [["NAME", "Sipho"], ["NAME", "Naledi"]])
    e, p = email("Zanele"), fake_phone("spaced")
    add(f"Zanele: {e} / {p}", [["NAME", "Zanele"], ["EMAIL", e], ["PHONE", p]])
    # Traps: things that look like PII but are not
    add(f"Invoice {not_luhn(13)} is overdue.", [])
    add("Your account has a 30-day grace period.", [])
    add("Grace Period Notice: your payment is now late.", [])
    add("The amount due is R1 250 000 by 31 March 2026.", [])
    add(f"Order reference {not_luhn(16)} has shipped.", [])
    add("Reply to support at example dot com, not by phone.", [])
    # Cases the rules will miss (honest recall test)
    add("My name is Mandla and I need help.", [["NAME", "Mandla"]])
    add("Mobile: 072 1234 567 (spaced oddly)", [["PHONE", "072 1234 567"]])
    add("Grace from accounts approved it.", [["NAME", "Grace"]])
    e = email("Bongani")
    add(f"Contact Bongani on {e}.", [["NAME", "Bongani"], ["EMAIL", e]])
    i = fake_sa_id()
    add(f"Spouse ID {i} attached.", [["SA_ID", i]])
    add("Nothing personal in this message at all.", [])
    return cases


def build_tickets() -> list[dict[str, str]]:
    issues = ["refund not received", "card declined", "change delivery address",
              "account locked", "double charge", "update phone number"]
    rows = []
    for n in range(1, 51):
        name = rng.choice(DEFAULT_NAMES)
        parts = [f"{name} reports: {rng.choice(issues)}."]
        if rng.random() < 0.6:
            parts.append(f"Reach me at {email(name)}.")
        if rng.random() < 0.5:
            parts.append(f"Phone {fake_phone(rng.choice(['spaced', 'plain', 'intl']))}.")
        if rng.random() < 0.35:
            parts.append(f"My ID is {fake_sa_id()}.")
        if rng.random() < 0.15:
            parts.append(f"Card {fake_card()}.")
        if rng.random() < 0.3:
            parts.append(f"Ref {not_luhn(13)}.")
        rows.append({"ticket_id": f"T{n:03d}", "channel": rng.choice(["email", "chat", "phone"]),
                     "message": " ".join(parts)})
    return rows


def main() -> None:
    cases = build_test_cases()
    with open(ROOT / "data" / "test_cases.jsonl", "w", encoding="utf-8") as fh:
        for c in cases:
            fh.write(json.dumps(c) + "\n")
    rows = build_tickets()
    with open(ROOT / "data" / "tickets.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(cases)} test cases and {len(rows)} synthetic tickets")


if __name__ == "__main__":
    main()
