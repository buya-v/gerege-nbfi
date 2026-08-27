# Driver re-derivation — local fire 20260820-140000

Written by the `/softhouse-program` driver **before** T66's worker reported, so that this fire's
ruling on T66 rests on the driver's own reading of the pinned source and the committed corpus
rather than on whose report reads better. Pattern P-6 (the driver re-derives) and P-13 (a written
rule is a deliverable and can be false even when the code is right).

> "The oracle" here means the Fineract reference implementation at pinned commit `426a23544`.
> Oracle Database is a prohibited product in this program and appears nowhere in this stack.

## What T66 was dispatched to settle

T63 reported two items **UNPROVEN** rather than as defects, and T69 declined to assert a third
reason for one of them, marking it `[UNVERIFIED]` in `emi.go` and naming T66 as the settling task.
Item 1: `futureUnrecognizedInterest` (`ProgressiveEMICalculator.java:1217`, `:1243-1251`,
`:1805-1814`) is not ported, and `applyFinalPeriodResidual` (`emi.go:824-880`) has no counterpart.

## The chain the driver read out of the source

Each step cites the pinned source. Steps 1-3 the driver considers **established**; step 4 is the
open one and is what T66 must settle.

1. `isFullyPaid()` is `getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest().isEqualTo(getTotalPaidAmount())`
   [VERIFIED: `RepaymentPeriod.java:371-373`].
2. The capture seam is a **pure generation** call — `EmbeddableProgressiveLoanScheduleGenerator`
   constructs `ProgressiveEMICalculator` and calls `ProgressiveLoanScheduleGenerator.generate(mc,
   modelData)` [VERIFIED: `.softhouse/capture/src/EmbeddableProgressiveLoanScheduleGenerator.java:40-46`].
   There are no repayment transactions, so `totalPaidAmount == 0` on every period, and a period is
   therefore `isFullyPaid()` **iff its EMI plus credited amounts plus FUI is exactly zero**. A
   **zero-EMI period is vacuously "fully paid" although nothing was paid.**
3. The selector is `.filter(rp -> !rp.isFullyPaid()).reduce((first, second) -> second)` — the last
   period that is not fully paid [VERIFIED: `ProgressiveEMICalculator.java:1176-1177`]. By step 2,
   on a schedule with a zero-EMI tail this returns the last **non-zero-EMI** period, and periods
   exist strictly after it. The fallback at `:1178-1181` does not rescue this, because it only fires
   when the first filter yields **empty**.
   **This is not hypothetical.** `T64-ZP-B-early-payoff-dead-rows-mnt0pt28-55x21pt6pct.json` has 55
   REPAYMENT rows of which installments **16-55 (40 rows) are zero-EMI** — `principal_minor "0"`,
   `interest_minor "0"`, `outstanding_principal_minor "0"` — the loan having fully amortized at
   installment 15 [VERIFIED: driver read the committed vector this fire]. T64-ZP-A/C/D have 55/33/71
   zero-**principal** rows and **zero** zero-EMI rows; their tails carry `interest_minor "1"`.
4. **OPEN.** `getPeriodWithUnrecognizedInterest` additionally requires the later period to have
   `getUnrecognizedInterest() > 0` [VERIFIED: `:1805-1814`], and
   `getUnrecognizedInterest() = negativeToZero(getCalculatedDueInterest() - getDueInterest())`
   [VERIFIED: `RepaymentPeriod.java:381-383`]. Whether any **admissible** input puts a period
   satisfying that **after** the last non-fully-paid period is what T66 must answer.

## The reading trap this fire is recording so it is not fallen into later

**An observed `interest_minor` of `0` on a dead row does not mean that period's
`calculatedDueInterest` is zero.** `getDueInterest()` takes
`min(getCalculatedDueInterest(), getEmiPlusCreditedAmountsPlusFutureUnrecognizedInterest())`
[VERIFIED: `RepaymentPeriod.java:271-286`], and for a zero-EMI period that minimum is `min(cdi, 0) = 0`
**whatever `cdi` is**. The observable is therefore blind to precisely the quantity the mechanism
tests. Any argument of the form "the capture shows 0 interest, so nothing is unrecognized" is
invalid, and a future task that makes it should be rejected on this note.

