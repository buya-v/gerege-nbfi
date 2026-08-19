# T9 — independent review: conformance harness + golden-vector store

- **Run:** `2026-08-17-run1-harness-schedule-poc`  **Context:** `harness`  **Task:** T9 (independent reviewer)
- **Reviewed tree:** branch `softhouse/T9-harness-vectors-review`, cut from `main` @ `30a030e`
  (`79233ca merge T8-promote`, `b87645d merge T20`). [VERIFIED: `git log --oneline -12 main`]
- **Reference oracle (Fineract):** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`,
  working tree clean. [VERIFIED: `git -C /Users/buv/fineract log -1 --format='%H %ci'` →
  `426a2354… 2026-08-12 14:59:16 +0200`; `git status --porcelain` empty]
- **Oracle reachable during this review:** yes.
  [VERIFIED: `curl -sk https://localhost:8443/fineract-provider/actuator/health` →
  `{"status":"UP","groups":["liveness","readiness"]}`]

> Throughout, **"the oracle" means the Fineract reference implementation**. Oracle Database is a
> prohibited product in this program and appears nowhere in this stack. PostgreSQL only.

## 0. A note on the starting state, because it nearly invalidated this review

The worktree I was given was checked out at `2ec5976` (the fire-lock commit), which **predates the
T8 promotion merge**. `.softhouse/vectors/loanschedule/` in that tree contained only the four
`REFUSE-*` vectors — no parity vectors at all. Had I graded what was in front of me I would have
reviewed an empty corpus and called it a store.

[VERIFIED: `git ls-tree -r --name-only softhouse/T7-conformance-harness -- .softhouse/vectors/`
returns 8 paths, none of them `P-*`; the same command against `softhouse/T8-promote-parity-vectors`
returns 19 paths including all eleven `P-*`.]

I re-cut onto `main` before doing any work. **Recommendation to the driver (process, P2):** a
reviewer worktree must be created from the commit that contains the artefact under review, or the
review brief must name the branch. This one silently did not.

---

## 1. Method — and why it is not the fourth run of the same method

The brief is right that three prior parties re-derived from DEC-1's *prose* (`r = rate/100 × 30/360`,
`EMI = P·r/(1−(1+r)^−n)`, HALF_UP 2 dp, balancing final principal) and that agreement among three
applications of one method is weak evidence.

I did two things instead.

1. **Traced the actual Java call path** for the Path A embeddable seam and re-implemented the
   oracle's algorithm **in the shape the source writes it**, not the shape DEC-1 summarises it —
   different formula, no `pow`, no closed form, per-period rate factors with the day ratio, and
   `Money`-level re-rounding at every intermediate. Then checked the corpus against *that*.
2. **Audited DEC-1's normative text against the source** in six places where a G-4-class
   disagreement could hide.

### 1.1 The source algorithm, cited

All Java paths below are relative to `/Users/buv/fineract` at the pinned commit.
`ProgressiveEMICalculator.java` =
`fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanproduct/calc/ProgressiveEMICalculator.java`.

| step | source | what it actually does |
|---|---|---|
| rate factor | `ProgressiveEMICalculator.java:1950-1963` (`rateFactorByRepaymentPeriod`) | `(rate/100) × ((30 × repaymentEvery)/360) × actualDays / calculatedDays`, each step under `mc`, then **`.setScale(mc.getPrecision(), mc.getRoundingMode())`** |
| nominal rate | `:1318-1320` (`calcNominalInterestRatePercentage`), `DIVISOR_100` at `:75` | `rate.divide(100, mc)` |
| days in year | `DaysInYearType.java:38,81-86` | `DAYS_360 → 360` |
| EMI numerator | `:1816-1820` (`calculateRateFactorPlus1NForEmi`) | `Π (1 + rᵢ)` folded with `acc.multiply(v, mc)` — **not** `pow` |
| per-period `1+r` | `RepaymentPeriod.java:216-218` | `interestPeriods.stream().map(getRateFactor).reduce(ONE, BigDecimal::add)` — a **sum**, not a product |
| EMI denominator | `:1822-1828` + `fnValue` at `:1991-1993` | fold over `periods.skip(1)`: `fn = 1 + fn_prev × rᵢ`, seeded `fn = 1` |
| EMI | `:1838-1841` (`calculateEMIValue`) | `rateFactorPlus1N × balance ÷ fnResult`, no closed form anywhere |
| EMI → money | `:1731-1733` → `Money.java:40-53` | `setScale(currency.getDecimalPlaces(), mc.getRoundingMode())` = **2 dp HALF_UP** |
| per-period interest | `InterestPeriod.java:145-158` | `balance × rateFactorTillPeriodDueDate ÷ lengthTillDue × length`, all under `mc`; wrapped in `Money.of` at `RepaymentPeriod.java:252-265` |
| principal | `RepaymentPeriod.java:345-350` (`getDuePrincipal`) | `EMI − dueInterest`, via `Money` (so re-rounded) — **never** "the remaining balance" |
| final-period balancing | `:1176-1210` (`calculateLastUnpaidRepaymentPeriodEMI`) | the **last unpaid period's EMI** absorbs `Σdisbursed + Σcapitalized + Σcredited + ΣdueInterest − ΣEMI` |
| `n` for the EMI | `:732` → `ProgressiveLoanInterestScheduleModel.java:191-198` | `relatedRepaymentPeriods.size()`, **not** `numberOfRepayments` |
| effective due date | `:250-263` (`getEffectiveRepaymentDueDate`) | when the disbursement equals a period's due date, **skip to the next period's due date** |
| row order | `ProgressiveLoanScheduleGenerator.java:111-150`, `:299-318`; `LoanSchedulePlan.java:45-97` | per repayment period, disbursements emitted at the **head of the period whose half-open `[from, due)` window contains them**; **no global sort by date**; `LoanScheduleModel.java:78-82` sorts nothing |
| month-end stepping | `DefaultScheduledDateGenerator.java:50-75`, `:128-131`, `:320-322`, `:168-176` | iterative `last.plusMonths(n)` (clamps) **then** re-anchor `min(lengthOfMonth, seedDay)` when `seedDOM > 28 && dateDOM >= 28` |

