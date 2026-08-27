# T10 — the Go native loan-schedule port

Run `2026-08-17-run1-harness-schedule-poc`, context `loan-schedule`, branch
`softhouse/T10-go-schedule-port`. **The first Go port in the program.**

Files written: `nexus/internal/apps/loanschedule/{generator.go,emi.go,rounding.go,loanschedule_test.go}`
and `nexus/internal/apps/loanschedule/conformance/cmd/conformance/impl_hook.go`.
Nothing else in the repository was touched. `contract/contract.go` is byte-identical
to the ratified artefact; `.softhouse/conformance.sh`, `.softhouse/vectors/**`,
`capabilities.json` and `PIN.json` are byte-identical to `main`.

## Headline

`.softhouse/conformance.sh` → **exit 0**, on the first run, with no edits to
anything it grades against.

```
    parity vectors          PASS 11   FAIL 0
    contract-refusal        PASS 4    FAIL 0
    self-test fixtures      PASS 1    FAIL 0
    refused                 0
    inadmissible            0
    harness errors          0
    cells compared          1046 graded, 22 ungraded (never recorded by the capture)
    invariant violations    0

VERDICT: PASS (exit 0) — 11 parity vectors match the pinned reference oracle, 1046 cells compared.
```

`.softhouse/conformance.sh --prove` → **14 passed, 1 failed**. The one failure is
`--prove` case 1, whose premise is *"no implementation registered"* — the premise
this task exists to negate. **It is reported, not fixed** (§7). Every other proof
is unaffected, and I measured the before/after directly rather than asserting it.

**A PASS here means "matches the reference oracle on captured vectors, within the
graded domain". It does not mean the port is right, and §6 measures exactly how
much of it the corpus is blind to — five defect classes, three of which move
money.**

---

## 1. The two driver corrections — both re-derived from source, both CONFIRMED, both already implemented

The driver's mid-task correction arrived after I had written `emi.go`. I had
implemented both correctly from the Java, and I re-checked both before replying.

### 1a. The oracle does NOT use the closed-form EMI. CONFIRMED.

`[VERIFIED: ProgressiveEMICalculator.java:1838-1840]`

```java
private BigDecimal calculateEMIValue(final BigDecimal rateFactorPlus1N, final BigDecimal outstandingBalanceForRest,
        final BigDecimal fnResult, MathContext mc) {
    return rateFactorPlus1N.multiply(outstandingBalanceForRest, mc).divide(fnResult, mc);
}
```

with `[VERIFIED: :1816-1820]` the product fold
`periods.stream().map(getRateFactorPlus1ForEmi).reduce(BigDecimal.ONE, (acc, value) -> acc.multiply(value, mc))`
and `[VERIFIED: :1822-1828]` the `fn` fold
`periods.stream().skip(1).map(...).reduce(BigDecimal.ONE, (previousFnValue, currentRateFactor) -> fnValue(previousFnValue, currentRateFactor, mc))`,
where `[VERIFIED: :1988-1990]` `fnValue = BigDecimal.ONE.add(previousFnValue.multiply(currentRateFactor, mc), mc)`.

There is no `pow` and no closed form anywhere on the path. **`emi.go`
`calculateLevelInstallment` is the fold**, per-period, with the MathContext
applied at every multiply, divide and add.

One detail the shape makes load-bearing and which I want on the record: **the
first product against `BigDecimal.ONE` is NOT a no-op.** A growth factor is
`1 + Σ rateFactor` where each rate factor carries 19 decimal places, so the growth
factor carries **20 significant digits** and `ONE.multiply(g, mc)` at precision 19
drops one. A port that starts the fold at `related[0].growthFactor` instead of at
`1` returns a different number.

I also confirmed `MathUtil.stripTrailingZeros` (applied to both fold results at
`[VERIFIED: :1725-1726]`) is **numerically inert** — it changes a `BigDecimal`'s
scale, never its value, and every downstream consumer is a MathContext-qualified
operation that reads only the value. It is therefore absent from the port rather
than approximated.

### 1b. There is no "final principal := the whole remaining balance". CONFIRMED — and trap #4 in my brief was wrong.

`[VERIFIED: RepaymentPeriod.java:339-344]` `getDuePrincipal()` is
`MathUtil.max(MathUtil.negativeToZero(getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().minus(getDueInterest(), getMc()), getMc()), getPaidPrincipal(), false)`
— **installment minus interest, on every row including the last**, with no
special case anywhere. I grepped `ProgressiveEMICalculator` and `RepaymentPeriod`
for a final-period principal assignment; there is none.

What makes the final row come out even is
`[VERIFIED: ProgressiveEMICalculator.java:1191-1206]` inside
`calculateLastUnpaidRepaymentPeriodEMI`: the **last unpaid period's EMI** absorbs

```
diff = totalDisbursedAmount + totalCapitalizedIncome + totalCreditedPrincipal
       + totalDueInterest - totalEMI            (:1203)
adjustedEmi = repaymentPeriod.getEmi().add(diff, mc)   (:1205)
```

and the ordinary split expression is then applied to that EMI unchanged. `emi.go`
does exactly this (`applyFinalPeriodResidual`), and `duePrincipalMinor` is one
uniform expression with a doc comment saying so in as many words.

**This distinction is invisible to the corpus.** Both readings produce the same
numbers on all 11 vectors, because on a fully amortizing schedule
`emi_final − interest_final` *is* the remaining balance. The driver is right that
the wrong mechanism would pass and be wrong in shape.

---

## 2. Every rule implemented, with its source citation