On `T64-ZP-B` the dead rows also carry a **zero outstanding balance**, which is an independent and
ordinary reason for `cdi` to be zero — consistent with ZP-B passing conformance today. That is a
statement about ZP-B, not about the mechanism.

## What a separating shape must satisfy, all three at once

- (a) EMI exactly zero, so the period is vacuously `isFullyPaid()` under step 2; **and**
- (b) that same period carrying **positive** `calculatedDueInterest` — which needs a positive
  outstanding balance, a `fixedInterest`, or an inherited previous-period `unrecognizedInterest`,
  since a zero balance yields zero; **and**
- (c) it lies strictly **after** the last period that is not fully paid.

(b) with a positive balance means **an EMI that quantizes to zero while principal is still
outstanding**. T63's `TestT63C` reported **101 admitted shapes** with a zero-EMI period carrying
positive calculated interest — the *necessary* half — and explicitly did not test the *position*
half, (c). **Position, not existence, is the unanswered question**, and existence is already
reported.

## Standing instruction for grading T66

- Verdict **(A) divergence exists** is admissible only with a PREDICTION registered **one commit
  before** the capture (P-9), the oracle confirming it, and a **measured** `graded_against` margin
  with a control showing the unmutated port reproduces every observed cell.
- Verdict **(B) provably inert** must separate **proof** (no admissible input can satisfy the
  conjunction, citing `admit.go`'s graded-domain predicates) from **corroboration** (a capture at
  the closest reachable shape). A (B) that rests only on ZP-B's observed zeroes is the trap above
  and must be rejected.
- Verdict **(C) still unproven** is acceptable and is not a failure, provided it names what was
  tried and what would settle it. T63 earned credit for withdrawing its own F-3 after going to look;
  the same standard applies here.

---

## Driver-re-run baseline for this fire, taken BEFORE T66 could change anything

So that any corpus change T66 makes is attributable, and so that T13 does not have to take these
numbers from a worker's report.

| check | result |
|---|---|
| `.softhouse/conformance.sh` | **exit 0** — 36 parity PASS / 0 FAIL, 4 contract-refusal PASS, 1 self-test PASS, **4034 graded cells**, 72 ungraded (never recorded by the capture), 0 refused, 0 inadmissible, 0 harness errors, 0 invariant violations, 0 invariant assertions NOT RUN |
| `go build ./...` / `go vet ./...` / `go test ./...` (repo-local toolchain go1.26.6 darwin/arm64, loaded via `.softhouse/bin/go-env.sh` — a bare `go` saying "command not found" is the EXPECTED state of a fresh shell here, not a broken environment) | **0 / 0 / 0** — all packages ok |
| `.softhouse/conformance.sh --prove` | **exit 0** — **21 proofs passed, 0 failed** |
| `contract.go` sha256 | `0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139` — **identical** to `contract_sha256` in `.softhouse/vectors/PIN.json`. The ratified artefact is byte-intact and the G-3 digest guard has nothing to fire on. |
| float in the non-test port | **none.** Every `float32`/`float64` occurrence under `nexus/internal/apps/loanschedule/` outside `_test.go` is inside a `contract.go` doc comment **prohibiting** it (`:121`, `:738`, `:1898`, `:2212`). |
| prohibited database engines | **none in use.** Every hit for `ojdbc` / `oracle.jdbc` / `:1521` / `com.mysql.cj` / `go-sql-driver/mysql` across `nexus/` and `.softhouse/` is either a **grep pattern inside a guard script** (`capture/charges/bin/selfcheck.sh:14`, `preconditions.sh:79,85`, `attest.py:142,145`), a **recorded zero-count assertion** (`reference-oracle.md:77,81`), or prose naming the prohibition (`program.json:893`, `ATTESTATION-T46.md:307-308`). PostgreSQL only. |

