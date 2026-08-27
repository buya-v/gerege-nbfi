# T34 — independent re-review of DEC-1 revision 6

# ACCEPTED WITH REQUIRED CHANGES

**One P0 and two P1s.** The P0 is a **new** money defect on a surface no previous
review examined: DEC-1 revision 6 states the `rateFactorTillPeriodDueDate`
multiplier as `RepaymentEvery`, and the pinned oracle passes `periodRatio`
instead on exactly that one entry point. The committed corpus is **entirely
blind** to the difference — 0 of 12 Path-A captures and 0 of the 13 observations
can separate the two readings — and where they separate they separate on
**100 % of the shapes swept**, up to **MNT 398,967.73** in total interest.

| | |
|---|---|
| Reviewer | task T34, independent; did not plan or write revision 6 |
| Subject | `docs/adr/DEC-1-schedule-generator-adapter.md` revision 6 and `nexus/internal/apps/loanschedule/contract/contract.go`, at merge `3a30154` |
| Pinned oracle | `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` — **verified** with `git -C /Users/buv/fineract log -1 --format=%H` before any citation, and treated read-only |
| Method | revision 6 transcribed **from its text alone** into a runnable exact-decimal / integer-minor-unit model (`.softhouse/reviews/t34-probe/t34_model.py`), validated against the committed corpus, then attacked |
| Oracle contact | **NONE.** No observation was taken, synthesised or implied by this task. Every number below is a **re-derivation** from the pinned checkout or a **transcription** of an already-committed capture. |

**Reproduction result before the attack.** The from-text model reproduces
**13 of 13** committed observations digit-for-digit
(`t34-validate-output.txt`) and, on a stricter check nobody has run before,
reproduces **11 of the 12 committed Path-A captures row by row** — due date,
principal, interest **and outstanding balance** on every repayment row, plus the
loan term in days (`t34-capture-check-output.txt`). The twelfth, `P-03`, fails on
one field of one row; that failure is P1-T34-1 below.

---

## 0. Summary of findings

| id | severity | where | what |
|---|---|---|---|
| **P0-T34-1** | P0 | `DEC-1 §4.1.1`, `§4.3.2`, `§9`; `contract.go:522-546` | The rate-factor multiplier on the `rateFactorTillPeriodDueDate` call site is `periodRatio` [`ProgressiveEMICalculator.java:1404-1413`], **not** `RepaymentEvery`. Both artefacts state `RepaymentEvery`. Diverges in money on 480 of 480 swept in-graded-domain shapes; worst total-interest gap MNT 398,967.73. **Corpus-blind.** |
| **P1-T34-1** | P1 | `DEC-1 §4.3.2` step 4; `contract.go:1533-1537` | The roll-forward rule and the segmentation table contradict each other on `OutstandingPrincipalMinor` for the repayment period whose `DueDate` equals the disbursement date. The literal step-4 reading returns the **whole principal** where committed capture `P-03` records `0.00`. Corpus-visible, hence P1 not P0. |
| **P1-T34-2** | P1 | `DEC-1 §4.5`; `contract.go:1105-1113` | Revision 6's new claim that the disbursement row's `OutstandingPrincipalMinor` "**is** graded" is false. All three Path-A harnesses emit only `type`/`dueDate`/`principal` for a `DISBURSEMENT` row, so no committed Path-A capture records that field. The *source* claim is correct; the *coverage* claim is not. |
| **P2-T34-1** | P2 | `DEC-1 §4.3.1` Provenance | The "13 of 13" standard compares three scalars per shape and never compares a due date or `OutstandingPrincipalMinor`. It is weaker than the paragraph implies, and it is why P1-T34-1 survived T33's own from-text check. |

None of the four requires a **contract-shape** change: no type, field, enum member
or vector field set moves, and §3.1's graded domain need not narrow. All four are
corrections to normative prose and to one coverage claim, i.e. agent-decidable
work on an unratified draft.

---