The reviewer re-derives against source. Each row is a rule in the port and the
line of the pinned checkout (`426a23544e8426a38ae43ae404670a0a7e85b9eb`) it comes
from.

### Date stepping (`generator.go`)

| rule | citation |
|---|---|
| N periods, each `[previous boundary, next]`, boundary stepped from `ScheduleStartDate` | `DefaultScheduledDateGenerator.java:49-73` |
| the FIRST repayment is stepped like every other — the first-repayment shortcut is unreachable | `DefaultScheduledDateGenerator.java:121-123` requires `getCalculatedRepaymentsStartingFromLocalDate()`, and the Builder constructor `LoanApplicationTerms.java:304-351` never assigns `calculatedRepaymentsStartingFromDate` (only the positional constructor at `:803` does), while `assembleFrom` builds exclusively through the Builder `:579-606` |
| step = `plusMonths(repaymentEvery)`, java.time semantics (day CLAMPED into the target month) | `DefaultScheduledDateGenerator.java:311-332` |
| month-end re-anchor: monthly ∧ `seed.day > 28` ∧ `stepped.day >= 28` ⇒ `day := min(len(month), seed.day)` | `DefaultScheduledDateGenerator.java:168-176` (`adjustDate`), reached at `:130-131` |
| the SEED is the DISBURSEMENT date, not `ScheduleStartDate` | `LoanApplicationTerms.java:583-589` (`assembleFrom` picks `modelData.disbursementDate()`), copied by the Builder at `:324` |
| `fixedLength` override absent — pinned null by the contract | `DefaultScheduledDateGenerator.java:60-64` |
| holiday / working-day adjustment absent — a guaranteed silent no-op on this seam | `DefaultScheduledDateGenerator.java:224` guards the whole body on `holidayDetailDTO != null`, and `ProgressiveLoanScheduleGenerator.java:83` hard-wires it null |
| loan-term variations absent | `DefaultScheduledDateGenerator.java:75-95`: the wrapper is never set by the Builder, so the `!= null` guard short-circuits |

### Model construction and membership (`emi.go`)

| rule | citation |
|---|---|
| one repayment period per due date, each carrying exactly ONE interest period spanning its whole window | `ProgressiveEMICalculator.java:100-111` → `RepaymentPeriod.java:143-151` |
| **M1** — `[from, due]` for the first period, `(from, due]` for every later one; decides where a balance change registers | `LoanRepaymentScheduleProcessingWrapper.java:251-254` via `ProgressiveLoanInterestScheduleModel.java:238-245` |
| **M3** — `[from, due)`; decides in which iteration the disbursement row is emitted and registered | `ProgressiveLoanScheduleGenerator.java:305-308` |
| **M2 / related periods** — `!(p.due < effectiveDue)`; the ONLY periods the level installment is computed over and written to | `ProgressiveLoanInterestScheduleModel.java:190-197`, list built at `ProgressiveEMICalculator.java:732` |
| effective due date: if the change lands on the matched period's due date, use the NEXT period's due date | `ProgressiveEMICalculator.java:249-262` |
| segmentation: a segment already ending on the date takes the amount with no split; otherwise split, the earlier segment taking the amount | `ProgressiveLoanInterestScheduleModel.java:264-296`, `:327-330`, `:439-441` |
| the amount enters the balance of the LATER segment | `InterestPeriod.java:166-186` |
| `interestCalculationPeriodMethod` branch unreachable (the assembler never sets it) | `ProgressiveEMICalculator.java:128-133` against `LoanApplicationTerms.java:579-606` |
| `addFullTermTrancheDisbursement` unreachable — `allowFullTermForTranche` pinned false | `ProgressiveEMICalculator.java:141-145` |

### Rate factors (`emi.go`)

| rule | citation |
|---|---|
| `interestRate = annualPercentage / 100` under the MathContext | `ProgressiveEMICalculator.java:1318-1320` |
| kernel: `fraction = daysInMonth × multiplier / daysInYear`, then `rate × fraction × actualDays / calculatedDays`, then `setScale(precision, mode)` | `ProgressiveEMICalculator.java:1947-1962` |
| `calculatedDaysInPeriod == 0` ⇒ exactly `ZERO`, before any operation | `ProgressiveEMICalculator.java:1953-1955` |
| the **recurrence's** factor: multiplier `RepaymentEvery`, span = the segment's own window | `ProgressiveEMICalculator.java:639-640` → `:1486-1541`, dispatch at `:1536` |
| the **interest's** factor: multiplier `periodRatio`, span = `[segment.from, repaymentPeriod.due]` | `ProgressiveEMICalculator.java:641-642` → `:1355-1418`, dispatch at `:1404-1413` |
| days-in-month is 30 on BOTH call sites on every reachable path — a port must NOT "correct" it | `:1508`'s ternary is consumed only at `:1537`, inside the `case DAYS_30 ->` arm at `:1536`, which is precisely where it yields 30; the interest site passes the literal 30 at `:1413` |
| argument-order swap: `rateFactorByRepaymentEveryMonth(rate, every, daysInMonth, …)` calls `rateFactorByRepaymentPeriod(rate, daysInMonth, every, …)` | `ProgressiveEMICalculator.java:1922-1926` |
| `periodRatio`: seed, packed month count, month-end special case, walk, single rounded division, EXACT integer add | `ProgressiveEMICalculator.java:1419-1459` |
| `calculateSeedDate` — schedule start iff BOTH conjuncts hold, else the period's own from-date | `ProgressiveEMICalculator.java:1461-1481` |
| the packed month rule `(year*12 + month-1)*32 + day`, difference ÷ 32 truncated toward zero | `DateUtils.java:308-317` → `ChronoUnit.MONTHS.between` → `LocalDate.monthsUntil` |
| the ACT/ACT partial-period arm not implemented — `partialPeriodCalculationNeeded` requires `daysInYearType == ACTUAL`, refused before it can be reached | `ProgressiveEMICalculator.java:1372-1374`, `:1505-1507` |