Oracle for this fire: `fineract-fineract-1` (`fineract:latest`) up ~44 h healthy, `fineract-db-1`
(`postgres:18.3`) up ~2 days healthy, `/fineract-provider/actuator/health` → `{"status":"UP"}`.
Pinned checkout `/Users/buv/fineract` at `426a23544`, clean.

---

# T66's verdict, and the driver's own re-derivation of it

**T66 returned verdict (B): provably inert on the graded domain — and it REFUTED the driver's
hypothesis at step 4.** The driver did not accept that from the report. All three of T66's legs were
re-run or re-derived by the driver independently, below. **The hypothesis was wrong and T66 was
right**, which is the outcome the honesty rule exists to make reportable.

## Where the driver's chain was wrong

Steps 1-3 hold and are now *observed*, not merely argued: 68 zero-EMI mechanism rows appear in the
oracle capture, and `T64-ZP-B` carries 40 of them after the last not-fully-paid period `L`.

**Step 4 was wrong, and wrong for a reason more general than the driver's own guess at how it might
fail.** The driver's note above speculated that ZP-B is inert because its tail rows have a zero
outstanding balance — a property of that one shape. The real reason is structural and applies to
every shape: the lookup does not run on the live model at all. It runs on a **deep copy** (`:1224`)
that `calculateRateFactorForScheduleTillDateInclusive` (`:1237`, `:1791-1803`) has re-rated only up
to `tillDate`, **zeroing `rateFactor` and `rateFactorTillPeriodDueDate` on every interest period
whose due date is after it** [VERIFIED by the driver at `ProgressiveEMICalculator.java:1791-1803`].
And `tillDate` is anchored at the **disbursement**, not maturity: `addDisbursement` passes
`getEffectiveRepaymentDueDate(..., operation.getSubmittedOnDate())` into
`calculateEMIValueAndRateFactors` [VERIFIED at `:137-151`], which reaches
`calculateLastUnpaidRepaymentPeriodEMI(scheduleModel, calculateFromRepaymentPeriodDueDate)` at
`:747`. So on the copy a tail period's **own** interest is zero by construction and cannot supply
the `u > 0` the precondition needs. The driver's step 4 reasoned about the live model and never
noticed the copy is truncated — which is the whole point of a method named
`...TillDateOnScheduleModelCopyAndDefer`.

The only surviving route is **inheritance** down the `u` chain from period `f`, via
`calculatedDueInterest += previous.getUnrecognizedInterest()` [VERIFIED at
`RepaymentPeriod.java:261-263`]. T66 closes that with the aggregate identity `Σ emi = P + I` that
`:1189-1207` has just enforced — which is precisely the step T69 marked `[UNVERIFIED]` at
`emi.go:315-325` and named T66 to settle.

## What the driver re-ran, rather than read

