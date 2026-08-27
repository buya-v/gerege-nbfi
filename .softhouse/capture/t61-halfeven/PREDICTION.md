# T61 — the prediction, recorded BEFORE the capture

**This file is committed before `run-pass3f.sh` is run against the reference oracle (Fineract).**
Its git history is the evidence that the numbers below were written down first. T11's precedent:
a prediction the oracle then confirms is much stronger evidence than a capture rationalised
afterwards.

> "The oracle" is the Fineract reference implementation. Oracle Database is a prohibited product
> in this program and appears nowhere in this stack. PostgreSQL is the only permitted database;
> this seam opens no database connection at all.

## What is being predicted, and why this shape

Mutation **M7 `MONEY-QUANTIZATION-HALF-EVEN`** — a port that applies `HALF_EVEN` where the oracle
applies the tenant's ratified `HALF_UP` at `Money.java:52` — **survives all 29 promoted parity
vectors** (`.softhouse/conformance.sh` exit 0). That is a blind spot in the CORPUS.

`HALF_UP` and `HALF_EVEN` differ **only on an exact tie**, and only when the truncated value is
even. So the shape must make the money quantization land exactly on a half-minor-unit boundary.

Derived from source rather than searched for. On an on-lattice `FIXED_30_360` monthly loan the
period-1 rate factor is exactly

    r = 0.018            (21.6% p.a., i.e. Rate{27,125}; 30/360 per period)

so period-1 interest in **minor units** is `18 * B / 1000`, where `B` is the principal in minor
units. That is an exact tie when

    18*B  ==  500  (mod 1000)      i.e.   B == 250 (mod 500)

and the two modes disagree only when `floor(18*B/1000)` is **even**.

`B = 100005250` satisfies both: `100005250 mod 500 = 250`, and `18*B/1000 = 1800094.5` with
`1800094` even. The same algebra is what `.softhouse/vectors/capabilities.json` already records
under `rounding.half.even` for principal MNT 1,162,502.50, from the other direction.

A 40,001-shape sweep of the Go port against the mutant (`.softhouse/handoff/T61-sweep/`) then
confirmed 104 separating shapes in 2,001 consecutive principals; the three below are the ones put
to the oracle.

## THE SHARP PREDICTION

**`T61-HE-B`, period 1, interest: the oracle will emit `18000.95`, not `18000.94`.**

The unrounded value is exactly `18000.945`. `HALF_UP` takes the tie away from zero and gives
`18000.95`; `HALF_EVEN` takes it to the even neighbour and gives `18000.94`. **Margin 1 minor
unit at that cell, and the divergence then compounds through the schedule.**

If the oracle emits `18000.94`, the prediction is WRONG, the ratified tenant rounding mode is not
what reaches this call site, and that is a finding to report loudly — not to reconcile.

## The three shapes, and the full schedule predicted for each

All three are strictly inside DEC-1's graded domain and are ordinary MNT loans: single
disbursement on the schedule start date, `RepaymentEvery` 1 `MONTHS`, `DECLINING_BALANCE`,
`FIXED_30_360`, no down payment, no installment rounding, MNT 2 decimals, `(19, HALF_UP)`.
Only the principal moves; `21.6%` and six repayments are already in the corpus.

Money below is **int64 minor units**.

```
T61-HE-A  principal_minor=100054150  n=6  rate=27/125  start=2024-01-01
  kind           no   from         due               principal       interest      outstanding
  DISBURSEMENT   0    2024-01-01   2024-01-01        100054150              0        100054150
  REPAYMENT      1    2024-01-01   2024-02-01         15940901        1800975         84113249
  REPAYMENT      2    2024-02-01   2024-03-01         16227838        1514038         67885411
  REPAYMENT      3    2024-03-01   2024-04-01         16519939        1221937         51365472
  REPAYMENT      4    2024-04-01   2024-05-01         16817298         924578         34548174
  REPAYMENT      5    2024-05-01   2024-06-01         17120009         621867         17428165
  REPAYMENT      6    2024-06-01   2024-07-01         17428165         313707                0

T61-HE-B  principal_minor=100005250  n=6  rate=27/125  start=2024-01-01
  kind           no   from         due               principal       interest      outstanding
  DISBURSEMENT   0    2024-01-01   2024-01-01        100005250              0        100005250
  REPAYMENT      1    2024-01-01   2024-02-01         15933110        1800095         84072140
  REPAYMENT      2    2024-02-01   2024-03-01         16219906        1513299         67852234
  REPAYMENT      3    2024-03-01   2024-04-01         16511865        1221340         51340369
  REPAYMENT      4    2024-04-01   2024-05-01         16809078         924127         34531291
  REPAYMENT      5    2024-05-01   2024-06-01         17111642         621563         17419649
  REPAYMENT      6    2024-06-01   2024-07-01         17419649         313554                0

T61-HE-C  principal_minor=100008950  n=6  rate=27/125  start=2024-01-01
  kind           no   from         due               principal       interest      outstanding
  DISBURSEMENT   0    2024-01-01   2024-01-01        100008950              0        100008950
  REPAYMENT      1    2024-01-01   2024-02-01         15933700        1800161         84075250
  REPAYMENT      2    2024-02-01   2024-03-01         16220506        1513355         67854744
  REPAYMENT      3    2024-03-01   2024-04-01         16512476        1221385         51342268
  REPAYMENT      4    2024-04-01   2024-05-01         16809700         924161         34532568
  REPAYMENT      5    2024-05-01   2024-06-01         17112275         621586         17420293
  REPAYMENT      6    2024-06-01   2024-07-01         17420293         313565                0
```

## What the HALF_EVEN mutant produces instead, cell for cell

Measured by re-running the identical shapes through a scratch copy of the port with `M7` applied
(`.softhouse/handoff/T61-sweep/run-sweep.py M7`). **These are DERIVED counterfactual values, never
observed, and no vector may transcribe them as an observation.**

| shape | cell | predicted (true, HALF_UP) | counterfactual (HALF_EVEN) | margin (minor) |
|---|---|---|---|---|
| `T61-HE-A` | period 1 principal | 15940901 | 15940900 | 1 |
| `T61-HE-A` | period 2 outstanding | 67885411 | 67885413 | 2 |
| `T61-HE-A` | period 3 outstanding | 51365472 | 51365475 | 3 |
| `T61-HE-A` | (widest cell in the schedule) | — | — | **6** |
| `T61-HE-B` | **period 1 interest** | **1800095** | **1800094** | **1** |
| `T61-HE-B` | period 3 outstanding | 51340369 | 51340371 | 2 |
| `T61-HE-B` | (widest cell in the schedule) | — | — | **4** |
| `T61-HE-C` | period 1 principal | 15933700 | 15933699 | 1 |
| `T61-HE-C` | period 3 outstanding | 51342268 | 51342271 | 3 |
| `T61-HE-C` | (widest cell in the schedule) | — | — | **5** |

## What this capture does NOT claim

It does not grade precision 19 against precision 12, and it does not grade a request configured
with `HALF_EVEN` — the capability `rounding.half.even` stays outside the graded domain, and these
requests are `HALF_UP` requests. What is graded is a **port** that applies the wrong tie rule at
the currency quantization while being handed a `HALF_UP` request. That is a `schedule.core`
counterfactual.
