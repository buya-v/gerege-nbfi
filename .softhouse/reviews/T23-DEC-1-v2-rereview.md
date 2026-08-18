# T23 — Independent re-review of DEC-1 revision 2 (adapter contract, `loanschedule`)

**Reviewer:** T23, independent re-reviewer. Not the author. No edit was made to
`docs/adr/DEC-1-schedule-generator-adapter.md` or to
`nexus/internal/apps/loanschedule/contract/contract.go`.

**Subject:** DEC-1 revision 2 (477 lines) and `contract.go` (1,140 lines), against
`.softhouse/reviews/T5-DEC-1-contract-review.md` §8's nine required changes and §9's reserved items,
`.softhouse/gates-proposed-answers.md` (Buyan 18 Aug 2026, P-1/P-2/P-3), `.softhouse/reviews/T21-capture-pass3-audit.md`,
`.softhouse/reviews/T22-pathb-capture-audit.md`, `.softhouse/reviews/T3b-progressive-schedule-behavior-rereview.md`,
and the pinned checkout `/Users/buv/fineract` @ `426a23544e8426a38ae43ae404670a0a7e85b9eb`.

**Terminology.** "The reference oracle" is the Fineract reference implementation at that commit.
Oracle Database is a prohibited product in this program and is not referred to anywhere below.

---

## VERDICT: **ACCEPTED WITH REQUIRED CHANGES**

**This is NOT ratifiable as it stands under P-2.** `ACCEPTED` would have meant "ratifiable as it
stands"; this is not that. The three P0 findings below are rejection-grade for the purpose of
freezing the document, because each is a **normative** statement that is wrong or missing, and after
ratification every one of them costs a gate to correct.

It is **not** a REJECT in T5's sense. Revision 2 does not need another rewrite. The structure is
sound, the contract-domain / graded-domain split survives the attack I put to it, all nine of T5's
required changes are addressed and eight are fully satisfied, every one of the ~101 distinct source
citations resolves in the pinned checkout, no progressive-vs-cumulative misattribution exists, the
Go artefact is clean on every non-negotiable, and **my own from-scratch re-derivation reproduces
eight of the twelve captures — every period, every column, to the minor unit.** The core money math
in this document is right.

What is wrong is bounded and localised: three normative paragraphs, fixable in place.

**P0-1 is the finding that decides the verdict.** DEC-1 §4.3 states that the EMI re-adjust loop
`checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` "is reachable only outside the graded domain",
and the Go module's obligation list in §9 omits it. **I observed the loop firing and changing the
schedule on 7 of 10 ordinary requests inside the stated graded domain**, with
`InstallmentRoundingMultipleMinor == 0`. A Go module built strictly to this frozen document would
misprice MNT 1,014,632 over 6 monthly installments at 7.0 % — every period, in the minor unit — and
no vector in the corpus could detect it.

---

## 1. Method

- Read the ADR and `contract.go` in full.
- Re-derived the algorithm from the pinned source independently (no reuse of
  `.softhouse/capture/out/t21-probe-rederive.py`, whose `EmiAdjustment` guard I found to be wrong —
  see §6.1). Artefact: `.softhouse/reviews/t23-probe/t23_rederive.py`.
- Ran **new observations against the pinned oracle** through the Path-A seam, in the pinned image
  (`sha256:e596339626bfca2b07d10fc294197c59118343423fd362f89f5f18ccd270459a`, verified by
  `docker image inspect`), seam class verified byte-identical to the pinned original by `diff`.
  Artefacts: `.softhouse/reviews/t23-probe/T23Probe.java`, `T23Probe2.java`, and their raw outputs
  `t23-probe-output.txt`, `t23-probe2-output.txt`.
- Mechanically diffed `LoanApplicationTerms.Builder`'s 37 fields against the 36 the private copy
  constructor reads, to hunt for a third silently-dropped component.
- Mechanically extracted and resolved every `file:line` citation in both artefacts.
- Ran `go build`, `go vet`, `gofmt -l`, `go test` and a comment-stripped known-bad scan myself.

---

## 2. T5's nine required changes — one verdict each

| # | T5 required change | Verdict | Evidence |
|---|---|---|---|
| 1 | Fix the precision/scale ambiguity; state both senses normatively; name the `setScale` site; add a discriminating vector | **SATISFIED** | see §2.1 |
| 2 | Fix the month-end rule; seed is the disbursement date; move it onto `Disbursement.Date` | **SATISFIED** | see §2.2 |
| 3 | Fix or fence the ordering rule (option a preferred) | **PARTIAL** | see §2.3 — **P0-2** |
| 4 | Constrain `InstallmentRoundingMultipleMinor` to whole major units | **SATISFIED** | see §2.4 |
| 5 | Define the final-period residual as a formula | **SATISFIED** | see §2.5 |
| 6 | Correct the `allowFullTermForTranche` / `allowPartialPeriodInterestCalculation` grounds | **SATISFIED** | see §2.6 |
| 7 | Make the `DayCountConvention` → oracle-enum mapping normative | **SATISFIED** | see §2.7 |
| 8 | Widen the adapter's tenant-context obligation to every `Money` path | **SATISFIED** | see §2.8 |
| 9 | Three minors: currency-code case; soften "never re-rounded"; no-`double` capture obligation | **SATISFIED** | see §2.9 |

### 2.1 (1) Precision vs scale — SATISFIED

`Rounding` now carries `SignificantDigits`, `RateFactorScale` and `Mode`
(`contract.go:372-527`). Both senses are stated normatively, the `setScale` site is named, and the
two are constrained equal with `ErrUnsupportedConfiguration` on a mismatch. I confirmed the source:

- `ProgressiveEMICalculator.java:1956-1958` computes `interestFractionPerPeriod` with three
  `mc`-qualified operations, and `:1959-1962` ends
  `.divide(calculatedDaysInPeriod, mc).setScale(mc.getPrecision(), mc.getRoundingMode())`.
  `setScale` takes a **scale**. The same pattern recurs at `:1976-1979` on the partial-period arm.
  Those are the only two occurrences on this path. The ADR's quoted snippet matches the file verbatim.
- `MoneyHelper.PRECISION = 19` is a `public static final int` at `MoneyHelper.java:35`;
  `getMathContext()` at `:91-93` returns `new MathContext(PRECISION, getRoundingMode())`.
  `initializeTenantRoundingMode` (`:54-65`) writes only the **mode** into a per-tenant cache. So the
  claim T5 item 8 asked about — *tenant precision is the compile-time 19 and cannot be pinned* — is
  **correct**, and the ADR's statement that "any prose implying precision is tenant-configurable is
  wrong" is right.

**The discriminating capture is OBSERVED, not derived.** I read it out of the committed raw capture
files, not out of the ADR:

| | period 5 principal | period 5 interest | period 5 balance | total interest |
|---|---|---|---|---|
| `D-01` (`capture-raw.json`, precision 12) | 4,531,420.**25** | 1,082,346.**53** | 65,674,840.**83** | 13,393,481.**05** |
| `D-01-p19` (`capture-raw.json`, precision 19) | 4,531,420.**26** | 1,082,346.**52** | 65,674,840.**82** | 13,393,481.**04** |
| `P-01` (`capture-prod-raw.json`, precision 19, second harness) | 4,531,420.**26** | 1,082,346.**52** | 65,674,840.**82** | 13,393,481.**04** |

