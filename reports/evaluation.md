# PII detection evaluation

29 labelled test sentences, including deliberate traps. Generated 2026-11-01 19:40.

**Overall:** precision 96%, recall 92% (24 found, 1 false alarms, 2 missed).

| Type | Found | False alarms | Missed | Precision | Recall |
| --- | --- | --- | --- | --- | --- |
| SA_ID | 6 | 0 | 0 | 100% | 100% |
| CARD | 2 | 0 | 0 | 100% | 100% |
| PHONE | 5 | 0 | 1 | 100% | 83% |
| EMAIL | 5 | 0 | 0 | 100% | 100% |
| NAME | 6 | 1 | 1 | 86% | 86% |

Precision: of the things flagged, how many were really PII. Recall: of the real PII, how much was caught. For redaction, **recall matters more**: a missed ID number is a privacy breach, a false alarm is just an over-redacted word.

## Every error

- **t20, false positive `NAME`:** "Grace Period Notice: your payment is now late."
- **t24, missed `NAME`:** "My name is Mandla and I need help."
- **t25, missed `PHONE`:** "Mobile: 072 1234 567 (spaced oddly)"

## Why these errors happen

- **Names outside the list are missed.** Rule-based name matching only knows the names it is given. A production system would add a named-entity recognition model.
- **Common words that are also names cause false alarms** ("grace period"), and the matcher is case-sensitive, so a lowercase name would be missed.
- **Unusually spaced numbers are missed** when they don't follow the expected grouping.