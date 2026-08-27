# T5 — Independent adversarial review of DEC-1 (draft adapter contract)

| | |
|---|---|
| Task | T5 — independent review of DEC-1 before the human ratification gate |
| Reviewer | Independent adversarial reviewer (no planning context) |
| Artefacts reviewed | `docs/adr/DEC-1-schedule-generator-adapter.md`, `nexus/internal/apps/loanschedule/contract/contract.go` |
| Reference oracle | Fineract, pinned checkout `426a23544e8426a38ae43ae404670a0a7e85b9eb` (verified: `/home/user/fineract/.git/HEAD` = `426a23544e8426a38ae43ae404670a0a7e85b9eb`) |
| Go toolchain | go1.24.7 linux/amd64 |

**Method, stated explicitly: a live reference oracle (Fineract) is NOT reachable from this sandbox — no JVM, no running server, no database.** Every figure in this review was derived from Fineract *source* at the pinned commit plus an independent exact-decimal re-implementation of `java.math.BigDecimal` + `MathContext` semantics (Python `decimal`, `prec` = significant digits, `ROUND_HALF_UP`, `quantize` for `setScale`). The re-implementation was validated by reproducing the shipped conformance test `EmbeddableProgressiveLoanScheduleGeneratorTest#testGenerate` **exactly** — all 7 rows, all splits, all outstanding balances, `loanTermInDays`, and all three asserted totals (see §5). No golden vector is asserted here that was not derived and shown. Neither DEC-1 nor `docs/analysis/progressive-schedule-behavior.md` was used as authority; both were treated as claims to be tested.

---

## VERDICT: **REJECTED**

**Grounds.** The contract's intermediate-precision field is defined as *significant decimal digits* (`contract.go:206-244`), but the reference oracle threads that same integer into `BigDecimal.setScale()` — a *decimal-place* count — at `ProgressiveEMICalculator.java:1962` and `:1979`, and it does so on the per-period rate factor, the single most parity-sensitive quantity in the algorithm. I re-derived both readings across a 560-configuration grid at the two precisions DEC-1 itself names: at precision 12 the two readings produce **different payable amounts** (a one-minor-unit divergence in period-5 principal and interest, and a persisting one-minor-unit divergence in outstanding balance through to the final period, on an 18-month 18.5% loan). The shipped conformance vector does **not** discriminate between the two readings, so this defect passes the only test currently in hand and then fails on a real loan — exactly the failure this contract exists to prevent. Independently and equally disqualifying, the contract's month-end date rule (`contract.go:301-305`) states the *opposite* of `DefaultScheduledDateGenerator.adjustDate` (`:168-176`): the source **re-anchors to the seed day**, the contract says "the clamped day is not remembered", and the seed is the **disbursement date** (`LoanApplicationTerms.java:585-589`), not `ScheduleStartDate` — so a 31 January loan yields 2024-03-31 in Fineract and 2024-03-29 under the contract's own specification, with loan terms of 182 vs 180 days. Beyond those two, the response ordering rule is refuted at a reachable boundary case, one unreachability claim (`allowFullTermForTranche`) is refuted at source, `InstallmentRoundingMultipleMinor` admits values the adapter provably cannot express, and the final-period residual is named but never defined. The Go artefact itself is clean on every non-negotiable and builds and vets without diagnostics; the defects are in the *specification carried by the doc comments*, which DEC-1 §1 declares to be the specification.

---

## §1 — The precision-vs-scale adjudication (settled against source)

### 1.1 What the source actually does

`ProgressiveEMICalculator.java:1950-1963` (`rateFactorByRepaymentPeriod`, the sole rate-factor producer for the 30/360 monthly path):

```java
final BigDecimal interestFractionPerPeriod = repaymentPeriodMultiplierInDays
        .multiply(repaymentEvery, mc)
        .divide(daysInYear, mc);
return interestRate
        .multiply(interestFractionPerPeriod, mc)
        .multiply(actualDaysInPeriod, mc)
        .divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
```

One `MathContext` is consumed in **two incompatible senses**:

1. **Significant digits.** The four `mc`-qualified operations (`multiply(…, mc)`, `divide(…, mc)`) round to `mc.getPrecision()` *significant decimal digits*. This is Java's contract for `MathContext`.
2. **Decimal places (scale).** The trailing `setScale(mc.getPrecision(), mc.getRoundingMode())` quantizes to `mc.getPrecision()` *decimal places*. `setScale` takes a scale, not a precision.

These are the only two occurrences of this pattern in Fineract main code (`ProgressiveEMICalculator.java:1962` and `:1979`; the third hit, `ProgressiveEMICalculatorTest.java:5257`, is a test helper). Both are rate-factor computations. Confirmed by exhaustive grep for `setScale(.*getPrecision`.

The call chain reaching `:1962` on the embeddable path: `EmbeddableProgressiveLoanScheduleGenerator.generate` → `ProgressiveLoanScheduleGenerator.generate` (`:81-84`) → `ProgressiveEMICalculator.calculateRateFactorPerPeriod` (`:1486-1540`, `case DAYS_30` at `:1536`) → `calculateRateFactorPerPeriodBasedOnRepaymentFrequency` (`:1598-1611`, `case MONTHS`) → `rateFactorByRepaymentEveryMonth` (`:1922-1927`) → `rateFactorByRepaymentPeriod` (`:1950`). The rate is pre-divided by 100 at `calcNominalInterestRatePercentage` (`:1318-1320`).

### 1.2 My re-derivation of the divergence

Shipped-test operands: `interestRate` = `7.0 / 100` = `0.07`; `daysInMonth` = 30 (`DAYS_30`, `:1508`); `daysInYear` = 360 (`DAYS_360`, via `getNumberOfDays` `:1346-1353`); `repaymentEvery` = 1; `actualDaysInPeriod` and `calculatedDaysInPeriod` are **real calendar days** (`:1500-1503`), 31 for period 1. `mc` = `MathContext(12, HALF_UP)`.

```
interestFractionPerPeriod = 30 × 1 = 30 ; 30 ÷ 360 = 0.0833333333333       (12 sig digits)
0.07 × 0.0833333333333    = 0.005833333333331   → 12 sig → 0.00583333333333
        × 31              = 0.18083333333323    → 12 sig → 0.180833333333
        ÷ 31              = 0.005833333333322…  → 12 sig → 0.00583333333332   ← 14 dp, 12 sig digits
setScale(12, HALF_UP)     =                                0.005833333333     ← 12 dp, 10 sig digits
```