### Interest and the split (`emi.go`)

| rule | citation |
|---|---|
| `lengthTillPeriodDueDate == 0` ⇒ interest exactly zero | `InterestPeriod.java:143-146` |
| **three** separately rounded operations, in order: `B × rateFactorTillDue`, `÷ lengthTillDue`, `× length` | `InterestPeriod.java:147-158` |
| SUM the segments, THEN make it money, exactly once | `RepaymentPeriod.java:246-252`, currency scale at `Money.java:52` |
| plus the PREVIOUS period's unrecognized interest, clamped at zero | `RepaymentPeriod.java:255-259`, `:381-383` |
| cap at the installment | `RepaymentPeriod.java:266-280` |
| principal = the balancing non-negative remainder | `RepaymentPeriod.java:339-344` |
| roll the balance forward, clamped at zero | `RepaymentPeriod.java:387-401` |
| growth factor = `1 + Σ segment rate factors`, additions EXACT (no MathContext) | `RepaymentPeriod.java:214-217` |
| opening balance for the EMI = previous period's closing balance + everything disbursed in this one | `RepaymentPeriod.java:418-432` |

### EMI, residual, smoothing (`emi.go`)

| rule | citation |
|---|---|
| level installment = `Π growth × openingBalance ÷ fn`, MathContext at every step | `ProgressiveEMICalculator.java:1722-1741`, `:1816-1840` |
| the installment is written to the RELATED periods only; earlier rows keep a ZERO installment | `ProgressiveEMICalculator.java:1735-1740` |
| final-period residual absorbed by the LAST UNPAID period's EMI | `ProgressiveEMICalculator.java:1176-1206` |
| the `outstandingPrincipal > totalDuePaidDiff` guard — ported although provably inert | `ProgressiveEMICalculator.java:1163-1174`; `getTotalDuePrincipal` is the sum of `getCreditedAmounts` (`ProgressiveLoanInterestScheduleModel.java:347-348` → `RepaymentPeriod.java:375-377`), i.e. everything DISBURSED |
| smoothing loop, ≤ 3 iterations, counter advances only on adoption | `ProgressiveEMICalculator.java:1258-1308` |
| the pair: scan from the END for the last adjacent pair where NEITHER is fully paid; `idx > 0` | `ProgressiveEMICalculator.java:1778-1789` |
| guard: all three conjuncts, threshold `floor(n/2)` WHOLE CURRENCY UNITS flat | `EmiAdjustment.java:31-36`; `Money.copy(double)` REPLACES the amount (`Money.java:219-222`) |
| divisor `max(1, n − uncountablePeriods)`, `uncountablePeriods` ≡ 0 here | `EmiAdjustment.java:38-40`, `ProgressiveEMICalculator.java:2027-2031` |
| trial is a REBUILD on a copy: balances recomputed, residual re-applied | `ProgressiveEMICalculator.java:1274-1288` |
| adoption test STRICT, `|new| < |old|`, failure DISCARDS the trial | `EmiAdjustment.java:46-48`, break at `:1290` before the copy-back at `:1293-1305` |
| the adoption test re-measures over the trial's FULL period list | `ProgressiveEMICalculator.java:1289` |

### Row emission and ordering (`generator.go`)

| rule | citation |
|---|---|
| disbursements emitted at the TOP of each iteration, the repayment row appended at the BOTTOM | `ProgressiveLoanScheduleGenerator.java:121-122` vs `:141` |
| the row's cells are read INSIDE its own iteration | `ProgressiveLoanScheduleGenerator.java:126-133` |
| disbursement row's outstanding balance = the amount advanced | `LoanSchedulePlan.java:52-56` |
| installment number: one shared counter, read before the increment; 0 on a disbursement row | `ProgressiveLoanScheduleGenerator.java:126`, `:143`; the record's `periodNumber()` returns null for a disbursement (`LoanSchedulePlanDisbursementPeriod.java:25-35`) |

---

## 3. The four named traps, and how the port avoids each

Each was then **measured** by mutating the port into the counterfactual and
running the real harness (§6 has the full sweep).

**① `ROW-ORDER-SORT-BY-DATE-DISBURSEMENT-FIRST` (P-03, structural).**
`generate` walks the model in period order and tests the disbursement against
**M3**, the half-open `[from, due)` window, at the top of each iteration
(`generator.go`, `inPeriodM3`). A disbursement on period 1's due date therefore
fails M3 for period 1, matches period 2, and is emitted after repayment 1 — which
was itself read from a model in which no disbursement exists, so every cell is 0.
There is no sort anywhere in the port; the order is the loop's.
**Measured:** the naive rule fails P-03 on `row 0 kind: expected REPAYMENT, got
DISBURSEMENT` and four more cells.

