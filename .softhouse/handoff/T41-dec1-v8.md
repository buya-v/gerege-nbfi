# T41 — DEC-1 revision 7 → revision 8, the ratification candidate

**Task:** T41, branch `softhouse/T41-dec1-v8`, worker `spec_writer`.
**Fire:** local `20260819-080001`, Buyan's Mac.
**Base:** `main` at `d42ccfc` (rebased onto it mid-task, so this branch is a strict superset).
**Branch check performed first, as briefed:** `git branch -a --list 'softhouse/T41*'` returned
**nothing** — no prior T41 work existed on any branch, local or remote, so nothing was duplicated
and nothing was rescued. The branch was created fresh.

> **NO LIVE ORACLE WAS CONTACTED BY THIS TASK.** No container was started, no Gradle ran, no HTTP
> request was issued. Every observation cited is quoted from a capture already committed on `main`,
> with its capture id. Every `file:line` was re-opened by this task in the pinned checkout
> `426a23544e8426a38ae43ae404670a0a7e85b9eb` — 52 of them, machine-checked (§7 below).

## Verdict

**DONE.** DEC-1 is at **revision 8**, the ratification candidate. All four required findings are
applied plus **two more that revision 8's own spec-check probe produced**. The from-text model
reproduces **4,578 cells** across four corpora with zero mismatches and discriminates every known
corpus-invisible wrong reading plus the three new ones.

**No gate is needed. No type, field set, enum member or graded-domain predicate moves** —
machine-verified: §3.1's graded-domain code block is **byte-identical** to revision 7's, and
`contract.go`'s 73 declaration lines are **identical line for line**; every added line in
`contract.go` is a comment (0 non-comment added lines).

**I did not ratify it.** That is the driver's call.

---

## 1. What changed, per finding

### T39 N-1 — the P0's framing, narrowed further than the brief asked (§4.1.1, §4.3.2, §9, `contract.go`)

Revision 7 said "two arguments differ" and scoped the days-in-month argument's inertness to the
graded domain. The brief asked me to say the second argument *would* differ outside the graded
domain. **Re-derived from source, it would not, and revision 8 says so** — this is a correction to
the brief's premise, in DEC-1's favour:

- `daysInMonth` is declared once [`ProgressiveEMICalculator.java:1508`] and consumed at exactly one
  place, `:1537`.
- `:1537` sits inside the `case DAYS_30 ->` arm at `:1536` of the `switch (daysInMonthType)` at
  `:1533-1539` — **precisely the branch in which `:1508`'s ternary yields `BigDecimal.valueOf(30)`**,
  the same literal the interest call site passes at `:1413`.
- On the other two enum values neither call site is reached with a days-in-month argument at all:
  under `ACTUAL` the recurrence takes `:1534-1535` and the interest site `:1400-1402`; under
  `INVALID` [`DaysInMonthType.java:34`] the recurrence throws at `:1538` and the interest site at
  `:1415-1416`.
- Confirmed by grep: `calculateRateFactorPerPeriodBasedOnRepaymentFrequency` has exactly two call
  sites [`:1412`, `:1536`] and `daysInMonth` exactly one use.

So **the days-in-month argument is 30 at both call sites on every path either is reachable on**,
and there is exactly **one** numeric difference between them — the multiplier. Revision 8 also
records a divergence from T39: T39's prose locates the assignment at `:1509` while its own
`[VERIFIED]` tag says `:1508`; **`:1508` is correct**, re-read here.

### T39 N-2 — item 3e needs two vectors; both are captured (§4.1.1, §4.3.1, §4.3.2, §5, §6, §8, §9, `contract.go`)