| leg | driver's independent result |
|---|---|
| **Source proof, crux (a)** | CONFIRMED at `:1791-1803` — post-`tillDate` rate factors set to `BigDecimal.ZERO`. |
| **Source proof, crux (b)** | CONFIRMED at `:137-151` → `:747` — `tillDate` anchored at the disbursement. |
| **Inheritance term** | CONFIRMED at `RepaymentPeriod.java:261-263`. This is why the proof needs the `u_k` cascade and cannot stop at "zeroed rate factors ⇒ zero". |
| **Oracle capture, pass 3h** | **RE-RUN BY THE DRIVER** from a scratch worktree with `CAP_OUT_DIR=/tmp`. `capturesCanonicalSha256` = `fdd751a209c9518b157ca6fd70aef06a91acff94953e1f8cc6c4d45162b90b73` — **identical** to the committed artefact. **8/8 rig calibrations reproduced cell-for-cell**, including `P-CAL-ZPA`/`P-CAL-ZPB` against the already-promoted `T64-ZP-A`/`T64-ZP-B`. Empty stderr. Effective MathContext `(19, HALF_UP ordinal 4)`. Every tenant logged `HALF_UP`. |
| **Mechanism rows** | **RE-COUNTED BY THE DRIVER** from its own run: 18 cases, **416 mechanism rows, 0 with `futureUnrecognizedInterest != "0.00"`, 0 with `interestMovedUpward != false`**, `pathIdentity.identical == true` on **18/18**. 68 zero-EMI rows present, so the shape under study is genuinely exercised. |
| **Port census** | **RE-RUN BY THE DRIVER** (`TestT66ZeroEMICensus`, 193 s): `admitted=21060, shapes with a zero-EMI period=9437, of which the zero-EMI period carries POSITIVE calculatedDueInterest=156, of which such a period lies STRICTLY AFTER L = 0`. The 156 and the 0 match T66's report exactly. Every logged example sits `at or before L`, at the rounding floor. |
| **Scope** | `git diff main...softhouse/T66-unrecognized-interest` touches **nothing** under `nexus/` or `.softhouse/vectors/`. The seam class `EmbeddableProgressiveLoanScheduleGenerator.java` is **byte-identical** (`bf397f0b…`) — the mechanism columns are read through a delegating `Proxy`, with path identity against the pristine seam as the guard. |
| **P-9 (prediction first)** | Commit order verified: `1c95499` PREDICTION at 14:27:41, capture output `b995572` at 14:37:22. The later re-run (`7a09130`) changed only `capturedAtUtc` and `Capture3h.java`'s own sha — **observations byte-identical, canonical digest unchanged**, which is a free determinism control. |

Three independent runs of pass 3h now agree on the canonical digest.

## FINDING P2-1 — the sufficient condition is incomplete in `PREDICTION.md`, and COMPLETE in the handoff

**This finding was overstated in the driver's first draft and is corrected here before being acted
on.** The first draft said "the written sufficient condition in step (e) is stated more generally
than its derivation supports", full stop. That is true of `PREDICTION.md` and **false of the
handoff**, which supplies exactly the missing premise. Leaving the finding in its first form would
have reproduced **P-11 / P-12** — a correction document wrong about its own reason — while citing
them, so it is restated accurately below and the earlier wording is withdrawn.

**The gap, in `PREDICTION.md:100` only.** Step (e) writes `u_L = 0` as soon as `cdi_f <= P + emi_f`.
That implication needs `Sum_{j<=f} emi_j <= I + emi_f`. Exact when `f = 0`; not derived there for
general `f`, and `I >= Sum_j dueInterest_j` with `dueInterest_j <= emi_j` runs the **wrong way
round** to supply it.

**The handoff closes it, and the driver verified the closure rather than accepting it.**
`T66.md:100-108` establishes `emi_j = 0` for every `j < f` as well, so `Sum_{j<=f} emi_j = emi_f`
*generally*, not merely at `f = 0` — and it reaches a **tighter** condition, `cdi_f <= P`. Both legs
check out:

- **Source.** `getRelatedRepaymentPeriods(d)` keeps only periods with `dueDate >= d`, so periods
  before `f` are outside the window [VERIFIED by the driver: `ProgressiveLoanInterestScheduleModel.java:191-198`],
  and `calculateEMIOnActualModel(List<RepaymentPeriod> repaymentPeriods, ...)` writes `setEmi` only
  on the list it is passed [VERIFIED: `ProgressiveEMICalculator.java:1674`]. A period outside the
  window is never assigned an EMI and keeps the zero it started with.
- **Observation.** The driver read its own pass-3h run: `T66-M-DISB-ON-DUE` and
  `T66-M-DISB-ON-DUE-HR` — the two `f = 1` shapes — both report period 0 `emi == "0.00"` and
  `calculatedDueInterest == "0.00"`.

**So the settled proof has no gap.** What remains is a **P3 documentation-hygiene** item: the
registered prediction states the condition without the premise the handoff later supplies. The
prediction's evidentiary value is that it was committed **before** the capture, so it must **not** be
rewritten; a dated forward-pointing CORRECTION block is the correct treatment, and that is what was
applied — the registered claim is left standing and annotated, exactly as T64's
`MECHANISM-CORRECTION.md` set the precedent.