## 1. P0-T34-1 — the rate factor's multiplier is `periodRatio`, not `RepaymentEvery`

### 1.1 What both artefacts say

DEC-1 §4.1 reproduces the oracle's rate-factor body and both artefacts repeat it:

```java
final BigDecimal interestFractionPerPeriod = repaymentPeriodMultiplierInDays
        .multiply(repaymentEvery, mc)
        .divide(daysInYear, mc);
return interestRate
        .multiply(interestFractionPerPeriod, mc)
        .multiply(actualDaysInPeriod, mc)
        .divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode());
```

§4.1.1, added by revision 6, then says (DEC-1 line 194):

> Both entry points reach that one routine on the graded domain's fixed-30/360
> monthly arm — `:1355-1356` → `:1403-1412` → `rateFactorByRepaymentEveryMonth`
> `:1923-1927` → `rateFactorByRepaymentPeriod` `:1950-1966`, and `:1486-1487` →
> `:1536` → the same two.

and its table names the **only** stated difference between the two call sites as
the *span*:

> | quantity | span passed | ratio | used by |
> | `rateFactor` | the interest period's own `[FromDate, DueDate]` … |
> | `rateFactorTillPeriodDueDate` | `[interest period FromDate, repayment period DueDate]` … |

§4.3.2 then writes the whole thing out **normatively** for the
`rateFactorTillPeriodDueDate` call site (DEC-1 lines 486-490, and
`contract.go:1455-1459` verbatim):

```
rateFactorTillPeriodDueDate = setScale( (rate × 30 × RepaymentEvery ÷ 360)
                                        × actualDaysInPeriod ÷ calculatedDaysInPeriod,
                                        RateFactorScale )                              # :1961-1962
```

An implementer reading only DEC-1 writes `RepaymentEvery`. Nothing in either
artefact licenses anything else.

### 1.2 What the pinned checkout does

**[VERIFIED: `ProgressiveEMICalculator.java:1400-1413`]** — opened in this
checkout, the `rateFactorTillPeriodDueDate` entry point
`calculateRateFactorPerPeriodForInterest`:

```java
1403        } else if (daysInMonthType.isDaysInMonth_30()) {
1404            BigDecimal periodRatio = switch (repaymentFrequency) {
1405                case YEARS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, ChronoUnit.YEARS, mc);
1406                case MONTHS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, ChronoUnit.MONTHS, mc);
1407                case WEEKS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, ChronoUnit.WEEKS, mc);
1408                case DAYS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, ChronoUnit.DAYS, mc);
1409                default -> throw new UnsupportedOperationException("Unsupported repayment frequency: " + repaymentFrequency);
1410            };
1411
1412            return calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency, periodRatio,
1413                    BigDecimal.valueOf(30), daysInYear, actualDaysInPeriod, calculatedDaysInPeriod, mc);
```

The recurrence's entry point `calculateRateFactorPerPeriod`
**[VERIFIED: `:1536-1537`]** passes something different:

```java
1536            case DAYS_30 -> calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency, repaymentEvery,
1537                    daysInMonth, daysInYear, actualDaysInPeriod, calculatedDaysInRepaymentPeriod, mc);
```

The third argument is the one that lands in `rateFactorByRepaymentPeriod`'s
`repaymentEvery` slot **[VERIFIED: `:1598-1601` signature, `:1607-1608` MONTHS
dispatch, `:1922-1926` `rateFactorByRepaymentEveryMonth`, `:1950-1957`]** and is
consumed at `:1957` as `.multiply(repaymentEvery, mc)`. So on the graded
domain's fixed-30/360 monthly arm:

| | interest fraction actually computed |
|---|---|
| `rateFactor` (the recurrence) | `30 × repaymentEvery ÷ 360` |
| `rateFactorTillPeriodDueDate` (the interest) | `30 × periodRatio ÷ 360` |