Two corrections to the folklore, both load-bearing for T10:

- **The EMI is not computed by the closed form.** `P·r/(1−(1+r)^−n)` is algebraically equal to
  `rateFactorPlus1N × P / fnResult` but is a **different sequence of finite-precision operations**.
  A port that implements the closed form is not obviously wrong and is not obviously right.
  DEC-1 does *not* mandate the closed form — it specifies "the recurrence that yields the raw
  installment" [VERIFIED: `contract.go:1630-1632`] — so DEC-1 is correct and the folklore is the
  problem. **A Go port must implement the accumulator, and no vector in this store can tell the two
  apart.** (I checked: both forms reproduce all 11.)
- **There is no "final principal := whole remaining balance" statement in the oracle.** Principal is
  *always* `EMI − interest` (`RepaymentPeriod.java:345-350`); it is the **last unpaid period's EMI**
  that is adjusted (`:1176-1210`). The observable consequence is identical, which is why the vectors
  reproduce either way, but `P-00`/`P-02`/`P-02b`/`P-03`'s counterfactual
  `LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT` describes the *effect*, not the
  mechanism. Accurate as a kill; imprecise as a description. P2.

### 1.2 Result — all eleven reproduce from the source-shaped algorithm

I implemented the table above (fold-accumulator EMI, per-period rate factor with the day ratio,
`balance × r ÷ L × L` interest, `Money` 2 dp HALF_UP at every step, last-period EMI absorption) and
ran it against every promoted vector, comparing **every** principal, interest and outstanding cell:

```
case         r                      EMI            every cell reproduces
P-00         0.0058333333333333333  17.01          True
P-01         0.0154166666666666667  5613766.78     True
P-02         0.0058333333333333333  17.01          True
P-02b        0.0058333333333333333  17.01          True
P-03         0.0058333333333333333  20.35          True
P-04f        0.0058333333333333333  17.01          True
P-04t        0.0058333333333333333  17.01          True
P-MNT-1M2    0.0180000000000000000  112082.37      True
P-MNT-4M999  0.0154166666666666667  320221.84      True
P-MNT-50M    0.0140000000000000000  1777663.51     True
P-MNT-5M     0.0154166666666666667  320221.91      True
```

[VERIFIED: my own re-derivation, run in this review; 1,046 graded cells across the store, zero
disagreements.] **No vector is rejected on arithmetic.**

---

## 2. (a) The three hand re-derivations, from source

### 2.1 `P-03` — disbursement exactly on repayment 1's due date

Request: start 2024-01-01, disbursement 2024-02-01 for USD 100.00, 6 × monthly, 7.0 % p.a., 30/360.

**Why `n = 5` and not 6, from source.** `getEffectiveRepaymentDueDate`
(`ProgressiveEMICalculator.java:250-263`) tests `changedRepaymentPeriod.getDueDate().isEqual(operationDueDate)`.
Period 1 is `[2024-01-01, 2024-02-01]` and the disbursement is 2024-02-01, so the test is true and
the effective due date becomes **period 2's** due date, 2024-03-01. `getRelatedRepaymentPeriods`
(`ProgressiveLoanInterestScheduleModel.java:191-198`) then filters
`!(p.DueDate < 2024-03-01)`, yielding periods 2..6 → **`n = 5`**. `calculateEMIOnActualModel…`
(`:1722-1741`) writes the installment onto that list only, so period 1 keeps the zero EMI it was
constructed with at `:105-109`. [VERIFIED: all four citations read in full.]

Arithmetic at `(19, HALF_UP)`:

```
r        = 0.07 × (30×1/360) = 0.005833333333333333333  → setScale(19) → 0.0058333333333333333
Π(1+r)   over 5 periods      = 1.029513623948…
fn       = fold over 4       = 5.058334856…
EMI      = Π(1+r) × 100.00 ÷ fn = 20.35135713667974312 → Money(2 dp, HALF_UP) = 20.35
```

| # | interest = round₂(bal×r) | principal | balance | vector |
|---|---|---|---|---|
| 1 | — (zero EMI, all-zero row) | 0.00 | 0.00 | `0 / 0 / 0` ✔ |
| 2 | 0.58 | 20.35 − 0.58 = **19.77** | 80.23 | `1977 / 58 / 8023` ✔ |
| 3 | 0.47 | **19.88** | 60.35 | `1988 / 47 / 6035` ✔ |
| 4 | 0.35 | **20.00** | 40.35 | `2000 / 35 / 4035` ✔ |
| 5 | 0.24 | **20.11** | 20.24 | `2011 / 24 / 2024` ✔ |
| 6 | 0.12 | balance **20.24** (total 20.36) | 0.00 | `2024 / 12 / 0` ✔ |

**Row order, from source.** `LoanSchedulePlan.from` iterates `model.getPeriods()` verbatim with no
sort (`LoanSchedulePlan.java:45-97`); `LoanScheduleModel` sorts nothing (`LoanScheduleModel.java:78-82`).
The emission loop (`ProgressiveLoanScheduleGenerator.java:111-150`) calls `processDisbursements`
**before** `periods.add(repaymentPeriod)` for each period, and `processDisbursements` admits a
disbursement only when `!disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate)`
(`:307-308`) — a **half-open `[from, due)`** window. 2024-02-01 is therefore *not* in period 1's
window, so period 1 is emitted alone; it *is* in period 2's window `[2024-02-01, 2024-03-01)`, so
period 2's iteration emits `DISBURSEMENT` first and then repayment 2. Observed order
`[REPAYMENT 1, DISBURSEMENT, REPAYMENT 2..6]` is exactly what the code produces. **VERIFIED, and the
vector's `ROW-ORDER-SORT-BY-DATE-DISBURSEMENT-FIRST` counterfactual is a real kill.**

`P-03` **ACCEPTED**.

### 2.2 `P-02` / `P-02b` — month-end seed days 31 and 30 across a leap February

