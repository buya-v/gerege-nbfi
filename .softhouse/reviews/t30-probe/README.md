# `t30-probe` — T30's from-source re-derivation of Path B `B-03` and `B-04`

> **NOT RUN AGAINST A LIVE ORACLE.** No Fineract instance and no PostgreSQL was reachable in the sandbox
> where this was written and run. **Nothing here observes the oracle**, and **no oracle value is synthesized,
> invented or extrapolated**. Every *observed* number is read from a capture already committed on `main`;
> every *derived* number is computed from the pinned Fineract source at `/home/user/fineract`
> @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` (verified: `git log -1` matches, tree clean).
>
> This closes **T22 §10 P1-14, first clause**, which T27 §7 named "the largest remaining hole in the Path B
> evidence" and confirmed needs no running server.

## What was open

T22 §3 re-derived `B-01` and `B-02` digit-for-digit but explicitly did **not** re-derive `B-03`/`B-04`:

> "B-03/B-04 are **not** re-derived here. They run the DAILY + `ACTUAL` + cross-year *partial-period* path
> (`ProgressiveEMICalculator.java:1400-1414`, `calculatePeriodFractions` at `:1550-1568`), which is a
> materially different arm of the code; modelling it honestly is more than this audit's remaining budget."

So two of the four Path B captures — including `B-04`, **the only vector in the whole corpus with
discriminating power over `daysInYearCustomStrategy`** — rested on reproduction and invariants alone. Nobody
had rebuilt them from source.

## What this does

`t30_rederive_b03_b04.py` implements the DAILY / `ACTUAL`-`ACTUAL` arm of the **progressive** generator
(never the cumulative one — that misattribution is a live hazard, T19 item 5), including the cross-year
partial-period branch and the `FEB_29_PERIOD_ONLY` special cases, from the pinned source. Every step carries
its `file:line` citation in the module docstring. It then compares, in **integer minor units with no
tolerance**, against the committed captures.

```sh
python3 .softhouse/reviews/t30-probe/t30_rederive_b03_b04.py   # exit 0
```

Full transcript: `t30-rederive-output.txt`.

## Result — **CONSISTENT**

| capture | `MathContext` | verdict |
|---|---|---|
| `B-03` `FULL_LEAP_YEAR` | `(19, HALF_EVEN)` — the mode the capture actually ran at (T22 §7(b)) | **RE-DERIVED DIGIT-FOR-DIGIT**, 12/12 periods + both totals |
| `B-03` `FULL_LEAP_YEAR` | `(19, HALF_UP)` — the ratified production mode | **RE-DERIVED DIGIT-FOR-DIGIT** |
| `B-04` `FEB_29_PERIOD_ONLY` | `(19, HALF_EVEN)` | **RE-DERIVED DIGIT-FOR-DIGIT** |
| `B-04` `FEB_29_PERIOD_ONLY` | `(19, HALF_UP)` | **RE-DERIVED DIGIT-FOR-DIGIT** |

**The committed `B-03`/`B-04` observations are consistent with the from-source re-derivation.** No
discrepancy was found; there is no adverse finding to report on the numbers.

Two by-products worth carrying forward:

- The identical output at HALF_UP and HALF_EVEN is a **from-source** demonstration that these two captures are
  mode-insensitive. That independently corroborates T22's fresh-tenant re-observation
  (`t22-audit/out-fresh-tenant/`) instead of resting on it. It does **not** make them production-settings
  parity vectors — T22 P0-3/P0-4/P0-6 still block that.
- The final-installment signed residual is `+0.05` on `B-03` and `−0.05` on `B-04`, computed by the rule at
  `ProgressiveEMICalculator.java:1202-1205`. Two more witnesses that the delta is **signed** (T22 P1-12).

## Normative facts the re-derivation establishes

1. **`FEB_29_PERIOD_ONLY` does two things, not one.** Besides capping days-in-year at 365 for a period that
   does not contain 29 February (`getNumberOfDays` `:1346-1353` → `numberOfDaysFeb29PeriodOnly` `:1342-1344`;
   the leap day is tested on the half-open range `(fromDate, dueDate]`, `:1330-1340`), it **suppresses the
   cross-year partial-period calculation** for such a period. `partialPeriodCalculationNeeded`
   (`:1372-1374`, and identically `:1505-1507`) is

   ```
   daysInYearType == ACTUAL
     && (interestPeriodDueDate.year - interestPeriodFromDate.year) > 0
     && (strategy != FEB_29_PERIOD_ONLY || isPeriodContainsFeb29(rpFrom, rpDue))
   ```

   In this corpus that is exactly period 12 (2024-12-01 → 2025-01-01), which contains no 29 February:
   **`B-03` takes the partial arm and `B-04` does not.**

2. **The partial arm is a sum of per-year day fractions, not a single day-count division.**
   `calculatePeriodFractions` (`:1550-1568`) accumulates `Σ days(segment) / Year.length(year)` under the
   tenant `MathContext`, splitting at 31 December (`getFractionPeriodDueDateForEndOfYear` `:1578-1584`,
   because `isInterestRecognitionOnDisbursementDate` is false for these products). For `B-03` period 12 that
   is `30/366 + 1/365` → rate factor `0.0182966988…`, where the non-partial arm would give
   `31/366 → 0.0182950819…`. The result is `rate × fraction` then `setScale(19, mode)`
   (`rateFactorByRepaymentPartialPeriod`, `:1965-1978`) — and note its `interestFractionPerPeriod` multiply is
   **exact**, deliberately without the `MathContext`, unlike every neighbouring operation.

   **A port that implements only fact 1 returns `B-03`'s period-12 numbers for `B-04`, or vice versa.**

3. **The EMI re-adjust loop does not fire on any of these four captures**, and the reason is worth pinning:
   `EmiAdjustment.shouldBeAdjusted()` is `|emiDifference| × 100 > originalEmi.copy(floor(n/2))`, and
   `Money.copy(double)` **replaces** the amount (`Money.java:219-221` → `:215-217`), so the right-hand side is
   `Money(6)`, **not** `EMI × 6`. With a `±0.05` residual, `5 > 6` is false. Reading that `copy` as a multiply
   is the defect that got three T21 probe scripts retracted.

## Method notes (CLAUDE.md compliance)

- Money is exact `decimal.Decimal` throughout. **No floating-point value is constructed anywhere** — the raw
  JSON is parsed with `parse_float=Decimal, parse_int=Decimal`, and every comparison is exact, in integer
  minor units, with **no tolerance**.
- `MoneyHelper.PRECISION = 19` is treated as the compile-time constant it is (`MoneyHelper.java:35`,
  `getMathContext()` `:91-93`); only the rounding mode varies between the two runs.
- The script is read-only with respect to the repository: it writes nothing under `.softhouse/capture/`.
- **Nothing here promotes any capture to the parity vector store.** T22 P0-3, P0-4 and P0-6 remain open, and
  the standing rule that nothing is promoted until the P0 lists are discharged is unchanged.
