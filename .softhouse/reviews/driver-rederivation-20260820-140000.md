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