**② `EMI-DENOMINATOR-USES-NUMBER-OF-REPAYMENTS…` (P-03, 334 minor units).**
The EMI is computed over `relatedPeriods(effectiveDue)`, and `effectiveDue` is the
NEXT period's due date when the disbursement lands on a due date. On P-03 that is
5 periods, not `NumberOfRepayments = 6`. `NumberOfRepayments` appears in the port
in exactly one place — the count of windows to step — and nowhere in the money.
**Measured:** the wrong `n` fails P-03 at `row 2 principal_minor: expected 1977,
got 1643 (delta -334)` — **the vector's stated margin, to the unit.**

**③ `MONTHEND-CONTINUE-FROM-CLAMPED-DAY` (P-02 / P-02b, structural, ZERO money margin).**
`reAnchorToSeed` re-anchors on the **seed** (the disbursement date), which is never
reassigned; `repaymentDueDates` steps from the previous *emitted* boundary and then
re-anchors, so 2024-01-31 → 2024-02-29 → **2024-03-31**. The clamped day lives in
the boundary, never in the seed. There is also a dedicated unit test, because under
30/360 the money is date-independent and no amount can catch this.
**Measured:** dropping the re-anchor fails P-02 and P-02b on
`row 2 due_date: expected 2024-03-31, got 2024-03-29` — and on **no money cell
whatsoever**, exactly as the vectors' `graded_against` claims.

**④ `LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT` (1 minor unit).**
Implemented as the driver's correction requires: the residual lands on the last
unpaid period's **EMI** (`applyFinalPeriodResidual`), and `duePrincipalMinor` is
the same `emi − interest` expression on every row.
**Measured:** removing the residual fails **10 of the 11** vectors (all but P-01),
at ±1 minor unit — `row 6 principal_minor: expected 1690, got 1691` on P-00 — and
also trips `principal_amortizes_to_zero`.

---

## 4. Verbatim conformance output

### BEFORE (`main` @ `30a030e`, nothing registered) — exit 2

```
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

=== GOLDEN-VECTOR CONFORMANCE — Fineract reference oracle vs Go module ===
    store           …/.softhouse/vectors
    implementation  (none)
    oracle probe    UP

CASE                         CLASS            SEAM        OUTCOME       CELLS UNGRADED  REASON
----------------------------------------------------------------------------------------------------------------------
SELFTEST-01-two-period-ze... selftest         none        HARNESS-ERROR      0        0  SELF-TEST FIXTURE — EXCLUDED FROM THE P...
P-00                         parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-01                         parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-02                         parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-02b                        parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-03                         parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-04f                        parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-04t                        parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-MNT-1M2                    parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-MNT-4M999                  parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-MNT-50M                    parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
P-MNT-5M                     parity           path_a_e... HARNESS-ERROR      0        0  no implementation to grade
REFUSE-01-actual-actual-u... contract-refusal none        HARNESS-ERROR      0        0  no implementation to grade
REFUSE-02-half-even-ungraded contract-refusal none        HARNESS-ERROR      0        0  no implementation to grade
REFUSE-03-annual-fixed303... contract-refusal none        HARNESS-ERROR      0        0  no implementation to grade
REFUSE-04-disbursement-af... contract-refusal none        HARNESS-ERROR      0        0  no implementation to grade

--- INVARIANT COVERAGE (checked against what the implementation RETURNED) ---
    principal_portions_sum_to_disbursed    hold 0    violated 0    exempt 0    n/a 0
    principal_amortizes_to_zero            hold 0    violated 0    exempt 0    n/a 0
    balance_roll_forward                   hold 0    violated 0    exempt 0    n/a 0
    splits_sum_to_whole                    hold 0    violated 0    exempt 0    n/a 0
    monotonic_due_dates                    hold 0    violated 0    exempt 0    n/a 0
    contract_row_ordering                  hold 0    violated 0    exempt 0    n/a 0

--- SUMMARY ---
    parity vectors          PASS 0    FAIL 0
    contract-refusal        PASS 0    FAIL 0   (derived from the ratified contract, NOT oracle-observed)
    self-test fixtures      PASS 0    FAIL 0   (hand-authored; EXCLUDED from the parity count)
    refused                 0   (no discriminating vector / seam blind — not a pass, not a failure)
    inadmissible            0
    harness errors          16
    cells compared          0 graded, 0 ungraded (never recorded by the capture)
    kills named             21 money, 3 structural (zero-margin by construction, never merged)
    recorded, never graded  0 rate factors (TRANSCRIBED-ROUNDED), 0 declared over-scaled money cells
    invariant violations    0

--- WHY THIS RUN CANNOT BE TRUSTED ---
    * NO IMPLEMENTATION REGISTERED: there is nothing to grade. This is exit 2, not a pass over zero work. Register the Go port in cmd/conformance/impl_hook.go once it exists.
    * NO PARITY VECTOR WAS GRADED. …

VERDICT: UNUSABLE (exit 2) — no trustworthy verdict is available. THIS IS NOT A PASS.
```

### AFTER (this branch) — exit 0