`periodRatio` is `calculatePeriodRatio(scheduleModel, repaymentPeriod,
ChronoUnit.MONTHS, mc)` **[VERIFIED: `:1419-1458`]**, seeded by
`calculateSeedDate` **[VERIFIED: `:1460-1479`]**, which starts from
`scheduleModel.getStartDate()` — the **first repayment period's `FromDate`**,
i.e. `GenerateRequest.ScheduleStartDate`
**[VERIFIED: `ProgressiveLoanInterestScheduleModel.java:209-211`]** — and falls
back to the repayment period's own `FromDate` when
`ScheduleStartDate + k months ≠ the period's DueDate`.

It returns exactly `repaymentEvery` **only** while every repayment period's
window is `seed + k months`. It returns a **fraction plus an integer**
[`:1450-1453`] the moment a period boundary drifts off that lattice.

**The word `periodRatio`, the routine `calculatePeriodRatio`, and the line range
`:1404-1413` appear NOWHERE in DEC-1, nowhere in `contract.go`, and nowhere in
any probe of T23, T26, T29, T31, T32 or T33.** §4.1.1's citation
`:1403-1412` walks through the block that computes it and describes it as
reaching "the same two" routines.

### 1.3 Where the boundaries drift — and they drift inside the graded domain

They drift precisely where §4.2's **month-end re-anchor** fires, because the
re-anchor is seeded on the **disbursement date**
**[VERIFIED: `LoanApplicationTerms.java:585-589`, passed to
`DefaultScheduledDateGenerator.java:130-131`, rule at `:168-176`]** while
`calculateSeedDate` reads the **schedule start date**. When those differ, the
generated due dates are no longer `ScheduleStartDate + k months`.

Worked, by hand and then by the probe — schedule start `2024-01-28`,
disbursement `2024-01-29`:

- period 1 steps to `2024-02-28`; re-anchor fires (seed day 29 > 28, stepped day
  28 ≥ 28) → `min(29, 29) = 29` → period 1 = `[2024-01-28, 2024-02-29]`;
- `calculateSeedDate`: `2024-01-28 + 2 months = 2024-03-28 ≠ 2024-02-29`, so the
  seed falls back to `2024-01-28`;
- `calculatePeriodRatio`: `2024-01-28 + 2 months = 2024-03-28` overshoots the due
  date, so the fractional branch [`:1447-1453`] returns
  `days(02-28 → 02-29) ÷ days(02-28 → 03-28) + 1 = 1 ÷ 29 + 1 =
  1.03448275862068965517`.

Period 1's interest is therefore computed at **3.448 % more** than DEC-1's text
says. Re-derived per-period, that is exactly the ratio my probe prints
(`t34-sweep-output.txt`, section 3: period-1 interest `19,575.00` under DEC-1 as
written against `20,250.00` under the pinned source — `20250 ÷ 19575 = 1.03448…`).

### 1.4 How wide, and how much money — all re-derivations

`.softhouse/reviews/t34-probe/t34_scan_broad.py`, over every
`(ScheduleStartDate, Disbursement.Date)` pair in the same month, all twelve
months, leap and common year:

| year | admissible same-month pairs | pairs with a non-unit `periodRatio` | by `ScheduleStartDate` day |
|---|---|---|---|
| 2024 | 5,767 | **55 (0.95 %)** | day 28: 30, day 29: 18, day 30: 7 |
| 2025 | 5,738 | **54 (0.94 %)** | day 28: 29, day 29: 18, day 30: 7 |

`.softhouse/reviews/t34-probe/t34_sweep.py`, over the January-2024 subset of
those date shapes × 4 terms × 4 rates × 5 principals:

- **480 of 480 (100 %)** return different money — different per-period
  principal, interest, outstanding balance and installment, and different totals;
- worst total-interest gap: **MNT 398,967.73**
  (schedule start `2024-01-28`, disbursement `2024-01-31`, MNT 50,000,000,
  36 × 21.6 %: `18,260,183.72` as DEC-1 is written, `18,659,151.45` from the
  pinned source);
