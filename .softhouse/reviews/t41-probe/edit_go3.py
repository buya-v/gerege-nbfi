#!/usr/bin/env python3
"""T41 — contract.go edits, batch 3: witness list, Period doc totalRepaymentExpected."""
import io
import sys

P = "nexus/internal/apps/loanschedule/contract/contract.go"
s = io.open(P, encoding="utf-8").read()
LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


sub(
    """// WHAT IS WITNESSED AND WHAT IS NOT (restated in revision 7, because the
// evidence base moved):""",
    """// WHAT IS WITNESSED AND WHAT IS NOT (restated in revision 7 and again in
// revision 8, because the evidence base moved twice; revision 8 closed the last
// NOT-OBSERVED row):""",
)

sub(
    """//   - the periodRatio MULTIPLIER (see Rounding.RateFactorScale) — NOT OBSERVED,
//     AND THE CORPUS CANNOT SEE IT. 0 of 21 committed production-setting captures
//     and 0 of 13 observations carry a non-unit periodRatio. DEC-1 section 8
//     item 3e.
//
// Two qualifications, both load-bearing. Every "OBSERVED" above is an ATTESTED
// RAW OBSERVATION, not an admissible parity vector: DEC-1's binding is a
// conformance precondition discharged by promoted vectors, and the promotion
// step (section 8 item 1) is outstanding. And item 3e has no capture at all, so
// THE MULTIPLIER RULE REMAINS SPECIFIED-FROM-SOURCE AND UNGRADED, on the same
// terms as the loop above: no conformance PASS for loanschedule may be read as
// evidence that a port implements this section.""",

    """//   - the periodRatio MULTIPLIER (see Rounding.RateFactorScale) — OBSERVED in
//     revision 8. 0 of the 21 pre-T39 captures carry a non-unit periodRatio, so
//     that corpus was blind; task T39 then captured 8 drift shapes and the
//     oracle agrees with periodRatio on 415 of 415 discriminating cells and
//     with RepaymentEvery on 0 of 415. DEC-1 section 8 item 3e.
//   - the MONTH-END SPECIAL CASE inside periodRatio's k step
//     (ProgressiveEMICalculator.java:1426-1436) — OBSERVED in revision 8.
//     Captures T39-ME-A..T39-ME-D: omitting it roughly doubles periodRatio on
//     alternate periods and is refuted on 116 of 116 discriminating cells.
//     DEC-1 section 8 item 3f — a SEPARATE vector, because the two questions
//     are disjoint in shape space and no one shape grades both.
//   - CHARGES — not a field of this contract, and OBSERVED in revision 8 to sit
//     ALONGSIDE the schedule rather than inside it. Across task T40's 21
//     charge-bearing captures the principal split, the interest, the outstanding
//     principal balance and the level installment are cell-for-cell identical to
//     the zero-charge control, so admitting charges later changes no field
//     specified here. DEC-1 section 4.5.1.
//
// Two qualifications, both load-bearing. Every "OBSERVED" above is an ATTESTED
// RAW OBSERVATION, not an admissible parity vector: DEC-1's binding is a
// conformance precondition discharged by promoted vectors, and the promotion
// step (section 8 item 1) is outstanding. So every rule this section states
// normatively is now WITNESSED and still UNGRADED — no conformance PASS for
// loanschedule may be read as evidence that a port implements any of it.""",
)

# --- Period doc: totalRepaymentExpected -------------------------------------
sub(
    """// A field whose only possible value is a constant would be surface with an
// unproven meaning, and a consumer reading it as a balance would be wrong. If a
// Go implementation is ever asked to render the oracle's PLAN shape for an audit
// comparison it must emit exactly zero there, and no scale-discipline invariant
// may be applied to that key without deciding the "0" case explicitly.""",

    """// A field whose only possible value is a constant would be surface with an
// unproven meaning, and a consumer reading it as a balance would be wrong. If a
// Go implementation is ever asked to render the oracle's PLAN shape for an audit
// comparison it must emit exactly zero there, and no scale-discipline invariant
// may be applied to that key without deciding the "0" case explicitly.
//
// THE ORACLE'S PLAN ALSO CARRIES totalRepaymentExpected. THIS CONTRACT DOES NOT
// CARRY IT EITHER, AND THE ADAPTER MUST DISCARD IT (revision 8, from task T40;
// DEC-1 section 4.5.1 decision C-1). On the progressive path it is seeded with
// the disbursement charges alone (LoanScheduleParams.java:211, :246), thereafter
// accumulates only principal + interest per period
// (ProgressiveLoanScheduleGenerator.java:137), and is NEVER raised by
// applyChargesForCurrentPeriod (:367-382 — the body is addLoanCharges,
// addTotalFeeChargesCharged, addTotalPenaltyChargesCharged and nothing else).
// The only later charge contribution is from updatePeriodsWithCharges (:486),
// which serves the two SEPARATED calculation types alone. The CUMULATIVE
// generator does add them (AbstractCumulativeLoanScheduleGenerator.java:504), so
// THE TWO GENERATORS DISAGREE and the field has no single meaning to specify.
//
// OBSERVED: totalRepaymentExpected == sum of totalDueForPeriod FAILS on 15 of
// task T40's 21 charge-bearing captures; on one of them MNT 51,900 of fees and
// penalties is visible in the rows and absent from the total
// (.softhouse/capture/charges/out/INVARIANTS.md, C5).
//
// It is not carried for four reasons: inside the graded domain there is no
// charge input, so it reduces to the sum of PrincipalMinor + InterestMinor and
// is DERIVABLE; it has no single meaning across the two generators; it is
// exactly the silent meaning-change a total-due column was rejected to avoid,
// since it equals the row sum today and stops equalling it the moment charges
// exist, with nothing breaking a compile; and the totalOutstandingAmount
// precedent applies with more force, that field being merely uninformative while
// this one is informative-looking and wrong.
//
// If a later amendment ever carries it, it carries the PROGRESSIVE generator's
// semantics, says so on the field, and is captured against that generator.
// NEITHER AN ADAPTER, NOR A HARNESS, NOR A CONFORMANCE CHECK MAY ASSERT THAT
// THIS FIELD EQUALS THE SUM OF THE ROWS: the assertion passes today only because
// the graded domain has no charges, and the day it fails it will be wrong about
// the ORACLE, not about the port. A caller wanting a total repayable sums the
// rows.""",
)

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