```
conformance: reference oracle (https://localhost:8443/fineract-provider/actuator/health) probe = up

=== GOLDEN-VECTOR CONFORMANCE — Fineract reference oracle vs Go module ===
    store           …/.softhouse/vectors
    implementation  loanschedule-go
    oracle probe    UP

CASE                         CLASS            SEAM        OUTCOME       CELLS UNGRADED  REASON
----------------------------------------------------------------------------------------------------------------------
SELFTEST-01-two-period-ze... selftest         none        PASS             21        0  SELF-TEST FIXTURE — EXCLUDED FROM THE P...
P-00                         parity           path_a_e... PASS             47        2
P-01                         parity           path_a_e... PASS            131        2
P-02                         parity           path_a_e... PASS             47        2
P-02b                        parity           path_a_e... PASS             47        2
P-03                         parity           path_a_e... PASS             47        2
P-04f                        parity           path_a_e... PASS             47        2
P-04t                        parity           path_a_e... PASS             47        2
P-MNT-1M2                    parity           path_a_e... PASS             89        2
P-MNT-4M999                  parity           path_a_e... PASS            131        2
P-MNT-50M                    parity           path_a_e... PASS            257        2
P-MNT-5M                     parity           path_a_e... PASS            131        2
REFUSE-01-actual-actual-u... contract-refusal none        PASS              1        0
REFUSE-02-half-even-ungraded contract-refusal none        PASS              1        0
REFUSE-03-annual-fixed303... contract-refusal none        PASS              1        0
REFUSE-04-disbursement-af... contract-refusal none        PASS              1        0

--- INVARIANT COVERAGE (checked against what the implementation RETURNED) ---
    principal_portions_sum_to_disbursed    hold 12   violated 0    exempt 0    n/a 0
    principal_amortizes_to_zero            hold 12   violated 0    exempt 0    n/a 0
    balance_roll_forward                   hold 12   violated 0    exempt 0    n/a 0
    splits_sum_to_whole                    hold 12   violated 0    exempt 0    n/a 0
    monotonic_due_dates                    hold 12   violated 0    exempt 0    n/a 0
    contract_row_ordering                  hold 12   violated 0    exempt 0    n/a 0

--- SUMMARY ---
    parity vectors          PASS 11   FAIL 0
    contract-refusal        PASS 4    FAIL 0   (derived from the ratified contract, NOT oracle-observed)
    self-test fixtures      PASS 1    FAIL 0   (hand-authored; EXCLUDED from the parity count)
    refused                 0   (no discriminating vector / seam blind — not a pass, not a failure)
    inadmissible            0
    harness errors          0
    cells compared          1046 graded, 22 ungraded (never recorded by the capture)
    kills named             21 money, 3 structural (zero-margin by construction, never merged)
    recorded, never graded  0 rate factors (TRANSCRIBED-ROUNDED), 0 declared over-scaled money cells
    invariant violations    0

VERDICT: PASS (exit 0) — 11 parity vectors match the pinned reference oracle, 1046 cells compared.
         This means "matches the reference oracle on captured vectors, within the graded domain".
         IT DOES NOT MEAN SAFE TO CUT OVER. Cutover is a user gate.
```

### Per-vector result

**Every vector passes. There is no failing cell and no margin to report.**

| case | class | outcome | cells graded | ungraded |
|---|---|---|---|---|
| `P-00` | parity | PASS | 47 | 2 |
| `P-01` | parity | PASS | 131 | 2 |
| `P-02` | parity | PASS | 47 | 2 |
| `P-02b` | parity | PASS | 47 | 2 |
| `P-03` | parity | PASS | 47 | 2 |
| `P-04f` | parity | PASS | 47 | 2 |
| `P-04t` | parity | PASS | 47 | 2 |
| `P-MNT-1M2` | parity | PASS | 89 | 2 |
| `P-MNT-4M999` | parity | PASS | 131 | 2 |
| `P-MNT-50M` | parity | PASS | 257 | 2 |
| `P-MNT-5M` | parity | PASS | 131 | 2 |
| `REFUSE-01` (ACT/ACT) | contract-refusal | PASS — `ErrNoDiscriminatingVector` | 1 | 0 |
| `REFUSE-02` (HALF_EVEN) | contract-refusal | PASS — `ErrNoDiscriminatingVector` | 1 | 0 |
| `REFUSE-03` (annual + 30/360) | contract-refusal | PASS — `ErrUnsupportedConfiguration` exactly | 1 | 0 |
| `REFUSE-04` (disbursement ≥ maturity) | contract-refusal | PASS — `ErrNoDiscriminatingVector` | 1 | 0 |
| `SELFTEST-01` | selftest | PASS (excluded from parity) | 21 | 0 |

The 2 ungraded cells per parity vector are the disbursement row's
`installment_number` and `interest_minor`, which the oracle's own record type has
no accessor for — correctly carried as UNGRADED by the harness, not compared.

**Per the driver: the 11 vectors are 9 DISTINCT SHAPES.** `P-00`, `P-04f` and
`P-04t` are byte-identical in request and expect. 11/11 is not eleven independent
confirmations, and I have not treated it as such anywhere above.

---

## 5. Other verification

| check | result |
|---|---|
| `go build ./...` | exit 0 |
| `go vet ./...` | exit 0 |
| `go test ./...` | `ok` — `loanschedule` 0.708s, `conformance` 1.004s |
| `gofmt -l .` from `nexus/` | **only** `internal/apps/loanschedule/contract/contract.go` (expected, gate **G-3**) |
| no-float guard (`TestNoFloatInTheLoanScheduleTree`, token stream) | passes over the new files |
| `.softhouse/conformance.sh` | **exit 0** |
| `.softhouse/conformance.sh --prove` | **14 passed, 1 failed** — see §7 |

`git diff --stat 30a030e...HEAD` touches only the five files named at the top.

### The port's own tests

`loanschedule_test.go` deliberately asserts nothing about a schedule the corpus
already grades. It covers the arithmetic and calendar primitives against
properties of `BigDecimal`/`LocalDate` (significant digits vs places, HALF_UP ties
away from zero, `plusMonths` clamping, the **packed** `monthsBetween` rule,
epoch-day round trips), the month-end date sequence, refusal precedence, and
determinism.