- smallest observed gap is one minor unit on a 100.00 principal, so there is no
  size threshold below which the reading is safe.

**Concrete config for the required vector** (a *re-derived candidate shape to
capture*, **not** an observation):

> MNT 1,200,000, 6 monthly installments, 21.6 % p.a., `ScheduleStartDate`
> 2024-01-28, single disbursement 2024-01-31, MNT 2 decimals, (19, HALF_UP),
> 30/360, no down payment, no installment rounding.
>
> DEC-1 as written: total interest **74,607.33**.
> Pinned source: total interest **76,984.00**. Gap **MNT 2,376.67**.
> Full row table in `t34-sweep-output.txt` section 3.

Every one of those figures is a **re-derivation**. None may be promoted to the
vector store.

### 1.5 The corpus cannot see any of it

`.softhouse/reviews/t34-probe/t34_corpus_blind.py`: **0 of the 12** committed
Path-A captures, and **0 of the 13** observations DEC-1 §4.3.1's Provenance
paragraph relies on, contains a repayment period whose `periodRatio` differs
from `RepaymentEvery`. Every one of them has either
`ScheduleStartDate == Disbursement.Date` (so the re-anchor seed and the
`calculateSeedDate` seed coincide) or a schedule start on the 1st (so the
re-anchor never fires at all). `P-02` (31st) and `P-02b` (30th) — the two
captures DEC-1 §5 credits with grading the month-end rule — are exactly the
aligned case.

This is the fifth consecutive round in which a reading reproduces the whole
corpus and is still wrong.

### 1.6 Required change

1. **§4.1.1** — add the multiplier to the two-call-sites table, as a column
   beside the span. State normatively that `rateFactorTillPeriodDueDate` uses
   `periodRatio` [`ProgressiveEMICalculator.java:1404-1413`] and `rateFactor`
   uses `RepaymentEvery` [`:1536-1537`], and that both land in
   `rateFactorByRepaymentPeriod`'s `repaymentEvery` parameter at `:1951`,
   consumed at `:1957`.
2. **§4.1.1** — define `periodRatio` normatively, with `file:line`, to the same
   standard §4.1.1 already applies to the two day counts: the seed
   [`:1460-1479`], including the `scheduleModel.getStartDate()` origin
   [`ProgressiveLoanInterestScheduleModel.java:209-211`] and the fall-back to the
   period's own `FromDate`; the `MONTHS` last-day-of-month adjustment
   [`:1421-1436`]; the walk and the fractional branch [`:1442-1457`], whose
   division is the only `MathContext`-rounded step and whose `.add` is exact.
   State that it equals `RepaymentEvery` **if and only if** every repayment
   period's window is `ScheduleStartDate + k × RepaymentEvery` months, and that
   the month-end re-anchor breaks that whenever the disbursement seed and the
   schedule start disagree near month end.
3. **§4.3.2** — correct the written-out formula: `RepaymentEvery` → `periodRatio`.
4. **§9** — extend "The rate-factor day-count obligation" so it cannot be met
   partially: the two entry points differ in **span and multiplier**, and a port
   that uses `RepaymentEvery` on the interest call site misprices every
   drifted-boundary loan. All of it exact; no float.
5. **`contract.go`** — the same corrections in the `Rounding.RateFactorScale`
   "two call sites" table (`contract.go:534-546`) and in the `Period`
   "per-period interest computation" formula (`contract.go:1455-1459`).
6. **§8** — a new capture item (**3e**) for a vector with `ScheduleStartDate` day
   in {28, 29, 30} and a disbursement later in the same month with day > 28, and
   the §8 item 3 binding widened from five vectors to six. The binding must keep
   gating **conformance PASS and cutover, not ratification**.

**Arm B (narrow the graded domain instead) is not recommended**, on revision 6's
own reasoning: refusing a loan whose schedule start and disbursement date differ
near month end refuses an ordinary retail shape and cannot be run against shadow
traffic. But if it is taken, §3.1 must gain a predicate, not a footnote.

