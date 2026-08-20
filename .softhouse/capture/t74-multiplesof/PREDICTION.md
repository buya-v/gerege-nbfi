# Pass 3i — the prediction, registered BEFORE the capture ran

Task **T74**. Pattern **P-9**: this file and `predicted.json` are committed to
`softhouse/T74-pathA-multiplesof` **one commit before** `run-pass3i.sh` is executed, so that
"we predicted this" is checkable in the git history rather than narrated afterwards.
`check-prediction.py` grades the capture against `predicted.json` and prints every mismatch.

> "The oracle" is the Fineract reference implementation this program grades Go output against.
> Oracle Database is a prohibited product here. PostgreSQL is the only permitted database; this
> seam is a library call and opens no database connection at all.

**A refuted prediction is a result, not a failure.** Whatever the oracle says is what goes in the
handoff, and where this document is wrong the handoff says which line was wrong.

---

## 1. What pass 3i changes, and why the change is what makes any of this predictable

Every Path A harness from `Capture3.java` through `Capture3h.java` carried a **single** field,
`installmentMultiplesOf`, and spent it in three places:

```java
new CurrencyData(code, code, digits, c.installmentMultiplesOf(), code, code)   // -> inMultiplesOf
...
c.installmentMultiplesOf(),   // -> LoanRepaymentScheduleModelData installmentAmountInMultiplesOf
...
"currencyInMultiplesOf":          c.installmentMultiplesOf()
"installmentAmountInMultiplesOf": c.installmentMultiplesOf()
```

That is T21 required change **P1-8**, which is T19 required change **10**, unfixed for six passes.
The consequence is not cosmetic: **two unrelated rounding mechanisms shared one slot**, so no
capture taken through those harnesses could say which of them moved a number.

`Capture3i.java` gives them separate components, separate constructor arguments and separate
emitted keys, and `run-pass3i.sh` refuses a run in which the emitted pair is not demonstrably
independent (precondition 16).

## 2. The two mechanisms, read out of the pinned checkout

**Channel 1 — the `Money` constructor leak.**

```java
// Money.java:44-52, at 426a23544e8426a38ae43ae404670a0a7e85b9eb
BigDecimal amountScaled = amountZeroed.stripTrailingZeros();
if (currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0
        && currency.getInMultiplesOf() > 0 && MathUtil.isGreaterThanZero(amountScaled)) {
    amountScaled = roundToMultiplesOf(amountScaled, currency.getInMultiplesOf());
}
this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode());
```

with

```java
// Money.java:150-157
public static BigDecimal roundToMultiplesOf(final BigDecimal existingVal, final Integer inMultiplesOf) {
    ...
    if (inMultiplesOfValue.compareTo(BigDecimal.ZERO) > 0) {
        amountScaled = existingVal.divide(inMultiplesOfValue, 0, MoneyHelper.getRoundingMode()).multiply(inMultiplesOfValue);
    }
```

Four properties matter and each is separately probed below.

1. It is gated on the **currency's** `decimalPlaces == 0`. MNT is minor unit 2, so it is **shut in
   production**.
2. It rounds to the **nearest** multiple, under **`MoneyHelper.getRoundingMode()`** — the *tenant's*
   mode, not the threaded `MathContext`'s.
3. It lives in the **private constructor**, so it fires on **every** `Money` the calculation builds:
   principal, interest, installment, balance, plan totals.
4. It has **no zero-guard**. If the rounding takes a positive amount to zero, zero is what you get.

**Channel 2 — the installment rounding.**

```java
// ProgressiveEMICalculator.java:1761-1776
private Money applyInstallmentAmountInMultiplesOf(final ProgressiveLoanInterestScheduleModel scheduleModel,
        final Money equalMonthlyInstallment) {
    return scheduleModel.installmentAmountInMultiplesOf() != null && scheduleModel.installmentAmountInMultiplesOf() > 0
            ? safeRoundingForEMI(equalMonthlyInstallment, scheduleModel.installmentAmountInMultiplesOf())
            : equalMonthlyInstallment;
}
private Money safeRoundingForEMI(final Money unRoundedEMI, final Integer multiplesOf) {
    final Money roundedEMI = Money.roundToMultiplesOf(unRoundedEMI, multiplesOf);
    if (roundedEMI.isZero() && unRoundedEMI.isGreaterThanZero()) {
        return unRoundedEMI;
    }
    return roundedEMI;
}
```

