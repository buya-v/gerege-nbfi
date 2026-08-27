# Driver re-derivation of Path A capture pass 3b — local fire `20260819-200001`

**Purpose.** The driver re-derives rather than accepts a worker's report. Before T8-promote's output could be
checked, the corpus it promotes from had to be checked. This file is that check, run in the main tree while
T8-promote and T20 ran in their own worktrees, and written **before** either reported.

**Source.** `.softhouse/capture/out/capture-prod3b-raw.json`, the 11 production-setting candidates named by
`capture-prod3b-attestation.json` → `productionSettingsCaptureIds`. `P-CAL` is excluded: it is calibration at
(12, HALF_UP) and is on `PIN.json`'s never-promotable list.

## Method — a model built from the documented rules, not from the capture

At `MathContext(19, HALF_UP)`, with `daysInMonth = DAYS_30` and `daysInYear = DAYS_360` on every candidate:

- monthly rate `r = annualNominalInterestRate / 100 x 30 / 360`
- level installment `EMI = P x r / (1 - (1+r)^-n)`, rounded **HALF_UP to 2 dp**
- per period: `interest = HALF_UP(balance x r, 2)`, `principal = EMI - interest`
- final period: `principal = the whole remaining balance` (the balancing remainder), `interest` as above

Nothing was read from the `observed` block into the model. The model was run first and the observed rows
compared afterwards.

## Result — 11 of 11 reproduce, digit for digit

| case | EMI derived | rows | total interest |
|---|---|---|---|
| `P-00` | `17.01` | MATCH | MATCH `2.05` |
| `P-01` | `5613766.78` | MATCH | MATCH `13393481.04` |
| `P-02` | `17.01` | MATCH | MATCH `2.05` |
| `P-02b` | `17.01` | MATCH | MATCH `2.05` |
| `P-03` | `20.35` (see below) | MATCH | MATCH `1.76` |
| `P-04f` | `17.01` | MATCH | MATCH `2.05` |
| `P-04t` | `17.01` | MATCH | MATCH `2.05` |
| `P-MNT-5M` | `320221.91` | MATCH | MATCH `763994.33` |
| `P-MNT-1M2` | `112082.37` | MATCH | MATCH `144988.47` |
| `P-MNT-50M` | `1777663.51` | MATCH | MATCH `13995886.40` |
| `P-MNT-4M999` | `320221.84` | MATCH | MATCH `763994.20` |

`[VERIFIED: driver re-derivation at (19, HALF_UP), main tree, this fire]`

The corpus is internally consistent with the rules DEC-1 documents. **This does not make any of it correct
by itself** — it makes the capture and the specification agree, which is the precondition for promotion, not
a substitute for it.

## Three graders in the set kill a wrong port at ZERO money margin

This is T55-N2's lesson (*pair difference is the wrong promotion filter*) arriving again from a different
direction, and it decides how `graded_against` must be written for these vectors.

### `P-02` / `P-02b` — the month-end re-anchor, discriminated purely in the date column

Both run `DAYS_30`/`DAYS_360`, so every period is exactly 30/360 **regardless of the calendar dates**. The
money columns of `P-00`, `P-02` and `P-02b` are consequently identical — `16.43 / 16.52 / 16.62 / 16.72 /
16.81 / 16.90` principal, `0.58 / 0.49 / 0.39 / 0.29 / 0.20 / 0.10` interest, `2.05` total.

The discrimination is entirely in `due_date`:

- `P-02`, seed day **31**: period 1 due `2024-02-29` (clamped), period 2 due **`2024-03-31`** — re-anchored
  on the disbursement-date seed, not continued from the clamped day.
- `P-02b`, seed day **30**: period 1 due `2024-02-29` (clamped), period 2 due **`2024-03-30`**.

A port that clamps and then continues from the clamped day emits `2024-03-29` in both cases, and every later
due date with it. **`margin_minor` is `"0"` and the vector still kills that port.** A non-zero margin here
would be fabricated.

### `P-03` — the row-ordering boundary, also at zero money margin

`scheduleGenerationStartDate = 2024-01-01`, `disbursementDate = 2024-02-01`. The oracle emits, in order:

1. `REPAYMENT` 1, `2024-01-01 -> 2024-02-01`, **all money zero**
2. `DISBURSEMENT`, `2024-02-01`, principal `100.00`
3. `REPAYMENT` 2 ... 6

The disbursement is dated **exactly on repayment 1's due date** and is emitted **after** it. The naive
"sort by date, disbursement first" rule — the obvious thing for a Go port to write — puts it first and is
refuted here at a reachable boundary. Zero money margin; structural kill.

## `P-03` also carries a NON-zero-margin counterfactual worth pricing

`numberOfRepayments` is **6**, but the EMI is computed over the **5** periods that remain after the
disbursement date, not over 6:

- over 5 periods: `100 x r / (1 - (1+r)^-5)` → **`20.35`** — the observed installment
- over 6 periods: → `17.01` — what a port using `numberOfRepayments` unconditionally would emit

Period 2 principal is then `19.77` observed against `17.01 - 0.58 = 16.43` counterfactual: **334 minor
units** on the first paying period alone, and the schedule never amortizes to zero. `[VERIFIED: driver
re-derivation]`

The empty leading period carries `totalOutstandingBalance = 101.76` = principal `100.00` + the full
`1.76` of interest yet to accrue, recorded before any payment.

## What this file does NOT license

Nothing here may be transcribed into a vector. Every `expect` cell must still come from the capture verbatim.
These derivations exist to **check** the promotion, and to price counterfactuals — which are claims about
hypothetical wrong ports, never claims about the oracle.