Two independently written harnesses agree at 19. The ADR's figures are exactly these.

**"No size threshold" is also observed, not modelled.** I traced it to
`.softhouse/capture/out/t21-probe-oracle.txt` §C, which is the *oracle's* answer (the Python
threshold scan is explicitly labelled "model-located" and its headline candidates were re-run through
`T21Probe.java`). Observed there: `36 × 16.8 %` at principal **4** is `*** DIFFERENT ***` between 12
and 19 (total interest 1.13 vs 1.14), and at principal **50,000,000** is `SAME`. The ADR's claim
holds.

**One numeric imprecision (P1-1).** The ADR and `contract.go` both say "**seventeen** per-period
divergences". I diffed `D-01` against `D-01-p19` field by field: **all 18 repayment rows differ** —
17 in `totalOutstandingBalance`, 13 in `balance`, 2 in `principal`/`interest`, 1 in `total`. "17" is
inherited verbatim from `.softhouse/gates-proposed-answers.md` G-1 §3. The conclusion is
*strengthened*, not weakened, but a figure in a document about to be frozen should be right.

### 2.2 (2) Month-end rule — SATISFIED

The rule is now two steps, stated on `Disbursement.Date` (`contract.go:530-577`) and in ADR §4.2, and
both are correct against source:

- Step: `getRepaymentPeriodDate` (`DefaultScheduledDateGenerator.java:311-333`) is
  `startDate.plusMonths(repaidEvery)` for MONTHS — `java.time` clamps the day to the target month's
  length. Called at `:128-129`.
- Re-anchor: `adjustDate` at `:168-176`, called at `:130-131` with
  `loanApplicationTerms.getSeedDate()`. The ADR's quoted Java block matches the file verbatim,
  including `Math.min(noOfDaysInCurrentMonth, seedDay)`.
- **Seed = the disbursement date**: `LoanApplicationTerms.assembleFrom` at `:583-589` —
  `seedDate = modelData.disbursementDate() != null ? disbursementDate : scheduleGenerationStartDate`.
  Confirmed.
- The first period does **not** short-circuit the re-anchor on this path:
  `generateNextRepaymentDate` at `:119-122` uses `getCalculatedRepaymentsStartingFromLocalDate()`
  when it is non-null, and `calculatedRepaymentsStartingFromDate` (`LoanApplicationTerms.java:117`)
  is assigned only in a positional constructor (`:803`) the Builder path never reaches. So it is
  null, and period 1 goes through step + re-anchor like every other. This is the detail that makes
  the observed `2024-01-31 → 2024-02-29 → 2024-03-31` sequence correct rather than accidental.

I re-derived both date sequences from scratch and they match the observed captures `P-02` and `P-02b`
exactly, including the 182-day term.

T3b is the specification of record where it and the parked T2 analysis disagree; revision 2's rule
agrees with T3b and with source.

### 2.3 (3) Ordering — PARTIAL (**P0-2**)

**What is satisfied.** Option (a) was taken, matching `gates-proposed-answers.md` G-1 §2. The window
key is genuinely derivable from the response alone — a repayment row's key is its own `DueDate`, a
disbursement row's key is the `DueDate` of the repayment period whose half-open window contains it,
and the repayment rows carry those windows. The mechanism is verified in source:
`ProgressiveLoanScheduleGenerator.java:307-308` tests
`!disbursementDate.isBefore(periodFromDate) && disbursementDate.isBefore(periodDueDate)` — half-open;
`:121` emits disbursements at the top of the loop and `:141` appends the repayment row at the bottom.

I re-observed both cases myself (`t23-probe-output.txt`, MNT 1,200,000 / 6 × 21.6 % at (19, HALF_UP)):

```
Q0a  disbursement 2024-01-01:  DISBURSEMENT, repayment 1 … repayment 6
Q0b  disbursement 2024-02-01:  repayment 1 (due 2024-02-01, all zero), DISBURSEMENT, repayment 2 … 6
```

Applying the contract's window key by hand: in Q0b the disbursement falls in period 2's window
`[2024-02-01, 2024-03-01)`, so its key is 2024-03-01, which sorts after repayment 1's key of
2024-02-01 and ties with repayment 2, broken by `Kind` with disbursement first. **The rule reproduces
the observed order.** In Q0a the disbursement falls in period 1's window, ties with repayment 1, and
sorts first. **Also correct.** T5's F-2 is fixed.

**What is not satisfied — P0-2.** The rule's third clause says: *"if the row's date is on or after the
last repayment period's `DueDate`, its key sorts after every repayment row."* That clause presupposes
the row exists. **It does not.** Observed, same probe, same settings:

```
Q1a  disbursement 2024-07-01 (exactly the last due date):
     rows: disbursement=0  repayment=6, all periods 0.00/0.00/0.00, totalDisbursed=0.00
Q1b  disbursement 2024-09-01 (after the last due date):     identical — no disbursement row
Q2   disbursement 2023-11-15 (before ScheduleStartDate):    identical — no disbursement row
```

The mechanism is in source and is not subtle:
`ProgressiveLoanScheduleGenerator.java:305-306` gates the after-maturity arm on
`includeDisbursementsAfterMaturityDate`, which is true only in the post-loop call at `:147-150`,
itself gated on `loanApplicationTerms.isMultiDisburseLoan()`. `multiDisburseLoan`
(`LoanApplicationTerms.java:165`) is assigned only at `:812`, in a positional constructor the Builder
path never reaches — so it is `false` on this seam and the post-loop call never happens.
`emiCalculator.addDisbursement` at `:351` is therefore never called either, which is why the
principal vanishes.

All three requests are **inside DEC-1's stated graded domain**: `len(Disbursements) == 1`,
`RepaymentEvery == 1`, `FrequencyMonths`, `InterestMethodDecliningBalance`,
`DayCountFixed30Over360`, `DownPaymentPercentage == Rate{0,1}`,
`InstallmentRoundingMultipleMinor == 0`, `MinorUnitDigits == 2`, `(19, HALF_UP)`. Nothing in the
graded-domain predicate constrains `Disbursement.Date` relative to `ScheduleStartDate` or to the
maturity date.

So a Go module written to the frozen contract would emit a disbursement row (and amortize the
principal) where the oracle emits none and amortizes nothing. That is a divergence produced *by
following the specification*, inside the domain the specification says is graded.

### 2.4 (4) `InstallmentRoundingMultipleMinor` constrained — SATISFIED

`contract.go:881-888` requires "0, or a positive exact multiple of `10^Currency.MinorUnitDigits`",
names `5000` and `1` as `ErrUnsupportedConfiguration`, and gives the reason. Verified:
`LoanRepaymentScheduleModelData.java:36` declares `Integer installmentAmountInMultiplesOf`;
`Money.java:150-157` and `:163-170` consume it as a divisor in major units. Mirrored in ADR §4.7
beside the `Rate{1,3}` argument, as T5 asked.

### 2.5 (5) Final-period residual — SATISFIED

The formula, the sign, the accumulation scale and the target period are all now stated, and all four
are right:

- `ProgressiveEMICalculator.java:1202-1203`
  `diff = totalDisbursedAmount + totalCapitalizedIncome + totalCreditedPrincipal + totalDueInterest − totalEMI`;
  applied at `:1205` (`getEmi().add(diff, mc)`), stored at `:1210`.