These are date kills at zero money margin, so I re-derived the **stepping rule**, not the arithmetic.

`EmbeddableProgressiveLoanScheduleGenerator.java:38-47` constructs the stock
`DefaultScheduledDateGenerator` — there is no embeddable-specific date generator.
`ProgressiveLoanScheduleGenerator.java:83` delegates with `generate(mc, terms, null, null)`, so
`loanCharges` and `holidayDetailDTO` are both null; `DefaultScheduledDateGenerator.java:224-247`
wraps its entire holiday/working-day body in `if (holidayDetailDTO != null)`, and the calendar block
at `:132-157` is gated on `loanCalendar != null`, which the Path A `LoanApplicationTerms.Builder`
never sets. **Nothing perturbs the dates.**

The rule itself (`DefaultScheduledDateGenerator.java:50-75`, `:128-131`, `:320-322`, `:168-176`):

```java
// :320-322                          // :168-176
startDate.plusMonths(repaidEvery)    if (frequencyType.isMonthly() && seedDate.get(DAY_OF_MONTH) > 28
                                             && date.get(DAY_OF_MONTH) >= 28) {
                                         int adjustedDay = Math.min(YearMonth.from(date).lengthOfMonth(), seedDay);
                                         return date.with(DAY_OF_MONTH, adjustedDay);
                                     }
```

so `due(k) = adjustDate(due(k−1).plusMonths(1), seed)`, `due(0) = ScheduleStartDate`, seed =
`Disbursement.Date` (`LoanApplicationTerms.java:583-589`).

Seed day 31: `01-31 →plus→ 02-29 →min(29,31)→ **02-29**`; `→plus→ 03-29 →min(31,31)→ **03-31**`;
`→ 04-30 →min(30,31)→ **04-30**`; `→ 05-30 →min(31,31)→ **05-31**`; `→ 06-30 →min(30,31)→ **06-30**`;
`→ 07-30 →min(31,31)→ **07-31**`.

Seed day 30: `**02-29**, **03-30**, **04-30**, **05-30**, **06-30**, **07-30**`.

Both sequences match the vectors **exactly, cell for cell**.
[VERIFIED: `P-02` due dates `2024-02-29, 03-31, 04-30, 05-31, 06-30, 07-31`; `P-02b`
`2024-02-29, 03-30, 04-30, 05-30, 06-30, 07-30`.]

Money columns of `P-02` and `P-02b` are **identical** (`1643/58/8357 … 1690/10/0`) — as they must be,
since 30/360 gives every period `actualDays == calculatedDays` regardless of month length. The
`margin_minor: "0"` on `MONTHEND-CONTINUE-FROM-CLAMPED-DAY` is therefore **honest and correct**, and
the kill is genuinely and only in the date column.

`P-02`, `P-02b` **ACCEPTED**.

**One thing the pair does NOT grade, worth recording for T10.** The re-anchor seed is
`disbursementDate` (`LoanApplicationTerms.java:583-589`) while the stepping start is
`scheduleGenerationStartDate` (`ProgressiveLoanScheduleGenerator.java:94-96`, reached because the
seam never sets `repaymentStartDateType`, so `RepaymentStartDateType.DISBURSEMENT_DATE.equals(null)`
is false). In both `P-02` and `P-02b` the two coincide, so **no vector separates the two seeds**.
A request with `ScheduleStartDate` on day 31 and a disbursement on day 15 would take the
`seedDOM > 28` guard to false and produce the lossy clamped sequence — the exact
`MONTHEND-CONTINUE-FROM-CLAMPED-DAY` counterfactual, but legitimately. DEC-1 states the distinction
correctly (`contract.go:1307-1318`); the corpus does not witness it.

### 2.3 `P-01` — 87,654,321.00 over 18 periods at 18.5 %

`r = 0.185 × 30/360 = 0.0154166666666666667`. Fold-accumulator EMI = `5,613,766.780111083901` →
`5,613,766.78`. Period 1: `87,654,321.00 × 37/2400 = 1,351,337.44875 → HALF_UP → 1,351,337.45`;
principal `5,613,766.78 − 1,351,337.45 = 4,262,429.33`; balance `83,391,891.67`. Vector:
`426242933 / 135133745 / 8339189167`. ✔ All 18 periods reproduce, final principal `5,528,535.20`
closing to exactly zero.

`P-01` **ACCEPTED**. `P-MNT-50M` (36 periods, 50 M, 16.8 %) likewise reproduces all 36 periods.

### 2.4 The two `graded_against` margins I was asked to re-derive independently

- **`P-01` `STRAIGHT-LINE-PRINCIPAL-DIVISION` = 65,885,070.** `87,654,321 ÷ 18 = 4,869,684.50`
  exactly → `486,968,450` minor. Observed principals span `426,242,933` … `552,853,520`; the widest
  gap is at period 18: `552,853,520 − 486,968,450 = **65,885,070**`. **CORRECT.**
  (`|426,242,933 − 486,968,450| = 60,725,517` is smaller, so "widest at period 18" is also correct.)
- **`P-03` `EMI-DENOMINATOR-…` = 334.** Counterfactual EMI over `n = 6` is `17.01`; counterfactual
  period-2 principal `17.01 − 0.58 = 16.43 = 1643`. Observed `1977`. `1977 − 1643 = **334**`.
  **CORRECT** — and `1643 / 58 / 1701` is *literally* `P-00`'s period-1 row, so the counterfactual is
  anchored on an observation rather than only on a derivation.
  [VERIFIED: `P-00` `expect.periods[1]` = `principal 1643, interest 58, total 1701`.]

---

## 3. DEC-1 (revision 12) audited against the source — six probes, no disagreement found

I went looking for another G-4. **I did not find one.** Every DEC-1 rule I checked is
source-accurate, and in two places DEC-1 is *more* precise than the folklore around it.