---

## 2. P1-T34-1 — the roll-forward contradicts the segmentation table

DEC-1 §4.3.2 step 4 (and `contract.go:1533-1537`) is normative:

> `OutstandingPrincipalMinor = max(0, balance carried in + amounts disbursed in
> this period − PrincipalMinor)` [`RepaymentPeriod.java:389-403`, the
> `negativeToZero` at `:399`]

The same subsection's segmentation table, row 2, is also normative:

> disbursement on period *j*'s `DueDate` → **one** interest period, unchanged;
> the amount is recorded on it **and enters period *j+1*'s balance**

Both sentences apply to the same row and give different answers. Under §4.3.1's
membership rule the disbursement **is** in period *j* ([`FromDate`, `DueDate`]
inclusive for the first period, (`FromDate`, `DueDate`] later), so "amounts
disbursed in this period" is the whole principal and step 4 returns the whole
principal. Under the segmentation sentence the amount is in period *j+1* and
period *j*'s outstanding is zero.

**Committed capture `P-03` settles it, and the literal step-4 reading is wrong**
(`t34-rollforward-output.txt`; the expectation is transcribed from
`.softhouse/capture/out/capture-prod-raw.json`, not observed by this task):

| period | due | principal | interest | step 4 read literally | segmentation read literally | **capture P-03** |
|---|---|---|---|---|---|---|
| 1 | 2024-02-01 | 0.00 | 0.00 | **100.00** | 0.00 | **0.00** |
| 2 | 2024-03-01 | 19.77 | 0.58 | 80.23 | 80.23 | 80.23 |
| 3–6 | … | … | … | identical | identical | identical |

The mechanism, for the corrected text
**[VERIFIED: `ProgressiveLoanScheduleGenerator.java:116-132` and `:294-352`]**:
the generator sets the row's outstanding balance at `:132`, inside period *j*'s
loop iteration, whereas `emiCalculator.addDisbursement` at `:351` only runs when
the disbursement date falls in the **half-open** window
`[periodFromDate, periodDueDate)` [`:307-308`] — which for a due-date
disbursement is period *j+1*. Period *j*'s row is therefore emitted from a model
in which the disbursement has not yet been registered. The oracle's own
post-registration `RepaymentPeriod.getOutstandingLoanBalance()` for period *j*
**would** be the whole principal [`:389-403`, `lastInterestPeriod.getDisbursementAmount()`
at `:396`]; the schedule simply never reads it again.

**Severity P1, not P0**, and the reason matters: unlike P0-T34-1 the committed
corpus **does** discriminate this — `P-03` records the answer — so a port that
gets it wrong cannot pass conformance. It is nonetheless a normative rule that
returns the wrong number on an entire row of §4.3.1's own related-periods table
("on period *j*'s due date, *j* < N"), and the gap is the **whole principal**.

**Required change.** §4.3.2 step 4 must say that a disbursement dated on a
repayment period's `DueDate` does **not** contribute to that period's
`OutstandingPrincipalMinor` and does contribute to the next period's balance
carried in, with the `:132` / `:305-308` / `:351` sequencing as the cited reason.
`contract.go`'s `Period.OutstandingPrincipalMinor` doc carries the same rule and
needs the same sentence; its existing line "It is observably 0 on a repayment row
that falls entirely before the disbursement" is true but does not cover the
on-the-due-date row, which is not "entirely before".

---

## 3. P1-T34-2 — the disbursement row's outstanding balance is not graded

Revision 6 added, in §4.5 and in `contract.go:1105-1113`:

> **Disbursement row** — `OutstandingPrincipalMinor` is **the amount advanced**
> … [`LoanSchedulePlan.java:52-56`, record fields
> `LoanSchedulePlanDisbursementPeriod.java:28-31`]. **Every committed capture
> contains a disbursement row, so this is graded.**