**The one test that carries real information: `TestEMIReAdjustLoopReproducesTheOraclesObservedFigures`.**
It PASSES. See §6.

---

## 6. What the corpus does NOT grade — measured, not assumed

I mutated the port into each named wrong implementation and ran the real harness.
The tree was restored after every case; the script is `/tmp` scratch and is not
committed, but every result below is reproducible in a minute.

### Killed by the corpus (5)

| counterfactual | caught by | evidence |
|---|---|---|
| EMI denominator = `NumberOfRepayments` | **P-03** | `row 2 principal_minor: expected 1977, got 1643 (delta -334)` |
| month-end continue-from-clamped-day | **P-02, P-02b** | `row 2 due_date: expected 2024-03-31, got 2024-03-29`; **no money cell moves** |
| row order sort-by-date-disbursement-first | **P-03** | `row 0 kind: expected REPAYMENT, got DISBURSEMENT` |
| no final-period balancing adjustment | **10 of 11** (all but P-01) | `row 6 principal_minor: expected 1690, got 1691 (delta 1)`; also violates `principal_amortizes_to_zero` |
| pre-disbursement row carries the whole principal (M1 used where M3 belongs) | **P-03** | `row 0 principal_minor: expected 0, got 10000 (delta 10000)` |

### NOT killed — the corpus is blind to these four, and three of them move money

| counterfactual | result | why it matters |
|---|---|---|
| **the entire EMI re-adjust smoothing loop removed** | **exit 0, all 11 PASS** | Confirms T9/the driver **by measurement.** DEC-1 calls the loop "a conformance obligation, not backlog" and records that it moves money on ordinary loans. **A conformance PASS is not evidence that this port implements it.** |
| **textbook `balance × rateFactor`** (the three separately rounded operations collapsed to one) | **exit 0, all 11 PASS** | DEC-1 re-derives 699 of 43,992 (1.59%) in-graded-domain shapes diverging. The promoted corpus cannot see any of it. |
| **rate factor without the trailing `setScale`** | **exit 0, all 11 PASS** | The mutation is NOT vacuous — at (19, HALF_UP), 7% / 30/360 the two values are `0.005833333333333333332` (5 mc ops) and `0.0058333333333333333` (after `setScale(19)`). They differ, and 1046 cells cannot tell. DEC-1's worked example of this defect is at precision **12**, where the loss is large; **at production precision 19 it is below the currency layer on every shape in the corpus.** |
| **`periodRatio` replaced by `RepaymentEvery`** on the interest call site | **exit 0, all 11 PASS** | Consistent with DEC-1: the two coincide on the lattice, and all 11 promoted vectors are on-lattice. DEC-1 records 415 of 415 cells separating them on drift shapes (T39) — **none of those captures is promoted.** |

**The four unkilled classes are the single most important thing in this handoff.**
The port implements all four correctly (each cited in §2), but *the corpus cannot
tell*, so a later reviewer must re-derive them from source rather than trust the
green.

### The one independent check of the EMI loop that does exist

DEC-1's doc comment on `Period` records two figures **observed on the pinned
oracle at (19, HALF_UP), strictly inside the graded domain**, where the loop
fires:

- MNT 1,014,632 / 6 × 7.0% → oracle level installment **172,574.64** (a no-loop model gives 172,574.63, and every period shifts)
- MNT 127,704 / 36 × 16.8% → oracle total interest **35,746.56** (a no-loop model gives 35,746.69)

**This port reproduces both, to the minor unit** — `TestEMIReAdjustLoopReproducesTheOraclesObservedFigures`
passes. That is the strongest statement available about the loop today, and it is
carefully NOT a parity claim: those figures are an attested reading of a ratified
document, not a promoted vector, which is exactly why they live in a test and not
in the vector store. **A vector for either shape would close the gap.** The
cheapest one is the 6-period MNT 1,014,632 / 7.0% shape: same shape family as
P-00, one capture, and it grades the loop, its guard and its divisor at once.

---

## 7. `--prove` — one proof went STALE, reported and not fixed

`.softhouse/conformance.sh --prove` on this branch: **14 passed, 1 failed.**

```
PROOF FAIL exit 0 (wanted 2)   no implementation to grade
PROOF OK   exit 2 (wanted 2)   reference oracle unreachable …
PROOF OK   exit 0 (wanted 0)   harness self-test over the pristine store
PROOF OK   exit 1 (wanted 1)   one-minor-unit perturbation of an expected value
PROOF OK   exit 2 (wanted 2)   integer perturbed but the oracle wire text not (transcription error)
PROOF OK   exit 2 (wanted 2)   empty vector store
PROOF OK   exit 2 (wanted 2)   absent vector store
PROOF OK   exit 2 (wanted 2)   self-test fixture excluded from the parity count
PROOF OK   exit 0               the fixture PASSES and parity stays 0, stamped NOT a conformance PASS
PROOF OK   exit 2 (wanted 2)   float token in a vector file
PROOF OK   exit 2 (wanted 2)   T17-F5: an UNDECLARED over-scaled money wire text is inadmissible
PROOF OK   exit 2 (wanted 2)   T17-F6: a rate factor claiming exactness is inadmissible
PROOF OK   exit 2 (wanted 2)   T17-F2: a corroboration claiming an unattested column is inadmissible
PROOF OK   exit 2 (wanted 2)   D-4: a structural counterfactual naming a money column is inadmissible
PROOF OK   exit 0 (wanted 0)   D-5: an unrecorded money cell costs the CELL, not the vector
PROOFS: 14 passed, 1 failed
```

