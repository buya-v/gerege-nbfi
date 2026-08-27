# T38 — DEC-1 revision 6 → revision 7, and `contract.go` in step

**Branch:** `softhouse/T38-dec1-v7` (rebased onto `main` at `37e0731` after main advanced mid-task).
**Pinned oracle:** `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb` — verified with
`git -C /Users/buv/fineract log -1 --format=%H` before any citation, treated read-only, working tree clean.
**Oracle contact: NONE.** No observation was taken, synthesised or implied by this task. Every figure this
task produces is a **re-derivation**; every observation cited is **quoted from a capture already committed on
`main`, with its id**.

**Files written (scope respected, verified by `git diff --stat main`):**
`docs/adr/DEC-1-schedule-generator-adapter.md`, `nexus/internal/apps/loanschedule/contract/contract.go`,
`.softhouse/reviews/t38-probe/**`, `.softhouse/handoff/T38-dec1-v7.md`. **Nothing else.** No file under
`.softhouse/capture/`, `.softhouse/reviews/T3*-*.md`, `program.json`, `tasks.json`, `RESUME.md` or
`.softhouse/bin/` was touched.

**`contract.go` diff is COMMENT-ONLY.** Verified mechanically:
`git diff main -- …/contract.go | grep -v '^[+-]\s*//'` on the non-hunk-header lines is **empty**. No type,
field, enum member, sentinel or graded-domain predicate moves — which is what T34 predicted and what keeps
this agent work rather than a `user` gate.

---

## Corrections applied (one block per P0/P1/P2, with the source re-derivation)

### P0-T34-1 — the rate factor's multiplier is `periodRatio`, not `RepaymentEvery`

**Re-derived by me, from the pinned checkout, before reading past T34's headline.**

`calculateRateFactorPerPeriodForInterest` — the entry point that produces `rateFactorTillPeriodDueDate`, i.e.
every interest number in the response — computes on its `DAYS_30` arm
[VERIFIED: `ProgressiveEMICalculator.java:1403-1413`]:

```java
1404            BigDecimal periodRatio = switch (repaymentFrequency) {
1406                case MONTHS -> calculatePeriodRatio(scheduleModel, repaymentPeriod, ChronoUnit.MONTHS, mc);
1410            };
1412            return calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency, periodRatio,
1413                    BigDecimal.valueOf(30), daysInYear, actualDaysInPeriod, calculatedDaysInPeriod, mc);
```

The recurrence entry point `calculateRateFactorPerPeriod` passes different things
[VERIFIED: `:1533-1537`]:

```java
1536            case DAYS_30 -> calculateRateFactorPerPeriodBasedOnRepaymentFrequency(interestRate, repaymentFrequency, repaymentEvery,
1537                    daysInMonth, daysInYear, actualDaysInPeriod, calculatedDaysInRepaymentPeriod, mc);
```

Both third arguments land in `rateFactorByRepaymentPeriod`'s `repaymentEvery` parameter
[VERIFIED: `:1598-1601` signature → `:1607-1608` MONTHS dispatch → `:1922-1927` → `:1950-1951`] and are
consumed once, at `.multiply(repaymentEvery, mc)` [VERIFIED: `:1957`].

**Two arguments differ — and I say so, but I also say which one is live, because the brief asked me to state
both and my own reading narrows the second.** The fourth argument is the hard-coded `BigDecimal.valueOf(30)`
on the interest call site [VERIFIED: `:1413`] and the local `daysInMonth` on the recurrence call site
[VERIFIED: `:1537`], where `daysInMonth = daysInMonthType.isDaysInMonth_30() ? BigDecimal.valueOf(30) :
calculatedDaysInRepaymentPeriod` [VERIFIED: `:1508`]. **Under `DayCountFixed30Over360` both are exactly 30,
so that difference is numerically inert inside the graded domain**; it can only bite under
`DaysInMonthType.ACTUAL`, which §4.9 refuses and on which the interest entry point takes a different branch
entirely [VERIFIED: `:1400-1402`]. **The multiplier is the live difference.** Revision 7 states both and
labels which is which, rather than implying two live divergences.

**`calculatePeriodRatio` and `calculateSeedDate`, re-derived line by line**
[VERIFIED: `:1419-1459` and `:1461-1481`]. The two facts that decide everything:

- **`calculateSeedDate` seeds from `scheduleModel.getStartDate()`** [VERIFIED: `:1462`], which is
  `repaymentPeriods.getFirst().getFromDate()` [VERIFIED: `ProgressiveLoanInterestScheduleModel.java:209-211`]
  — i.e. the **SCHEDULE START DATE**. See *Anything I found that contradicts the review* below: the task
  brief states this the other way round.
- **The fall-back has TWO conjuncts**, not one [VERIFIED: `:1477-1480`]: the seed stays `ScheduleStartDate`
  only if the landing date equals the period's `DueDate` **AND** that landing date minus `RepaymentEvery`
  months equals the period's `FromDate`; otherwise it becomes the period's own `FromDate`. T34's prose gives
  only the first conjunct. Revision 7 states both.