The **source** half is exact
**[VERIFIED: `LoanSchedulePlan.java:52-56`** passes
`disbursementPeriod.getPrincipalDisbursed().getAmount()` as both the third and
fourth constructor argument; **`LoanSchedulePlanDisbursementPeriod.java:28-31`**
is `periodFromDate, periodDueDate, principalAmount, outstandingLoanBalance`**]**.

The **coverage** half is false. All three Path-A capture harnesses emit, for a
`DISBURSEMENT` row, only `type`, `dueDate` and `principal`:

- `.softhouse/capture/src/Capture.java:180-181`
- `.softhouse/capture/src/Capture2.java:231-232`
- `.softhouse/capture/src/Capture3.java:251-252`

— and each of them **does** emit `balance` on the `DOWN_PAYMENT` and `REPAYMENT`
branches immediately below, so the omission is specific. Inspecting the committed
`capture-prod-raw.json` confirms it: every `DISBURSEMENT` object has three keys.
Containing a disbursement *row* is not the same as recording that row's
*outstanding balance*.

The field is recorded only by the four Path-B server-path captures
(`principalLoanBalanceOutstanding` on the disbursement period of
`.softhouse/capture/pathb/out/B-01-baseline-raw.json` and siblings), which §5
itself states are "not yet admissible".

**Required change.** Mark the disbursement row's `OutstandingPrincipalMinor`
**UNGRADED by Path A** in both artefacts, name the Path-B captures as the only
present evidence, and add the missing column to §8 item 1's list of "three
per-period columns the harness does not yet emit" — it is a fourth. This is the
document's own discipline: a false coverage claim is exactly the "the vectors
cover it" illusion §3.1 exists to prevent.

---

## 4. P2-T34-1 — what "13 of 13" actually grades

§4.3.1's Provenance paragraph and revision 6's history entry both rest the
from-text experiment on "reproduces **13 of 13** already-committed observations
digit-for-digit". Reading `.softhouse/reviews/t33-probe/t33_spec_check.py`, the
comparison is a triple per shape — level installment, final installment, total
interest. It never compares a due date, a per-period split, or
`OutstandingPrincipalMinor`. That is why P1-T34-1 survived it: my own model
passes the same 13/13 triple check **and** fails `P-03`'s balance column.

**Recommended change (not blocking).** State in the Provenance paragraph which
fields the 13/13 grades, and raise the standard to the row-level check
(`t34_capture_check.py` does it in 60 lines against the committed capture file,
with no oracle).

---

## 5. What I checked and found clean — so silence is distinguishable from not looking

**T33's own claims, every cited line opened in the pinned checkout:**

| claim | verdict |
|---|---|
| `actualDaysInPeriod` = `getDifferenceInDays(interestPeriodFromDate, interestPeriodDueDate)` at `:1367-1368` | **exact** |
| the same at `:1500-1501` | **exact** |
| `calculatedDaysInPeriod` = `getDifferenceInDays(repaymentPeriod.getFromDate(), repaymentPeriod.getDueDate())` at `:1369-1370` | **exact** |
| the same, spelled `calculatedDaysInRepaymentPeriod`, at `:1502-1503` | **exact** |
| numerator/denominator roles `.multiply(actual, mc).divide(calculated, mc)` at `:1961-1962` | **exact** |
| exact-zero guard when `calculatedDaysInPeriod == 0` at `:1953-1955` | **exact** (`MathUtil.isZero` → `return BigDecimal.ZERO`) |
| two call sites with two different spans at `:638-643`, `:639-640`, `:641-642` | **exact** — and this is where the *multiplier* difference also lives (P0-T34-1) |
| the deleted "exactly 1 … which is every period in the graded domain" clause | **deletion complete.** The only surviving occurrences in `contract.go` are the revision-6 note recording the deletion (`:327-328`) and the corrected rule (`:317-322`, `:1460`). Nothing in either artefact depends on the deleted falsehood. |
| §8 item **3d** broken out of 3c; binding widened four → five vectors | **present**, and the binding still reads "This is a UAT/cutover precondition, **not a ratification precondition**". **The distinction survives.** |