- Target: `:1176-1181` — the last not-fully-paid period; on a fresh schedule, the last one.
- **"Accumulated at currency scale, not at `SignificantDigits`" is precisely correct**, and I checked
  it rather than taking it: `Money.plus(BigDecimal, mc)` at `Money.java:253-259` performs
  `this.amount.add(amountToAdd)` with **no** `MathContext` and then constructs a `Money`, whose
  constructor `setScale`s to the currency's decimal places at `:52`. The `mc` supplies only the tie
  rule. The reductions at `:1190-1200` therefore add exactly and quantize at currency scale.
- Signed: my re-derivation reproduces `diff` = −0.01 (`P-00`), −0.05 (`P-MNT-5M`), +0.03
  (`P-MNT-1M2`), +0.04 (`P-MNT-50M`), +0.08 (`P-MNT-4M999`), 0.00 (`P-01`) — each matching the
  oracle's final installment to the minor unit.
- "Final unpaid period" is gone; `contract.go` says "the last period".

### 2.6 (6) The two pin grounds — SATISFIED

- `allowFullTermForTranche`: the Builder setter **is** reached (`LoanApplicationTerms.java:606`) and
  **is** copied out (`:348` — it is one of the 36 fields the copy constructor reads). The consuming
  guard `ProgressiveEMICalculator.java:142-144` is
  `isAllowFullTermForTranche() && numberOfRepayments > 0 && action == DISBURSEMENT` — **no
  multi-disbursement test**. `true` routes to `addFullTermTrancheDisbursement` at `:155-174`, which
  builds a synthetic `LoanApplicationTerms` (`buildLoanApplicationTerms`, `:176-`) and a temporary
  schedule model. Every element of the corrected account checks out.
- `allowPartialPeriodInterestCalculation`: its only calculation-path use in the progressive module is
  `ProgressiveEMICalculator.java:130`, inside the guard at `:128-130` that first requires
  `getInterestCalculationPeriodMethod() != null && …isSameAsRepaymentPeriod()`. That field
  (`LoanApplicationTerms.java:108`) has no initialiser and is assigned only at `:796`, in a positional
  constructor; the Builder never sets it. So it is `null` and the branch short-circuits. Correct.
  (The only other reference, `:201`, is inside `buildLoanApplicationTerms` — propagation, not use.)

### 2.7 (7) Day-count mapping normative — SATISFIED

Both rows appear in ADR §4.9 and in `contract.go`'s `DayCountConvention` doc:
`DayCountFixed30Over360 → (DAYS_30, DAYS_360)`, `DayCountActualActual → (ACTUAL, ACTUAL)`. The
"load-bearing" claim is verified: `ProgressiveEMICalculator.java:1533-1539` switches on
`daysInMonthType` into materially different arms, and `:1505-1507` gates the cross-year arm
(`:1526-1531`) on `daysInYearType == ACTUAL`.

The monthly consistency result in §4.9 is also correct, and I checked the arithmetic rather than the
prose: the same-as-repayment monthly arm (`:1513-1515`) calls
`rateFactorByRepaymentPeriod(rate, ONE, repaymentEvery, 12, …)` giving `1 × 1 ÷ 12`; the 30/360 arm
reaches `rateFactorByRepaymentEveryMonth` (`:1922-1927`) giving `30 × 1 ÷ 360`. At `MathContext(19)`
both are the correctly-rounded 19-significant-digit form of the same exact rational, so they are
bit-identical. For weekly they are `1/52` versus `7/360`, which differ — as the document says.

### 2.8 (8) Adapter obligation widened — SATISFIED

`contract.go:502-526` and ADR §4.1 now state it for **every** `Money` construction without an
explicit `MathContext`. Verified: `Money.java:52` reads `getMc()` (`:494-496`, falling back to
`MoneyHelper.getMathContext()`); `:102-104` is the two-argument `of`; `:150-157` reads
`MoneyHelper.getRoundingMode()` unconditionally; and `:163-170` — the very overload
`safeRoundingForEMI` reaches via `:159-161` — divides under the threaded `mc` but **returns through
the two-argument `Money.of` at `:169`**, so its `setScale` reads tenant-global state. That is exactly
T5's F-6, correctly recorded. `MoneyHelper.java:74-82` throws `IllegalStateException` outside an
initialised tenant, as claimed.

### 2.9 (9) The three minors — SATISFIED

- Currency-code case: `contract.go:106-121` requires upper case, cites the shipped fixture's `"usd"`
  at `EmbeddableProgressiveLoanScheduleGeneratorTest.java:47` (verified — the line is
  `new CurrencyData("usd", "US Dollar", 2, null, "usd", "$")`), and puts the normalisation on the
  adapter.
- The "money is never re-rounded" overclaim is **gone** — `grep` finds no such sentence in either
  artefact.