**Case 1 is `expect 2 "no implementation to grade" -- "$bin" -oracle-probe=up`.**
It asserts that a run with the oracle reachable exits 2 *because nothing is
registered*. Registering the port — which is this task's deliverable, and which
`impl_hook.go`'s own comment instructs — necessarily negates that premise: the run
now grades everything and exits 0.

**Measured, not argued.** I restored the pre-T10 `impl_hook.go` from `30a030e`,
re-ran `--prove`, and got **`PROOFS: 15 passed, 0 failed`** with
`PROOF OK   exit 2 (wanted 2)   no implementation to grade`; I then restored my
version and got 14/15 with only that case flipping. **Nothing else changed and no
proof lost its power.** In particular case 8 still returns exit 2 — a self-test
fixture buys no parity even when graded by a real port.

This is structurally the harness's own **"STALE"** concept (`grade.go` marks a
refusal vector INADMISSIBLE the moment its capability enters the graded domain,
with the words "this is not a defect in any implementation"). Case 1 is the same
thing applied to a proof.

**I did not fix it — the harness is not mine to edit.** For whoever does, the
minimal repairs, in order of preference:

1. Give the binary a way to demonstrate the empty case without unregistering:
   `expect 2 "no implementation named" -- "$bin" -oracle-probe=up -impl=__none__`
   already exits 2 today via `main.go`'s "no implementation named %q is
   registered" path, and the property it proves — *nothing to grade is exit 2,
   never a pass over zero work* — is preserved exactly.
2. Or build a second binary from a tag-excluded `impl_hook.go` for case 1 only.

Option 1 is one line and needs no new build.

---

## 8. Where DEC-1's text and Fineract's source disagree, or DEC-1 disagrees with itself

**Flagged, never silently reconciled.** None of these blocked the port; all are
gate material.

### 8a. DEC-1 says zero interest is outside the graded domain; DEC-1's own graded-domain LIST does not, and the ratified harness does not either

`contract.go`, `GenerateRequest.AnnualNominalInterestRate`:

> Zero interest is `Rate{0, 1}` … **It is nonetheless outside the graded domain,
> because no capture exercises it.**