**Beyond the closed-form bound, the conclusion is carried by evidence, not by the inequality**, and
T66 says so itself: above a per-period rate factor of 1.00 the bound is not tight, which is why
`T66-M-R12000` and `T66-M-DRIFT-R12000` (rate factor **10.00**, ten times past it) are in the
capture. The driver re-ran both and they are inert.

## What the driver did NOT verify, so silence is distinguishable from not looking

- The `u_k` cascade's **intermediate** state on the till-date copy is not observable through the
  Proxy and was not observed by anyone. T66 says this itself in `PASS3H-REPORT.md:140-146` — "It is
  **not** an observation of the copy's internal state" — before the driver could raise it. The
  oracle confirms the **outcome**; the proof and the port census cover the mechanism.
- T66's report says "6,377 with a zero-EMI tail"; the driver's re-run of the census reports "9,437
  shapes with a zero-EMI period". These are different predicates (tail vs anywhere) and are not in
  conflict, but the driver did not reconcile them and does not assert they agree.
- The proof's premises lapse under multi-tranche, payments, credits, capitalized income, re-aging
  and interest pauses. T66 records that list; none of it is graded today.


---

# CORRECTION — the driver propagated an unchecked line number into the document whose job was checking

Added at the end of local fire `20260820-140000`, after **T70** found it.

**`:1226` above was wrong; `deepCopy` is at `:1224`.** `:1226` is a *comment line*. The driver took the
number from T66's `PREDICTION.md`, repeated it in this re-derivation, **and passed it into T70's dispatch
prompt** — so an unchecked citation propagated from the artefact under review into the review, and then into
the next task's instructions. That is **P-12** (a correction document wrong about its own reason) recurring
one level up, and it is the second time this fire the driver has had to withdraw something it wrote.

T70 found the same drift in **three** committed artefacts. Verified by the driver by reading
`ProgressiveEMICalculator.java` at pinned `426a23544`:

| claim, as written in `T66.md` / `PASS3H-REPORT.md:141,143` / this document | actual line at `426a23544` |
|---|---|
| `deepCopy` at `:1226` | **`:1224`** — `:1226` is a comment |
| the `futureUnrecognizedInterest` write at `:1250` | **`:1246`** — `:1250` is a closing brace |
| the residual assignment at `:1207` (`T66.md`) | **`:1210`** (`setEmi(adjustedEmi)`); `:1205` is `Money adjustedEmi = …` and `:1207` sits inside the `getFixedInterest()` guard condition |

**None of this moves the verdict.** Every cited *method* is the right method and every step of the argument
stands; the drift is in the line numbers, which is exactly the class of error T69 caught in T67's own
replacement text (`:247` is on the `allowFullTermForTranche` branch; the ordinary path is `:747`). It is
recorded because a wrong citation in a money-path document is how the next reader is sent to the wrong code.
`T66.md` and `PASS3H-REPORT.md` are **not** corrected here — they are T66's artefacts and are filed as
follow-up **F-1**.

## F-2 — a gap in the T66 proof that neither T66 nor the driver noticed

**T70 raised it and, correctly, did not close it by reading.** `:1214` recursively re-enters
`calculateLastUnpaidRepaymentPeriodEMI` (declared `:1160`), and the `:1217` defer then runs in the **outer**
frame — so the lookup can execute after an inner frame has re-established step (d) on a possibly different
`L`. **T66 states (d) for a single entry only.** Neither T66's proof nor the driver's re-derivation above
analysed the recursive frame; the census covers it **empirically, not deductively**. [VERIFIED by the driver
at `:1211-1215` and `:1160`.]

The driver's own refinement, **offered to T71 to verify or refute and NOT adopted here**: the guard at
`:1211-1212` is `getEmi().isLessThan(totalPaidAmount.minus(totalCreditedAmount))`, and on the graded domain
nothing is paid and nothing credited, so it *appears* to reduce to `emi_L < 0`. **Whether `emi_L` can be
negative on an admissible shape is not established**, and the driver does not claim it cannot — asserting
that from reading alone would be precisely the move this comment's own history forbids.