| # | DEC-1 claim | source | verdict |
|---|---|---|---|
| 1 | Month-end: step-then-re-anchor, seed = **disbursement date**, guards `seedDOM > 28` and `dateDOM >= 28` (`contract.go:1050-1064`) | `DefaultScheduledDateGenerator.java:168-176`; seed at `LoanApplicationTerms.java:583-589` | **MATCHES**, including the `>`/`>=` asymmetry, which is easy to get wrong and is stated correctly |
| 2 | `ScheduleStartDate` is the stepping start, not the disbursement date (`contract.go:1307-1318`) | `ProgressiveLoanScheduleGenerator.java:94-96`; `repaymentStartDateType` never set by the Builder so the ternary takes `getSubmittedOnDate()` = `scheduleGenerationStartDate` | **MATCHES**, and DEC-1 correctly identifies the *reason* (the seam never sets the type) |
| 3 | Five different period-membership conventions M1–M5 (`contract.go:2028-2070`) | M1 `LoanRepaymentScheduleProcessingWrapper.java:251-254` via `ProgressiveLoanInterestScheduleModel.java:238-245`; M2 `:195-197`; M3 `ProgressiveLoanScheduleGenerator.java:307-309` | **MATCHES all three of the three I traced.** DEC-1 correctly records that M1 is inclusive-at-both-ends for the first period while M3 is half-open — the exact trap a port would fall into |
| 4 | `n` is the related-period count, not `NumberOfRepayments` (`contract.go:1673-1697`) | `ProgressiveEMICalculator.java:732`, `:250-263`; `ProgressiveLoanInterestScheduleModel.java:191-198` | **MATCHES**, and DEC-1 explicitly records that revision 4 got this wrong and cited the unreachable null branch |
| 5 | `RateFactorScale` is a **scale** (`setScale`), `SignificantDigits` a **precision**, one integer read in two senses (`contract.go:609-623`, `:822-832`) | `ProgressiveEMICalculator.java:1959-1962` — `.divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode())` | **MATCHES** verbatim. See §3.1 for what the *corpus* does about it |
| 6 | The EMI re-adjust smoothing loop is normative and fires on every ordinary generation (`contract.go:1627-1648`) | `ProgressiveEMICalculator.java:1258-1309` called at `:749`; guard `EmiAdjustment.java:31-44` | **MATCHES.** See §3.2 |

### 3.1 The `RateFactorScale` distinction is real but the corpus cannot see it — **F-4, P2**

DEC-1's structural claim is correct at the production MathContext, not only at the precision-12
example it uses. Re-derived here for 7 % p.a., 30/360, month lengths 31/29/30:

```
precision 12 :  mc-only → 0.00583333333332 / …34 / …33          (3 distinct)   setScale(12) → 1 distinct
precision 19 :  mc-only → 0.005833333333333333332 / …34 / …33   (3 distinct)   setScale(19) → 1 distinct
```

So `setScale` genuinely collapses three rate factors into one at `(19, HALF_UP)` too — DEC-1 is right
about the mechanism. **But no vector in the store can grade it.** I ran the full source-faithful
derivation of all 11 vectors twice, once with the `setScale(19 dp)` rate factor and once with the
`precision-19 significant-digit` rate factor: **every cell of every vector is byte-identical under
both**. The spread between the two senses is ≈2×10⁻²¹ absolute in `r`; on `P-01`'s 87 M balance that
is ≈2×10⁻¹³ currency units, twelve orders of magnitude below a minor unit.

DEC-1 says an implementation applying only the significant-digit sense "misprices an ordinary loan"
(`contract.go:828-831`). At `(19, HALF_UP)`, on every shape in the graded domain that the corpus
contains, **that is not witnessed** — and I could not construct a monthly, single-interest-period
shape where it would be. I am **not** claiming DEC-1 is wrong (the claim may hold on the
`periodRatio` multiplier arm or at `RepaymentEvery > 1`, neither of which is captured). I am claiming
the store gives it **zero backing**, and that a port implementing the wrong sense passes 11/11.
[UNVERIFIED: whether any in-domain shape separates the two senses at precision 19 — I found none,
but I did not search exhaustively.]

### 3.2 The EMI smoothing loop is ungraded by all eleven vectors — **F-2, P1**

DEC-1 calls this "a conformance obligation, not backlog" (`contract.go:1660-1661`) and discloses that
"None of the twelve Run-1 captures trips this guard". **The promotion did not fix that.** I evaluated
the guard `|lastEMI − penultimateEMI| × 100 > floor(n/2)` currency units
(`EmiAdjustment.java:31-44`, threshold in minor units = `floor(n/2)`) on every promoted vector:

```
case          n   last      penult    |Δ|  threshold  trips?
P-00          6   1700      1701        1      3        no
P-01         18   561376678 561376678   0      9        no
P-02          6   1700      1701        1      3        no
P-02b         6   1700      1701        1      3        no
P-03          5   2036      2035        1      2        no
P-04f/P-04t   6   1700      1701        1      3        no
P-MNT-1M2    12   11208240  11208237    3      6        no
P-MNT-4M999  18   32022192  32022184    8      9        no   ← one minor unit short
P-MNT-50M    36   177766355 177766351   4     18        no
P-MNT-5M     18   32022186  32022191    5      9        no
```

**A Go port that omits `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` entirely passes 11 of
11.** My own re-derivation (§1.2) does not implement the loop and reproduces every cell — which is
the proof. `P-MNT-4M999` misses the guard by **one minor unit**, so the family plainly can trip it;
the corpus stops just short.

DEC-1 already names two shapes that *do* trip it, at `contract.go:1655-1658`:
`MNT 1,014,632 / 6 × 7.0 %` (oracle 172,574.64 vs no-loop 172,574.63, *every period shifts*) and
`MNT 127,704 / 36 × 16.8 %` (total interest 35,746.56 vs 35,746.69). **Neither was captured and
neither was promoted.** This is the largest gap between what DEC-1 obliges and what the store can
enforce.

---

## 4. (b) Mutation testing — the harness proved, and one hole found