- **`periodRatio` is now OBSERVED**, not only specified from source: 415 of 415 discriminating cells
  to `periodRatio`, 0 of 415 to `RepaymentEvery`, across 8 drift shapes; the `periodRatio` reading
  reproduces all 1,239 cells of all 15 parity-setting T39 captures [VERIFIED:
  `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. Revision 7's re-derived worst
  case — **MNT 398,967.73** — is observed to the cent [VERIFIED: capture `T39-P0-D`]. Three further
  re-derived properties became observations: no size threshold (MNT **100** separates on 27 cells,
  `6.41` observed against `6.21` — `T39-P0-F`); not a January/leap/31-day artefact (`T39-P0-G`,
  `T39-P0-H`, `T39-P0-E`); and the **due dates move**, `loanTermInDays` **185** not 182
  (`T39-P0-A`).
- **§8 item 3e SPLITS into 3e (drift) and 3f (month-end special case)**, both marked **CAPTURED,
  NOT YET PROMOTED** with capture ids, exactly as revision 7 marks 3–3d. **The binding widens from
  six vectors to SEVEN.**
- The split is justified by measurement, not style: over 51,729 same-month pairs × 3 terms the
  special case fires on **210** and on **0 of those 210** does `ScheduleStartDate ≠
  Disbursement.Date`. On all 15 captured shapes exactly one of the two questions has any
  disagreeing cells. (That sweep is T39's re-derivation with uncommitted raw output — tagged
  `[UNVERIFIED as a committed artefact]`; the disjointness it asserts is
  `[VERIFIED: analysis/discriminate-output.txt]` on the 15 shapes.)
- §4.1.1 step B now states the month-end special case **normatively and literally**, with the
  predicate spelled out [`:1426-1436`, predicate `:1432`, effect `:1433`], as T39's follow-up 1
  asked.

### T39 N-3 — the ambient `MathContext`, and the mechanism T39 could not supply (new §4.1.2, §4.1, §5, §8, §9, `contract.go`)

Every §4.1 sentence resting on the **ambient** `MoneyHelper` reading is re-scoped. New **§4.1.2**
states the rule, what the ambient reading *is* still evidence of, and a falsification test T42 can
run.

**This task added the mechanism, re-derived from source, and it explains T39's observation exactly:**

- `Money` holds its own `MathContext` field [`Money.java:32`], assigned in the constructor at `:42`
  **before** the currency-scale `setScale` at `:52` runs.
- `getMc()` is an **instance** method: `return mc != null ? mc : MoneyHelper.getMathContext();`
  [`Money.java:494-496`]. It is the ambient context **only on the null branch**.
- So `:52` reads the **threaded** mode whenever one was threaded. Revision 7 cited `:52` among the
  *tenant-global* sources; **that was the imprecision**, and it is what made N-3 look like a
  contradiction rather than a prediction.
- The ambient context is reached only where none is threaded: `Money.java:102-104`, `:114-116`,
  `:118-120`, `:150-157`, `:159-161`, `:163-170` (the two-arg `Money.of` at `:169`), `:372-378`
  (at `:377`) — **every one on the installment-multiple or `multipliedBy(double)` path, which the
  graded domain excludes.**

**Not overcorrected.** §4.1.2 states four things the ambient reading is still evidence of: the
tenant configuration; that the run would not throw [`MoneyHelper.java:74-82`]; **the arithmetic on
Path B**, where nothing threads a context (which is why §4.1's HALF_UP/HALF_EVEN pair and T36/T40's
canary are real arithmetic evidence *there*); and `PRECISION = 19` as a property of the deployed
binary [`MoneyHelper.java:35`]. §4.1's adapter obligation is **re-justified**: it does not rest on
the ambient mode changing the answer (observation says it does not), it rests on the **throw**.

**The falsification test, stated for T42** (whose results I do not have): P1 an ambient-only change
moves no in-graded-domain Path-A cell (*observed on 16 for the mode; not tested for the ambient
precision* — `[UNVERIFIED beyond those 16]`); P2 a threaded change moves cells (*observed 15 of
16*); **P3 on Path B an ambient-only change DOES move money — supported only indirectly, never by a
controlled Path-B negative test on a schedule, `[UNVERIFIED]`, and this is the cheapest gap left**;
P4 no in-graded-domain Path-A call site reaches an ambient `Money` construction (*re-derived above*).
**One counter-example falsifies §4.1.2 and every §4.1 attestation sentence must then be re-scoped
again.**

### T40 — charges (new §4.5.1, §4.3.2 M4, §4.5, §6.1, §8 items 1 and 9, §9, `contract.go`)

**Decision C-1 — `totalRepaymentExpected` is NOT carried.** ENGINEERING/PRODUCT, `chosen_by: agent`,
decided here per CLAUDE.md § Answering gates, not raised as a gate.

*Mechanism re-derived by this task, not read back:* `applyChargesForCurrentPeriod`'s body is exactly
`addLoanCharges`, `addTotalFeeChargesCharged`, `addTotalPenaltyChargesCharged` and nothing else
[VERIFIED: `ProgressiveLoanScheduleGenerator.java:367-382`, re-opened and read in full]; the running
total is seeded with disbursement charges alone [`LoanScheduleParams.java:211`, `:246`], accumulates
principal + interest per period [`:137`], and the only later charge contribution is
`updatePeriodsWithCharges` [`:486`], which serves the two separated types. **The cumulative
generator does the opposite** [VERIFIED: `AbstractCumulativeLoanScheduleGenerator.java:504`].

*Reasoning, in the order that decides it:* (1) §3.3 rule 4 — inside the graded domain there is no
charge input, so the field reduces to `Σ(PrincipalMinor + InterestMinor)` and is **derivable**;
(2) it has **no single meaning** across two generators, and a field whose value depends on which
implementation answered is the opposite of a parity boundary; (3) it is exactly the **silent
meaning-change** §6.1 was shaped to avoid — equal to the row sum today, not equal the moment charges
exist, with nothing breaking a compile; (4) the `totalOutstandingAmount` precedent applies with more
force, that field being merely uninformative while this one is informative-looking and **wrong**.

*Which generator's semantics the contract specifies, since the question must be answered:* **the
PROGRESSIVE one**, unconditionally, as every citation in the document already is. If a later
amendment carries the field, it carries the progressive reading, says so on the field, and is
captured against that generator.

*Alternative rejected:* carry `TotalRepaymentExpectedMinor` and specify it as the progressive value.
Rejected — it buys contract surface (a field, a later gate, a vector-set invalidation) to express a
quantity that is derivable today, disputed between two generators, and destined to disagree with its
own rows tomorrow.

*Obligations added (§9):* the adapter must **discard** it; **no adapter, harness or conformance check
may assert it equals the sum of the rows** — that assertion passes today only because the graded
domain has no charges, and the day it fails it will be wrong about the **oracle**, not the port
(observed: C5 fails on **15 of 21**); a caller wanting a total sums the rows.

**Decision C-2 — a silently-dropped charge is REFUSED, never reproduced.** ENGINEERING,
`chosen_by: agent`.

Two paths return HTTP 200 and a response **byte-identical to the zero-charge control**: a charge
dated after the final due date (one-sided guard, [`LoanChargeValidator.java:59-67`, predicate
`:61`]) and a percent-of-interest specified-due-date charge on the disbursement date (stale
`isFirstPeriod()`, [`LoanScheduleParams.java:533-535`] versus
[`ProgressiveLoanScheduleGenerator.java:143`]) — while an identical **flat** charge on that same
date pays 9,000.00.

*Why refuse, given §4.6 decided the opposite question the opposite way:* §4.6's argument turns on
the oracle's answer **carrying information about the input**. Here it provably does not — the
response is byte-identical to the no-charge response, so there is no cell in which two
implementations could be seen to agree or disagree about the charge, and nothing to shadow-compare.
**§3.1 and §4.6 already drew exactly this line once**, refusing a disbursement the seam silently
discards, with `ErrNoDiscriminatingVector`. Two further reasons, each sufficient: a schedule that
omits a fee the caller asked to charge is a money-losing **silent wrong answer**; and a borrower
charged a fee that never appears on the schedule is a regulatory exposure.

*Alternative rejected:* reproduce the drop for bug-for-bug parity. Rejected — bug-for-bug parity is
meaningful only where a vector can witness it, and **no vector can witness this one**, so
reproducing it is indistinguishable, forever, from not implementing it.

*Scope, stated so it cannot be read as a widening:* `GenerateRequest` carries **no charge field**, so
neither shape is expressible today. C-2 is a **forward disposition** binding on whatever admits
charges, **not a predicate added to §3.1**.

**M4 — the fourth date-membership rule (§4.3.2, §9, `contract.go`).** Added to the same one-place
reconciliation, with **which rule governs which field** stated explicitly. My re-derivation sharpens
T40's framing: M4 shares **M1's predicate function**
[`LoanRepaymentScheduleProcessingWrapper.java:251-254`], reached via `LoanCharge.isDueInPeriod`
[`LoanCharge.java:371-373`, `ProgressiveLoanScheduleGenerator.java:400-403`]. **What makes it a
different rule is the source of the "is first" flag**: M1 passes the period's own *structural*
`isFirstRepaymentPeriod()` = `previous == null`
[`ProgressiveLoanInterestScheduleModel.java:243`, `RepaymentPeriod.java:449-451`]; M4 passes the
*mutable counter* `LoanScheduleParams.isFirstPeriod()` = `1 == instalmentNumber`
[`LoanScheduleParams.java:533-535`]. Inside the main loop the counter is correct (charge at `:140`,
increment at `:143`); on the separated path `updatePeriodsWithCharges` runs at `:154`, after the loop
at `:116-145`, so the flag is **false for every period including period 1** [`:479`, `:483`] and M4
degenerates. **That staleness is the whole of C-2b.**

**Charges sit alongside the EMI — recorded as observed.** §4.5 and §6.1 upgraded from re-derivation
to observation: across 21 charge-bearing captures the principal split, interest, outstanding
principal and level installment are cell-for-cell identical to the zero-charge control
[VERIFIED: `.softhouse/capture/charges/out/INVARIANTS.md`, C8/C9 PASS 21/21].

**Blind spots recorded** in §4.5.1 and new §8 item 9, in the same place §8 item 1 records the
others: `OVERDUE_INSTALLMENT` (the most operationally important penalty type, entirely ungraded),
tranche charges, `minCap`/`maxCap`, the **cumulative generator** (C-1's premise is observed only on
the progressive side; the cumulative side is `[UNVERIFIED by observation]`), waiver/payment,
half-cent-tie charge arithmetic, and the standing fact that **Path A can never grade a charge**.

---

## 2. Findings this task's own probe produced

A probe that finds nothing has not been run. Both were found by the spec-check, in revision 8's own
draft, and both are now fixed in the document.

**F-1 — §4.1.1 step B's `k` function was under-specified, and the under-specification is invisible.**
"Whole months, truncated toward zero" names **two** functions:

- `ChronoUnit.MONTHS.between`'s **packed** rule — `packed = (year×12 + month−1)×32 + day`,
  `k = (p₂−p₁)/32` truncated — which is what `DateUtils.getExactDifference` resolves to
  [VERIFIED: `DateUtils.java:308-317`, `getExactDifference` → `getDifference` →
  `unit.between(first, second)`]; and
- "the largest `k` with seed + k months ≤ FromDate".

They differ **exactly** when `plusMonths` would have clamped — `MONTHS.between(2024-01-31,
2024-02-29)` is **0** packed and **1** clamped-step — which is **exactly** the condition the
month-end special case tests. So they coincide *while the special case is present* and diverge the
instant it is dropped. **This task's first transcription used the clamped-step reading, reproduced
all 4,578 cells, and reported the special case as inert** — a wrong reading that passes the entire
corpus, the sixth of its kind in this program. Step B now pins the packed rule with its citation and
states that a port must implement the packed rule **with** the special case or the clamped-step rule
**without** it; the packed rule minus the special case is the combination a careless port lands on
and it double-charges alternate periods. The JDK packing formula itself is
`[UNVERIFIED as a file:line in this checkout]`; **which rule is in force is settled by observation**,
because the special case is load-bearing only under the packed rule and T39 observed it load-bearing
116 of 116.

**F-2 — the pre-T39 corpus was never blind to the month-end special case.** The omitted reading also
fails **3 of the 21 pre-T39 production-setting captures** — `P-02`, `P-02b` and `T37-3b-2` — as well
as T39's four. §5 credits `P-02`/`P-02b` with grading §4.2's *re-anchor*; they grade §4.1.1 step B's
special case too, which no previous revision measured. So **seven** committed captures separate item
3f, more than any other binding item, **and it is still undischarged because none is promoted** —
the clearest available statement of what §8 item 1 is for.

Two smaller measurements, folded into §4.3.1's discrimination table: the textbook
`balance × rateFactor` reading also fails `T39-ME-A`; and the M3-where-M1 collapse remains **inert on
all 36** captures (21 + 15), extending T38's measurement.

---

## 3. The spec-check probe — comparison shape stated

`.softhouse/reviews/t41-probe/t41_model.py` transcribes revision 8 from the document text alone —
§2.1, §4.1, §4.1.1 (including `periodRatio`, the seed, step B and the walk), §4.1.2, §4.2, §4.3,
§4.3.1, §4.3.2 (three operations, the membership rules, steps 4a/4b), §4.5 — in exact `Decimal` and
integer minor units with **no float anywhere**; capture files are loaded with `parse_float=Decimal`.
Disclosed rather than hidden, exactly as T38 disclosed the same about T34: the helper conventions and
capture plumbing follow T38's so the two models are cell-comparable; every money rule was
re-transcribed here, and F-1 is the proof that this was a second independent reading and not a copy —
T38's model already had the packed rule and mine did not.

`t41_validate.py` — **4,578 cells, zero mismatches** [`t41-validate-output.txt`]:

| check | corpus | cells compared | result |
|---|---|---|---|
| A1 | the 13 committed observation triples | 39 (level, final, total interest) | **13 of 13** |
| A2 | 11 Path-A pass-3 captures at (19, HALF_UP) | 712 — fromDate, dueDate, principal, interest, balance, total per row; + loanTermInDays, totalInterest | **11 of 11** |
| A3 | 10 T37 binding captures | 776 — same cells | **10 of 10** |
| **A4** | **15 parity-setting T39 captures** | **1,224** — fromDate, dueDate, principal, interest, **fee, penalty**, balance, total, **totalOutstandingBalance** per row; + loanTermInDays, totalDisbursed, totalInterest, totalRepayment, and the disbursement row's published columns | **15 of 15** |
| **A5** | **21 T40 charge captures, schedule core** | **1,827** — fromDate, dueDate, principalOriginalDue, principalDue, interestDue, principalLoanBalanceOutstanding, totalInstallmentAmountForPeriod per row; + loanTermInDays, totalPrincipalExpected, totalInterestCharged | **21 of 21** |

Captures whose **threaded** context is not (19, HALF_UP) are skipped and named — `P-CAL`, `T37-CAL`,
`T39-CAL` (§4.1.2, made executable as `assert_threaded_context`).

**A5 is the executable form of C-1/C-2's premise:** a model that computes **no charge at all**
reproduces the principal split, the interest, the outstanding principal and the level installment of
twenty-one charge-bearing schedules exactly. **A4 reproduced `totalOutstandingBalance`**, a derived
aggregate the contract declines to carry, from the rows alone on all 15 captures — a direct test of
§4.5's derivability argument on a column no earlier probe of this document ever compared.

`t41_discriminate.py` — **does revision 8 still tell the wrong answer from the right one?**
[`t41-discriminate-output.txt`]

| wrong reading | fails, of the 21 pre-T39 | fails, of T39's 15 | first witness |
|---|---|---|---|
| ratio-is-always-1 (P0-T32-1) | 12 | 15 | `P-01` `R1.balance` |
| textbook `balance × rateFactor` (P0-T29-2) | 2 | **1** | `T37-3b` `R6.interest` |
| `n = NumberOfRepayments` (P0-T29-1) | 2 | 0 | `T37-3c` `R2.balance` |
| whole-principal pre-disbursement row (P0-T37-1) | 3 | 0 | `P-03` `R1.balance` |
| EMI loop absent (item 3) | 6 | 8 | `T37-3-A` `R1.balance` |
| loop without the adoption test (item 3a) | 1 | 0 | `T37-3a` `R1.balance` |
| **`RepaymentEvery` instead of `periodRatio` (P0-T34-1)** | **0 — that corpus was blind** | **8** | `T39-P0-A` `R1.balance` |
| **month-end special case omitted (T39 N-2)** | **3** (F-2) | **4** | `P-02` `R1.balance` |
| M3 reused where M1 belongs | 0 | 0 | **none — still inert on all 36** |

The three readings revision 8 must newly separate, tested against the capture artefacts directly
because they are claims about the **oracle**, not model switches:

- **N1, ambient-vs-threaded `MathContext`** — re-measured from T39's committed negative runs, every
  published cell of every row: forcing the **ambient** tenant mode to DOWN moves **0 of 16** capture
  blocks (0 cells); forcing the **threaded** mode moves **15 of 16** (**494 cells**). The reading
  "the ambient `MoneyHelper` context is the arithmetic in force on Path A" is **REFUTED**.
- **N2, charges-inside-the-EMI** — of 21 charge captures, **19 carry a charge that landed somewhere**
  (the two that do not are exactly `FC-17` and `FC-20`, C-2's two silent-loss paths, independently
  re-confirmed here) and **0 moved any of the four core schedule cells**. **REFUTED.**
- **N3, `totalRepaymentExpected` == Σ period totals** — **FAILS on 15 of 21**. **REFUTED**, which is
  decision C-1's premise.

---

## 4. Leak grep

`.softhouse/reviews/t41-probe/leakgrep.py`, seven patterns × two files
[`t41-leakgrep-output.txt`]. **Two hits, both judged correct and left:**

- `docs/…:27` — the **revision-7** history entry saying its binding widened "from five vectors to
  six". That is history and correctly preserves what revision 7 said.
- `docs/…:20` — my own **revision-8** entry, which *quotes* T37's phrase "the `MathContext` actually
  in force" in order to correct it.

Everything else: 0 hits. Also checked by hand and machine: 44 `[VERIFIED:]` tags, **0 containing a
hedge**; no markdown table malformed by this task (the one flagged row is `` `n = |related|` `` in a
header, pre-existing on `main` and unchanged).

---

## 5. What I deliberately did NOT change

- **The protected blocks.** T38 pass 2 re-ran all seven committed probes byte-identically and
  re-opened every cited `file:line`. I changed no byte of the EMI-loop pseudocode, the residual
  rule, §4.3.2's steps 1–5, the `periodRatio` walk, the segmentation table or the worked examples.
- **§4.3.2's strictly-inside worked table stays a re-derivation** and is not overwritten with
  `T37-3d`'s observed figures — T37's F-2, revision 7's deliberate choice, unchanged.
- **§3.1's graded-domain block** — byte-identical, machine-verified.
- **No capture was promoted.** All seven binding shapes are captured and all seven separate; the
  promotion step is §8 item 1 and it is gated on this document.
- **Revision 1–7 history entries** are untouched; they record what those revisions said.
- **The `RepaymentEvery` field doc in `contract.go`** — re-read and still accurate.

---

## 6. Where the binding stands

**Seven vectors: 3, 3a, 3b, 3c, 3d, 3e, 3f. All seven are now CAPTURED and all seven SEPARATE.**
Not one is promoted. So the binding is **one promotion decision away from dischargeable**, and that
decision is gated on this document being ratified — which is the loop revision 8 exists to let the
driver close. **Captured is not promoted, and promoted is not cut over.**

---

## 7. Citation audit

All **52** `file:line` citations added or changed by this task were machine-checked against the
pinned checkout by opening the exact line and matching an expected token — `ProgressiveEMICalculator`
(`:1400`, `:1412`, `:1413`, `:1415`, `:1432`, `:1433`, `:1435`, `:1457`, `:1508`, `:1536`, `:1537`,
`:1538`), `DaysInMonthType` (`:34`, `:71`), `DateUtils` (`:308`, `:312`, `:315`), `Money` (`:32`,
`:42`, `:52`, `:114`, `:118`, `:169`, `:377`, `:494`, `:495`), `MoneyHelper` (`:35`, `:91`),
`ProgressiveLoanScheduleGenerator` (`:137`, `:140`, `:143`, `:154`, `:367`, `:374`, `:377`, `:403`,
`:479`, `:483`, `:486`, `:492`), `AbstractCumulativeLoanScheduleGenerator` (`:504`),
`LoanScheduleParams` (`:211`, `:246`, `:533`, `:534`), `LoanCharge` (`:371`), `LoanChargeValidator`
(`:61`), `LoanRepaymentScheduleProcessingWrapper` (`:251`, `:252`),
`ProgressiveLoanInterestScheduleModel` (`:243`), `RepaymentPeriod` (`:449`, `:450`). **52 checked,
0 mismatches.**

---

## 8. Unverified / limits

- **`go build ./...` and `go test ./...` were NOT run — no Go toolchain exists in this environment.**
  Mitigation: the `contract.go` diff is **comments only** (0 non-comment added lines, machine-checked)
  and its 73 declaration lines are identical to `main`'s line for line, so no compile-visible change
  was made. This should still be re-run by UAT.
- **Java's `LocalDate.monthsUntil` packing** is not a `file:line` in the pinned checkout —
  `[UNVERIFIED in this checkout]`. Which rule is in force is settled by observation (F-1).
- **The 51,729-pair disjointness sweep** is T39's re-derivation with uncommitted raw output —
  `[UNVERIFIED as a committed artefact]`; the conclusion is corroborated by 15 captured shapes.
- **P3 of §4.1.2's falsification test** — that an ambient-only change *does* move money on Path B —
  is supported only indirectly and has never been run as a controlled Path-B negative test.
  `[UNVERIFIED]` **This is the cheapest gap left in §4.1.2 and T42 should close it.**
- **C-1's premise on the cumulative generator** is re-derived from source only
  [`AbstractCumulativeLoanScheduleGenerator.java:504`]; no cumulative capture exists.
  `[UNVERIFIED by observation]`
- **The ambient PRECISION** was never negative-tested; T39 tested the ambient *mode* and the
  *threaded* precision. `[UNVERIFIED]`
- **Generalisation.** 4,578 cells grade 60 shapes. They license no claim about an un-sampled tuple.
- **Whether revision 8 is complete.** Revision 7's model was 21-of-21 clean before T39 attacked it;
  my own probe found two things in my own draft. **Assume the next review finds something.**

---

## 9. For the reviewer

1. **Attack §4.1.2 first.** It is the newest reasoning, it re-scopes claims three earlier tasks made,
   and its P3 is unverified. If T42 finds an in-graded-domain Path-A cell that moves under an
   ambient-only change, §4.1.2 is falsified and §4.1 must be re-scoped again.
2. **Attack F-1's resolution.** I chose the packed rule on the strength of an *indirect* argument
   (the special case is load-bearing only under it, and it is observed load-bearing). A reviewer with
   a JVM could settle it directly in one line.
3. **Attack C-2's sentinel.** I said the refusal takes `ErrNoDiscriminatingVector` by analogy with
   §3.1, subject to §4.11's precedence — but no charge field exists, so the analogy is the whole
   argument. If it is wrong, the disposition (refuse) survives and only the sentinel moves.
4. **Attack A5's request reconstruction.** A5 assumes every `FC-nn` shares the committed B-01
   baseline with only a `charges` array injected, which is what T40 states and its `bin/mkcalcs.sh`
   does; I did not re-derive the injection. If any FC request differs otherwise, A5's 1,827 cells
   are grading the wrong request.
5. **The M3-where-M1 collapse is inert on 36 captures and still normative.** Nothing tests it under
   multi-tranche, an interest pause or a rate change. `[UNVERIFIED outside the graded domain]`