It is gated on the **schedule model's** field, it touches the **equal monthly installment only**,
and it **has** the zero-guard channel 1 lacks.

**And on the Path A seam it never fires at all.** The model's `installmentAmountInMultiplesOf` comes
from `loanApplicationTerms.getInstallmentAmountInMultiplesOf()`
[`ProgressiveLoanScheduleGenerator.java:108-110`], and the entry point this seam uses,
`LoanApplicationTerms.assembleFrom(LoanRepaymentScheduleModelData, MathContext)`
[`:579-607`], builds exclusively through `Builder` and contains **zero** occurrences of
`MultiplesOf`; the `Builder` has no setter for it and the field's only assignment is at `:828`, in
a positional constructor this path never reaches.

## 3. Two corrections to the brief that dispatched this task, made before running anything

Pattern **P-16**: a number copied from the artefact under review is that artefact's claim, not
evidence. Both of these were checked against the pinned source.

1. **The brief quotes the `Money.java:48-51` guard as three conjuncts**
   (`inMultiplesOf != null && getDecimalPlaces() == 0 && inMultiplesOf > 0`). **There are four.**
   The fourth is `MathUtil.isGreaterThanZero(amountScaled)` at `:49`. It is inert on a schedule,
   because rounding zero to a multiple yields zero anyway and no cell here is negative — but a Go
   port that reproduced only three conjuncts would differ from the oracle on any negative amount,
   and a document that lists three is the document the next contributor copies.
2. **The brief cites `Money.java:159-171` for the installment rounding.** `:159-161` is a two-argument
   overload that delegates to `:163-170`, which is the one that does the arithmetic; `:171` is blank.
   The substantive difference between the two `roundToMultiplesOf` overloads is not the line range:
   the `BigDecimal` form at `:150-157` reads `MoneyHelper.getRoundingMode()` **directly**, while the
   `Money` form at `:163-170` takes the mode from a `MathContext` **parameter**, defaulted at `:160`
   to `MoneyHelper.getMathContext()`. Under our ratified tenant both are HALF_UP, so no capture in
   this pass can separate them; that is recorded as a follow-up rather than claimed as tested.

## 4. The registered predictions

`predicted.json` is the machine-checkable form. In prose:

### Identities — `observed` equal cell for cell

| case | must equal | because |
|---|---|---|
| `T74-A2-DP0-INST100` | `T74-A0-DP0-NONE` | channel 2 is unreachable on this seam |
| `T74-A3-DP0-BOTH100` | `T74-A1-DP0-CUR100` | same — adding the installment field adds nothing |
| `T74-B1-DP2-CUR100` | `P-CAL-MNT5M` | channel 1 shut at `decimalPlaces = 2` |
| `T74-B2-DP2-INST100` | `P-CAL-MNT5M` | both channels off |
| `T74-B3-DP2-BOTH100` | `P-CAL-MNT5M` | both channels off |
| `T74-C1-DP0-CUR1` | `T74-A0-DP0-NONE` | rounding to multiples of 1 is inert at scale 0 |
| `T74-C2-DP0-CUR0` | `T74-A0-DP0-NONE` | `inMultiplesOf > 0` is false |
| `T74-C3-DP0-CURNEG` | `T74-A0-DP0-NONE` | same conjunct, negative side |
| `T74-D2-DP0-SMALL-INST1000` | `T74-D0-DP0-SMALL-NONE` | channel 2 unreachable |

**The B row is the one with the production consequence.** If it holds, then at MNT's real minor unit
of 2 **neither** multiples-of input can move a single cell through this seam, and no vector over
either of them can grade anything.

### Differences

`T74-A1-DP0-CUR100` ≠ `T74-A0-DP0-NONE`; `T74-C4-DP0-CUR7` ≠ A0; `T74-C5-DP0-CUR1000` ≠ A0;
`T74-D1-DP0-SMALL-CUR1000` ≠ `T74-D0-DP0-SMALL-NONE`; and `T74-A0-DP0-NONE` ≠ `P-CAL-MNT5M`
(different quantization scale — a difference that has nothing to do with either multiples-of input,
predicted here so it cannot later be mistaken for one that does).

