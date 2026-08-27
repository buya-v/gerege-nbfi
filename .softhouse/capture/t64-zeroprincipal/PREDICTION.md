# T64 — the prediction, recorded BEFORE the capture

**This file and `predicted-schedules.json` are committed BEFORE `run-pass3g.sh` is run against the
reference oracle (Fineract).** Its git history is the evidence that the numbers below were written
down first (pattern **P-9**, T61's precedent). A prediction the oracle confirms is much stronger
evidence than a capture rationalised afterwards; a prediction the oracle **refutes** is a FINDING,
and this file will not be retuned to match.

> "The oracle" is the Fineract reference implementation. Oracle Database is a prohibited product in
> this program and appears nowhere in this stack. PostgreSQL is the only permitted database; this
> seam opens no database connection at all.

---

## 1. What is being predicted, and why this shape

T59 found `applyFinalPeriodResidual` — a faithful port of
`ProgressiveEMICalculator.java:1160-1219` — is O(n²) on **near-interest-only** shapes (n=1100 →
2.31 s, 929 zero-principal rows, 34.9 % cumulative in the profile) and correctly declined to fix it,
because **no vector grades that shape**.

That is a blind spot in the CORPUS, and it is measurable: across all 32 promoted parity vectors the
longest term is **n = 36** and the smallest principal is **MNT 100.00** (`P-DRIFT-F`,
10,000 minor units). Not one promoted vector contains a REPAYMENT row whose `principal_minor` is
`0`, and not one contains a REPAYMENT row after the loan has already amortized to zero.

This capture asks the oracle for four shapes that do.

---

## 2. Derivation from the pinned Java source

Every line number below was re-opened in `/Users/buv/fineract` at the pinned commit
`426a23544e8426a38ae43ae404670a0a7e85b9eb`, clean tree.

### 2.1 A repayment row's principal is `max(0, EMI − dueInterest)`

```java
public Money getDuePrincipal() {
    // Due principal might be the maximum paid if there is pay-off or early repayment
    return MathUtil.max(MathUtil
            .negativeToZero(getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().minus(getDueInterest(), getMc()), getMc()),
            getPaidPrincipal(), false);
}
```
[VERIFIED: `fineract-progressive-loan/.../calc/data/RepaymentPeriod.java:345-350`]

On the Path A origination seam nothing is paid and nothing is credited, so
`getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest()` is just the period's EMI and
`getPaidPrincipal()` is zero. **Principal is therefore exactly `EMI − dueInterest`, clamped at
zero.** There is no "final principal := remaining balance" rule — pattern P-6 established that
already.

**So a row amortizes exactly zero principal with non-zero interest iff its quantized EMI equals its
quantized due interest** (or is smaller, in which case the `negativeToZero` clamp fires).

### 2.2 Both quantities are quantized to the currency scale before they meet

The EMI is built through `Money.of(...)`:

```java
final Money equalMonthlyInstallment = Money
        .of(outstandingBalance.getCurrencyData(), calculateEMIValue(rateFactorN, outstandingBalance.getAmount(), fnResult, mc), mc)
        .add(calculateEMIValueForFixedInterest(repaymentPeriods, mc));
```
[VERIFIED: `ProgressiveEMICalculator.java:1731-1733`]

and every `Money` quantizes in its constructor:

```java
this.amount = amountScaled.setScale(currency.getDecimalPlaces(), getMc().getRoundingMode());
```
[VERIFIED: `fineract-core/.../organisation/monetary/domain/Money.java:52`]

The due interest is quantized the same way at
[VERIFIED: `RepaymentPeriod.java:252-265`, `calculateCalculatedDueInterest()` → `Money.of(..., mc)`
then `MathUtil.negativeToZero`].

For MNT, `decimalPlaces` is 2 and the tenant mode is the ratified `HALF_UP`, so both land on a whole
minor unit.

### 2.3 Condition A — the exact EMI/interest gap must close below half a minor unit

Writing `B` for the principal in **minor units** and `r` for the per-period rate factor
(`FIXED_30_360`, `RepaymentEvery` 1 `MONTHS`, so `r = annual/12` exactly on this lattice):

* exact period-1 interest = `B·r`
* exact EMI = `B·r·(1+r)ⁿ / ((1+r)ⁿ − 1)`  — the oracle folds this rather than using `pow`
  [VERIFIED: `ProgressiveEMICalculator.java:1816-1827`, fold at `:1827`; `calculateEMIValue` at
  `:1838-1840`]
* exact gap = `EMI − interest₁ = B·r / ((1+r)ⁿ − 1)`, which is **strictly positive for every finite
  n**.

So the two can only quantize to the same minor unit if the gap is under half a minor unit, which
needs

> **(1+r)ⁿ > 1 + 2·r·B**

and the interest must itself quantize to at least 1 minor unit, which needs `B·r ≥ 0.5`, i.e.

> **B ≥ ceil(0.5 / r) =: B_min**

### 2.4 Condition B — the EMI smoothing loop must not undo it

If every row amortizes zero principal the balance never moves, so
`calculateLastUnpaidRepaymentPeriodEMI` dumps the entire principal onto the last period's EMI:

```java
Money diff = totalDisbursedAmount.plus(totalCapitalizedIncome, mc).plus(scheduleModel.getTotalCreditedPrincipal(), mc)
        .plus(totalDueInterest, mc).minus(totalEMI, mc);
Money adjustedEmi = repaymentPeriod.getEmi().add(diff, mc);
```
[VERIFIED: `ProgressiveEMICalculator.java:1202-1205`]

`checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` then sees a last-vs-penultimate EMI difference
of ≈ `B` and wants to spread it:

```java
public boolean shouldBeAdjusted() {
    double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);
    return lowerHalfOfRelatedPeriods > 0.0 && !emiDifference.isZero() && emiDifference.abs()
            .multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods));
}
public Money adjustment()  { return emiDifference.dividedBy(Math.max(1, numberOfRelatedPeriods() - uncountablePeriods)); }
public Money adjustedEmi() { return originalEmi.plus(adjustment()); }
```
[VERIFIED: `fineract-progressive-loan/.../calc/data/EmiAdjustment.java:31-43`]

`uncountablePeriods` counts periods where `originalEmi < totalPaidAmount`
[VERIFIED: `ProgressiveEMICalculator.java:2027-2031`]; at origination nothing is paid, so it is
**0**.

The loop then breaks without doing anything if the spread EMI quantizes back to where it started:

```java
Money adjustedEqualMonthlyInstallmentValue = applyInstallmentAmountInMultiplesOf(scheduleModel, emiAdjustment.adjustedEmi());
if (adjustedEqualMonthlyInstallmentValue.isEqualTo(emiAdjustment.originalEmi())) {
    break;
}
```
[VERIFIED: `ProgressiveEMICalculator.java:1270-1273`]

`adjustment()` is `B/n` minor units. Under `HALF_UP` at scale 2 that quantizes to **zero** iff
`B/n < 0.5`, i.e.

> **n > 2·B**

### 2.5 The derived bound, in one line

> **A repayment row can amortize exactly zero principal with non-zero interest only at the ROUNDING
> FLOOR: `B ≥ ceil(0.5/r)` and `n ≳ 2·B`, with `B` the principal in MINOR UNITS.**

This is a real and unflattering result about the shape: at any realistic Mongolian principal the
term required is astronomical (MNT 10,000 at 21.6 % would need n ≈ 2,000,000). The path T59
profiled is **reachable only in the dust region**, and a vector that grades it must live there.

### 2.6 The bound was checked against the Go port BEFORE the oracle was asked

The port is used here purely as a **search device**, exactly as T61 used a 40,001-shape sweep. It is
not evidence about the oracle and nothing derived from it is promoted.

`src/t64predict_test.go.txt`, run over ten rates:

| annual rate | derived `B_min` | observed `B_min` | derived `n_min` | observed `n_min` |
|---|---|---|---|---|
| 21.6 % (27/125) | 28 | **28** | 56 | **56** |
| 16.8 % (21/125) | 36 | **36** | 72 | **72** |
| 18.5 % (37/200) | 33 | **33** | 66 | **66** |
| 7 % (7/100) | 86 | **86** | 172 | **172** |
| 24 % (6/25) | 25 | **25** | 50 | 26 |
| 36 % (9/25) | 17 | **17** | 34 | **34** |
| 48 % (12/25) | 13 | **13** | 26 | **26** |
| 60 % (3/5) | 10 | **10** | 20 | 16 |
| 120 % (6/5) | 5 | **5** | 10 | **10** |
| 240 % (12/5) | 3 | **3** | 6 | **6** |

`B_min` is exact on **10 of 10**. `n_min` is exact on **8 of 10** and is an over-estimate on the
other two, where the loop stops for one of its other reasons rather than because the adjustment
quantizes away. **Stated honestly: `n > 2·B` is SUFFICIENT, and is not proven necessary.**

---

## 3. THE SHARP PREDICTIONS

Four claims, each of which the oracle can refute on its own:

1. **`T64-ZP-A` (MNT 0.28, n = 56, 21.6 %): the oracle emits 55 REPAYMENT rows whose principal is
   `0.00` and whose interest is `0.01`, and its outstanding balance stays at `0.28` through all of
   them.** The final row 56 carries principal `0.28` and interest `0.01`. Total interest `0.56`.

2. **`T64-ZP-B` (MNT 0.28, n = 55, 21.6 %) — ONE PERIOD SHORTER — is a completely different
   schedule.** Condition B fails at n = 55 (`28/55 = 0.509 ≥ 0.5`), the smoothing loop fires, the
   level EMI becomes `0.02`, the loan amortizes to zero at **period 15**, and rows **16 through 55
   are entirely dead**: principal `0.00`, interest `0.00`, balance `0.00`. Total interest is
   `0.01` — **one minor unit for the whole loan**.

3. **`T64-ZP-C` (MNT 0.17, n = 34, 36 %)** reproduces claim 1 at an independent rate: 33
   zero-principal rows, interest `0.01` each, final row principal `0.17`.

4. **`T64-ZP-D` (MNT 0.36, n = 72, 16.8 %)** reproduces it at a third: 71 zero-principal rows,
   final row principal `0.36`.

**If the oracle instead returns a schedule in which `T64-ZP-A` period 1 carries a non-zero
principal, the derivation in §2 is WRONG — the `negativeToZero`/quantization reading of
`RepaymentPeriod.java:345-350` does not describe the oracle, and that is to be reported loudly, not
reconciled.**

**If `T64-ZP-B` comes back looking like `T64-ZP-A`, then `EmiAdjustment.shouldBeAdjusted` /
`:1270-1273` is not the gate §2.4 claims it is**, and the "one period shorter changes everything"
pair is not a pair.

Every predicted cell of all four schedules — 221 rows, `principal_minor`, `interest_minor`,
`outstanding_principal_minor`, `from_date`, `due_date` — is committed in
**`predicted-schedules.json`** next to this file, and `check-prediction.py` compares the oracle's
answer against it cell for cell after the capture.

## 4. What this capture does NOT claim

* It does **not** claim the shape is commercially realistic. It is a dust-principal loan; §2.5 is
  the reason, and the reason is the finding.
* It does **not** grade `applyFinalPeriodResidual`'s *cost*. A vector grades values, never
  complexity. What it does is make the zero-principal path **observable**, so that a later change to
  that function has an oracle to check against — which is exactly what T59 said it lacked.
* It does **not** grade precision 19 against 12, or `HALF_UP` against `HALF_EVEN`. Those axes stay
  where T61 left them.