The prior review's measurement is **confirmed exactly**: `0.00583333333332` (14 dp) becomes `0.005833333333` (12 dp). Because the rate factor is a small number (≈ 0.0058), `setScale(precision)` is *always strictly lossier* than significant-digit rounding on this quantity — it discards the digits that the leading zeros would otherwise have bought. At precision 19 it costs two digits; at precision 12 it costs two digits.

The un-`setScale`d rate factors also differ **from each other across periods** (0.00583333333332 / …34 / …33, tracking `actualDays` = 31/29/31/30/31/30), whereas after `setScale` all six collapse to the identical `0.005833333333`. So the two readings are not merely a fixed offset — they have different *shape*.

Note `RepaymentPeriod.calculateRateFactorPlus1` (`RepaymentPeriod.java:216-218`) does `reduce(BigDecimal.ONE, BigDecimal::add)` — **no `MathContext`**, an exact addition. So `1 + rateFactor` is carried at full width and the rate factor's scale propagates unrounded into the recurrence.

### 1.3 Does it change money? Yes.

I computed the complete schedule under both readings across a grid of 560 configurations per precision (precisions 12 and 19; terms 3/6/12/18/24/36/60 monthly; rates 7.0, 24.0, 18.5, 21.75, 19.99, 13.75, 36.0, 12.0, 0.5, 33.33 %; principals 100 / 1,000 / 5,000 / 250,000 / 999,999 / 1,250,000 / 3,000,000 / 87,654,321 major units).

- **The shipped conformance vector does NOT discriminate.** At principal 100, 7.0 %, 6 months, precision 12, both readings give the identical schedule (§5). The difference is absorbed by the currency layer.
- **At precision 12, three grid configurations diverge in a payable amount.** First divergence — 18 monthly installments, 18.5 % p.a., principal 87,654,321 (a wholly ordinary Mongolian SME/mortgage size):