`.softhouse/conformance.sh --prove` reports **15 passed, 0 failed** in my tree.
[VERIFIED: `PROOFS: 15 passed, 0 failed`.] I did not take it on trust. Everything below ran against
scratch copies under `/tmp/t9/`; the committed store was never modified.
[VERIFIED: `git status` clean apart from this review file.]

Baseline: `--self-test` over an unmodified copy → **exit 0**, 11 parity PASS, 1,046 graded / 22
ungraded cells, 0 invariant violations.

| # | perturbation | expected | observed | |
|---|---|---|---|---|
| M1 | `P-03` period 6 `interest_minor` 12→13, wire text left at `0.12` | red | **exit 2 INADMISSIBLE** — "expect.periods[6].interest_minor is 13 minor units …" | ✔ transcription cross-check fires before grading |
| M2 | **rounding step**: `P-03` period 6 interest 12→13 *consistently* (`0.12`→`0.13`) | red | **exit 1 FAIL**, `row 6 interest_minor: expected 13, got 12 (delta -1)` | ✔ |
| M3 | **period split**: `P-03` moves 1 minor unit of principal from period 2 to period 3, totals and roll-forward preserved | red | **exit 1 FAIL**, three cells named (`row 2 principal`, `row 2 outstanding`, `row 3 principal`) | ✔ |
| M4 | **date cell**: `P-02` period 2 `due_date` 2024-03-31 → 2024-03-29 (the clamped-rule counterfactual) | red | **exit 1 FAIL**, `row 2 due_date: expected 2024-03-29, got 2024-03-31` | ✔ **`monthend.reanchor`'s structural backing is real, not decorative** |
| M5 | oracle pointed at a closed port, real grading mode, live containers untouched | exit 2, never PASS | **exit 2**, `the reference oracle is UNREACHABLE … never becomes one` | ✔ |
| M6 | oracle genuinely UP, no port registered | exit 2 | **exit 2**, `NO IMPLEMENTATION REGISTERED` | ✔ (expected: T10's port is in another worktree) |

`diffSchedule` (`grade.go:485-540`) compares `kind`, `installment_number`, `from_date`, `due_date`
and all three money columns **separately, per row**, and reports each separately. The date-grading
capability is genuine. **The brief's worry about `monthend.reanchor` is resolved: it is backed.**

### 4.1 THE HOLE — a perturbation the harness does **not** catch — **F-1, P1**

`unrecorded_fields` accepts **`kind`, `installment_number`, `from_date` and `due_date`**
(`admit.go:825-832`, `gradedPeriodField`), and `diffSchedule` silently skips any cell named there
(`grade.go:502-528`). But the admission rule that a cell "marked unrecorded but carries a value" is
inadmissible (`admit.go:669-680`) is applied **only to the three money columns** — the `cells` slice
at `admit.go:667-671` contains `principal_minor`, `interest_minor`, `outstanding_principal_minor` and
nothing else.

**Consequence, demonstrated.** I put a *wrong* due date into `P-02` and declared `due_date`
unrecorded on that row:

```
P-02   parity   path_a_e...   PASS   46 cells   3 ungraded
parity vectors  PASS 11  FAIL 0     inadmissible 0
VERDICT: SELF-TEST PASS (exit 0)
```

Then the full version. I took **every one of the nine cells** that
`MONTHEND-CONTINUE-FROM-CLAMPED-DAY` names in `divergent_cells`, in **both** `P-02` and `P-02b`,
wrote `1999-01-01` into each, and added each to that row's `unrecorded_fields`:

```
P-02    parity  PASS  38 cells  11 ungraded
P-02b   parity  PASS  38 cells  11 ungraded
monthend.reanchor    killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY [structural], MONTHEND-… [structural]
parity vectors  PASS 11  FAIL 0     inadmissible 0
VERDICT: SELF-TEST PASS (exit 0)
```

**The store still claims `monthend.reanchor` is killed, while grading none of the cells the kill
rests on, and exits 0.** Two independent defects produce this:

- **F-1a** — `admit.go` does not enforce "unrecorded means empty" for `kind`, `installment_number`,
  `from_date`, `due_date`. A non-money cell can be simultaneously **populated and ungraded**, which
  is precisely the "storing a derivation as an observation" failure `unrecorded_fields` exists to
  prevent — applied to the half of the row where the month-end capability lives.
- **F-1b** — **nothing cross-checks `graded_against[].divergent_cells` against the rows'
  `unrecorded_fields`.** `admit.go:294-357` validates that a divergent cell is well-formed, in range,
  and not a money column; it never asks whether that cell is actually *compared*.
  `CounterfactualCoverage` (`grade.go:305-311`) reads `graded_against` only. The T20/D-4 rule went to
  real trouble to stop *a money kill wearing a structural coat*; the mirror image — **a structural
  kill whose every cell has been withdrawn from grading** — is unguarded.

**Is it exploited today? No.** The only `unrecorded_fields` in the committed store are
`installment_number` + `interest_minor` on the single `DISBURSEMENT` row of each of the 11 vectors —
22 cells, exactly as claimed, and genuinely unrecorded (§5.3). So this is a **latent hole, not an
active misstatement**, which is why it is P1 and not P0. It becomes P0 the first time a promotion
uses it.

**F-1c (P2), and it is already live.** `installment_number` on every `DISBURSEMENT` row is declared
unrecorded **and carries the value `0`**. That is benign (DEC-1 normalises the oracle's `null` to 0
and the Go type is `int32`, for which 0 is also the zero value), but it means the store already
contains a populated-yet-unrecorded non-money cell, and `P-03`'s own transcription note claims
filling such a cell "would be storing a derivation as an observation, the exact defect
`unrecorded_fields` exists to prevent" — while the field is, textually, filled. The disclosure is
unenforceable as written.

### 4.2 Two more things the harness cannot see — **F-3, P2**

- **A fabricated `margin_minor` is admitted.** I changed `P-01`'s
  `STRAIGHT-LINE-PRINCIPAL-DIVISION` margin from `65885070` to `999999999`: exit 0, no complaint.
  Margins and `evidence` prose are **unverified assertions**. This is unavoidable in code (the
  harness has no schedule generator by design — `admit.go:837-845`), but it means the *only* defence
  against a wrong margin is a human re-derivation, which is what §2.4 is.
- **A byte-identical clone is admitted and inflates every count.** I copied `P-MNT-50M` to
  `P-CLONE.json`, changing only `case_id`: `parity vectors PASS 11 → 12` and
  `counterfactuals named 24 → 26`. There is **no duplicate-shape detection**.

### 4.3 What `--prove` does *not* prove — **F-5, P2**

All fifteen proofs perturb exactly one file: `_selftest/SELFTEST-01-two-period-zero-rate.json`.
[VERIFIED: `conformance.sh:300-455`; every `perl -0pi` target is that path.] **No proof perturbs a
parity vector, and no proof perturbs a date cell.** Proofs 1, 2, 3, 6, 7, 8, 8b are not perturbations
at all; 4/5 are money; 9 is a float token; 10–14 are schema/metadata rules.

So before this review, the claim "the harness catches a wrong due date" rested on reading
`diffSchedule` rather than on any executed proof. It is **true** — M4 above establishes it — but
`--prove` did not establish it, and `--prove` is what a later agent will run instead of reasoning.
The number 15/15 is honest about what it tests and silent about what it does not.

---

## 5. (c) Structural checks

### 5.1 No floats — **PASS**

- **Vector JSON:** 18 files scanned; string literals stripped first; **zero** bare JSON number tokens
  containing `.`, `e` or `E`. [VERIFIED: my own scanner, independent of `guard_no_float_in_vectors`.]
- **Go tree:** the only occurrences of `float32`/`float64`/`big.Float` in
  `nexus/internal/apps/loanschedule/` are inside **doc comments that forbid them**
  (`contract.go:121, 738, 1898-1899, 2212`; `conformance_test.go:761`). Zero in the token stream.
  [VERIFIED: `grep -rnE '\bfloat(32|64)\b|big\.Float|ParseFloat|FormatFloat|%f|%g|%e' --include='*.go' nexus/`
  returns only those five comment lines.]
- Money is carried as **integer strings in minor units** with a `*_major_text` wire-text cross-check;
  the transcription check (M1) is what makes that pairing load-bearing rather than decorative.

### 5.2 Coverage — the real number is **9 distinct shapes, not 11** — **F-6, P2**

The promoting worker's disclosure is **correct, and I verified it rather than accepting it**. Hashing
`request` and `expect` separately over all eleven vectors:

```
P-00    req 90f615291689   exp e40120239185
P-04f   req 90f615291689   exp e40120239185
P-04t   req 90f615291689   exp e40120239185     ← all three byte-identical in BOTH
DISTINCT (request, expect) SHAPES: 9
```

[VERIFIED: SHA-256 over canonicalised JSON; the other eight vectors are pairwise distinct.]

The cause is structural and not the promoter's fault: the frozen contract has **no
`allowFullTermForTranche` field**, so the flag that `P-04f`/`P-04t` exist to vary is not expressible
in a request, and the two vectors are `P-00` under different names. But the consequences are real and
currently unreported:

- `parity vectors PASS 11` overstates independent coverage by **2**.
- `counterfactuals named 24 (21 money, 3 structural)` counts `LEVEL-INSTALLMENT-…` and
  `STRAIGHT-LINE-…` **ten times each** — visible in the report's own capability line, which prints
  `STRAIGHT-LINE-PRINCIPAL-DIVISION` ten times in a row. A reader sees breadth where there is
  repetition.
- The store has no de-duplication check, so nothing prevents this growing (§4.2).

**The honest headline is: 9 distinct oracle observations, 21 money-kill claims of which 2 distinct
ids, 3 structural kills of which 2 distinct ids, across 2 graded capabilities.**

Against the approved capture matrix, `capabilities.json` marks exactly **two** capabilities
`in_graded_domain: true` — `schedule.core` and `monthend.reanchor` — and both are covered by a named
counterfactual, so the harness's own coverage gate passes legitimately. Every other capability is
`false` with a cited reason, and the four `REFUSE-*` vectors are the contract-derived refusals. That
part of the matrix is sound.

### 5.3 The 22 `unrecorded_fields` cells are genuine — **PASS**

Claim: `LoanSchedulePlanDisbursementPeriod` has four fields, `periodNumber()` returns null, there is
no interest accessor. Checked at source
(`fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/data/`):

```java
// LoanSchedulePlanDisbursementPeriod.java:25-36
@Data
public final class LoanSchedulePlanDisbursementPeriod implements LoanSchedulePlanPeriod {
    private final LocalDate  periodFromDate;          // :28
    private final LocalDate  periodDueDate;           // :29
    private final BigDecimal principalAmount;         // :30
    private final BigDecimal outstandingLoanBalance;  // :31
    @Override public Integer periodNumber() { return null; }  // :34-36
```

[VERIFIED: full file read, 47 lines; the interface `LoanSchedulePlanPeriod.java:23-29` declares only
`periodNumber`, `periodFromDate`, `periodDueDate`.] **Four fields, `periodNumber()` returns `null`,
no interest accessor of any kind.** And the capture emits every field the type carries:
`Capture3b.java:458-462` writes `periodFromDate`, `dueDate`, `principal`, `balance` for a
`DISBURSEMENT` row and nothing else. **So the two cells were genuinely not observed.**

Exactly 22 such cells exist, on the 11 `DISBURSEMENT` rows, and nowhere else.
[VERIFIED: audit of every `unrecorded_fields` array in the store; the harness independently reports
`22 ungraded`.]

Two small corrections to `P-03`'s transcription note (**P2, documentation only**):
(i) it calls the type a "record"; it is a Lombok `@Data final class`, not a Java `record`.
(ii) it cites `LoanSchedulePlanDisbursementPeriod.java:25-35`; the fields and the `periodNumber()`
override span `:25-36`.
Also worth recording for T10: `LoanSchedulePlan.java:53-56` constructs the disbursement row with
`outstandingLoanBalance := principalDisbursed`, so on a `DISBURSEMENT` row
`outstanding_principal_minor` is a **duplicate of `principal_minor` by construction** and grades
nothing independent.

### 5.4 Provenance and pins — **PASS with one caveat**

- `provenance.capture_sha256` **is** verified against the referenced file when present
  (`admit.go:517-527`), and the referenced capture hashes correctly:
  `.softhouse/capture/out/capture-prod3b-raw.json` →
  `8d23c48fa13c04677b51bacdf07d101d6a061c79815d76b4983eccdbac945c79`, matching every vector.
  [VERIFIED: independent `sha256`.]
- **Caveat (P2):** the digest is **optional** (`CaptureSHA256 != ""` gate), and — more importantly —
  it binds the *capture file*, not the *transcription*. Nothing in the harness checks that a vector's
  expected cells actually appear in the capture it cites. A self-consistent mis-transcription (minor
  and `*_major_text` both wrong in the same way) is invisible to the rig. §1.2 and §2 are the only
  defence, which is why an independent re-derivation is a required part of promotion and not a nicety.
- `PIN.json` pins commit, DEC-1 revision 12, contract SHA-256 and `production_rounding`
  `(19, 19, HALF_UP)`; every vector's `dec1_revision`, `fineract_commit` and both MathContexts are
  checked against it and all eleven agree.

### 5.5 Toolchain state — **as expected**

`go vet ./...` clean; `go test ./...` → `ok …/conformance 0.913s`;
`gofmt -l internal/apps/loanschedule/` → **exactly `contract/contract.go`**, which is the documented
G-3 state. I ran no `gofmt -w` anywhere. `impl_hook.go` registers nothing, which is correct for this
worktree (T10 is elsewhere).

---

## 6. Findings

| id | severity | finding |
|---|---|---|
| **F-1** | **P1** | `unrecorded_fields` is an unguarded escape hatch for non-money cells. (a) `admit.go:669-680` enforces "unrecorded ⇒ empty" only for the three money columns, so `kind`/`installment_number`/`from_date`/`due_date` may be populated **and** ungraded. (b) Nothing cross-checks `graded_against[].divergent_cells` against `unrecorded_fields`, so a structural kill can name cells the vector has withdrawn from grading and still count toward `CounterfactualCoverage`. **Demonstrated:** all nine cells of `MONTHEND-CONTINUE-FROM-CLAMPED-DAY` withdrawn in both `P-02` and `P-02b`, garbage dates left in place → 11/11 PASS, `monthend.reanchor` still reported killed, **exit 0**. Not exploited by the committed store today. |
| **F-2** | **P1** | The EMI re-adjust smoothing loop (`ProgressiveEMICalculator.java:1258-1309`, guard `EmiAdjustment.java:31-44`) — which DEC-1 `contract.go:1627-1661` calls a normative conformance obligation that "moves money on ordinary loans" — is tripped by **none** of the 11 promoted vectors (closest: `P-MNT-4M999`, \|Δ\| 8 vs threshold 9). A port that omits it entirely passes 11/11; my no-loop re-derivation reproduces every cell, which is the proof. DEC-1 names two shapes that do trip it (`MNT 1,014,632/6×7.0%`, `MNT 127,704/36×16.8%`); neither is captured or promoted. |
| **F-3** | **P2** | `margin_minor` and `evidence` are unverifiable by construction and unverified in fact — a fabricated margin (`65885070`→`999999999`) is admitted silently. There is also no duplicate-shape detection: a byte-identical clone raises `parity PASS` 11→12 and `counterfactuals named` 24→26. |
| **F-4** | **P2** | `Rounding.RateFactorScale` — DEC-1's scale-vs-precision rule (`contract.go:609-623`, `:822-832`) — is confirmed correct against `ProgressiveEMICalculator.java:1959-1962`, but **no vector grades it**: all 11 are byte-identical under both senses at `(19, HALF_UP)`. DEC-1's "misprices an ordinary loan" is not witnessed by anything in the corpus at production precision. |
| **F-5** | **P2** | `--prove`'s 15 cases all perturb the one hand-authored self-test fixture. No proof perturbs a **parity** vector and no proof perturbs a **date** cell. The date capability is real (M4 proves it) but `--prove` does not demonstrate it, and `--prove` is what a later agent will run instead of reasoning. |
| **F-6** | **P2** | Coverage is **9 distinct shapes, not 11**: `P-00`, `P-04f`, `P-04t` are byte-identical in request *and* expect (SHA-256 verified). Reports say `parity vectors PASS 11` and count `STRAIGHT-LINE-PRINCIPAL-DIVISION` / `LEVEL-INSTALLMENT-…` ten times each. Root cause is structural (the contract has no `allowFullTermForTranche` field), so the fix is disclosure, not deletion. |
| **F-7** | **P2** | `provenance.capture_sha256` is optional, and binds the capture *file* rather than the *transcription*: a self-consistent mis-transcription is invisible to the harness. Independent human re-derivation is therefore a required promotion step, not an optional one. |
| **F-8** | **P2** | Documentation precision in `P-03`'s transcription note: `LoanSchedulePlanDisbursementPeriod` is a Lombok `@Data final class`, not a Java `record`, and its cited span `:25-35` should be `:25-36`. Also: `LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT` describes the *effect* correctly but the *mechanism* wrongly — the oracle adjusts the last unpaid period's **EMI** (`:1176-1210`), and derives principal as `EMI − interest` always (`RepaymentPeriod.java:345-350`). |
| **F-9** | **P2** | Process: the reviewer worktree was cut from `2ec5976`, which predates the T8 merge, so the artefact under review was **absent** from the tree handed to the reviewer. A review brief must name the branch, or the worktree must be cut from the commit containing the artefact. |

### Not findings — things I checked and found sound

- All 11 vectors reproduce **cell for cell** from a source-shaped re-implementation that shares no
  formula with DEC-1's prose. 1,046 graded cells, zero disagreements.
- Both re-derived margins (`P-01` 65,885,070 and `P-03` 334) are **correct**.
- `P-03`'s row ordering, its `n = 5`, and its all-zero leading period are all **confirmed from
  source**, at three separate call sites.
- `P-02`/`P-02b`'s due dates are exactly what `DefaultScheduledDateGenerator.java:168-176` produces,
  and their zero money margin is arithmetically necessary under 30/360.
- The 22 `unrecorded_fields` cells are **genuinely unrecorded**, confirmed from the oracle's own type.
- The harness goes **red** on a rounding step, a period split and a **date cell**, and **exit 2** on
  an unreachable oracle and on a transcription inconsistency. It never produced a false PASS in any
  experiment I ran.
- No floats anywhere. PostgreSQL-only, no prohibited driver or dialect, no US payment rails,
  no deposit-taking surface. Money is integer minor units throughout.
- **DEC-1 revision 12 disagreed with the Fineract source in none of the six places I probed.** I was
  asked to find another G-4 and I did not. Where DEC-1 and the folklore differ (the closed-form EMI,
  "final principal := remaining balance"), **DEC-1 is the one that matches the source.**

---

## 7. Required changes

**None of these may be made by amending DEC-1 — its month-end, membership, `n` and `RateFactorScale`
rules were all confirmed correct. The changes are to the harness, the store and the disclosure.**

1. **[P1, F-1a]** Extend `admit.go`'s "marked unrecorded but carries a value" rule to `kind`,
   `installment_number`, `from_date` and `due_date`. `installment_number` needs a representation that
   distinguishes absent from zero (a `*int32` or a sentinel), or it must be removed from
   `gradedPeriodField`'s unrecordable set and handled by the existing normalisation rule instead.
2. **[P1, F-1b]** Make it inadmissible for a `graded_against[].divergent_cells` entry to name a cell
   that the vector's own `unrecorded_fields` withdraws from grading, and make
   `CounterfactualCoverage` require that at least one divergent cell of each structural kill is
   actually compared. Add a `--prove` case for it, in both directions.
3. **[P1, F-2]** Capture and promote the two shapes DEC-1 already names at `contract.go:1655-1658`
   (`MNT 1,014,632 / 6 × 7.0 %` and `MNT 127,704 / 36 × 16.8 %`), so the EMI smoothing loop is graded
   before any port is called conformant. Until then, the report must state that the loop is
   **ungraded**, in the "WHAT THIS RUN DOES NOT GRADE" block where the rate-factor disclosure already
   lives.
4. **[P2, F-5]** Add `--prove` cases that perturb a **parity** vector and a **date** cell. My M2/M3/M4
   are directly reusable.
5. **[P2, F-6]** Report distinct `(request, expect)` shapes alongside the vector count, and refuse (or
   at minimum warn on) two parity vectors with identical request-and-expect hashes. State plainly in
   `README.md` and in the report that `P-00`/`P-04f`/`P-04t` are one observation stored three times,
   and de-duplicate the counterfactual-coverage line so ten copies of one kill id print once with a
   count.
6. **[P2, F-4]** Record `RateFactorScale` in the "recorded, never graded" disclosure block: it is
   normative in DEC-1 and unbacked by the corpus at `(19, HALF_UP)`.
7. **[P2, F-3/F-7]** Make `provenance.capture_sha256` **mandatory** for `class: parity`, and consider
   a promotion-time check that each expected cell's `*_major_text` occurs in the cited capture for
   that `capture_case_id`. That would close F-7 mechanically rather than by review.
8. **[P2, F-8]** Correct `P-03`'s transcription note (`record` → Lombok `@Data final class`; `:25-35`
   → `:25-36`) and the `LEVEL-INSTALLMENT-…` description (the oracle adjusts the last unpaid period's
   **EMI**; principal is always `EMI − interest`).