- The no-`double` capture obligation is in ADR §9 ("must never route an amount through a
  floating-point type") and §8 item 7. `EmbeddableProgressiveLoanScheduleGeneratorTest.java:120-122`
  is verified as `return value == null ? 0.0 : value.doubleValue();`.

**One residual error inside item 9 (P1-2).** ADR §8 item 7 calls `Money.java:134-148` and `:220-222`
"traps for a harness author, **not parts of the calculation**". `Money.java:220-222` is
`Money copy(double)`, and it **is** on the calculation path: `EmiAdjustment.java:35` calls
`originalEmi.copy(lowerHalfOfRelatedPeriods)` where `lowerHalfOfRelatedPeriods` is a `double` from
`Math.floor(n / 2.0)` (`EmiAdjustment.java:32`), and `ProgressiveEMICalculator.java:1788` calls
`getEmi().copy(0.0)`. Both feed the EMI re-adjust loop, which P0-1 shows is live inside the graded
domain. The values happen to be exact small integers so no precision is lost, but the sentence is
false and it is exactly the kind of "no float here" assurance this program must not get wrong.

---

## 3. The contract-domain / graded-domain split

**Verdict: the split is SOUND and the widening-without-amendment claim HOLDS.** This is the load-bearing
idea and I tried hard to break it.

**Can the graded domain widen without amending a ratified DEC-1? Yes.** Widening admits a value the
frozen types already accept. No identifier is added, removed, renamed or retyped; no struct layout
moves; no vector's field set changes; a vector captured before the widening remains a legal encoding
after it. Under DEC-1 §1's own definition of an amendment, none of the triggers fire.

**The one tension, and why it is not a loophole.** §1's definition also catches "**re-documenting**
any identifier in `contract.go`", and the graded domain is recorded as a literal list of equalities
in a doc comment on `GenerateRequest` (`contract.go:610-621`). Widening therefore means editing a
frozen doc comment. §1 resolves this explicitly and in both artefacts — "Widening the graded domain
(§3) is NOT an amendment… no ratified sentence is contradicted" (ADR §1; `contract.go:28-30`) — and
the per-field refusal sentences are all worded *indexed to the graded domain* rather than as
unconditional refusals ("Outside the graded domain — refuse with `ErrNoDiscriminatingVector`",
`contract.go:211-212`, `:220`, `:299`, `:360-362`, `:798-799`, `:838-839`, `:891-892`), so widening genuinely
contradicts none of them. The specific carve-out governs the general definition. This is a
deliberate, twice-stated exception, not a gap someone can drive through by accident.

**What is missing is the mechanism, not the principle (P1-3).** The document never says *who* records
a widening, *where* it is recorded, or *on what evidence*. As written, "widening is not an amendment"
is an unbounded licence for a later agent to edit one doc comment and thereby enlarge what the port
is allowed to answer. It needs one paragraph: a widening requires (a) an admissible vector in the
vector store that discriminates the value, (b) a dated entry naming the vector, and (c) the same
independent-review bar the contract itself passed. Cheap to add; genuinely load-bearing.

### 3.1 The pivotal structural claim (§3.2) — the pair is TRUE, the conclusion is REFUTED

The claim: *the two components the Path A seam silently drops are exactly the two the graded domain
pins to inert values, therefore inside the graded domain the seam's blind spot is empty.*

**The pair claim is true, and I verified it mechanically rather than by reading.** I extracted the 37
`private` fields of `LoanApplicationTerms.Builder` (`:353-577`) and the 36 `builder.X` reads in the
private copy constructor (`:304-351`) and diffed them:

```
BUILDER FIELDS NEVER READ BY THE COPY CONSTRUCTOR:
daysInYearCustomStrategy
```

Exactly one, and it is the one the author names. Separately I walked all 19 components of
`LoanRepaymentScheduleModelData` (`:32-39`) against `assembleFrom` (`:579-607`): exactly one —
`installmentAmountInMultiplesOf` — is never mentioned there at all (the only assignment in the class
is `:828`, positional). `daysInYearCustomStrategy` is passed at `:604`, stored by the Builder at
`:380`/`:567-568`, and dropped at `:304-351`; its only assignment is `:881`, positional.
**There is no third dropped component of that class.** The author's account is exact.

**The conclusion does not follow.** "Faithfully rendered" is not the same as "no blind spot", and the
seam has two blind spots that are not dropped fields:

1. **The graded domain admits requests the oracle answers degenerately** — §2.3's Q1a/Q1b/Q2. The
   request is rendered perfectly; the *generator* then discards the disbursement and returns an
   all-zero schedule. No capture covers this and the contract's normative ordering text describes a
   row that is not emitted.
2. **The corpus does not grade everything the request carries** — §6.1's EMI re-adjust loop. It moves
   money on graded-domain requests and none of the twelve captures trips its guard.

So §3.2's sentence "**Therefore, inside the graded domain, the seam's blind spot is empty:** every
admissible request is faithfully rendered, and a Path-A capture grades everything the request
carries" is **overclaimed on both halves** and must be narrowed. The premise it rests on (the pair)
is sound; the inference from "rendered" to "graded" is not.

---

## 4. The two flagged judgement calls

### 4.1 (a) Omitting `InterestCalculationPeriod` / `PartialPeriodInterest` — **CORRECT OMISSION**

- `allowPartialPeriodInterestCalculation` **is** a record component and **is** renderable; the ADR
  does not claim otherwise — it pins it `true` and argues inertness from
  `interestCalculationPeriodMethod == null`. Verified in §2.6. Sound.
- `interestCalculationPeriodMethod` is genuinely **not** a component of
  `LoanRepaymentScheduleModelData` (`:32-39` — I enumerated all 19). The seam cannot express it. The
  ADR says exactly this ("pinned by omission… not a contract field because the seam cannot express
  it") and flags that re-binding to the server path makes exposing it a gate. That is the honest
  disposition, and it is not the F-3 defect class: F-3 was a field the contract *carried* while the
  seam dropped it; this is a field the contract does not carry and the seam cannot set.

**One caveat to record (P1-4).** The ADR wants Path-B (running-server) captures admitted as vectors
once §8 item 2 lands. On the server path `interestCalculationPeriodMethod` is **non-null**
(`SAME_AS_REPAYMENT_PERIOD`), which un-short-circuits `ProgressiveEMICalculator.java:128-133`; the
branch then stays inert only because `allowPartialPeriodInterestCalculation` is *also* `true` there
(the guard is `… && !isAllowPartialPeriodInterestCalculation()`). The ADR does not state what the
Path-B products set for that flag. If a Path-B product ever has it `false`, the disbursement's
effective due date shifts to the next period's from-date and the capture is not comparable with a
Path-A vector at all. Worth one sentence in §8 item 2.

### 4.2 (b) Refusing `FrequencyYears` because "the oracle throws" — **REFUTED (P0-3)**

The oracle throws **only on the 30/360 arm.** Observed, same probe, same settings
(`t23-probe-output.txt`):

```
Q3a  freq=YEARS, dim=DAYS_30, diy=DAYS_360
     THREW java.lang.UnsupportedOperationException: Invalid repayment frequency

Q3b  freq=YEARS, dim=ACTUAL, diy=ACTUAL
     OK  loanTermInDays=1096 totalInterest=551982.62 totalRepayment=1751982.62
         repayment 1 due 2025-01-01  324792.27 / 259201.94
         repayment 2 due 2026-01-01  394949.34 / 189044.87
         repayment 3 due 2027-01-01  480258.39 / 103735.81
```

The mechanism is in the source the ADR itself cites. `ProgressiveEMICalculator.java:1533-1539`
switches on `daysInMonthType`: the `DAYS_30` arm (`:1536`) dispatches through
`calculateRateFactorPerPeriodBasedOnRepaymentFrequency`, whose `switch` at `:1602-1610` handles DAYS,
WEEKS, MONTHS and throws on anything else. The **`ACTUAL` arm at `:1534-1535` never reaches that
dispatch at all** — it calls `rateFactorByRepaymentPeriod` directly. And
`DefaultScheduledDateGenerator.getRepaymentPeriodDate` (`:311-333`) handles `case YEARS` with
`plusYears`, so the dates generate fine.

So the normative sentences

> "**`FrequencyYears` the oracle cannot answer at all**" (ADR §4.10)
> "The reference oracle CANNOT answer it on this path… throws UnsupportedOperationException for
> anything else" (`contract.go:236-241`)

are **false as written**, and the error-taxonomy consequence they justify —
`ErrUnsupportedConfiguration` "not `ErrNoDiscriminatingVector`, because the problem is not a missing
vector but a missing answer" — has no basis for the `DayCountActualActual` case.

**Practical impact is small; correctness impact is not.** `DayCountActualActual` is itself refused
with `ErrNoDiscriminatingVector`, which wraps `ErrUnsupportedConfiguration`, so a caller checking
`errors.Is(err, ErrUnsupportedConfiguration)` gets a refusal either way. But the contract nowhere
states an **error precedence** when two refusal reasons apply, so two conforming implementations may
legitimately return different sentinels for the identical request — and `contract.go:1101-1103` says "two implementations must reject the same requests, or a request accepted by one and refused by the
other would be indistinguishable from a conformance failure." That precedence rule is missing.

This is a normative justification frozen into `contract.go`'s doc comment. T5 rejected revision 1
partly for attaching wrong reasons to right pins; this is the same class and must be fixed before
freezing.

---

## 5. My own re-derivation, shown

Independent, written from scratch for this review from the pinned PROGRESSIVE source
(`.softhouse/reviews/t23-probe/t23_rederive.py`; every step carries its `file:line`). It applies:
dates by step-then-re-anchor to the disbursement seed; `rate/100` under `mc`; interest fraction
`30 × 1 ÷ 360` under `mc`; rate factor `rate × frac × actual ÷ calc` under `mc` then
`setScale(19, HALF_UP)`; `1 + rf` **exact**; `Π(1+rf)` and the `fn` recurrence under `mc`;
`EMI = Π × balance ÷ fn` under `mc` then currency scale; interest-first capped at EMI with principal
as the clamped remainder; and the signed final-period residual accumulated at currency scale. It
deliberately **omits** the EMI re-adjust loop.

**`P-MNT-1M2` — MNT 1,200,000, 12 monthly installments, 21.6 % p.a., start and disbursement
2024-01-01, `(19, HALF_UP)`, MNT minor unit 2.**

Level installment `Π(1+rf) × 1,200,000 ÷ fn` → **112,082.37**; residual `diff` = **+0.03**; final
installment **112,082.40**.

| # | due date | my principal | oracle | my interest | oracle | my balance | oracle | match |
|---|---|---|---|---|---|---|---|---|
| 1 | 2024-02-01 | 90482.37 | 90482.37 | 21600.00 | 21600.00 | 1109517.63 | 1109517.63 | YES |
| 2 | 2024-03-01 | 92111.05 | 92111.05 | 19971.32 | 19971.32 | 1017406.58 | 1017406.58 | YES |
| 3 | 2024-04-01 | 93769.05 | 93769.05 | 18313.32 | 18313.32 | 923637.53 | 923637.53 | YES |
| 4 | 2024-05-01 | 95456.89 | 95456.89 | 16625.48 | 16625.48 | 828180.64 | 828180.64 | YES |
| 5 | 2024-06-01 | 97175.12 | 97175.12 | 14907.25 | 14907.25 | 731005.52 | 731005.52 | YES |
| 6 | 2024-07-01 | 98924.27 | 98924.27 | 13158.10 | 13158.10 | 632081.25 | 632081.25 | YES |
| 7 | 2024-08-01 | 100704.91 | 100704.91 | 11377.46 | 11377.46 | 531376.34 | 531376.34 | YES |
| 8 | 2024-09-01 | 102517.60 | 102517.60 | 9564.77 | 9564.77 | 428858.74 | 428858.74 | YES |
| 9 | 2024-10-01 | 104362.91 | 104362.91 | 7719.46 | 7719.46 | 324495.83 | 324495.83 | YES |
| 10 | 2024-11-01 | 106241.45 | 106241.45 | 5840.92 | 5840.92 | 218254.38 | 218254.38 | YES |
| 11 | 2024-12-01 | 108153.79 | 108153.79 | 3928.58 | 3928.58 | 110100.59 | 110100.59 | YES |
| 12 | 2025-01-01 | 110100.59 | 110100.59 | 1981.81 | 1981.81 | 0.00 | 0.00 | YES |

Total interest mine **144,988.47** / oracle **144,988.47**. Loan term mine **366** / oracle **366**.
Every date, every principal, every interest, every balance identical to the minor unit.

The same model was run against seven more captures:

```
P-00           MATCH   EMI=17.01        diff=-0.01
P-01           MATCH   EMI=5613766.78   diff=0.00
P-02           MATCH   EMI=17.01        diff=-0.01   (seed 31 Jan, month-end re-anchor)
P-02b          MATCH   EMI=17.01        diff=-0.01   (seed 30 Jan)
P-MNT-5M       MATCH   EMI=320221.91    diff=-0.05
P-MNT-1M2      MATCH   EMI=112082.37    diff=0.03
P-MNT-50M      MATCH   EMI=1777663.51   diff=0.04
P-MNT-4M999    MATCH   EMI=320221.84    diff=0.08

ALL 8 RE-DERIVED CAPTURES MATCH THE ORACLE TO THE MINOR UNIT
```

**This is the strongest positive evidence in this review**: the algorithm DEC-1 specifies — the
recurrence not the annuity formula, both rounding senses at the right points, the exact `1 + rf`, the
month-end seed, the signed residual at currency scale — is reproducible from the document alone, and
it is right.

---

## 6. Claims imported from the two fresh audits

Every one I could check, I checked against the primary artefact rather than the audit's prose.

| Imported claim | Verdict |
|---|---|
| Round to the **NEAREST** multiple under the tenant mode, not up (`Money.java:163-171`) | **CORRECT** — `:167` is `divide(inMultiplesOfValue, 0, mc.getRoundingMode()).multiply(inMultiplesOfValue)`; nothing ceils |
| Observed round-down `111,148.35 → 111,100.00`, principal MNT 1,190,000, multiple 100 | **CORRECT** — `T22-pathb-capture-audit.md:260-264`, `:490` |
| Zero guard at `ProgressiveEMICalculator.java:1772-1774` | **CORRECT**, verified in source |
| Tie rule from the tenant-global context via the two-arg `Money.roundToMultiplesOf` (`:159-161`) | **CORRECT** — `safeRoundingForEMI` at `:1771` calls the two-arg overload |
| Last period's total deliberately not a multiple: 112,100.00 ×11, final 111,866.22 | **CORRECT** — `T22:164-165` |
| `FULL_LEAP_YEAR` ≡ the field being unset | **CORRECT** — `DaysInYearType.java:81-86` has no branch for it, `ProgressiveEMICalculator.java:1346-1352` special-cases only `FEB_29_PERIOD_ONLY`; and `t21-probe-oracle.txt` §B3 shows null / FULL_LEAP_YEAR / FEB_29_PERIOD_ONLY all byte-identical through the seam |
| `daysInYearCustomStrategy` inert under `SAME_AS_REPAYMENT_PERIOD` (`:1510-1516`) | **CORRECT** — the monthly/weekly returns at `:1513-1519` never consume `daysInYear` |
| No size threshold: divergence at principal 4.00 on 36 × 16.8 %, absent at 50,000,000 | **CORRECT, and oracle-observed** — `t21-probe-oracle.txt` §C |
| `currency.inMultiplesOf` moves money only at 0 decimal places: 763,994 vs 764,100 | **CORRECT** — `t21-probe-oracle.txt` §B2 |
| Reflective drop of both fields at (19, HALF_UP) | **CORRECT** — `t21-probe-oracle.txt` §A; the "999" figure is `T21-capture-pass3-audit.md:398` |
| HALF_UP 20,925.05 vs HALF_EVEN 20,925.04 on MNT 1,162,502.50 | **CORRECT** — `T22:369-374` |
| Four Path-B captures byte-identical on an `Asia/Ulaanbaatar` / HALF_UP fresh tenant | **CORRECT** — `T22:333-338`, `:378-380` |
| The EMI re-adjust loop "is named as unpinned" | **INSUFFICIENT** — see §6.1 |

### 6.1 P0-1 — the EMI re-adjust loop is live inside the graded domain

**What DEC-1 says.** §4.3: the loop "fires on none of the twelve Run-1 captures… **it is reachable
only outside the graded domain**". `contract.go` mentions it **only** inside the doc comment for
`InstallmentRoundingMultipleMinor` (`:872-880`), a field pinned to `0` in the graded domain, and warns
only that "an implementation that implements the rounding but not the loop will diverge". ADR §9's
"the **Go module** must reproduce …" obligation list **does not mention it at all**.

**What the source says.** `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods` is called at
`ProgressiveEMICalculator.java:749`, inside
`calculateEMIValueAndRateFactorsForDecliningBalanceInterestMethod`, gated on
`onlyOnActualModelShouldApply`, which is `true` when `scheduleModel.isEmpty()` — i.e. on the initial
disbursement of every ordinary loan. It is on the main path, not a corner. Its guard,
`EmiAdjustment.shouldBeAdjusted()` (`EmiAdjustment.java:31-36`), is

```java
double lowerHalfOfRelatedPeriods = Math.floor(numberOfRelatedPeriods() / 2.0);
return lowerHalfOfRelatedPeriods > 0.0 && !emiDifference.isZero()
        && emiDifference.abs().multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods));
```

`Money.copy(double)` (`Money.java:220-222` → `:216-218`) **replaces** the amount; it does not scale
it. So the threshold is a `Money` of amount `floor(n/2)` **currency units** — 3.00 for a 6-period
loan, 18.00 for 36. The guard has **nothing to do with `installmentAmountInMultiplesOf`**: it fires
whenever the final-period residual exceeds `floor(n/2)/100` of a currency unit.

*(Aside, and it matters for the corpus: `.softhouse/capture/out/t21-probe-rederive.py:165` models this
guard as `abs(emi_diff) * 100 > periods[-2]["emi"] * lower_half` — multiplying by the EMI. On an MNT
loan with EMI ≈ 320,000 that threshold is ~10^5 times too large, so that model reports the loop as
never firing, always. Any claim about the loop that rests on that model is unsupported.)*

**What the oracle does.** I put ten requests to the pinned oracle at `(19, HALF_UP)`, all inside the
stated graded domain (one disbursement on the schedule start, `RepaymentEvery` 1, MONTHS, declining
balance, 30/360, no down payment, **`installmentAmountInMultiplesOf` null**, MNT 2 decimals), and
compared each against my no-loop re-derivation:

| principal | n | rate | oracle EMI | no-loop EMI | oracle final | no-loop final | |
|---|---|---|---|---|---|---|---|
| 135,623 | 6 | 7.0 % | **23,067.56** | 23,067.57 | 23,067.59 | 23,067.53 | **diverges** |
| 1,014,632 | 6 | 7.0 % | **172,574.64** | 172,574.63 | 172,574.62 | 172,574.67 | **diverges** |
| 2,345,024 | 6 | 7.0 % | **398,855.60** | 398,855.61 | 398,855.63 | 398,855.57 | **diverges** |
| 167,299 | 6 | 21.6 % | **29,665.91** | 29,665.92 | 29,665.94 | 29,665.88 | **diverges** |
| 64,352 | 12 | 21.6 % | **6,010.61** | 6,010.60 | 6,010.55 | 6,010.68 | **diverges** |
| 1,000 | 18 | 18.5 % | 64.04 | 64.04 | 64.14 | 64.14 | identical |
| 246,489 | 18 | 18.5 % | 15,786.24 | 15,786.24 | 15,786.14 | 15,786.14 | identical |
| 16,838 | 36 | 16.8 % | 598.65 | 598.65 | 598.46 | 598.46 | identical |
| 40,595 | 36 | 16.8 % | **1,443.28** | 1,443.29 | 1,443.47 | 1,443.04 | **diverges** |
| 127,704 | 36 | 16.8 % | **4,540.30** | 4,540.29 | 4,540.06 | 4,540.54 | **diverges** |

**7 of 10.** The loop changes the level installment, and therefore **every period's principal and
interest**, and the totals: on MNT 127,704 / 36 × 16.8 % the oracle's total interest is
**35,746.56** against the no-loop model's **35,746.69** — a 0.13 error, in a document that grades to
the minor unit. On MNT 1,014,632 / 6 × 7.0 % — an entirely ordinary Mongolian retail loan — the
oracle says 172,574.64 and the specification as written yields 172,574.63.

The correlation is exact: my model's guard predicts `True` on all seven divergent cases (and on the
three identical ones the loop was entered and exited without adopting — `:1271` or `:1289`). Raw
observations: `.softhouse/reviews/t23-probe/t23-probe2-output.txt`; comparison:
`t23_compare.py`.

**Why this is P0 and not P1.** DEC-1 §9 is the normative obligation list for the Go module. It is
missing a step that moves money on ordinary loans. §4.3 contains a positively false reachability
claim that would tell a future implementer not to look. None of the twelve captures trips the guard,
so the corpus cannot catch the omission — this is precisely "a port that passes its corpus and is
wrong", the failure the contract exists to prevent. And after ratification, correcting §4.3 and §9
costs a gate.

**A second-order consequence worth stating.** Reproducing the loop in Go means reproducing
`Math.floor(n / 2.0)` and `BigDecimal.valueOf(double)` semantics from `Money.copy(double)`. The
values involved are exact small integers, so no float is *required* in a Go port — but the contract
must say so explicitly, or an implementer will either introduce a float (a non-negotiable violation)
or guess at the threshold.

---

## 7. Citation audit

Mechanically extracted every `File.java:N[-M]` and every bare `:N[-M]` from both artefacts.

- **157 citation occurrences, 101 distinct `(file, range)` pairs, across 13 source files.**
- **101 of 101 distinct ranges resolve** to a real line range in the pinned checkout. I opened and
  read every range that carries a load-bearing claim (about 55 of them); each says what the document
  says it says. No fabricated citation, and none of the four bad citations T5 caught survives.
- **Progressive-vs-cumulative: ZERO misattributions.** Six cited files are in
  `fineract-progressive-loan/` (`ProgressiveEMICalculator`, `RepaymentPeriod`, `EmiAdjustment`,
  `LoanSchedulePlan`, `ProgressiveLoanScheduleGenerator`, and the embeddable test). The seven outside
  it are all genuinely on the progressive path and I checked each:
  `DefaultScheduledDateGenerator` is instantiated by the seam itself
  (`EmbeddableProgressiveLoanScheduleGenerator.java:39-42`); `LoanApplicationTerms` and
  `LoanRepaymentScheduleModelData` are entered from `ProgressiveLoanScheduleGenerator.java:82`;
  `Money`, `MoneyHelper`, `DaysInYearType` are `fineract-core` shared utilities; `LoanProduct` is
  cited *precisely* for the product-validation layer the document says this entry point bypasses.
  **No cumulative-generator file is cited anywhere, and no progressive behaviour is attributed to
  one.**
- **Five dangling bare citations (P1-5).** A bare `` `:N-M` `` inherits the nearest preceding named
  file, and in five places that antecedent is the wrong file. All five *intended* targets exist and
  are correct; the *written* form does not resolve:

  | Where | Written | Resolves to | Intended |
  |---|---|---|---|
  | ADR §4.3, the re-adjust loop | `` `:1258-1308` `` | `RepaymentPeriod.java` (537 lines) | `ProgressiveEMICalculator.java:1258-1308` |
  | ADR §4.7, the zero guard | `` `:1772-1774` `` | `Money.java` (497 lines) | `ProgressiveEMICalculator.java:1772-1774` |
  | ADR §5, `RepaymentEvery` row | `` `:1956-1958` `` | `ProgressiveLoanScheduleGenerator.java` (505 lines) | `ProgressiveEMICalculator.java:1956-1958` |
  | ADR §8 item 5 | `` `:1505-1507` `` | `ProgressiveLoanScheduleGenerator.java` | `ProgressiveEMICalculator.java:1505-1507` |
  | ADR §8 item 5 | `` `:1526-1531` `` | `ProgressiveLoanScheduleGenerator.java` | `ProgressiveEMICalculator.java:1526-1531` |

  Notably these are progressive-file-vs-progressive-file slips, not the recurring
  progressive-vs-cumulative error. But the ADR's own header promises "**every** `file:line` citation
  in this document is to that pinned checkout", and a frozen document should keep that promise.

- **Two counting errors in §2 / §4.5 (P1-6).** `LoanSchedulePlan.java:32-97` declares **ten** fields
  (`periods`, `currency`, `loanTermInDays`, and **seven** `BigDecimal` totals). The ADR says "eight
  aggregate totals" and "eleven oracle response members"; both are one too many, and §4.5 counts
  `loanTermInDays` separately from the eight, so it cannot be the eighth. The "nineteen oracle
  inputs" and "thirteen request fields / seven response fields per row / one top-level field" counts
  are all **correct** — I counted them.

---

## 8. Non-negotiables in the Go artefact — re-run, not trusted

Go is at `/Users/buv/sdk/go` (go1.23.4 darwin/arm64), not on `PATH`.

```
go build ./...        clean
go vet ./...          clean
gofmt -l .            no output
go test ./...         [no test files]
```

**Comment-stripped known-bad scan.** I stripped all `//` comments (the file has no block comments)
and scanned the 703 remaining non-blank lines:

```
grep -nEi 'float32|float64|big\.Float|first_name|last_name|insured|protected|guaranteed|
           FixedZone|\+07|\+08|ojdbc|oracle\.jdbc|mysql|mariadb'   ->  no matches
```

The entire executable surface is 13 request fields, 7 period fields, 1 schedule field, 4 enums and
3 sentinels. Verified by inspection of the stripped file:

- **Money** — `Disbursement.AmountMinor`, `Period.PrincipalMinor`, `Period.InterestMinor`,
  `Period.OutstandingPrincipalMinor`, `GenerateRequest.InstallmentRoundingMultipleMinor` are all
  `int64` minor units. `Currency.MinorUnitDigits int32` with MNT = 2 documented as ISO 4217 numeric
  496. No float anywhere, including intermediates — the `Rounding` doc explicitly forbids
  representing intermediates as floats.
- **Rates** — `Rate{Numerator, Denominator int64}`, exact rational, canonical lowest terms,
  `Denominator > 0`, zero rate = `Rate{0,1}`. Not basis points, not float. The `Rate{1,3}`
  representable-domain limit is stated.
- **Dates** — `CivilDate{Year, Month, Day int32}` plus `TimeZone string` required to be an IANA name;
  fixed offsets rejected with `ErrInvalidRequest`. No `time.Time`, no `FixedZone`, no `+07`/`+08`
  literal in executable code. `Asia/Ulaanbaatar` / `Asia/Hovd` appear only in doc comments, correctly,
  with "neither observes daylight saving time".
- **Names / insurance / rails / DB** — no party identity of any kind; the prohibition on
  `first_name`/`last_name` and on insured/protected/guaranteed language is stated as a rule, not used
  as a string. No payment rail, no vendor, no database.
- **Idempotency-Key** — correctly argued as inapplicable: `Generate` is pure and moves no money.

**Error taxonomy — I executed it rather than reading it.** A temporary probe test (since removed)
compiled against the package:

```
errors.Is(ErrNoDiscriminatingVector, ErrUnsupportedConfiguration)  ==  true    (collapsible)
errors.Is(ErrUnsupportedConfiguration, ErrNoDiscriminatingVector)  ==  false   (distinguishable)
errors.Is(ErrNoDiscriminatingVector, ErrInvalidRequest)            ==  false
errors.Unwrap(ErrNoDiscriminatingVector) == ErrUnsupportedConfiguration
"loanschedule: unsupported: no discriminating vector: loanschedule: unsupported configuration"
```

**The wrapping behaviour is exactly as specified.** The only gap is the missing *precedence* rule when
two refusal reasons apply (§4.2).

**No non-negotiable is violated by either artefact.**

---

## 9. Ratifiability

- **Self-contained: YES.** A ratifier can decide from the ADR alone. Every observation is restated
  with its numbers, every pin with its source lines and its reason, the graded domain in full, the
  corpus in full, the forward-compatibility analysis, the switch mechanism, the backlog, and the
  consequences. It never says "see the review".
- **States the amendment gate: YES.** ADR §1 and `contract.go:18-30`, with three substantive reasons,
  and it correctly preserves cutover / regulatory sign-off / licence facts as hard `user` gates.
- **Does not smuggle a reserved decision: CONFIRMED.** No cutover is proposed (§7 says flipping the
  switch *is* a cutover and a `user` gate); no deposit-taking is implicated; no licence fact is
  asserted; nothing spends money or exposes an endpoint.
- **Does not ask what standing policy already answers: CONFIRMED.** I checked all six of T5 §9's
  reserved items against `gates-proposed-answers.md`: item 1 is now P-2 (agent-decidable); item 2 is
  answered by G-1 §1 (split, not rename) and the contract does split; item 3 by G-1 §2 (option a) and
  the contract reproduces; item 4 by G-1 §4 (keep the enum, refuse the computation) and it does; item
  5 by Buyan's HALF_UP decision, and the ADR pins it; item 6 by G-1 §5 (accept the obligation) and
  §4.4 does; item 7 by G-1 §3 (captured, done). **The document poses no open question to the
  ratifier.** It is decision-shaped throughout, which is what P-2 requires.
- **Discloses its own limits honestly.** §5's two "admissibility facts" — that the eleven
  production-setting captures are audited observations not yet promoted to the vector store, and that
  the Path-B captures are admissible at `(19, HALF_UP)` only on a fresh-tenant re-observation — are
  exactly the disclosures a ratifier needs, and they are volunteered.

---

## 10. Required changes

### P0 — blocks ratification

**P0-1. Record the EMI re-adjust loop as a graded-domain obligation.** (§6.1)
Strike "it is reachable only outside the graded domain" from ADR §4.3 — it is refuted by observation.
State that `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
(`ProgressiveEMICalculator.java:1258-1308`) runs on **every** generation via `:749`, that its guard
(`EmiAdjustment.java:31-36`) compares `|lastEMI − penultimateEMI| × 100` against a `Money` of amount
`floor(n/2)` — note that `Money.copy(double)` at `Money.java:220-222` **replaces** the amount rather
than scaling it — and that it therefore has no dependence on `InstallmentRoundingMultipleMinor`. Add
it to ADR §9's "the **Go module** must reproduce …" list and to `contract.go` somewhere that is not
the doc comment of a field pinned to zero. State whether reproducing `Math.floor(n/2.0)` and
`BigDecimal.valueOf(double)` requires exact-integer arithmetic in Go (it does; say so, so nobody
reaches for a float). Cite the observed divergences: MNT 1,014,632 / 6 × 7.0 % → oracle 172,574.64
vs 172,574.63 without the loop; MNT 127,704 / 36 × 16.8 % → total interest 35,746.56 vs 35,746.69.
Backlog §8 item 3 should be re-scoped from "a vector that forces the loop to iterate" (framed as an
installment-rounding concern) to "vectors that trip the guard inside the graded domain", and the ten
cases in §6.1 are ready-made candidates.

**P0-2. Close the disbursement-window hole in the graded domain, and fix the ordering rule's third
clause.** (§2.3)
Observed: a single disbursement dated on or after the last repayment due date, or before
`ScheduleStartDate`, is **silently discarded** — no disbursement row, no principal, an all-zero
schedule (`ProgressiveLoanScheduleGenerator.java:305-308` with `isMultiDisburseLoan() == false`).
Either add `ScheduleStartDate ≤ Disbursement.Date < the last computed due date` to the graded-domain
predicate on `GenerateRequest` and refuse outside it, or specify the degenerate answer normatively.
Either way, delete or correct the `Schedule` ordering rule's clause "if the row's date is on or after
the last repayment period's `DueDate`, its key sorts after every repayment row", which describes a row
this seam never emits. A widening later, once multi-tranche vectors exist, is behaviour and needs no
amendment — but the current text is a normative statement that observation contradicts.

**P0-3. Correct the `FrequencyYears` justification and add an error-precedence rule.** (§4.2)
Observed: `FrequencyYears` throws only on the 30/360 arm; under `DayCountActualActual` the oracle
returns a complete 3-period schedule (term 1096 days, total interest 551,982.62). Rewrite ADR §4.10
and `contract.go`'s `FrequencyYears` doc to say "the oracle throws on the fixed-30/360 arm
(`ProgressiveEMICalculator.java:1536` → `:1602-1610`); the ACTUAL arm at `:1534-1535` never reaches
that dispatch". Then state which sentinel wins when a request is refusable for more than one reason —
without it, two conforming implementations may return different errors for the identical request,
against `contract.go:1101-1103`'s own equal-rejection requirement.

### P1 — fix after ratification (none blocks the freeze)

**P1-1.** "Seventeen per-period divergences" → all **18** repayment rows of `D-01` vs `D-01-p19`
differ (17 in `totalOutstandingBalance`, 13 in `balance`, 2 in `principal`/`interest`). ADR §4.1,
`contract.go` `SignificantDigits` doc, and `gates-proposed-answers.md` G-1 §3 all carry the inherited
figure.

**P1-2.** ADR §8 item 7's "`Money.java:134-148`, `:220-222` … traps for a harness author, **not parts
of the calculation**" is false for `:220-222`: `Money.copy(double)` is called from
`EmiAdjustment.java:35` and `ProgressiveEMICalculator.java:1788`, both on the live re-adjust path.

**P1-3.** Specify the **mechanism** for widening the graded domain: who records it, where, and on
what evidence (an admissible discriminating vector in the store, a dated entry naming it, and the same
independent-review bar). Without it, "widening is not an amendment" is an unbounded licence.

**P1-4.** ADR §8 item 2 should record that Path-B products run with
`interestCalculationPeriodMethod = SAME_AS_REPAYMENT_PERIOD`, which un-short-circuits
`ProgressiveEMICalculator.java:128-133`; the branch stays inert only while
`allowPartialPeriodInterestCalculation` is also `true` there. A Path-B product with it `false` shifts
the disbursement's effective due date and its captures are not comparable with Path-A vectors.

**P1-5.** Five dangling bare `` `:N-M` `` citations whose nearest antecedent file is wrong (§7 table).
All five intended targets are correct; only the written form fails to resolve.

**P1-6.** `LoanSchedulePlan` has **ten** members and **seven** `BigDecimal` totals; ADR §2 and §4.5
say eleven and eight.

**P1-7.** §3.2's conclusion "inside the graded domain, the seam's blind spot is empty: every
admissible request is faithfully rendered, and a Path-A capture grades everything the request
carries" should be narrowed to what is proven — that the two dropped components are pinned inert, so
*those two* are not a blind spot. Faithful rendering does not imply full grading (P0-1) and does not
imply a non-degenerate answer (P0-2).

---

## 11. What ratifying this would freeze that I am not certain about

Not empty. Five things, ordered by how much they would cost if wrong.

1. **The corpus is twelve captures, and I have shown it is not dense enough to grade its own graded
   domain.** P0-1 and P0-2 are two holes I found by looking; I do not claim they are the last two.
   The `36 × 16.8 %` shape shows precision sensitivity at principal 4 and none at 50,000,000, so the
   input space is not smooth and sampling gives weak coverage guarantees. Freezing the contract is
   safe (it is a shape); believing the graded domain is *graded* is not yet.

2. **`DayCountActualActual` and the cross-year partial-period arm are un-re-derived.** The ADR says so
   (§8 item 5), and my re-derivation covers only the 30/360 arm. Nobody in this program has yet
   reproduced `ProgressiveEMICalculator.java:1526-1531` from source. That arm also decides whether
   `daysInYearCustomStrategy` needs a contract field — which the ADR correctly calls an amendment.
   Ratifying does not freeze the answer, but it does freeze the *shape* that answer will have to fit
   into.

3. **`Currency.MinorUnitDigits` as a field rather than a constant.** It exists because the shipped
   fixtures are USD, and only `2` is graded. A 0-decimal currency switches on a second rounding
   channel that was measured to move money. The field is right; I am not certain the graded domain
   will ever widen to justify it, and an unexercised field is surface.

4. **Charges/fees/penalties.** §6.1 is honest that this is the largest unmitigated forward risk and
   that the likely resolution is composition rather than amending `Period`. I have no evidence either
   way, and the argument that omitting a total-due column makes the addition purely additive is
   sound — but it is an argument, not an observation.

5. **The corpus is not yet in the vector store.** §5 discloses this. Eleven audited observations that
   reproduce and re-derive are strong evidence, but "the contract is frozen against the corpus" is
   currently a claim about files in `.softhouse/capture/out/`, not about promoted vectors with
   attestation blocks. Nothing about that is hidden; it is simply outstanding, and ADR §8 items 1 and
   2 are the right place for it.

**What I am confident about:** the shape, the two-domain structure, the split of `Rounding` into two
senses, the month-end rule, the window-key ordering (minus its third clause), the signed residual, the
six pins and their reasons, the day-count mapping, the error taxonomy's wrapping behaviour, and the
absence of any non-negotiable violation. Eight independent re-derivations matching to the minor unit
is the reason.

---

## Artefacts produced by this review

All committed under `.softhouse/reviews/t23-probe/`:

| File | What it is |
|---|---|
| `T23Probe.java` | Oracle probe: disbursement-window cases, `FrequencyYears` on both arms, small-principal shapes |
| `t23-probe-output.txt` | Its raw observed output (pinned image, seam verified byte-identical) |
| `T23Probe2.java` | Oracle probe: the ten EMI-re-adjust candidates at `(19, HALF_UP)` |
| `t23-probe2-output.txt` | Its raw observed output |
| `t23_rederive.py` | My from-scratch re-derivation of the progressive algorithm, without the re-adjust loop |
| `t23_scan_readjust.py` | Model-located search for graded-domain inputs that trip the re-adjust guard |
| `t23_compare.py` | Diff of oracle output against the no-loop model — the P0-1 evidence |
| `EmbeddableProgressiveLoanScheduleGenerator.java` | Seam class copy, `diff`-verified identical to the pinned original |

Reproduction: the `docker run` recipe in `.softhouse/capture/README-pass2.md`, substituting
`T23Probe.java` / `T23Probe2.java`.
