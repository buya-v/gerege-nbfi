# T24 handoff — DEC-1 revision 3: T23's three P0 corrections applied

**Task:** Apply the three P0 corrections from independent re-review T23
(`.softhouse/reviews/T23-DEC-1-v2-rereview.md` §10) to the UNRATIFIED DEC-1 draft,
bumping revision 2 → revision 3. Agent work on an unratified draft, not a user gate.
No live oracle used or needed: every cited divergence was already observed and committed
by T23 under `.softhouse/reviews/t23-probe/`. No oracle value was synthesized, derived,
or invented — all are re-citations of committed T23 artifacts.

**Branch:** `softhouse/T24-dec1-v3-p0-corrections`
**Reviewer to read this from:** T26 (independent).

## Files changed

1. `docs/adr/DEC-1-schedule-generator-adapter.md` — status → revision 3, revision-history
   note added at top, three P0 fixes applied in place.
2. `nexus/internal/apps/loanschedule/contract/contract.go` — three P0 fixes applied in
   doc comments and one refinement to an error variable's doc.

No types, fields, enum members, or signatures changed. The contract SHAPE is untouched;
only normative doc text was corrected. This is consistent with "widening/clarifying is not
an amendment" and, more importantly, the draft is unratified so correction is permitted.

## Build / format result

Run in `/home/user/wt-T24/nexus`:

- `gofmt -l ./internal/apps/loanschedule/contract/contract.go` → **empty (clean)**
- `go build ./...` → **exit 0 (clean)**
- `go vet ./internal/apps/loanschedule/contract/` → **clean (no output)**
- Forbidden-token scan (`float32|float64|big.Float|ojdbc|oracle.jdbc|mysql|mariadb|first_name|last_name|stripe|plaid`)
  over contract.go → only matches are in prose that PROHIBITS those tokens (the pre-existing
  invariants block at lines ~66/86-87, and my new line ~1027 which explicitly forbids a float
  on the EMI-loop path). No executable float introduced. No non-negotiable weakened.

## P0-1 — EMI re-adjust loop recorded as a graded-domain obligation — DONE

The revision-2 claim that `checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods`
"is reachable only outside the graded domain" is STRUCK and replaced with the observed fact
that it fires on every ordinary generation and moves money inside the graded domain.

- **ADR §4.3** (the "second smoothing pass" paragraph): rewritten. States the loop runs on
  every generation via `ProgressiveEMICalculator.java:749` gated on `onlyOnActualModelShouldApply`
  (true when `scheduleModel.isEmpty()`); its guard `EmiAdjustment.shouldBeAdjusted`
  (`EmiAdjustment.java:31-36`) compares `|lastEMI − penultimateEMI| × 100` against a `Money` of
  amount `floor(n/2)` currency units; `Money.copy(double)` (`Money.java:220-222`) REPLACES the
  amount rather than scaling it, so the guard has NO dependence on `InstallmentRoundingMultipleMinor`.
  Adds the exact-integer-arithmetic requirement (no float) explicitly.
- **ADR §9** ("the Go module must reproduce …" obligation list): the EMI re-adjust smoothing loop
  is added to the list, with the guard description and the exact-integer/no-float note.
- **ADR §4.7**: the bullet mentioning the loop under `InstallmentRoundingMultipleMinor` is
  corrected to say the loop is a §9 obligation firing independently of that field, not
  installment-rounding-specific.
- **ADR §8 item 3**: re-scoped from "a vector that forces the loop to iterate" (installment-rounding
  framing) to "vectors that trip the EMI re-adjust guard INSIDE the graded domain", noting the ten
  §6.1 cases as ready-made candidates and that reproducing the loop is already a §9 obligation.
- **contract.go `Period` type doc**: authoritative normative obligation added here — NOT in the
  doc comment of `InstallmentRoundingMultipleMinor` (the field pinned to zero), as required. Full
  guard mechanism, the two observed divergences, the corpus blind spot, and the exact-integer /
  no-float directive.
- **contract.go `InstallmentRoundingMultipleMinor` doc**: the pre-existing loop bullet corrected to
  cross-reference the `Period` obligation and to state the loop is not conditional on a non-zero
  multiple.

**Observed values cited (source):**
- `MNT 1,014,632 / 6 × 7.0% → oracle 172,574.64 vs 172,574.63 without the loop`
  — oracle 172,574.64 from `.softhouse/reviews/t23-probe/t23-probe2-output.txt` line 4
  (CASE P=1014632 n=6 rate=7.0, per-period total 172574.64); the no-loop `172,574.63` from
  T23 re-review §6.1 table (no-loop EMI column).
- `MNT 127,704 / 36 × 16.8% → total interest 35,746.56 vs 35,746.69`
  — oracle 35,746.56 from `t23-probe2-output.txt` line 12 (CASE P=127704 n=36 rate=16.8,
  `totalInterest=35746.56`); the no-loop `35,746.69` from T23 re-review §6.1 prose.

## P0-2 — disbursement-window hole closed; ordering rule's third clause fixed — DONE