**Regression checks against revision 5 (`cc3abb7`):**

- **§4.3.1's EMI re-adjust loop, steps 1–8: byte-identical.** SHA-256 of the
  fenced block is `2ccf0f040428570c…` in both revisions. T28's specification and
  T29's verification of it are undamaged.
- **§4.3.2's three-operation interest block: byte-identical.** SHA-256
  `f45eac5891685e4f…` in both. T31's arithmetic is unchanged.
- **T29's `n = |relatedRepaymentPeriods|`:** intact. The only two statements
  tying `n` to `NumberOfRepayments` are the correct biconditionals at DEC-1
  lines 332 and 340; the `EmiAdjustment.java:54-56` /
  `ProgressiveLoanInterestScheduleModel.java:195-197` citations stand.
- **Eight consequences of §4.3.1:** untouched by the revision-5 → 6 diff.

**Other source claims re-verified independently (not taken on any review's word):**

- growth factor `1 + Σ rateFactor`, every addition carrying **no** `MathContext`
  [`RepaymentPeriod.java:216-218`] — **exact**; my model implements the sum and
  reproduces the corpus.
- month-end rule: step at `DefaultScheduledDateGenerator.java:128-129`,
  re-anchor at `:168-176` called from `:130-131`, seed = the disbursement date
  [`LoanApplicationTerms.java:585-589`], `calculatedRepaymentsStartingFromDate`
  never set by the Builder path so `:119-123` is dead here — **all exact**. My
  from-text date generator reproduces `P-02` (seed 31) and `P-02b` (seed 30) row
  for row, including `2024-02-29, 03-31, 04-30, 05-31, 06-30, 07-31`.
- currency layer: `Money.java:40-53`, scale applied at `:52` from
  `getMc().getRoundingMode()`; `inMultiplesOf` gated on `getDecimalPlaces() == 0`
  at `:48-51` — **exact**, so `Currency.MinorUnitDigits == 2` really does switch
  that channel off.
- `MoneyHelper.PRECISION = 19` [`:35`], `getMathContext()` =
  `new MathContext(PRECISION, getRoundingMode())` [`:91-94`], uninitialised
  tenant throws `IllegalStateException` [`:74-82`] — **exact**.
- `Money.copy(double)` **replaces** the amount [`:220-222`];
  `Money.dividedBy(long)` [`:352-358`] divides at `getMc()`, which returns the
  instance's own threaded context when one was set [`:494-496`] — so DEC-1's
  "divides at the threaded `MathContext`" is **correct in effect**, not a defect;
  the tenant-global readers are the 2-argument overloads at `:103`, `:115`,
  `:160`, `:169`, `:377`, all off the graded path. `contract.go`'s list (which
  includes `:169`) is the more complete of the two.
- down-payment arm, end to end: percentage at
  `ProgressiveLoanScheduleGenerator.java:332-334`, multiple-rounding at
  `:335-338`, the row built with
  `outstandingBalance.plus(disbursedAmount).minus(downPaymentAmount)` at
  `:340-343`, the shared installment counter at `:123`, `:143`, `:341`, `:346`,
  and the net amount registered into the interest model at `:349-351` —
  **all exact**, and `LoanSchedulePlanDownPaymentPeriod.java:33` is indeed
  `outstandingLoanBalance`. The arm is refused (`DownPaymentPercentage` pinned to
  `Rate{0,1}`), so it carries no money risk today; I found no defect in it beyond
  P1-T34-2's neighbouring coverage claim.
- `FrequencyYears` on the fixed-30/360 arm throws
  `UnsupportedOperationException("Invalid repayment frequency")` at `:1609`, from
  **both** entry points — the `ForInterest` path handles `case YEARS` at `:1405`
  and then hits the same dispatch at `:1602-1610`. §4.10's conclusion stands.
