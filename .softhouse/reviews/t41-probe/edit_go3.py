#!/usr/bin/env python3
"""T41 — contract.go edits, batch 3: witness list, Period doc totalRepaymentExpected.

HARDENED BY T187 (21 August 2026) - P-22, P-48 rule 4.  This file REUSES T178's
shared guard verbatim (`../t47-probe/t178_guard.py`, itself T167's shape).  It
introduces no third guard shape and contains no copy of the guard.

AS SHIPPED BY TASK T41 this file ended in

    io.open(<a hard-wired repo-relative path>, "w", encoding="utf-8").write(s)

with no authorisation, no content gate, no atomicity and no trap.  `io.open(p,
"w")` opens with O_TRUNC, so the target was EMPTIED before a single byte of
replacement text was written, and any interruption from that instant until the
last flush left it truncated or half-edited.  Its target was the FROZEN adapter contract.
Amending a ratified DEC-n, or the frozen adapter contract that gate G-3 forbids
even `gofmt -w` from touching, is a hard `user` gate under CLAUDE.md.  An unguarded
rewriter aimed at either is a GATE BYPASS whether or not anybody runs it.

MEASURED BY T187 ON SCRATCH COPIES, NOT ASSERTED.  INERT TODAY.  Against byte-identical scratch copies of the CURRENT artefacts the
PRE-FIX bytes exited 1 at an anchor (`FAIL: expected 1, found 0 for:`)
and left both copies byte-identical.  An anchor that does not match today is not a
guarantee for tomorrow - the ADR is a living artefact and a later revision can
restore a phrase - so this file is hardened regardless of whether it applies now.

THE EDIT ITSELF DID NOT CHANGE.  Every anchor and every replacement string
below is byte-for-byte T41's.  What changed is the head and the tail: the
hard-wired target and the unguarded read are gone (the target now arrives from
argv under default-deny authorisation, and there is deliberately NO override
that reaches a ratified or frozen artefact); the write is atomic (`mkstemp` in
the target's own directory, `st_dev` compared, `fsync`, `os.replace`) and is
gated on sha256 BOTH on the target read and on the candidate text.  There is no
bare `assert` anywhere - `python3 -O` strips those - and every refusal is an
explicit exit.

PINNED CONTENT GATE, AND THIS IS WHAT ACTUALLY CLOSES THE BYPASS.
  contract.go  BEFORE_SHA256 = 5ec9b10060e053bbbf4410525429ecaaabab11285f560859066a4a798fbea789
  contract.go  AFTER_SHA256  = aaee90a81b9c7bb1e7ee9d0983941fec8b664081d51e6b5d56364534f2a3a660

HOW THE PINNED PAIR WAS DERIVED, RE-MEASURABLE BY ANYONE.  BEFORE_SHA256 is the
target's state at THIS script's position in T41's own edit chain, obtained by
replaying every T41 rewriter in commit order on scratch copies seeded from
  ADR          `git show 3594820^:docs/adr/DEC-1-schedule-generator-adapter.md`
               (sha256 35e513cdec69913caed759daee92626f2248c5c6fe2ca9ead6ed9968dc5f78e2)
  contract.go  `git show e96541d^:nexus/internal/apps/loanschedule/contract/contract.go`
               (sha256 c7cb53819bf0dea5c0327d3b4dc997a6f1feb14137e1c551059185bad0721a82)
AFTER_SHA256 is this script's DETERMINISTIC OUTPUT on that exact input, measured
by T187 - not a committed blob, because T41's commits carried hand edits
alongside the scripts' output.  The replayed chain is nevertheless faithful to
history where it can be checked: it reproduces the COMMITTED contract.go blobs
at b299ade (0e5468c470...) and at 0881cc0^ (4f986bb157...) exactly.

The ratified DEC-1 on `main` is sha256
  49dc89231ccf0615aa59603f2858025b0d489d48f0bf88df5b122f6c9cc7c9ab
and the frozen contract.go is
  0db73d4af996737d2f1a33c6d6aa4ac6cc35a33fbae57afbeb0d81e67e37f139
NEITHER is any BEFORE_SHA256 above, so no run of this file can reach either
artefact's CURRENT contents even if every other guard were stripped.

Guard, exit codes and the argv-token rationale: `../t47-probe/t178_guard.py`.
  0 ok / dry-run ok
  1 anchor mismatch (the edit does not apply)
  2 refused - authorisation, or target policy
  3 refused - unexpected target content (target sha != BEFORE_SHA256)
  4 refused - candidate content is not the historical result
  5 refused - temp file not on the target's filesystem
  6 post-write verification failed
"""
import os
import sys

# T178's guard is the ONE guard this program has, and it lives beside the
# t47-probe scripts.  It is resolved from THIS FILE's own location - never from
# the cwd, never from PYTHONPATH - so it cannot be shadowed.  A missing or
# unimportable guard raises ImportError and this script exits non-zero having
# written nothing: it fails CLOSED.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "t47-probe"))
import t178_guard as guard  # noqa: E402


NAME = 'edit_go3'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT-GO3-ON-A-SCRATCH-COPY-NOT-THE-FROZEN-CONTRACT')

BEFORE_SHA256 = \
    '5ec9b10060e053bbbf4410525429ecaaabab11285f560859066a4a798fbea789'
AFTER_SHA256 = \
    'aaee90a81b9c7bb1e7ee9d0983941fec8b664081d51e6b5d56364534f2a3a660'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.FROZEN_CONTRACT)

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

guard.commit(s)
print("\n".join(LOG))