Option T23 preferred (add to the graded-domain predicate and REFUSE outside it, per standing
G-1 "refuse rather than guess"). The degenerate all-zero answer is NOT reproduced.

- **ADR §3.1 graded-domain list**: added the semantic predicate
  `ScheduleStartDate ≤ Disbursements[0].Date < the last repayment period's DueDate`, with a
  paragraph explaining it is checkable from already-computed quantities, that out-of-window
  disbursements are silently discarded by the seam, and that they are refused with
  `ErrNoDiscriminatingVector`; widening with multi-tranche vectors is behaviour, not amendment.
- **ADR §4.6**: the ordering rule's third clause ("or a key after every repayment row if its date
  is on or after the last due date") DELETED; added the observation (Q1a/Q1b/Q2, all-zero schedule,
  `totalDisbursed = 0.00`) and the mechanism (`ProgressiveLoanScheduleGenerator.java:305-306`,
  after-maturity arm gated on `isMultiDisburseLoan()`, `:147-150`, so `addDisbursement` at `:351`
  is never called), and the note that such a row is refused and never keyed.
- **contract.go `Schedule` ordering doc**: the third clause of the window-key rule DELETED and
  replaced with the same explanation, encoding the refusal path as `ErrNoDiscriminatingVector`
  (consistent with the other graded-domain refusals).
- **contract.go `GenerateRequest` graded-domain list**: the semantic predicate added, with the
  refusal-with-`ErrNoDiscriminatingVector` disposition and the mechanism citation.

**Observed values cited (source):** cases Q1a (disbursement 2024-07-01, the last due date),
Q1b (2024-09-01, after), Q2 (2023-11-15, before ScheduleStartDate) all yielding an all-zero
schedule — from `.softhouse/reviews/t23-probe/t23-probe-output.txt` and T23 re-review §2.3.
Mechanism lines (`ProgressiveLoanScheduleGenerator.java:305-308`, `:147-150`, `:351`) from T23 §2.3.

## P0-3 — FrequencyYears justification corrected; error-precedence rule added — DONE

- **ADR §4.10**: retitled and rewritten. `FrequencyYears` throws ONLY on the fixed-30/360 arm
  (`ProgressiveEMICalculator.java:1536` → `:1602-1610`); the ACTUAL arm at `:1534-1535` never
  reaches that dispatch (`rateFactorByRepaymentPeriod` direct, dates via
  `DefaultScheduledDateGenerator.getRepaymentPeriodDate:311-333` `case YEARS`). Observed Q3a
  (30/360 throws) and Q3b (ActualActual returns term 1096 days, total interest 551,982.62).
  Refusal split: 30/360 → `ErrUnsupportedConfiguration` (missing answer); ActualActual →
  `ErrNoDiscriminatingVector` (missing vector, ActualActual itself ungraded).
- **ADR §4.11**: error-precedence rule added —
  `ErrInvalidRequest` > `ErrUnsupportedConfiguration` > `ErrNoDiscriminatingVector`; an
  implementation returns the first applicable sentinel, so a multiply-refusable request is
  deterministic across both implementations (satisfies the equal-rejection requirement).
- **contract.go `FrequencyYears` doc**: rewritten to match (throws on 30/360 arm only; ACTUAL arm
  answers; observed 1096 days / 551,982.62; refusal split; refers to the precedence rule).
- **contract.go error-variable block**: precedence rule added as a normative preamble to the `var (…)`
  block (right above `ErrInvalidRequest`, adjacent to the `contract.go:~1101-1103` equal-rejection
  sentence). `ErrUnsupportedConfiguration` doc's FrequencyYears example refined to "on the
  fixed-30/360 arm … (on the ACTUAL arm the oracle answers but the request is ungraded)".

**Observed values cited (source):** Q3a threw `UnsupportedOperationException: Invalid repayment
frequency` (30/360); Q3b `loanTermInDays=1096 totalInterest=551982.62 totalRepayment=1751982.62`
(ActualActual) — both from `.softhouse/reviews/t23-probe/t23-probe-output.txt` lines 62-68, and
T23 re-review §4.2.

## [UNVERIFIED] items

None. Every observed value cited resolves to a committed T23 artifact:
oracle-side figures to `t23-probe-output.txt` / `t23-probe2-output.txt`; the two no-loop
comparison figures (172,574.63 and 35,746.69) to T23 re-review §6.1, which is the committed record
of T23's no-loop re-derivation (`t23_rederive.py` / `t23_compare.py`). No value was recomputed by T24.

## What was deliberately NOT changed

- **ADR §4.4 line ~265** and **contract.go:~667** carry "reachable only on the actual/actual arm,
  which is outside the graded domain" for `interestRecognitionOnDisbursementDate` — a DIFFERENT,
  un-refuted claim about a different pin, not the EMI loop. Left as-is (T23 P0-1 targets only the
  EMI-loop reachability claim).
- The P1 findings (P1-1 … P1-7) are explicitly "fix after ratification" per T23 §10 and are out of
  scope for this P0-only task. Not touched.
- DEC-1 was NOT ratified by T24, and no gate disposition was altered.
