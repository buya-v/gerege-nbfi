# T37 — provenance and storage status of these captures

## Status: RAW OBSERVED FORM ONLY. NOT vector-store entries.

DEC-1 (`docs/adr/DEC-1-schedule-generator-adapter.md`) is at **revision 6 and UNRATIFIED** —
user gate **G-1** is open. While a contract gate is open, a capture may **not** be stored in
contract-shaped form, because the shape is precisely what is being ratified. What is stored
here is therefore exactly three things per capture:

1. the **raw observed output**, verbatim, at the scale the oracle returned
   (`out/t37-binding.json`, and the unsplit stdout in `out/t37-binding-raw.json`);
2. the **request that produced it**, as an `inputs` block on the same record — every one of the
   nineteen oracle inputs plus the tenant, its rounding-mode ordinal, its timezone, and the
   ambient `MathContext` the oracle reported back;
3. the **provenance**: this file, `ATTESTATION.md` and `REPRODUCE.md`.

**Nothing here is promoted to `.softhouse/vectors/`.** Promotion is a separate decision that
belongs after G-1 closes, and it is not this task's to make.

## What is an observation here, and what is not

| Artefact | Status |
|---|---|
| `out/t37-binding.json`, `out/t37-binding-raw.json`, `out/t37-binding-log.txt` | **OBSERVATIONS** from the pinned reference oracle (Fineract), Path A |
| `analysis/dec1_readings.py`, `analysis/select_shapes.py`, `analysis/discriminate.py` and their `-output.txt` files | **RE-DERIVATIONS.** No oracle is contacted by any of them. A figure they print for a reading is a prediction of that reading, never an oracle output |

The capture program **asserts nothing and predicts nothing**: no expected value appears anywhere
in `src/CaptureBinding.java`. Every number in `out/` is what the oracle emitted, rendered with
`BigDecimal.toPlainString()`.

## Where the shapes came from

Each of the five binding items names a *candidate shape* in DEC-1 §8 or in the review that
raised it. Those candidates are **re-derivations by earlier tasks, never observations**. This
task used them only as starting points, checked with `analysis/select_shapes.py` that each one
actually separates the readings it claims to (a re-derivation, before any capture was spent),
and then **captured** it. The captures are the evidence; the candidates were only the shopping
list.

| Item | Shape | Named in |
|---|---|---|
| 3 | MNT 1,014,632 / 6 × 7.0 %; MNT 127,704 / 36 × 16.8 % | DEC-1 §8 item 3, from `.softhouse/reviews/T23-DEC-1-v2-rereview.md` §6.1 |
| 3a | MNT 100,025 / 12 × 16.8 % | DEC-1 §8 item 3a, from T26's sweep |
| 3b | MNT 13,202 / 6 × 16.8 %; MNT 3,924,149 / 6 × 16.8 % (31 Jan seed) | DEC-1 §8 item 3b / `.softhouse/reviews/T29-DEC-1-v4-rereview.md` |
| 3c | MNT 10,548,069 / 6 × 16.8 %, disb 2024-02-01; MNT 13,549,647 / 6 × 21.6 %, disb 2024-02-01 | DEC-1 §8 item 3c / T29 |
| 3d | MNT 1,200,000 / 6 × 21.6 %, disb 2024-01-15; MNT 127,704 / 36 × 16.8 %, disb 2024-01-20 | DEC-1 §8 item 3d / `.softhouse/reviews/T32-DEC-1-v5-rereview.md` §4 |

All eleven cases are inside DEC-1 §3.1's **graded domain**: `MinorUnitDigits` 2, `(19, HALF_UP)`
(except the labelled calibration), one disbursement, `RepaymentEvery` 1, MONTHS,
DECLINING_BALANCE, fixed 30/360, zero down payment, `InstallmentRoundingMultipleMinor` 0, and
`ScheduleStartDate ≤ Disbursement.Date < the last repayment period's DueDate`. §3.1's note that
the embeddable seam does not honour a non-zero installment multiple is respected by pinning it
to zero (`currencyInMultiplesOf: null`, `installmentAmountInMultiplesOf: null`).