But the graded domain is *defined* by the enumerated conjunction under
"# The graded domain" ("A request is in the GRADED DOMAIN when all of the
following hold"), and `AnnualNominalInterestRate` is **not in that list** — it is
explicitly in the other category, "continuous or unbounded inputs … graded by
sampling rather than by enumeration". The harness agrees with the list:
`conformance/admit.go:846-907` `GradedDomain()` has **no rate predicate**.

**Consequence, and it is not academic.** `SELFTEST-01` is a zero-rate request. A
port that reads the prose sentence refuses it; the harness then grades that
refusal against a `schedule` expectation and reports **FAIL**, i.e. exit 1.

**What I implemented and why:** the enumerated list, matching the harness. The
list is the normative definition; the prose sentence is a coverage remark that
contradicts it. **This is a DEC-1 internal inconsistency and needs a gate** — one
sentence deleted, or `AnnualNominalInterestRate == 0` added to the list *and*
`SELFTEST-01` re-authored. The two artefacts must not disagree about which
requests a conforming port answers.

### 8b. DEC-1 pins `interestCalculationPeriodMethod` as "left unset"; the same seam's `getInterestCalculationPeriodMethod()` gates a live branch of `addDisbursement`

`ProgressiveEMICalculator.java:128-133` selects a *different effective due date*
when the method is non-null, same-as-repayment-period and partial-period
calculation is off. DEC-1 pins it unset and I ported the null branch. Not a
disagreement about the answer — but the pin is a **behavioural** pin on the
disbursement-registration path, not merely a dropped input, and DEC-1 lists it
parenthetically among the "no counterpart in this contract" constants rather than
among the pins with a stated reason. Worth an explicit reason next revision.

### 8c. `contract.go` cites `ProgressiveLoanScheduleGenerator.java:305-308` for the M3 window; the predicate is at `:306-307`

Cosmetic, and I re-read it rather than trusting it (patterns.md: "a citation
nobody re-opens is a claim, not a fact"). `:305` is the local `periodDueDate`
binding and `:308` is the `continue` guard. The rule is unchanged. Recording it
because the last fire found a one-line citation slip of exactly this kind (D-1).

---

## 9. Judgements the contract did not pin

Every one is inside the graded domain's blind spots or outside the graded domain
entirely, so none can move a graded cell. All are cheap to change.

1. **`TimeZone` validation is STRUCTURAL, not a zone-database lookup.** The
   contract requires "an IANA zone name" and forbids a fixed offset, but does not
   say how to check. I reject empty, offset-shaped strings (`+08:00`, `UTC+8`,
   `GMT+8`, `-05`) and anything outside `letter [letter|digit|_|-|+]*` segments
   separated by `/`; I accept `Asia/Ulaanbaatar`, `Asia/Hovd` and bare `UTC`.
   **Why not `time.LoadLocation`:** it reads the host's tzdata, so generation
   would acquire a failure mode that changes no answer — the contract itself says
   the arithmetic is zone-free civil-date arithmetic and no capture can
   discriminate this field. **Cost of being wrong:** a valid-but-exotic zone name
   is rejected; no graded cell moves.
2. **`Currency.Code` must be exactly three A–Z characters.** The contract says
   "ISO 4217 alpha-3 code, upper case" and that an adapter must upper-case on the
   way in; it does not name a sentinel for a malformed code. I chose
   `ErrInvalidRequest`.
3. **`Currency.MinorUnitDigits` outside 0..9 is `ErrInvalidRequest`.** The
   contract bounds neither end. The graded domain pins it to 2 regardless.
4. **The 2s-and-5s terminating-decimal restriction is applied to
   `DownPaymentPercentage` as well as to `AnnualNominalInterestRate`.** The
   contract states the limit on the `Rate` *type*, and names only the interest
   rate under `ErrUnsupportedConfiguration`. A non-zero down payment is refused as
   ungraded anyway, so this is unreachable today.
5. **Unordered `Disbursements` is `ErrInvalidRequest`.** The contract says the
   slice is "ordered ascending by Date" without naming a sentinel. Unreachable
   while exactly one element is legal.
6. **Order of checks inside `ErrUnsupportedConfiguration`.** The contract fixes
   precedence *between* the three sentinels, not within one; every path returns
   the same sentinel value, so no ordering is observable.
7. **`ctx.Err()` is checked once, at entry, and its error is returned
   unwrapped.** The contract says a purely computational implementation "may
   honour cancellation and otherwise ignore it". Generation is microseconds; a
   cancellation error is not one of the three sentinels and callers distinguish it
   with `errors.Is(err, context.Canceled)`.
8. **`impl_hook.go` imports the port and registers it, instead of blank-importing
   a port that registers itself.** The hook's comment suggested the latter; that
   would make the production package import the conformance harness, so every
   binary generating a schedule would link the grading rig. Inverting the
   dependency keeps the port ignorant of being graded and keeps this file the
   single place the binary learns of an implementation. Documented in the file.
9. **The oracle's memoisation is not reproduced.** `Memo` invalidates on the hash
   of its declared dependencies (`Memo.java:56-72`), so it is a pure cache; the
   port recomputes. **But note:** the same mutual recursion without a cache is
   *exponential* — my first version hung on the 36-period vector — so
   `interestChainUpTo` walks the previous-period unrecognized-interest chain
   forward in one pass. Same function, `O(n)` instead of `O(2ⁿ)`.
10. **The provably-inert `outstandingPrincipal > totalDuePaidDiff` guard
    (`:1163-1174`) is ported rather than dropped.** It cannot fire on an unpaid
    schedule. patterns.md: both money defects of the first run hid behind a step
    an author had dismissed as a no-op.

---

## 10. Money-rule compliance

- **No binary fraction type anywhere.** `float32`, `float64`, `big.Float`,
  `complex64/128`, `ParseFloat`/`FormatFloat`/`AppendFloat` and `Decimal` do not
  appear as identifiers in any file I wrote. Enforced by
  `TestNoFloatInTheLoanScheduleTree` over the Go **token** stream and by
  `conformance.sh`'s comment-stripping grep guard; both pass.
- **Money is `int64` minor units** in every struct field, every intermediate that
  represents an amount, and every returned cell. The only non-integer quantities
  are `*big.Rat` — **exact rationals**, carrying no rounding of their own — and
  they hold exactly what the oracle holds in a bare `BigDecimal`: rate factors,
  growth factors and the EMI recurrence. Rounding happens only at the points the
  oracle rounds, through `roundSignificant` (significant digits) and `roundScale`
  (decimal places), which are two functions precisely because the oracle reads one
  `MathContext` in both senses.
- **The doubles in the Java are NOT reproduced.** `Math.floor(n/2.0)` and
  `Money.copy(double)` operate on exact small integers; the guard is
  `|difference| × 100 > floor(n/2) × 10^minorDigits` in exact integer arithmetic.
- **Deterministic:** no clock, no locale, no environment, no map anywhere in the
  port; iteration is over slices only. `TestGenerationIsDeterministic` asserts it.
- **No database, no driver, no persistence, no money movement.** PostgreSQL
  remains the program's only database and this context needs none.
- **No party identity, no `first_name`/`last_name`, no insurance/protection/
  guarantee string.** The port returns no free text at all except error messages,
  which name only request fields and sentinels.

---

## 11. What this does NOT license

**No cutover.** A PASS means "builds, tests green, known-bad patterns absent,
matches the reference oracle on captured vectors, within the graded domain". It is
not a shadow-parity window and it is not regulatory sign-off, both of which are
hard `user` gates.

Concretely, and by measurement rather than by disclaimer:

- **9 distinct shapes**, not 11.
- **Four defect classes are invisible to the corpus** (§6), three of which move
  money on shapes DEC-1 has already re-derived or observed.
- The corpus grades **one** day-count arm, **one** rounding mode, **one**
  frequency, **one** currency scale, **zero** charges, **zero** down payments,
  **zero** multi-tranche disbursements and **zero** installment rounding. The port
  refuses every one of those with the contract's own sentinel rather than
  returning a number.

### Recommended next captures, in the order that buys the most

1. **A shape that trips the EMI re-adjust guard** — e.g. MNT 1,014,632 / 6 ×
   7.0%. Grades the loop, its guard and its divisor, and closes the largest
   ungraded money surface in the context.
2. **A drift shape** (schedule start ≠ disbursement date with a month-end
   re-anchor) — grades `periodRatio` against `RepaymentEvery`; DEC-1 records 415
   of 415 separating cells from T39, none promoted.
3. **A strictly-inside-a-period disbursement** — grades the day-count proration
   and the three-operation interest round-trip together; T37-3b/3d already
   observed both, neither promoted.
4. **A rate factor whose 20th–21st decimal places reach a payable amount** —
   grades the trailing `setScale` at production precision, which nothing does
   today.