| period | `setScale` reading (correct) | significant-digit reading (contract's) |
|---|---|---|
| 5 | principal 4,531,420.25 · interest 1,082,346.53 · outstanding 65,674,840.83 | principal 4,531,420.**26** · interest 1,082,346.**52** · outstanding 65,674,840.**82** |
| 6–17 | outstanding …61,073,561.18 … 5,528,535.21 | outstanding one minor unit lower throughout |
| 18 (final) | principal 5,528,535.**21** | principal 5,528,535.**20** |

A one-minor-unit error that appears in period 5 and never heals, ending in a different final principal. Across the wider grid (precisions 8/10/12/15/16/19), 189 configurations diverge, several by more than one minor unit (e.g. precision 8, 7.0 %, 3 months, principal 87,654,321 diverges by 0.28 in period 1).

### 1.4 Answer to the question posed

**Does the contract's current field definition make a bit-exact Go port possible? No.** `contract.go:233-237` defines `IntermediatePrecisionDigits` as "the number of significant decimal digits retained by the intermediate layer", and `contract.go:218-221` says intermediates are "rounded to `IntermediatePrecisionDigits` significant decimal digits under Mode after each multiplication and each division". A Go implementer following that text literally implements sense (1) only, omits the `setScale`, passes the shipped vector, and diverges on a real loan. DEC-1 §5.2 reinforces the error — "Java's `MathContext` carries exactly two things: a significant-digit count and a tie-breaking rule. `Rounding` carries exactly those two things… The Java class does not cross the boundary; its information content does." The information content is *not* fully carried: the fact that the same integer is *also* used as a scale is dropped, and that fact is worth a minor unit.

This is precisely the case the task description anticipated: a single `MathContext`-shaped pair is threaded but used in **both** senses at different call sites, so the contract must say so explicitly.

### 1.5 Proposed exact field definition and doc-comment wording

Keep one integer field (the oracle has one integer; two fields would admit combinations no deployment can produce). Rename it so the name stops asserting one of the two senses, and state both senses normatively. Replace `contract.go:233-237` with:

```go
type Rounding struct {
	// IntermediatePrecision is the single integer that the reference oracle
	// carries as java.math.MathContext precision. It is consumed in TWO
	// different senses at different points of the algorithm. Both senses are
	// normative and both are load-bearing: an implementation that applies only
	// one of them passes the shipped conformance vector and then diverges by a
	// minor unit on ordinary loans.
	//
	//  1. As a SIGNIFICANT-DIGIT count. Every dimensionless intermediate — the
	//     per-period interest fraction, the per-period rate factor, the running
	//     product of (1 + rate factor), the fn recurrence, and the level
	//     installment before it becomes money — is rounded to this many
	//     significant decimal digits under Mode immediately after each
	//     multiplication, each division and each addition, in the order the
	//     algorithm performs them.
	//
	//  2. As a DECIMAL-PLACE count (a scale). The per-period rate factor, and
	//     only the per-period rate factor, is additionally quantized to this
	//     many decimal places under Mode once it is fully computed, before it
	//     is used anywhere else. Because a rate factor is a small number
	//     (typically of order 0.005), sense 2 is strictly lossier than sense 1
	//     on that quantity, and the loss is observable in a payable amount.
	//
	// Concretely, the reference oracle computes the rate factor as
	//
	//     interestRate.multiply(interestFractionPerPeriod, mc)
	//                 .multiply(actualDaysInPeriod, mc)
	//                 .divide(calculatedDaysInPeriod, mc)
	//                 .setScale(mc.getPrecision(), mc.getRoundingMode())
	//
	// where the three mc-qualified operations are sense 1 and the trailing
	// setScale is sense 2 — both driven by this one integer. Worked example at
	// IntermediatePrecision 12, Mode RoundingHalfUp, 7% p.a., 30/360, a
	// 31-day period: sense 1 alone yields 0.00583333333332; sense 2 then
	// yields 0.005833333333, and 0.005833333333 is the value that must enter
	// the recurrence.
	//
	// The exact addition (1 + rateFactor) that forms the recurrence's
	// multiplicand is NOT rounded: it is carried at full width.
	//
	// It must be > 0. The reference oracle's hosted configuration uses 19; its
	// shipped conformance test uses 12.
	IntermediatePrecision int32
	...
}
```

and amend the package-level and `Rounding`-level prose at `contract.go:216-232` correspondingly, so the "Intermediate layer" bullet no longer says "significant decimal digits" unqualified.

**Note for the ratifier:** whether `IntermediatePrecision` should be *renamed* (a breaking identifier change) or merely re-documented is a human decision. Re-documenting alone is sufficient for correctness; renaming is what stops the next reader from re-introducing the same misreading. Both are inside the amendment gate.

---

## §2 — Fidelity

Verified against the 19-field `LoanRepaymentScheduleModelData` (`LoanRepaymentScheduleModelData.java:32-39`), `LoanApplicationTerms.assembleFrom` (`LoanApplicationTerms.java:579-607`), and `LoanSchedulePlan` (`LoanSchedulePlan.java:32-97`).

**Verified correct:**

| Contract | Source | Finding |
|---|---|---|
| `Rate` as exact rational, not percentage (`contract.go:96-99`) | `ProgressiveEMICalculator.java:1318-1320` divides by `DIVISOR_100` (`:75`) under `mc` | ✓ Correct. Input `BigDecimal` scale does not affect the value (`7` and `7.0` both give `0.07`). |
| `ScheduleStartDate` separate from `Disbursement.Date` (`contract.go:291-299`) | `ProgressiveLoanScheduleGenerator.java:94-96` — `repaymentStartDateType` is never set by `assembleFrom`, so `periodStartDate` = `submittedOnDate` = `scheduleGenerationStartDate`, while `seedDate` = `disbursementDate` (`LoanApplicationTerms.java:585-589`) | ✓ The separation is real and load-bearing. DEC-1 §4.1's justification holds. |
| `InstallmentNumber` is a dense 1-based counter shared by down-payment and repayment rows (`contract.go:413-417`) | `LoanScheduleParams.java:169-170` (`instalmentNumber = 1`), `ProgressiveLoanScheduleGenerator.java:123,143` (repayment) and `:341,346` (down payment) — one shared counter | ✓ Verified. |
| Disbursement row carries no installment number, normalised to 0 | `LoanSchedulePlanDisbursementPeriod.periodNumber()` returns `Integer`; the shipped test asserts `null` (`EmbeddableProgressiveLoanScheduleGeneratorTest.java:97`) | ✓ Verified. |
| Interest first, principal as balancing remainder (`contract.go:436-438`) | `RepaymentPeriod.java:345-350` — `getDuePrincipal()` = `negativeToZero(EMI − getDueInterest())` | ✓ Verified. |
| `OutstandingPrincipalMinor` is clamped at zero, not a pure running difference (`contract.go:449-458`, DEC-1 §4.3) | `RepaymentPeriod.java:389-403` ends in `MathUtil.negativeToZero(...)`; `InterestPeriod.java:168-179` likewise | ✓ Verified — the justification for carrying rather than deriving it is sound. |
| `DayCountFixed30Over360`: real calendar days enter only as a proportional correction that is exactly 1 over a whole period (`contract.go:151-155`) | `:1500-1503` take real day differences; `:1961-1962` multiply by `actualDays` then divide by `calculatedDays` | ✓ Verified — for a single full-length interest period the ratio is 1 (subject to §1's rounding). |
| No float on the money path in the oracle either (DEC-1 §5.1) | `Money` is `BigDecimal`-backed; the only `double` reached is `toDouble` in the JUnit helper (`EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122`) — but see F-8 | ✓ mostly; see F-8. |

**Defects found:**

**F-1 (BLOCKING) — the month-end date rule is stated backwards and anchored to the wrong date.**
`contract.go:301-305` states:

> "Month-end stepping clamps: advancing 31 January by one month yields 28 February (29 February in a leap year), and advancing that result by a further month yields 28 March, not 31 March. **The clamped day is not remembered.**"

Source, `DefaultScheduledDateGenerator.java:168-176`, called at `:128-131`:

```java
private Temporal adjustDate(final Temporal date, final Temporal seedDate, final PeriodFrequencyType frequencyType) {
    if (frequencyType.isMonthly() && seedDate.get(ChronoField.DAY_OF_MONTH) > 28 && date.get(ChronoField.DAY_OF_MONTH) >= 28) {
        int noOfDaysInCurrentMonth = YearMonth.from(date).lengthOfMonth();
        int seedDay = seedDate.get(ChronoField.DAY_OF_MONTH);
        int adjustedDay = Math.min(noOfDaysInCurrentMonth, seedDay);
        return date.with(ChronoField.DAY_OF_MONTH, adjustedDay);
    }
    return date;
}
```

The stepping is `LocalDate.plusMonths` (`:311-333`), which clamps — and then `adjustDate` **re-anchors the day to the seed day**, clamped only by the length of the target month. The clamped day *is* remembered, in the seed. And the seed is `modelData.disbursementDate()` (`LoanApplicationTerms.java:585-589`), **not** `ScheduleStartDate`, so the contract attaches the rule to the wrong field.

Re-derived, 6 monthly periods, `ScheduleStartDate` = seed = 2024-01-31:

| | period due dates | term |
|---|---|---|
| Fineract (`adjustDate` re-anchor) | 02-29, **03-31**, 04-30, **05-31**, 06-30, **07-31** | 182 days |
| `contract.go:301-305` as written | 02-29, **03-29**, 04-29, **05-29**, 06-29, **07-29** | 180 days |

Every due date after the first differs, and `loanTermInDays` differs by 2. Same divergence for seed day 30 (181 vs 182 days). Month-end disbursement is routine in retail lending, so this is not an edge case. A Go implementation written to the doc comment — which DEC-1 §1 declares *is* the specification — fails date parity on every such loan.

**F-2 (BLOCKING) — the response ordering rule is refuted at a reachable boundary.**
`contract.go:467-472` / DEC-1 §5.4 specify: non-decreasing by `DueDate`; ties broken by `Kind` (disbursement < down payment < repayment); then by `InstallmentNumber`. DEC-1 §5.4 claims this was checked against the oracle's emission order "including the case where a disbursement row falls inside a later repayment window and the case where a disbursement falls after the maturity date". Both of those check out. The **untested** case is a disbursement dated exactly on a repayment due date.

`ProgressiveLoanScheduleGenerator.java:307-308`:

```java
boolean hasDisbursementInCurrentRepaymentPeriod = !includeDisbursementsAfterMaturityDate
        && !disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate);
```

The window is `[fromDate, dueDate)` — **half-open**. A disbursement dated exactly on period *k*'s due date therefore falls into period *k+1*, and since `processDisbursements` runs at `:121` *before* `periods.add(repaymentPeriod)` at `:141`, it is emitted **after** repayment *k*.

Reachable today with the contract's one-element `Disbursements`: `ScheduleStartDate` = 2024-01-01, `Disbursement.Date` = 2024-02-01, monthly.

- Oracle emission order: repayment 1 (due 2024-02-01), **disbursement (2024-02-01)**, repayment 2 (due 2024-03-01), …
- Contract-derived order: **disbursement (2024-02-01)**, repayment 1 (2024-02-01), repayment 2, …

The contract's derived order does not reproduce the emitted order. The same mismatch applies to a down-payment row, which inherits the disbursement date (`:340-343`) — and there the `InstallmentNumber` tiebreak would have given the right answer had `Kind` not been applied first. Either the ordering rule must be corrected, or requests placing a disbursement on a repayment due date must be rejected — but the contract currently does neither, and "two implementations agree on it without mirroring each other's control flow" (DEC-1 §5.4) is false as written.

**F-3 (BLOCKING) — `InstallmentRoundingMultipleMinor` admits values the adapter cannot express.**
`contract.go:359-375` types the field `int64` in **minor** units. The oracle's counterpart is `Integer installmentAmountInMultiplesOf` (`LoanRepaymentScheduleModelData.java:36`), consumed at `Money.java:150-157` and `:163-170` as `amount.divide(BigDecimal.valueOf(inMultiplesOf), 0, mode).multiply(inMultiplesOf)` — where `amount` is in **major** units. The multiple is therefore a whole number of **major** units.

`InstallmentRoundingMultipleMinor = 10000` (100.00 MNT) maps cleanly. `= 50` (0.50 MNT) or `= 1` (0.01 MNT) has **no** representation in an `Integer` count of major units, so the Fineract-JVM adapter cannot render such a request and would have to round or drop it silently. This is the exact hazard DEC-1 §5.1 handles honestly for `Rate{1, 3}` ("must be rejected with `ErrUnsupportedConfiguration` rather than silently rounded") — and it is unstated here. The contract must require `InstallmentRoundingMultipleMinor` to be either 0 or an exact positive multiple of 10^`MinorUnitDigits`, and reject otherwise.

**F-4 — the final-period residual is named but not defined.**
`contract.go:437-441`: "The final unpaid period additionally absorbs the whole accumulated rounding residual." DEC-1 §2 and §9 repeat the phrase. Nowhere is the residual *computed*. The oracle's rule is at `ProgressiveEMICalculator.java:1190-1210`:

```
diff          = Σ disbursed + Σ capitalizedIncome + creditedPrincipal + Σ dueInterest − Σ EMI
adjustedEmi   = lastUnpaidPeriod.emi + diff
```

with each Σ accumulated through `Money.plus(…, mc)` — i.e. **summed at currency scale, not at intermediate precision** — and the adjustment applied to the period's **EMI**, after which principal falls out as `EMI − interest` (`RepaymentPeriod.java:345-350`). Two implementers reading only the contract could equally plausibly define the residual as "make the final outstanding balance exactly zero" or "make Σ principal equal principal advanced". Those coincide on the shipped vector but are not identical in general (the `negativeToZero` clamps at `RepaymentPeriod.java:348` and `:399` can bite). DEC-1 §6.9 and §9 claim the contract "cannot encode a schedule that contradicts itself" — true of the *encoding*, but the *value* is underdetermined. Under the stated verdict rule ("any money-path ambiguity"), this is an independent rejection ground.

Also: "final **unpaid** period" is a dangling term — this contract has no notion of payment (`Generate` is pure, `contract.go:481-495`). It should read "the last period".

**F-5 — the `DayCountConvention` → (`DaysInMonthType`, `DaysInYearType`) mapping is not normative.**
DEC-1 §4.2's table is declared normative and "is what makes the adapter fully determined by the contract". It pins six inputs but omits the mapping from `DayCountConvention` to the oracle's two enums. `DayCountFixed30Over360` → (`DAYS_30`, `DAYS_360`) is inferable; `DayCountActualActual` → (`ACTUAL`, `ACTUAL`) is a guess, and it selects between materially different branches at `ProgressiveEMICalculator.java:1533-1539` (`case ACTUAL` at `:1534` vs `case DAYS_30` at `:1536`). Since `DayCountActualActual` is in the value domain **today** (`contract.go:159-162`) and no Run-1 vector exercises it, this is undetermined adapter surface in a frozen contract.

**F-6 — the `Rounding.Mode` "one mode, not two" claim is weaker than stated.**
`contract.go:240-243` and DEC-1 §5.2: "the reference oracle derives its currency-scale tie rule from the same source as its intermediate tie rule." Partly true: `Money`'s constructor uses `getMc().getRoundingMode()` (`Money.java:52`), so a `Money` built with the threaded `mc` does share the tie rule. But the **two-argument** `Money.of(currency, amount)` (`Money.java:102-104`) and `Money.roundToMultiplesOf(Money, Integer)` (`:159-161`) both fall back to `MoneyHelper.getMathContext()` — the **tenant-global** context (precision fixed at 19, `MoneyHelper.java:35`; `getRoundingMode()` throws `IllegalStateException` outside an initialised tenant, `:74-78`). DEC-1 §4.1 describes this hazard as applying to the installment only, and says the down payment "uses the threaded `MathContext`". In fact the down-payment path also reaches the tenant global: the three-argument `roundToMultiplesOf` (`Money.java:163-170`) divides under the threaded `mc` but *returns* `Money.of(currencyData, amountScaled)` — the two-argument overload. So **both** call sites touch tenant-global state and **both** throw outside an initialised tenant. The adapter obligation in DEC-1 §8 item 2 is therefore correct but under-scoped; it should be stated as covering every path that constructs `Money` without an explicit `MathContext`.

**F-7 — `Money` re-rounds on every operation; "money is never re-rounded" is a modelling claim, not a source fact.**
`contract.go:222-226`: "A quantity becomes money exactly once… Money is never re-rounded after that point." `Money`'s constructor (`Money.java:40-53`) applies `stripTrailingZeros().setScale(currency.getDecimalPlaces(), mc.getRoundingMode())` on **every** `plus`/`minus`/`add`/`of`. For operands already at scale this is value-preserving, so the contract's claim is *operationally* true on the traced path — but it is a claim the Go implementer must not generalise, because it is true by accident of the operands rather than by construction. Worth a sentence; not by itself blocking.

**F-8 — a `double` does exist on the shipped-vector capture path.**
DEC-1 §5.1: "the only `double` in the whole traced call chain is inside a JUnit assertion helper". Accurate for the *calculation*, but that helper (`EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122`, `value.doubleValue()`) is exactly what a vector-capture harness would be tempted to reuse, and `Money.roundToMultiplesOf(double, Integer)` (`Money.java:134-148`) and `Money.plus(double)` (`:261-267`) are `double`-typed public API on the `Money` class itself. The contract is clean; the *capture harness* must be explicitly forbidden from crossing through `double`, and that obligation is not recorded in DEC-1 §9.

---

## §3 — Deliberate omissions: verified / refuted

| # | DEC-1 claim (§4.2, §2, §4.1) | Verdict | Evidence |
|---|---|---|---|
| 1 | `allowFullTermForTranche` — "Dead on the single-disbursement path — **no builder setter reaches it**." | **REFUTED (both halves)** | The builder setter *does* reach it: `LoanApplicationTerms.java:606` `.allowFullTermForTranche(modelData.allowFullTermForTranche())`, fed by `LoanRepaymentScheduleModelData.java:39` and passed explicitly by the shipped test (`…GeneratorTest.java:70`, `false`). And it is *not* dead on the single-disbursement path: the guard at `ProgressiveEMICalculator.java:142-144` is `isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` — **no multi-disburse condition** — and `addDisbursement` is invoked for every disbursement including the sole one (`ProgressiveLoanScheduleGenerator.java:351`). Setting it `true` would route into `addFullTermTrancheDisbursement` (`:155-174`), a full re-amortization through a synthetic `LoanApplicationTerms` and a temporary schedule model. Fineract blocks the combination only at *product validation* (`LoanDisbursementDetailsIntegrationTest.java:772`, `validation.msg.loanproduct.allowFullTermForTranche.requires.multi.disburse.loan`) — a layer the embeddable entry point does not pass through. **The pin to `false` is still the right call, but it is a genuine behavioural constant the Go module must honour, not a dead field, and DEC-1's stated ground is false.** |
| 2 | `allowPartialPeriodInterestCalculation` pinned `true` — "With a single disbursement and no mid-term rate change, interest sub-periods coincide with repayment periods and the switch is inert." | **VERIFIED (conclusion) / wrong reason** | Its only calc-path uses are `ProgressiveEMICalculator.java:130` and `:201`. At `:128-133` the whole ternary is gated on `getInterestCalculationPeriodMethod() != null && …isSameAsRepaymentPeriod()`. `assembleFrom` (`LoanApplicationTerms.java:591-606`) never sets `interestCalculationPeriodMethod`, and the field has no initialiser (`:108`), so it is `null` on this path and the branch short-circuits. The switch is inert **because `interestCalculationPeriodMethod` is null**, not because sub-periods coincide. Conclusion stands; the reasoning does not, and the reasoning is what a future reader will use to decide whether the pin can be relaxed. |
| 3 | `daysInYearCustomStrategy` — "unreachable under the fixed 360-day year". | **VERIFIED** | `getNumberOfDays` (`ProgressiveEMICalculator.java:1346-1353`) applies the custom strategy only when `numberOfDays == 366`; `DAYS_360` never yields 366. The second use, `partialPeriodCalculationNeeded` (`:1372-1374`), requires `daysInYearType == ACTUAL`. Inert under 30/360. **Caveat:** it is *not* inert under `DayCountActualActual`, which is already in the contract's value domain (`contract.go:162`) — pinning it `null` there is a real behavioural choice, correctly foreseen by DEC-1 but interacting with F-5. |
| 4 | Multi-disbursement unreachable from the embeddable entry point. | **VERIFIED** | `assembleFrom` sets `.disbursementDatas(new ArrayList<>())` (`LoanApplicationTerms.java:600`); `prepareDisbursementsOnLoanApplicationTerms` (`ProgressiveLoanScheduleGenerator.java:285-292`) then synthesises exactly one from `expectedDisbursementDate` + `principal`. The tranche pass at `:147-150` is gated on `isMultiDisburseLoan()`, never set. |
| 5 | `PeriodFrequencyType.WHOLE_TERM` not reachable (DEC-1 §4.1). | **VERIFIED** | `getRepaymentPeriodDate` (`DefaultScheduledDateGenerator.java:328-330`) leaves `WHOLE_TERM` unimplemented (returns the start date); `calculateRateFactorPerPeriodBasedOnRepaymentFrequency` (`ProgressiveEMICalculator.java:1609`) throws `UnsupportedOperationException` for anything outside DAYS/WEEKS/MONTHS. Rejecting it at the boundary is correct. |
| 6 | `currency.inMultiplesOf` — "applies only when the currency has zero decimal places". | **VERIFIED** | `Money.java:48`: `currency.getInMultiplesOf() != null && currency.getDecimalPlaces() == 0 && …`. MNT is 2, so inert. |
| 7 | `fixedLength` pinned `null`. | **VERIFIED as a real behavioural pin** | Consumed at `DefaultScheduledDateGenerator.java:62-65` and `:108-111` and `:184-188`; it overrides the final due date. Correctly identified as a genuine omission (not dead), correctly backlogged. |
| 8 | `interestRecognitionOnDisbursementDate` pinned `false`. | **VERIFIED as a real behavioural pin** | Consumed at `getFractionPeriodDueDateForEndOfYear` (`ProgressiveEMICalculator.java:1578-1584`) — shifts the year-end fraction boundary from 31 Dec to 1 Jan — reachable only on the actual/actual path. Correctly identified as a switch, correctly named as forward risk. |

Net: **one unreachability claim refuted (#1), one verified with a false stated ground (#2), six verified.**

---

## §4 — Non-negotiables in the artefact (`contract.go`)

Grepped the whole Go module for `float`, `big.Float`, `time.Time`, `first_name`/`last_name`/`firstName`/`lastName`, `insur*`/`guarante*`/`protect*`, `mysql`/`mariadb`/`ojdbc`/`oracle.jdbc`/`1521`, `+08:00`/`+07:00`, `stripe`/`plaid`. **Seven hits, all of them prohibition statements inside doc comments** (`contract.go:21, 24, 26, 40, 41, 105, 275`), zero of them declarations or values.

| Non-negotiable | Status |
|---|---|
| Money is integer minor units; no float anywhere on a money path | ✓ `AmountMinor`, `PrincipalMinor`, `InterestMinor`, `OutstandingPrincipalMinor`, `InstallmentRoundingMultipleMinor` are all `int64`. No `float32`/`float64`/`big.Float`/decimal string/float-backed decimal declared or implied. |
| Rates as exact ratio, not float | ✓ `Rate{Numerator, Denominator int64}` in canonical lowest terms (`contract.go:96-99`). |
| MNT = ISO 4217 numeric 496, minor unit 2 | ✓ Documented at `contract.go:57` and `:62-64`; `MinorUnitDigits` is an `int32` input, not hard-coded. |
| IANA time-zone identifiers, never hard-coded offsets | ✓ `TimeZone string` (`contract.go:281`) with explicit rejection of `"+08:00"`, `"UTC+8"`, `"GMT+8"` (`:275-277`). The `(+08)`/`(+07)` parentheticals at `:272-273` are explanatory prose about the named zones, not values. |
| Three-field Mongolian names if names appear | ✓ No party identity of any kind appears; `contract.go:38-41` records the ovog/patronymic/given-name mandate and the `first_name`/`last_name` prohibition. |
| No deposit-insurance language | ✓ Absent. |
| No MySQL/MariaDB/Oracle-Database anything | ✓ Absent. No persistence surface at all. |
| Idempotency-Key on money-movement POSTs | ✓ N/A and correctly argued: `Generate` is a pure function that moves no money (`contract.go:481-495`). |
| Ledger double-entry / append-only | ✓ N/A; schedule generation posts nothing. |

**No non-negotiable is violated by the artefact.** The rejection is on specification correctness and ambiguity, not on the non-negotiables.

---

## §5 — Golden-test round-trip walkthrough, field by field

Target: `EmbeddableProgressiveLoanScheduleGeneratorTest#testGenerate` (`…GeneratorTest.java:42-93`).

### 5.1 Request → `GenerateRequest`

| Oracle input (`…GeneratorTest.java`) | Value | `GenerateRequest` field | Encoding | Lossless? |
|---|---|---|---|---|
| — | — | `TimeZone` | `"Asia/Ulaanbaatar"` (no oracle counterpart; contract carries strictly more) | ✓ |
| `currency` `:47` | `CurrencyData("usd","US Dollar",2,null,"usd","$")` | `Currency{Code, MinorUnitDigits}` | `{"USD", 2}` | ✓ arithmetically. **Note:** the vector's code is lower-case `"usd"`; `contract.go:56-57` requires upper case. Not an arithmetic input (`:58-59`), so the adapter may normalise — but the normalisation must be stated, or two capture runs disagree structurally. |
| `mc` `:44` | `MathContext(12, HALF_UP)` | `Rounding{IntermediatePrecisionDigits, Mode}` | `{12, RoundingHalfUp}` | **✗ — §1.** The integer round-trips; its *meaning* does not. |
| `startDate` `:48` | 2024-01-01 | `ScheduleStartDate` | `CivilDate{2024,1,1}` | ✓ |
| `disbursementDate` `:49` | 2024-01-01 | `Disbursements[0].Date` | `CivilDate{2024,1,1}` | ✓ value. **✗ semantics** — this is the month-end *seed* (`LoanApplicationTerms.java:585-589`), and the contract documents the seed as `ScheduleStartDate` (F-1). Invisible here because both are the 1st. |
| `disbursedAmount` `:50` | `BigDecimal.valueOf(100)` | `Disbursements[0].AmountMinor` | `10000` (100.00 × 10²) | ✓ exact in both directions |
| `noRepayments` `:52` | 6 | `NumberOfRepayments` | `6` | ✓ |
| `repaymentFrequency` `:53` | 1 | `RepaymentEvery` | `1` | ✓ |
| `repaymentFrequencyType` `:54` | `"MONTHS"` (String) | `RepaymentFrequencyUnit` | `FrequencyMonths` | ✓ — de-stringly-typed, correct |
| `annualNominalInterestRate` `:57` | `BigDecimal.valueOf(7.0)` | `AnnualNominalInterestRate` | `Rate{7, 100}` | ✓ — `7/100` is in lowest terms; denominator 100 = 2²·5² so it renders to an exact terminating decimal percentage |
| `daysInMonthType` `:58` + `daysInYearType` `:59` | `DAYS_30`, `DAYS_360` | `DayCount` | `DayCountFixed30Over360` | ✓ value; **F-5** — the reverse mapping is not normative |
| `interestMethod` `:64` | `DECLINING_BALANCE` | `InterestMethod` | `InterestMethodDecliningBalance` | ✓ |
| `downPaymentPercentage` `:55` + `isDownPaymentEnabled` `:56` | `ZERO`, `false` | `DownPaymentPercentage` | `Rate{0, 1}` | ✓ — the two-fields-into-one collapse is correct; `assembleFrom` reads `downPaymentEnabled()` (`LoanApplicationTerms.java:601`) which the test derives from the percentage anyway (`:56`) |
| `installmentAmountInMultiplesOf` `:60` | `null` | `InstallmentRoundingMultipleMinor` | `0` | ✓ here; **F-3** in general |
| `fixedLength` `:61` | `null` | — | pinned (DEC-1 §4.2) | ✓ |
| `interestRecognitionOnDisbursementDate` `:62` | `false` | — | pinned | ✓ |
| `daysInYearCustomStrategy` `:63` | `null` | — | pinned | ✓ |
| `allowPartialPeriodInterestCalculation` `:65` | `true` | — | pinned | ✓ |
| `allowFullTermForTranche` `:70` | `false` | — | pinned | ✓ value; **§3 #1** — ground refuted |

All 19 oracle inputs are accounted for: 13 contract fields + 6 pinned constants. Principal 100 **does** express exactly as integer minor units (`10000`).

### 5.2 My independent re-derivation of the expected schedule

Computed with exact decimal arithmetic under `MathContext(12, HALF_UP)`, applying the `setScale` at `:1962`:

```
period bounds (plusMonths, adjustDate no-op since seed day = 1):
  2024-01-01→02-01 (31d)  02-01→03-01 (29d)  03-01→04-01 (31d)
  04-01→05-01 (30d)       05-01→06-01 (31d)  06-01→07-01 (30d)
loanTermInDays = 182

interestRate            = 7.0 / 100                      = 0.07
interestFraction        = (30 × 1) / 360                 = 0.0833333333333
rateFactor (all six)                                     = 0.005833333333
rateFactorPlus1N = Π (1 + rf)                            = 1.03551440397
fnResult         = fold (fn → 1 + fn·(1+rf)) over 5      = 6.08818353993
EMI raw = 1.03551440397 × 100.00 / 6.08818353993         = 17.0085937321  → Money 17.01
residual diff = (100.00 + 2.05) − (6 × 17.01) = 102.05 − 102.06 = −0.01
adjusted final EMI = 17.01 + (−0.01)                     = 17.00
```

| # | from → due | principal | interest | total | outstanding |
|---|---|---|---|---|---|
| 1 | 2024-01-01 → 2024-02-01 | 16.43 | 0.58 | 17.01 | 83.57 |
| 2 | 2024-02-01 → 2024-03-01 | 16.52 | 0.49 | 17.01 | 67.05 |
| 3 | 2024-03-01 → 2024-04-01 | 16.62 | 0.39 | 17.01 | 50.43 |
| 4 | 2024-04-01 → 2024-05-01 | 16.72 | 0.29 | 17.01 | 33.71 |
| 5 | 2024-05-01 → 2024-06-01 | 16.81 | 0.20 | 17.01 | 16.90 |
| 6 | 2024-06-01 → 2024-07-01 | 16.90 | 0.10 | **17.00** | 0.00 |

Totals: principal 100.00, interest 2.05, repayment 102.05, term 182 days. **Every figure matches the shipped assertions at `…GeneratorTest.java:74-92` exactly**, which is what validates my model of the algorithm and therefore validates §1's divergence analysis.

### 5.3 Response → `Schedule`

7 rows, all expressible without loss:

| Row | `Kind` | `InstallmentNumber` | `FromDate`/`DueDate` | `PrincipalMinor` | `InterestMinor` | `OutstandingPrincipalMinor` |
|---|---|---|---|---|---|---|
| 0 | `PeriodKindDisbursement` | `0` (oracle `null`) | 2024-01-01 / 2024-01-01 | `10000` | `0` | `10000` |
| 1 | `PeriodKindRepayment` | `1` | 2024-01-01 / 2024-02-01 | `1643` | `58` | `8357` |
| 2 | … | `2` | … / 2024-03-01 | `1652` | `49` | `6705` |
| 3 | … | `3` | … / 2024-04-01 | `1662` | `39` | `5043` |
| 4 | … | `4` | … / 2024-05-01 | `1672` | `29` | `3371` |
| 5 | … | `5` | … / 2024-06-01 | `1681` | `20` | `1690` |
| 6 | … | `6` | … / 2024-07-01 | `1690` | `10` | `0` |

Omitted oracle members, all derivable from the rows and checked numerically:

- `loanTermInDays` 182 = span first→last date ✓
- `totalDisbursedAmount` 100.00 = Σ disbursement rows ✓
- `totalInterestAmount` 2.05 = Σ `InterestMinor` ✓
- `totalRepaymentAmount` 102.05 = Σ (`PrincipalMinor` + `InterestMinor`) over payable rows ✓
- per-row `totalDueAmount` = `PrincipalMinor` + `InterestMinor` ✓ (17.01 ×5, 17.00)
- per-row `totalOutstandingLoanBalance` (85.04, 68.03, 51.02, 34.01, 17.00, 0.00) = Σ total due over **later** rows — verified: 17.01×4 + 17.00 = 85.04 ✓, 17.01×3 + 17.00 = 68.03 ✓, and so on to 0.00 ✓
- `feeAmount` / `penaltyAmount` identically 0 under the pinned configuration ✓
- `currency` echo — carried on the request ✓

**Round-trip conclusion: the shipped golden vector round-trips completely through `GenerateRequest`/`Schedule` with no loss of value.** The response shape is sound; the defects are in the request-side *semantics* (§1, F-1, F-3) and the ordering rule (F-2), not in the response's expressiveness. The decision to omit the EMI field (DEC-1 §4.4) is vindicated by row 6: 16.90 + 0.10 = 17.00 ≠ 17.01, and the residual is visible in the split with nothing to contradict it.

---

## §6 — Ordering, sign conventions, residual absorption

- **Per-period order (interest first, principal as remainder):** stated at `contract.go:436-438`, verified at `RepaymentPeriod.java:345-350`. ✓
- **Sign convention:** `PrincipalMinor` never negative, direction carried by `Kind` (`contract.go:428-434`, DEC-1 §5.5). Consistent with the oracle, which emits all-positive `BigDecimal` amounts and distinguishes rows by Java subclass (`LoanSchedulePlan.java:52-79`). ✓
- **Ordering:** ✗ — F-2.
- **Residual absorption:** ✗ — F-4. DEC-1 §1 claims "the doc comments *are* the specification". Tested: they are sufficient for the split rule and the sign convention, **not** sufficient for the residual (no formula, and "unpaid" is undefined in a contract with no notion of payment) and **not** sufficient for the ordering or the date rule.

---

## §7 — Go artefact quality

```
$ cd nexus && /usr/local/go/bin/go build ./...
(no output; exit 0)

$ cd nexus && /usr/local/go/bin/go vet ./...
(no output; exit 0)
```

**`go build ./...` PASS. `go vet ./...` PASS — no diagnostics.** The package is a single file, 534 lines, one exported interface, no dependencies beyond `context` and `errors`. Doc-comment density and structure are good; the failure is in the *content* of three of those comments, not in their form.

---

## §8 — Required changes (priority-ordered, actionable without me)

Each of these is inside the `user` amendment gate. I have **not** edited `contract.go` or the ADR.

1. **Fix the precision/scale ambiguity (§1).** Adopt the field definition and doc comment in §1.5 verbatim, or an equivalent that states *both* senses normatively and names the `setScale` site. Amend `contract.go:206-244` (the `Rounding` type comment and the field), `contract.go:216-221` (the package-level "Intermediate layer" bullet), and DEC-1 §5.2 (which currently asserts the information content is fully carried). Add a Run-1 golden vector that **discriminates** the two readings — the derived case *18 monthly installments, 18.5 % p.a., principal 87,654,321 major units, precision 12, HALF_UP* is one; capture it against the reference oracle before ratification, because until it is captured the corpus cannot detect this class of defect at all.

2. **Fix the month-end date rule (F-1).** Replace `contract.go:301-305`. The rule is: step with calendar-month addition clamped to the target month's length; **then**, for monthly frequencies only, if the **seed day** > 28 and the stepped date's day ≥ 28, set the day to `min(days in target month, seed day)`. The **seed is the disbursement date**, not `ScheduleStartDate`. Move the rule off `ScheduleStartDate`'s doc comment and onto `Disbursement.Date`'s (or state it on both with the anchor named explicitly). Cite `DefaultScheduledDateGenerator.java:168-176` and `LoanApplicationTerms.java:585-589`. Add golden vectors for seed days 29, 30 and 31 spanning a February, in both a leap and a non-leap year — none of which the current corpus contains.

3. **Fix or fence the ordering rule (F-2).** Either (a) redefine the total order so a disbursement/down-payment row dated exactly on a repayment due date sorts **after** that repayment (which reproduces the oracle's half-open window at `ProgressiveLoanScheduleGenerator.java:307-308`), or (b) reject with `ErrUnsupportedConfiguration` any request whose `Disbursement.Date` coincides with a computed repayment due date. (a) is preferable — it is a documentation change, whereas (b) removes a schedule the oracle can produce. Correct DEC-1 §5.4, which currently claims the derived order was checked and reproduces the emitted order.

4. **Constrain `InstallmentRoundingMultipleMinor` (F-3).** Add to `contract.go:359-375`: the value must be 0, or a positive exact multiple of 10^`Currency.MinorUnitDigits`; anything else is `ErrUnsupportedConfiguration`. State the reason (the oracle's counterpart is an `Integer` count of **major** units, `LoanRepaymentScheduleModelData.java:36`, consumed at `Money.java:150-157`). Mirror it in DEC-1 §5.1 beside the existing `Rate{1,3}` argument, which is the same class of honesty.

5. **Define the final-period residual (F-4).** Replace the prose at `contract.go:437-441` with the formula: the last period's installment is adjusted by `(Σ principal advanced + Σ period interest) − Σ unadjusted installments`, with every sum accumulated **at currency scale under `Mode`**, and the period's principal then taken as adjusted installment minus that period's interest. Replace "final unpaid period" with "last period". Cite `ProgressiveEMICalculator.java:1190-1210`.

6. **Correct the §4.2 unreachability grounds (§3 #1, #2).** `allowFullTermForTranche`: the reason is not "no builder setter reaches it" (`LoanApplicationTerms.java:606` does) and it is not dead on the single-disbursement path (`ProgressiveEMICalculator.java:142-144` has no multi-disburse guard); it is pinned `false` because Fineract's *product-level* validation forbids the combination and the embeddable entry point bypasses that validation. Record it as a **behavioural pin with a conformance obligation on the Go module**, not as a dead field. `allowPartialPeriodInterestCalculation`: the reason is that `interestCalculationPeriodMethod` is `null` on this path (`LoanApplicationTerms.java:108`, never set by `assembleFrom`), which short-circuits `ProgressiveEMICalculator.java:128-133`.

7. **Make the `DayCountConvention` → oracle-enum mapping normative (F-5).** Add two rows to DEC-1 §4.2's table: `DayCountFixed30Over360` → (`DAYS_30`, `DAYS_360`); `DayCountActualActual` → (`ACTUAL`, `ACTUAL`). Alternatively, remove `DayCountActualActual` from the Run-1 value domain until a vector exercises it — but that is a value-domain narrowing and therefore also a gate.

8. **Widen the `InstallmentRoundingMultipleMinor` adapter obligation (F-6).** DEC-1 §8 item 2 should cover *every* path that constructs `Money` without an explicit `MathContext` — including the three-argument `Money.roundToMultiplesOf`, which returns via the two-argument `Money.of` (`Money.java:169`) and therefore also reads tenant-global state and also throws outside an initialised tenant.

9. **Minor, non-blocking:** normalise the currency-code case rule for captured vectors (the shipped vector is `"usd"`, `contract.go:56-57` requires upper case); soften the "money is never re-rounded" claim to reflect `Money.java:40-53` (F-7); add a §9 obligation that the vector-capture harness never routes an amount through `double`, given `Money.java:134-148` and `:261-267` expose `double` overloads (F-8).

---

## §9 — Reserved for the human ratifier (no agent may decide these)

1. **Ratification of DEC-1 itself**, and of every change listed in §8 — the contract and its ADR are a `user` gate by CLAUDE.md and by DEC-1 §1. This review recommends; it does not amend.
2. **Whether `IntermediatePrecisionDigits` is renamed or only re-documented.** Correctness needs only the doc comment. A rename is an identifier change that invalidates any code already written against the draft, and is the stronger guard against the same misreading recurring. Judgement call, not a technical one.
3. **Ordering fix (a) vs (b) in §8 item 3** — reproduce the oracle's emitted order, or refuse the request. (b) narrows what the boundary can express relative to the oracle; that is a product decision.
4. **Whether `DayCountActualActual` stays in the Run-1 value domain** without a capturable vector, or is deferred. Removing it later is a narrowing and a second gate; keeping it means shipping surface with an unproven claim.
5. **The reference instance's actual tenant rounding mode** (DEC-1 §8 item 1, still open; `MoneyHelper.java:74-78`, per-tenant, not traceable from source). It determines whether `RoundingMode` needs a member beyond `HalfUp`/`HalfEven`. Must be settled by inspecting the live tenant before large-scale vector capture — an operational act outside this sandbox.
6. **Accepting `allowFullTermForTranche = false` as a behavioural conformance obligation** on the Go module rather than as a dead field (§3 #1). The pin is right; whether the program accepts an obligation it had believed was free is the ratifier's call.
7. **Whether the discriminating vector in §8 item 1 must be captured against the live reference oracle before ratification, or may be captured after.** I recommend before: the corpus currently cannot detect the §1 defect class, so ratifying first means freezing a contract whose central money claim is untested. This is a sequencing decision with schedule cost, hence a human one.
8. **All standing gates are untouched by this review:** no cutover is proposed, no deposit-taking activation is implicated, and a corrected contract that passes vectors still means only "matches the reference oracle on captured vectors" — never "safe to cut over."