### Full schedules, cell for cell

`T74-A0-DP0-NONE` and `T74-A1-DP0-CUR100` must reproduce **arms A and B of T21's section-B probe**
exactly — 19 rows each, every column, plus term, disbursed, interest and repayment:
**763994 against 764100 total interest**, period 1 at `243139 / 77083 / 320222` against
`243100 / 77100 / 320200`, and so on
[`.softhouse/reviews/t21v2/t21v2-probe-oracle-out.txt` §B, transcribed by `extract-t21v2-AB.py`].

This is the strongest half of the prediction and it does two things at once: it reproduces T21's
observation independently, and — because pass 3i's fields are **separated** — it attributes the
whole movement to `CurrencyData.inMultiplesOf` alone.

### Multiple-of structure

Every money cell of `T74-A1`, `T74-A3` is an exact multiple of **100**; of `T74-C4`, of **7**; of
`T74-C5` and `T74-D1`, of **1000**.

**This is the SCOPE argument, and it is what pins channel 1 rather than merely observing it.**
Channel 2 rounds the installment and nothing else. It could not make the **interest** column a
multiple of anything. If the interest column comes back quantized, the operative mechanism is the
constructor, not the installment rounding.

The modulus 7 matters separately: a port that implemented "round to multiples of *m*" by shifting a
decimal scale gets powers of ten right and 7 wrong.

### Group E totals — the `36 × 16.8 %` shape (T21 P1-11)

| principal (MNT) | predicted p19 interest | predicted p12 interest |
|---|---|---|
| 4.00 | `1.14` | `1.13` |
| 59.00 | `16.51` | `16.52` |
| 72.00 | `20.14` | `20.13` |
| 340.00 | `95.15` | `95.16` |
| 426.00 | `119.18` | `119.20` |
| 6,940.00 | `1942.65` | `1942.66` |

[`t21v2-probe2-oracle-out.txt`]. Predicting these is also a **P-16 check on T21's own transcript**:
twelve numbers from a document under this task's review, re-put to the oracle.

### Sharp claims

- **S1** — `T74-D1` total interest is `0`, and every repayment row's interest is `0`.
- **S2** — `T74-D1` has **exactly one** repayment row with non-zero principal: period 6, principal
  `1000`, interest `0`, total `1000`, balance `0`; periods 1–5 carry `0/0/0` with balance `1000`.
  Derivation in `predicted.json`, from `:1178-1181`, `:1202-1210`, `:1779-1788` and
  `EmiAdjustment.java:32-35`.
- **S3** — at least **five** of `T74-D1`'s six mechanism rows report `emi == 0`. **This is the
  observation that tells the two mechanisms apart**: `safeRoundingForEMI` exists precisely to stop a
  positive EMI rounding to zero, and it does not protect these rows, because the rounding that
  zeroed them is not the one it wraps.
- **S4** — `pathIdentity.identical` true on all 36 cases; ambient MoneyHelper `(19, ordinal 4)` on
  every one.
- **S5** — `T74-A1` period 1 interest is `77100`, not `77083` and not `77000`. Separates
  nearest-multiple from floor. It does **not** separate HALF_UP from HALF_EVEN, and the claim does
  not pretend to.
- **S6** — all six group-E pairs differ from their precision-12 companion in at least one money cell.
  If any comes back identical, T21 §6.2's refutation of the "size threshold" claim is weakened and
  the handoff must say so.

## 5. What this pass CANNOT settle, stated before the numbers arrive

- **Whether channel 1 reads the tenant mode or the threaded mode.** Separating them needs a case
  whose threaded `MathContext` mode differs from its tenant mode, and the runner's precondition 9 —
  correctly — refuses any case not at HALF_UP ordinal 4 in both. Weakening that check to answer this
  question would trade a standing guard for one observation. Recorded as a follow-up.
- **Anything about channel 2's actual behaviour.** The seam never delivers its input, so every
  statement about `safeRoundingForEMI` in this document is read from source and stays
  `[UNVERIFIED-BY-CAPTURE]` on Path A. Path B is where it can be observed, and T22 recorded it there.
- **Whether any of this may be promoted.** Promotion is decided against the frozen contract and
  `.softhouse/vectors/capabilities.json`, not against how interesting a number is.