9. **[P2, F-9]** Fix the reviewer-worktree provenance so the next reviewer is not handed an empty
   corpus.

Nothing here is a `user` gate. No DEC-1 amendment is proposed, no cutover is implied, and no vector
needs to be withdrawn.

---

## 8. Verdict

# ACCEPTED WITH REQUIRED CHANGES

**The eleven parity vectors are accepted.** Every one reproduces cell for cell from a
source-faithful re-implementation of the Fineract algorithm — a different formula shape from the one
three earlier parties used — and the two `graded_against` margins I re-derived independently are
correct to the minor unit. The 22 `unrecorded_fields` cells are genuinely unrecorded, confirmed from
the oracle's own type declaration. No float appears anywhere. The corpus is honest about what it
observed.

**The harness is accepted as a grader and is proven to fail.** It goes red on a rounding step, on a
period split, and — the one the brief was rightly worried about — on a **date** cell, so
`monthend.reanchor`'s zero-money-margin backing is real and not decorative. It returns exit 2, never
a false PASS, on an unreachable oracle, an empty store, a transcription inconsistency and a missing
port.

**Two P1 changes are required before this store may be used to certify a port.** First, a vector can
withdraw its own date cells from grading while still claiming the capability they back — I
demonstrated a store in which every month-end date is garbage, the report still says
`monthend.reanchor killed by MONTHEND-CONTINUE-FROM-CLAMPED-DAY`, and the run exits 0. Second, the
EMI re-adjust smoothing loop, which DEC-1 itself calls a conformance obligation that moves money on
ordinary loans, is tripped by none of the eleven vectors, so a port that omits it passes 11 of 11 —
and DEC-1 already tells us which two shapes would catch it.

**A conformance PASS on this store today would mean: "matches the oracle on 9 distinct observations,
across 2 capabilities, with the EMI smoothing loop and the rate-factor scale rule ungraded."** It
would not mean the port is correct, and it comes nowhere near meaning safe to cut over — which
remains a `user` gate regardless.

---

### Appendix — reproducing this review

Scratch artefacts (never the committed store): `/tmp/t9/{pristine,m1,m2,m3,m4,h1,h2,h3}`.
Reproduce with `.softhouse/conformance.sh --prove`, then the six mutations in §4 and the two
derivations in §1.2 / §3.1. Fineract citations are all from
`/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`, verified clean at the start and
untouched by this review.
