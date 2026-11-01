# Redaction summary

Redacted 132 items across 50 rows of `tickets.csv`.

| Type | Items redacted |
| --- | --- |
| NAME | 50 |
| EMAIL | 33 |
| PHONE | 27 |
| SA_ID | 15 |
| CARD | 7 |

## Residual risk scan: 19 rows need a human look

These rows still contain long digit runs or an '@' after redaction. Most will be harmless (order references), but each must be checked before the data is shared.

- `T001`: 6507529170342
- `T002`: 6563212233079
- `T005`: 1177774121547
- `T015`: 6134125242731
- `T017`: 3114402426462
- `T020`: 7167868433532
- `T022`: 8014126906044
- `T024`: 8890931002516
- `T025`: 1881817414333
- `T026`: 2544992070741
- `T030`: 5166915640410
- `T032`: 2138783757628
- `T039`: 5378383064003
- `T040`: 5656304813734
- `T041`: 6092603092600
- `T046`: 9045440910317
- `T047`: 2361078852611
- `T048`: 7938144494544
- `T050`: 4310399315827

## Spot check

A random sample of 10 redacted rows is in `spot_check.csv`, with columns for a reviewer to mark each row OK or not. Sampling is how QA teams estimate the miss rate on data too large to review in full.