The month-end special case at `:1430-1433` (target date is the last day of its month **and** the seed's day
is later → measure to `FromDate.plusDays(1)`), the walk at `:1441-1458`, and the fact that **the division at
`:1453` is the only `MathContext`-rounded step while the `.add` at `:1454` is exact**, are all transcribed
normatively into §4.1.1. `periodRatio` is computed **per repayment period** [VERIFIED: `:1404-1410` takes
`repaymentPeriod`], so every interest period in one repayment period shares it — a fact no prior artefact
states.

**Mechanism, re-derived:** §4.2's month-end re-anchor is seeded on the **disbursement date**
[VERIFIED: `LoanApplicationTerms.java:583-589` → `DefaultScheduledDateGenerator.java:130-131`, rule at
`:168-176`] while `calculateSeedDate` reads the **schedule start**. Two different seeds; when they disagree
near month end the generated boundaries leave the lattice `calculatePeriodRatio` measures against.

**Independent re-derivation of the numbers** (`.softhouse/reviews/t38-probe/`, written from the revision-7
text, not from T34's probe):

| claim | T34 | T38, independently | agree? |
|---|---|---|---|
| same-month `(start, disb)` pairs, 2024 | 5,767 | **5,767** | yes |
| of those, drifted | 55 (0.95 %) | **55 (0.95 %)** | yes |
| distribution by start day, 2024 | 28: 30, 29: 18, 30: 7 | **28: 30, 29: 18, 30: 7** | yes |
| 2025 | 54 of 5,738 (0.94 %) | **54 of 5,738 (0.94 %)** | yes |
| money sweep | 480 of 480 (100 %) | **480 of 480 (100 %)** | yes |
| worst total-interest gap | MNT 398,967.73 | **MNT 398,967.73** (18,659,151.45 vs 18,260,183.72) | yes |
| 3e candidate total interest | 76,984.00 vs 74,607.33 | **76,984.00 vs 74,607.33**, gap 2,376.67 | yes |
| period-1 `periodRatio` on start 01-28 / disb 01-31 | `1.03448275862068965517` | **same** | yes |

A re-derivation cross-checking a re-derivation. **Not an observation of either.**

**Corpus blindness, checked two ways and stronger than T34's.** Directly: across **all 35** committed
captures (12 Path-A pass 3, 12 pass 3b, 11 T37 binding) **not one repayment period has a non-unit
`periodRatio`** [`t38-corpus-blind-output.txt`]. Operationally: the two readings return identical money on
all **21** production-setting captures [`t38-discriminate-output.txt`].

**Where it landed.** §4.1.1 gains the span+multiplier table and a normative `periodRatio` subsection (seed,
offset, walk, rounding points, consequence, re-derived figures, corpus blindness); §4.3.2's written-out
formula is corrected; §4.9's cross-seam consistency result is **narrowed** (see the leak sweep below); §9
gains "The rate-factor MULTIPLIER obligation"; §8 gains item **3e** and the binding widens **five → six**,
with the "**conformance PASS and cutover, NOT ratification**" wording unchanged. `contract.go` carries the
same corrections on `Rounding.RateFactorScale` and on `Period`.

### P0-T37-1 — the pre-disbursement row's outstanding balance

**Re-derived by me** [VERIFIED: `ProgressiveLoanScheduleGenerator.java:116-145`, `:294-353`]:

- the plan row's balance is written at `:132`, **inside that period's own loop iteration**;
- `processDisbursements` is called at the **top** of each iteration [`:121-122`] and registers the
  disbursement into the interest model at `:351`;
- it fires only for the period satisfying `!disbursementDate.isBefore(periodFromDate) &&
  disbursementDate.isBefore(periodDueDate)` — **`[from, due)`, from-inclusive, DUE-EXCLUSIVE**
  [VERIFIED: `:307-308`, guard at `:309`].

So for a disbursement dated on period *j*'s `DueDate`, registration happens during period *j+1*'s iteration
and period *j*'s row is read from a model in which no disbursement exists — every balance in it zero. The
oracle's own post-registration `RepaymentPeriod.getOutstandingLoanBalance()` for period *j* **would** be the
whole principal [VERIFIED: `RepaymentPeriod.java:389-403`, `lastInterestPeriod.getDisbursementAmount()` at
`:396`]; the plan never reads it again.

**The three membership rules, all re-verified in the checkout and now stated together in §4.3.2:**

| id | rule | verified at |
|---|---|---|
| M1 | `[From, Due]` for the FIRST repayment period, `(From, Due]` for every later one | `LoanRepaymentScheduleProcessingWrapper.java:251-254`, reached from `ProgressiveLoanInterestScheduleModel.java:238-245` |
| M2 | `¬(p.DueDate < effectiveDueDate)` | `ProgressiveLoanInterestScheduleModel.java:195-197` |
| M3 | `[From, Due)` — from-inclusive, **due-exclusive** | `ProgressiveLoanScheduleGenerator.java:307-308` |

**M1 and M3 disagree on exactly one date.** I also proved a fact neither T34 nor T37 states and which makes
the rule writable without a new concept: **inside the graded domain M3's owner period IS the first RELATED
repayment period**, in all three rows of §4.3.1's table. So "rows before the first related period" and "rows
emitted before the disbursement is registered" are the same rows.

**§4.3.2 step 4 is split** into **(4a)** the carried-forward balance the next period computes on — the
existing formula, with "amounts disbursed in this period" now explicitly **M1**'s attribution, which is what
reconciles it with the segmentation table — and **(4b)** the **emitted** `OutstandingPrincipalMinor`, which
is **zero before M3's owner and (4a) from it onward**. §9 gains a matching obligation; `contract.go` carries
both on `Period.OutstandingPrincipalMinor` and in the step list.

**This is the correction that made my from-text model reproduce `P-03`, `T37-3c` and `T37-3c-2` end to end**
— it is not a wording fix.

### P1-T34-2 — the disbursement row's balance, coverage stated per harness

Read the committed artefacts rather than either party's summary
[`t38-disbrow-coverage-output.txt`]:

| harness | captures | DISBURSEMENT rows recording `balance` | keys emitted |
|---|---|---|---|
| Path A pass 3 (`Capture3.java`) | 12 | **0** | `type`, `dueDate`, `principal` |
| Path A pass 3b (`Capture3b.java`, landed by T35) | 12 | **12**, and `balance == principal` on all twelve | `type`, `periodFromDate`, `dueDate`, `principal`, `balance` |
| Path A T37 binding harness | 11 | **0** | `type`, `fromDate`, `dueDate`, `principal` |
| Path B `B-01`…`B-04` | 4 | **4**, as `principalLoanBalanceOutstanding` | — |

**So the claim was FALSE when written and is TRUE now for the pass-3b corpus only.** Both artefacts now say
exactly that, per harness, and neither writes "graded" unqualified. The honest summary I put in both:
**recorded by two harnesses, promoted by neither.**

### P2-T34-1 — "13 of 13" qualified, and the standard raised

§4.3.1's Provenance now states that the thirteen-observation check compares **three scalars per shape**
(level installment, final installment, total interest) and never a due date, a from date, a per-period split
or an outstanding balance — and that this is precisely why P0-T37-1 survived revision 6's own experiment.

Revision 7's own check is **full-row**: 21 committed captures at the production `MathContext`, compared cell
by cell on from date, due date, principal, interest, outstanding balance, row total, loan term and total
interest — **1,488 cells** [`t38-validate-output.txt`]. Both artefacts carry the qualified form.

---

## Evidence folded in from T35/T36/T37

1. **All five binding vectors captured and all five discriminate (T37).** §8 items 3, 3a, 3b, 3c, 3d each
   carry a **STATUS: CAPTURED, NOT YET PROMOTED** block naming the capture ids, the discriminating-cell
   counts and what the wrong reading returns. §4.3.1 and §4.3.2 restate "specified but ungraded" as a table
   of what is now observed and what is not. **T37's F-3 is honoured throughout:** the binding wants an
   *admissible vector*; an attested raw observation is not one until §8 item 1's promotion step, which T37
   recommends deferring past G-1. The phrase used in both artefacts is *"Captured is not promoted, and
   promoted is not cut over."*
2. **T37's F-2 honoured.** §4.3.2's re-derived 3d table is **not** overwritten with the observed figures. A
   new paragraph says an observation exists, cites `T37-3d` / `T37-3d-2` and the discrimination output, and
   states why the numbers are not copied: *the capture id is the citation, the capture file is the number.*
   `contract.go` carries the same paragraph.
3. **The EMI re-adjust loop is now normative AND witnessed (T36, T37).** §4.3.1 gains an observation block:
   the `Money.copy(double)` trap makes the `n = 12` threshold `Money(6.00)` so the loop needs
   `|residual| > 0.06`; six captures refute the no-loop model by one minor unit on every one of periods 1–11
   (MNT 1,200,001 → observed **112,082.46** against the no-loop model's 112,082.47); two more enter and back
   out at `hasLessEmiDifference`, pinning that guard. T37's `T37-3a` reproduces the adoption-test separation
   through Path A, and is measured to be a **pure** 3a discriminator. **The two sub-behaviours T36 names as
   still unvectored are recorded as new §8 item 6a** — a shape that adopts **twice**, and the loop firing
   **with** `installmentAmountInMultiplesOf` — and both artefacts say plainly that they are unwitnessed.
4. **`totalOutstandingAmount` decided (T35).** DEC-1 was silent; revision 7 decides **not to carry it**
   (ENGINEERING, `chosen_by: agent`) and records the reasoning: it is the literal `BigDecimal.ZERO`
   [VERIFIED: `ProgressiveLoanScheduleGenerator.java:157`, `:159-164`, `LoanSchedulePlan.java:43`], observed
   as `"0"` at **scale 0** on all twelve pass-3b captures while every other money string is scale 2, and
   carries no information. The adapter must **discard** it; no scale-discipline invariant may be applied to
   that key without deciding the `"0"` case explicitly. §9 carries the obligation; `contract.go` carries it
   on `Period`.
5. **The charges blind spot recorded as OBSERVED (T35).** Every `feeAmount` and `penaltyAmount` on every row
   of all twelve pass-3b captures is `0.00`, as are both plan totals — confirmed by reading the file
   [`t38-disbrow-coverage-output.txt`]. §4.5 now says the Path-A corpus has **zero discriminating power over
   charges**, and §8 item 1 / §9 require that fact to travel with any promoted record as machine-readable
   data.
6. **Provenance is attested, not inferred (T35, T36).** §4.1's `(19, HALF_UP)` paragraph now cites
   `MoneyHelper.PRECISION = 19` read by `javap` from the **deployed** jar inside the running container, the
   mode read three independent ways including a behavioural canary (`20925.05` on `gerege` vs `20925.04` on
   `default` in one run), and the image's own `git.properties` reporting the pinned commit with
   `git.dirty=false`.
7. **§5's two admissibility facts rewritten**, and a new paragraph naming the **three distinct capture sets**
   so a ratifier cannot conflate them. §8 items 1 and 2 re-scoped: their prerequisites are **done**; only the
   promotion decision remains, and it is gated on G-1. §8 item 6b records `Asia/Hovd` as unexercised.

---

## From-text spec check (which wrong readings now fail)

Scripts and full transcripts under `.softhouse/reviews/t38-probe/`, committed. Exact `Decimal` under explicit
contexts and integer minor units; **no float anywhere on a money path** (grep-checked — the only `float`
token in the probe is the word in a docstring and `parse_float=Decimal`, which exists precisely to stop one
being constructed).

`t38_model.py` transcribes revision 7 from the document text alone. Result:

- **13 of 13** observation triples (the old standard) — `t38-validate-output.txt`;
- **11 of 11** Path-A pass-3 production-setting captures, **cell by cell**, 712 cells;
- **10 of 10** T37 binding production-setting captures, **cell by cell**, 776 cells;
- **21 of 21 captures, 1,488 cells, zero mismatches.** The two precision-12 calibration captures are skipped
  and named.

Discrimination over the same 21 captures [`t38-discriminate-output.txt`]:

| wrong reading | captures failed | first witness cell |
|---|---|---|
| ratio-is-always-1 (P0-T32-1) | **12 of 21** | `P-01` `R1.principal` 4,262,182.87 vs observed 4,262,429.33 |
| textbook `balance × rateFactor` (P0-T29-2) | **2 of 21** | `T37-3b` `R6.interest` 31.89 vs observed 31.88 |
| `n = NumberOfRepayments` (P0-T29-1) | **2 of 21** | `T37-3c` `R2.principal` 2,051,365.77 vs observed 2,051,365.78 |
| **whole-principal pre-disbursement row (P0-T37-1)** | **3 of 21** | `P-03` `R1.balance` 100.00 vs observed **0.00** |
| EMI loop absent (§8 item 3) | **6 of 21** | `T37-3-A` `R1.principal` |
| loop without the adoption test (§8 item 3a) | **1 of 21** | `T37-3a` `R1.principal` |
| **`RepaymentEvery` instead of `periodRatio` (P0-T34-1)** | **0 of 21 — CORPUS BLIND** | none exists |

**Six of the seven now fail. The seventh cannot, and that is the result, not a gap in the experiment.** On
the §8 item 3e candidate the two readings differ on 18 of 25 cells and by MNT 2,376.67 in total interest
(re-derived). That is exactly why item 3e exists and why the binding is six vectors — and why, on this
evidence, **gate G-1 should not close on revision 7 alone unless the reviewer accepts a normative rule that
no capture can grade** (the same standing the document already gives §4.3.1's loop before T37).

---

## No-regression checks

`t38_no_regression.py` extracts each protected block by **content** (not line number, since revision 7
inserts text above several of them) from `git show main:docs/adr/…` and from the working copy, and compares
SHA-256. Result — **all IDENTICAL**:

| block | SHA-256 (revision 6 and revision 7) | verdict |
|---|---|---|
| §4.3.1's EMI re-adjust loop, steps 1–8 (fenced block) | `2ccf0f040428570c16d824c32d2a0c6268318b373c6645066db7d007fe98312f` | **IDENTICAL** — and it matches the digest T34 independently recorded |
| §4.3.2's three-operation per-period-interest block (fenced) | `f45eac5891685e4f81b2b6118aa68590974d40c57a5f38fa41c3197ec5f792cc` | **IDENTICAL** — matches T34's digest |
| §4.1.1's day-count definition table | `760b96643ab8eb33c18bd128bd5e0ec635ba1897fdb12e76d9ee6ec632b55bcb` | **IDENTICAL** (the multiplier went into the *two-call-sites* table, deliberately leaving the day-count table untouched) |

Phrases required to survive verbatim — **all present**:

- `This is a UAT/cutover precondition, **not a ratification precondition**` — **present**, in the widened
  six-vector binding.
- `relatedRepaymentPeriods.size()` and `**not `NumberOfRepayments`**` — **present**.
- the residual rule's `diff        = ` block — **present**.
- `` `1 +` the SUM of its interest periods' rate factors `` — **present**.

**`n` claims:** the script enumerates every sentence of the form "`n` is …". Revision 6 has **7 distinct**;
revision 7 has **the same 7, unchanged**. No new binding of `n` was introduced and none was disturbed.

**Corrections-leak sweep** (the `.softhouse/patterns.md` Run-1 lesson). Grepped both artefacts for
restatements of every corrected claim. **One real leak found and fixed:** §4.9's cross-seam consistency
result asserted that the 30/360 arm and the same-as-repayment-period arm compute the identical interest
fraction. That is true of the **recurrence's** `rateFactor`, but **not** of `rateFactorTillPeriodDueDate`,
because `calculateRateFactorPerPeriodForInterest`'s same-as-repayment-period branch passes `repaymentEvery`
[VERIFIED: `:1377-1382`] while its 30/360 branch passes `periodRatio` [VERIFIED: `:1404-1413`]. §4.9 is now
narrowed to "if and only if `periodRatio == RepaymentEvery`", with a warning that a future cross-seam
comparison on a drifted shape must not be expected to agree. A second, smaller leak: §4.5's sentence
"*Observed*: it is 0 on a repayment row falling entirely before the disbursement" is true but does not cover
the on-the-due-date row, which is not "entirely before" — completed, with the four capture ids.

**Also verified unchanged:** §3.1's graded-domain block and `contract.go`'s (byte-identical to `main`);
`contract.go`'s type surface (comment-only diff).

---

## Anything I found that contradicts the review

1. **The task brief inverts the seed asymmetry. My reading, and T34's actual text, are the other way round.**
   The brief says "T34's finding turns on the seed being taken from the **disbursement** while the period
   sequence is anchored on the **schedule start**". **It is the reverse.** `calculateSeedDate` reads
   `scheduleModel.getStartDate()` = the **SCHEDULE START** [VERIFIED: `ProgressiveEMICalculator.java:1462`,
   `ProgressiveLoanInterestScheduleModel.java:209-211`], while the month-end **re-anchor** that generates the
   boundaries is seeded on the **DISBURSEMENT DATE** [VERIFIED: `LoanApplicationTerms.java:583-589` →
   `DefaultScheduledDateGenerator.java:130-131`, `:168-176`]. T34 §1.3 states it correctly; only the brief
   restates it backwards. **I followed my own reading**, and revision 7 says "the re-anchor is seeded on the
   disbursement date while `calculateSeedDate` reads the schedule start". The conclusion — that the asymmetry
   is the mechanism — is unaffected; only the direction of the sentence is.
2. **"Two arguments differ" is true textually, but only ONE differs numerically inside the graded domain.**
   The brief asks me to "say both". I do — and I also state that the days-in-month argument is `30` on the
   interest call site [`:1413`] and `daysInMonth` on the recurrence call site [`:1508`, `:1537`], and that
   `daysInMonth` **evaluates to 30** under `DayCountFixed30Over360`. Presenting them as two live divergences
   would have been an overstatement in a money document.
3. **T34's `calculateSeedDate` description is incomplete.** It gives the fall-back condition as
   "`ScheduleStartDate + k months ≠ the period's DueDate`". There is a **second conjunct**
   [VERIFIED: `:1477-1480`]: the landing date minus `RepaymentEvery` months must also equal the period's
   `FromDate`. Immaterial at `RepaymentEvery == 1` with regular boundaries, material as soon as a period's
   window is not exactly `RepaymentEvery` months long. Revision 7 states both and marks both as required.
4. **T37's F-1 says the `[from, due)` rule "is a third date-membership rule … and DEC-1 states it nowhere".**
   Not quite: DEC-1 §4.6 **does** state it, with the same `:307-308` citation, as the ordering window key.
   What was true is that it was stated **in a different section, for a different purpose, and never
   reconciled with §4.3.2's roll-forward** — which is how the contradiction survived. Revision 7 says that,
   rather than repeating "stated nowhere".
5. **T34's line citations `:1950-1966` and `:1923-1927` are off by a line or two** (`rateFactorByRepaymentPeriod`
   is `:1950-1963`; `rateFactorByRepaymentEveryMonth` is `:1922-1927`). Immaterial, but revision 7 uses the
   ranges I read.
6. **Nothing in T34, T35, T36 or T37 was found to be substantively wrong.** Every source claim I re-opened —
   the day counts at `:1367-1370` / `:1500-1503`, the numerator/denominator roles at `:1961-1962`, the
   exact-zero guard at `:1953-1955`, the growth-factor sum at `RepaymentPeriod.java:216-217`, the three
   interest operations at `InterestPeriod.java:145-158`, the `[from, due)` window, `totalOutstanding =
   BigDecimal.ZERO` at `:157` — checked out exactly.

---

## Unverified

- **`go build ./...` and `go test ./...` were NOT run: there is no Go toolchain on this host** (`go` and
  `gofmt` are both absent from `PATH`, `/usr/local/go/bin`, `/opt/homebrew/bin` and `~/go/bin`). The
  `contract.go` diff is **comment-only**, verified mechanically, so it cannot change compilation — but I did
  not compile it, and I did not `gofmt` it. A reviewer with a toolchain should run both. `[UNVERIFIED]`
- **I did not re-run T32's 2,913/2,913 sweep or its MNT 1,816,050.11 figure**, and I do not assert them; they
  remain attributed to T32 in the document. Nor did I re-run T26's 2,855/2,156/699 or T29's 2,143/120,000 and
  699/43,992. `[UNVERIFIED here]`
- **"The guard fired" is not directly observed anywhere**, on any path — T36 and T37 both say so. What is
  observed is that the oracle's answer is the one only a loop-present execution produces. Revision 7 repeats
  that qualification rather than smoothing it. `[UNVERIFIED as a direct observation]`
- **The `DayCountActualActual` / cross-year partial-period arm was not re-examined** by this task. It is
  refused (§4.9) and T30/T29 covered it. I did **not** check whether `periodRatio` has an analogue there —
  the `ForInterest` entry point's ACTUAL arm at `:1400-1402` takes a different route and I did not trace it.
  **This is a genuine open question for the day `DayCountActualActual` is admitted**, and I have recorded it
  here rather than in the ADR because I did not verify it. `[UNVERIFIED]`
- **`periodRatio` for `FrequencyWeeks`, `FrequencyDays` and `FrequencyYears`** is dispatched at `:1405-1408`
  and I read the `MONTHS` arm only. §4.1.1 is written for MONTHS and says so. `[UNVERIFIED for the other
  three]`
- **The behaviour of `calculatePeriodRatio` when `RepaymentEvery > 1`** is re-derived from source but
  exercised by no capture and by no sweep in this task (every sweep is `RepaymentEvery == 1`, the graded
  domain's pin). Recorded in §8 item 6. `[UNVERIFIED empirically]`
- **I did not verify that the pass-3b captures are input-for-input identical to pass 3**; I read T35's
  1,560/0/0/12 result out of its handoff and cited it as T35's. My own model reproduces both files
  independently, which is corroboration but not the same check. `[UNVERIFIED here]`
- **No claim is made that revision 7 is now correct.** It is correct on every cell of every committed
  capture and against six of the seven wrong readings tested. The seventh is invisible to the corpus, and
  five consecutive rounds have shown what that state predicts.

---

## Follow-ups and new backlog items

1. **`/softhouse` reviewer, or the next fire: CAPTURE §8 item 3e.** It is the only one of the six binding
   shapes with no capture, it is the reason G-1 does not close on this revision's evidence, and the oracle
   was reachable this fire. Config in §8 item 3e; **do not** author an expected value — capture it.
2. **Promotion of the five T37 binding captures, the twelve pass-3b records and the four Path-B captures to
   the vector store** is now blocked by **gate G-1 alone**. The moment DEC-1 is ratified this becomes the
   next unit of work, and it must carry the blind-spot list as machine-readable data (§8 item 1).
3. **New §8 item 6a**: capture a shape where the EMI loop **adopts twice**, and one where it fires **with**
   `installmentAmountInMultiplesOf`. Both need the server path.
4. **New §8 item 6b**: `Asia/Hovd`. Costs a container restart; mandatory before any clock-sensitive capture.
5. **`periodRatio` on the ACTUAL/ACTUAL arm** — see *Unverified*. Whoever admits `DayCountActualActual` must
   re-derive the `ForInterest` entry point's ACTUAL branch [`:1400-1402`] and decide whether §4.1.1 needs a
   second arm. **Not a defect today; a landmine for the day the graded domain widens.**
6. **T37's F-4 is implemented and should become the house standard.** Every corpus-validation script in this
   program should compare **every cell**, not a summary triple. `t38_validate.py`'s `cells_from_model` /
   `cells_from_capture` pair and `t38_discriminate.py`'s "compare only the cells where the two readings
   disagree" are drop-in. Two of the last two defects in this program were found by looking at a cell the
   existing check did not look at.
7. **A note for whoever writes revision 8's reviewer brief:** the brief for this task restated T34's seed
   asymmetry backwards (see *Anything I found that contradicts the review*, item 1). It cost nothing here
   because the instruction to follow my own reading was explicit and I did. Keep that instruction.

---

# T38 — SECOND PASS (fire `20260819-080001`), independent verification of the above

**Why there is a second pass.** The orchestrator re-dispatched T38 in the next fire. The branch
`softhouse/T38-dec1-v7` already carried a complete revision 7 from the previous fire (never merged — the
fire ended before the merge step), and that branch is checked out in a stale sibling worktree, so this pass
ran on **`softhouse/T38-dec1-v7-pass2`**, branched from `softhouse/T38-dec1-v7` at `7447705`. **That branch
is the deliverable**; it is a strict superset of `softhouse/T38-dec1-v7`.

**Disposition: revision 7 VERIFIED, with two stale claims corrected and one new measurement added.** Rather
than re-author work already done, this pass re-derived the citations independently, re-ran every probe, and
attacked the document for leaks. Everything material in pass 1 held.

## What was re-verified independently (pinned checkout, every line opened here)

`git -C /Users/buv/fineract rev-parse HEAD` = `426a23544e8426a38ae43ae404670a0a7e85b9eb`, working tree clean,
treated read-only; no build run inside it; **no oracle contacted by this pass either.**

| claim in revision 7 | re-read at | verdict |
|---|---|---|
| interest call site passes `periodRatio` + hard-coded `BigDecimal.valueOf(30)` | `ProgressiveEMICalculator.java:1403-1413` | **exact** |
| recurrence call site passes `repaymentEvery` + `daysInMonth` | `:1533-1537`, `daysInMonth` at `:1508` | **exact** — and `daysInMonth` is 30 under `DAYS_30`, so the multiplier is the only live difference, as revision 7 says |
| both land in `rateFactorByRepaymentPeriod`'s `repaymentEvery` slot, consumed once | `:1598-1601` → `:1607-1608` → `:1922-1927` (argument **swap** at `:1925`) → `:1950-1951`, `:1956-1957` | **exact** |
| `calculatePeriodRatio` seed / offset / walk, and which step is rounded | `:1419-1459` (`k` `:1423-1439`, month-end case `:1430-1433`, walk `:1441-1458`, the **only** `mc` division `:1453`, exact `.add` `:1454`) | **exact**, step for step against §4.1.1's pseudo-code |
| `calculateSeedDate`, origin and **both** fall-back conjuncts | `:1461-1481`, origin `:1462`, `ProgressiveLoanInterestScheduleModel.java:209-211`, conjuncts `:1477-1480` | **exact** — the second conjunct is real; T34's prose gives only the first |
| the ratio's day counts, roles and zero guard | `:1367-1370`, `:1500-1503`, `:1961-1962`, `:1953-1955` | **exact** |
| the two call sites' spans | `:638-643`, `:639-640`, `:641-642` | **exact** |
| M1 | `LoanRepaymentScheduleProcessingWrapper.java:251-254` ← `ProgressiveLoanInterestScheduleModel.java:238-245` | **exact** |
| M2 | `ProgressiveLoanInterestScheduleModel.java:195-197` | **exact** |
| M3, and the sequencing that produces step 4b | `ProgressiveLoanScheduleGenerator.java:307-308`, guard `:309`, row balance `:132` inside the iteration, `processDisbursements` called `:121-122`, `addDisbursement` `:351`, disbursement row `:318` | **exact** |
| post-registration balance would be the whole principal | `RepaymentPeriod.java:389-403`, `:396` | **exact** |
| growth factor `1 + Σ`, no `MathContext` | `RepaymentPeriod.java:216-217` | **exact** |
| month-end re-anchor seeded on the **disbursement** date | `LoanApplicationTerms.java:583-589`, `DefaultScheduledDateGenerator.java:128-131`, rule `:168-176` | **exact** — pass 1 was right; the task brief's inversion is confirmed a brief error |
| `totalOutstandingAmount` is the literal `ZERO` | `ProgressiveLoanScheduleGenerator.java:157`, `:159-164`, `LoanSchedulePlan.java:43` | **exact** |
| disbursement row's balance = the amount advanced | `LoanSchedulePlan.java:52-56` | **exact** |
| §4.9's narrowed cross-seam result | `:1377-1382` (interest arm passes `repaymentEvery`), `:1513-1515`, `:1517-1519` | **exact** |
| rate ÷ 100 under the threaded `mc` (§4.8) | `:1318-1320` | **exact** |

**Hand re-derivation of `periodRatio`, independent of any probe.** Schedule start `2024-01-28`, disbursement
`2024-01-31`, repayment period 2 = `[2024-02-29, 2024-03-31]`: `calculateSeedDate` lands on `2024-04-28 ≠
2024-03-31`, so the seed is the period's own `FromDate`; `k = 0` (the month-end case does **not** fire —
`seedDay > targetDay` is strict and both are 29); the walk overshoots at `2024-04-29`, backs off to
`base = 2024-03-29`, and returns `2 ÷ 31 + 1 = 1.06451612903225806452` — **the second entry in §4.1.1's list
of six ratios**, reproduced by hand from the source, not from either probe.

## Probes re-run — all seven reproduce their committed output byte-identically

`t38_validate` (21/21 captures, 1,488 cells), `t38_discriminate`, `t38_corpus_blind` (35 captures, 0 non-unit
`periodRatio`), `t38_no_regression`, `t38_periodratio_scan`, `t38_periodratio_sweep`, `t38_disbrow_coverage`:
each re-executed and diffed against the committed transcript — **identical, all seven.** `t38_model.py` was
additionally read against the revision-7 text: `calculate_seed_date`, `period_ratio`, `rate_factor`,
`membership_interest_model` (M1), `membership_attachment` (M3), `segment`, `first_related` and `split_rows`'
4a/4b split are faithful transcriptions of the document, not of the source. No `float` on any money path
(grep-checked; the only hit is the word in a docstring).

`t38_no_regression` and `t38_validate` were re-run **after** this pass's edits: still **NO REGRESSION** and
**PASS**.

## Two defects found in revision 7 and fixed here

**1. A false provenance claim, twice.** §4.3.1 and §4.3.2 both ended "No live oracle was reachable when this
revision was written." True of revisions 4–6; **false of revision 7** — a live pinned reference oracle was
reachable in the same fire and tasks T35, T36 and T37 captured from it
[VERIFIED: `.softhouse/capture/dec1-binding/ATTESTATION.md` — "executed on the local fire of **2026-08-18**";
branch tips `softhouse/T37-…` 23:19, `softhouse/T36-…` 23:23, `softhouse/T35-…` 23:27 on 2026-08-18, the same
fire whose T38 commits run to 00:12 on 2026-08-19]. Revision 7 cites those captures throughout, so the
sentence contradicted its own document. **Replaced** in both places with the accurate claim — *this task
contacted no oracle; the reason is the labelling discipline, not unavailability* — which is what the
revision-7 history entry already said correctly. A wrong statement about the evidence base is the one class
of error this document's whole method exists to prevent, so it is fixed rather than noted.

**2. A P0-T34-1 leak in the §5 corpus table and on `GenerateRequest.RepaymentEvery`.** Both said
`RepaymentEvery` "enters the interest fraction directly [`:1956-1958`]" — the exact sentence P0-T34-1
corrects, surviving in a table and a field doc after the formula was fixed (the Run-1 "corrections leak"
pattern). Both now say it is the multiplier of the **recurrence's** `rateFactor` [`:1536` → `:1956-1958`],
that the interest call site takes `periodRatio` [`:1404-1413`], and that `RepaymentEvery > 1` is additionally
the only way to reach `periodRatio`'s whole-period branch [`:1457-1458`].

## One new measurement added (an eighth candidate wrong reading)

Revision 7 says "a port that assumes one convention throughout is wrong somewhere" and did not say **where**.
`.softhouse/reviews/t38-probe/t38_pass2_membership.py` measures the collapse pass 1 did *not* test — using
**M3 where M1 belongs**, which is what an implementer gets by reusing §4.6's ordering window key for §4.3.2's
segmentation (§4.6 was the only place revisions 1–6 stated M3). Result, cell by cell:

- **inert**: identical money on **21 of 21** committed production-setting captures and on **108 of 108**
  re-derived in-graded-domain shapes whose disbursement is dated exactly on a repayment period's `DueDate`
  [`t38-pass2-membership-output.txt`];
- the probe was checked to be non-vacuous — on `T37-3c`'s dates the two readings genuinely select different
  target periods (index 0 vs 1) and different interest-period segmentations, and still return the same money,
  because M3's owner period opens on that same date and so yields the zero-length first segment and the same
  effective due date;
- so the money consequence of confusing M1 and M3 lives **only** in the emitted balance (step 4b), which the
  corpus *does* grade (3 of 21). Recorded in §4.3.2 and in `contract.go`, labelled a re-derivation, with
  `[UNVERIFIED outside the graded domain]` — nothing here tests multi-tranche, an interest pause or a rate
  change, where the two conventions attribute different amounts to different periods.

## Leak sweep, run again from scratch over both artefacts

Grepped for every corrected claim: `RepaymentEvery`-as-interest-multiplier (**one leak, fixed — above**), the
literal step-4 roll-forward as an *emitted* value (**none**; it survives only inside 4a and §9's 4a, both
explicitly the carried-forward quantity), "is graded" unqualified for the disbursement row (**none**; §4.5 is
per-harness and says "recorded by two harnesses, promoted by neither"), "13 of 13" unqualified (**none**;
every occurrence names the three scalars it compares), the deleted ratio-is-1 clause (**none outside the two
notes recording its deletion**), and §§6 and 7 (**clean**). §4.9's cross-seam result is correctly narrowed to
"if and only if `periodRatio == RepaymentEvery`".

## Scope and shape

- The three-dot diff against `main` touches **only** `docs/adr/DEC-1-schedule-generator-adapter.md`,
  `nexus/internal/apps/loanschedule/contract/contract.go`, `.softhouse/reviews/t38-probe/**` and this
  handoff. Nothing under `.softhouse/capture/`, `tasks.json`, `program.json`, `RESUME.md`,
  `reference-oracle.md`, `patterns.md`, `LOCK`, or `/Users/buv/fineract`.
- **`contract.go` remains COMMENT-ONLY** after this pass's two edits, verified the same mechanical way (the
  diff against `main` with comment lines filtered out has no non-hunk-header lines). No type, field, enum
  member, sentinel or graded-domain predicate moved. Still agent work, still not a `user` gate.
- **`go build` / `go test` still NOT run — no Go toolchain on this host** (`go` and `gofmt` absent from
  `PATH`, `/usr/local/go/bin`, `/opt/homebrew/bin`, `~/go/bin`). Comment-only, so it cannot change
  compilation, but it is unbuilt and un-`gofmt`'d. `[UNVERIFIED]`

## What this pass did NOT change, deliberately

§4.3.1's steps 1–8 and §4.3.2's three-operation block (both still byte-identical to revision 5 by SHA-256),
§4.1.1's day-count table, §3.1's graded domain, the seven `n` bindings, every figure labelled a re-derivation
(including the 3d table — T37's F-2 stands), and the six-vector binding's "conformance PASS and cutover,
**NOT ratification**" wording.

## Findings for the next reviewer (raised, not self-applied)

1. **G-1 still should not close on this evidence alone.** §8 item **3e** has no capture, and the
   `RepaymentEvery`-instead-of-`periodRatio` reading remains **0 of 21** — corpus-blind. Revision 7 says so
   plainly; a ratifier has to decide knowingly to ratify a normative rule no vector can grade. Capturing 3e
   is cheap while the oracle is up and is the single highest-value next action.
2. **The stale-provenance class of defect deserves a mechanical check.** Sentences like "no live oracle was
   reachable" are environment claims that silently expire between revisions. One line in the reviewer's
   checklist — "does every environment claim in the document still hold for THIS revision?" — would have
   caught it in either of the last two rounds.
3. **The pass-2 membership probe is a template.** Every normative distinction the document draws should be
   asked "does collapsing it move money, and can the corpus see it?" Three answers are possible — moves and
   visible, moves and invisible, inert — and the document should say which. It now does for the growth factor
   (§2.1, inert), for `periodRatio` (moves, invisible) and for M1/M3 (one side moves and is visible, the other
   inert).