- the two graded-domain blocks (DEC-1 §3.1 and `contract.go`) are
  **semantically identical**, differing only in "the last repayment period's
  DueDate" vs "the last repayment DueDate" and `≤` vs `<=`.
- the balance roll-forward's **zero clamp** [`RepaymentPeriod.java:399`,
  `InterestPeriod.java:173`, `:183`] is real and is correctly the reason
  `OutstandingPrincipalMinor` is carried rather than derived; the clamp never
  bites on any committed capture, and it does not bite on any shape my sweep
  produced.

**What I could not verify, stated plainly:**

- **No live oracle was contacted, and none was needed.** Every figure in
  sections 1 and 2 is a re-derivation from the pinned checkout or a
  transcription of a committed capture file. Nothing here may be promoted to the
  vector store.
- I did **not** independently re-derive T32's "2,913 of 2,913" or
  "MNT 1,816,050.11" figures for the strictly-inside-a-period case. My model
  reproduces the same qualitative behaviour (the ratio is `< 1` on the
  balance-carrying segment) but I did not reproduce those counts, and I do not
  assert them.
- I did **not** examine the `DayCountActualActual` / cross-year partial-period
  arm; it is refused, and T30/T29 covered it.
- I did **not** assess whether the Path-B captures are admissible; I only
  observed that they carry the disbursement row's outstanding balance and that
  §5 calls them not yet admissible.
- I did **not** run `go build` / `go test`; `contract.go` is types and doc
  comments and no code changed in this revision.

---

## 6. Verdict and disposition

**ACCEPTED WITH REQUIRED CHANGES.**

Revision 6's own corrections are **sound**: T33's §4.1.1 is accurate line for
line, the false ratio-is-1 clause is fully removed, the P1/P2 corrections check
out against source, §8 item 3d and the five-vector binding are in place with the
ratification distinction intact, and nothing T28, T29 or T31 fixed has been
damaged. Convergence is real.

It is not ratifiable yet, for one reason: **§4.1.1 and §4.3.2 specify the
`rateFactorTillPeriodDueDate` call site with the wrong multiplier**, and the
corpus cannot tell. That is the same failure mode as P0-T29-2 and P0-T32-1 — a
normative formula that is right on every captured shape and wrong off it — on a
surface the new §4.1.1 was written specifically to close. Fix P0-T34-1 and the
two P1s and revision 7 should, on this evidence, be ratifiable.

**Not a contract amendment.** All required edits are prose and one new backlog
capture item. No identifier, type, field set or graded-domain predicate changes,
so this is agent work on an unratified draft, not a `user` gate.

---

## 7. Artefacts

All under `.softhouse/reviews/t34-probe/`, committed on
`softhouse/T34-dec1-v6-rereview`:

| file | what |
|---|---|
| `t34_model.py` | DEC-1 revision 6 transcribed from its text alone; exact `Decimal` + integer minor units, no float anywhere |
| `t34_validate.py` / `t34-validate-output.txt` | the 13 committed observations — **13/13** |
| `t34_capture_check.py` / `t34-capture-check-output.txt` | row-by-row against all 12 committed Path-A captures — 11/12, `P-03` fails on one field (P1-T34-1) |
| `t34_periodratio.py` | `calculatePeriodRatio` + `calculateSeedDate` transcribed from the pinned source |
| `t34_sweep.py` / `t34-sweep-output.txt` | the money divergence: 480/480, worst gap MNT 398,967.73, worked row table |
| `t34_scan_broad.py` / `t34-scan-broad-output.txt` | how wide the drifted-boundary region is: 0.95 % of same-month date pairs, all with start day 28/29/30 |
| `t34_rollforward.py` / `t34-rollforward-output.txt` | the two roll-forward readings against capture `P-03` |
| `t34_corpus_blind.py` / `t34-corpus-blind-output.txt` | 0 of 12 captures and 0 of 13 observations can see the `periodRatio` question |
