#!/usr/bin/env python3
"""T41 — contract.go edits, batch 2: M4, Period doc totalRepaymentExpected, ungraded list.

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
  contract.go  BEFORE_SHA256 = b6a6e0308f66d4106bca01246a5e0bd0c3d1a519bde2ef708dff847421213f93
  contract.go  AFTER_SHA256  = 5ec9b10060e053bbbf4410525429ecaaabab11285f560859066a4a798fbea789

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


NAME = 'edit_go2'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT-GO2-ON-A-SCRATCH-COPY-NOT-THE-FROZEN-CONTRACT')

BEFORE_SHA256 = \
    'b6a6e0308f66d4106bca01246a5e0bd0c3d1a519bde2ef708dff847421213f93'
AFTER_SHA256 = \
    '5ec9b10060e053bbbf4410525429ecaaabab11285f560859066a4a798fbea789'

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
    """// ## The THREE date-membership rules (normative; revision 7, P0-T37-1)
//
// The reference oracle uses THREE different membership conventions on the
// disbursement date, and they do not agree. A port that assumes one convention
// throughout is wrong somewhere.
//""",
    """// ## The FOUR date-membership rules (normative; revision 7, P0-T37-1; M4 added
// in revision 8 from task T40's charge observations)
//
// The reference oracle uses FOUR different membership conventions when it
// decides which repayment period a dated thing belongs to, and they do not all
// agree. A port that assumes one convention throughout is wrong somewhere.
//""",
)

sub(
    """//	M3  [FromDate, DueDate) — from-inclusive, DUE-EXCLUSIVE.
//	    (ProgressiveLoanScheduleGenerator.java:307-308, guard at :309)
//	    Decides: during which period's iteration processDisbursements runs, so
//	    in which period's iteration the disbursement is REGISTERED into the
//	    interest model (:351) and the disbursement row EMITTED (:318). It is
//	    also the ordering window key (see the Kind / ordering doc).
//""",
    """//	M3  [FromDate, DueDate) — from-inclusive, DUE-EXCLUSIVE.
//	    (ProgressiveLoanScheduleGenerator.java:307-308, guard at :309)
//	    Decides: during which period's iteration processDisbursements runs, so
//	    in which period's iteration the disbursement is REGISTERED into the
//	    interest model (:351) and the disbursement row EMITTED (:318). It is
//	    also the ordering window key (see the Kind / ordering doc).
//	M4  [FromDate, DueDate] for the FIRST repayment period and
//	    (FromDate, DueDate] for every later one — THE SAME PREDICATE FUNCTION
//	    AS M1 (LoanRepaymentScheduleProcessingWrapper.java:251-254), reached
//	    through LoanCharge.isDueInPeriod (LoanCharge.java:371-373,
//	    ProgressiveLoanScheduleGenerator.java:400-403).
//	    Decides: which repayment row a CHARGE lands on — the fee and penalty
//	    columns and totalDueForPeriod.
//	    NOT CARRIED BY THIS CONTRACT: GenerateRequest has no charge field and
//	    Period has no fee or penalty. M4 is stated so that a port which later
//	    admits charges does not reuse M1, M2 or M3 for them.
//
// M4 IS A DIFFERENT RULE FROM M1 EVEN THOUGH IT SHARES M1'S INTERVAL SHAPE,
// because the input that SELECTS the shape is different — and on one path it is
// STALE. M1 passes the repayment period's own structural property,
// period.isFirstRepaymentPeriod() (ProgressiveLoanInterestScheduleModel.java:243),
// which is `previous == null` (RepaymentPeriod.java:449-451) — true of the first
// period and nothing else, always. M4 passes LoanScheduleParams.isFirstPeriod(),
// which is `1 == instalmentNumber` (LoanScheduleParams.java:533-535) — a MUTABLE
// RUNNING COUNTER. Inside the main schedule loop it is correct, because
// applyChargesForCurrentPeriod runs at ProgressiveLoanScheduleGenerator.java:140
// and incrementInstalmentNumber() only at :143. On the SEPARATED charge path it
// is not: updatePeriodsWithCharges runs at :154, after the loop at :116-145 has
// incremented the counter once per period, so isFirstPeriod() is FALSE FOR EVERY
// PERIOD INCLUDING PERIOD 1 (:479, :483) and M4 degenerates to
// (FromDate, DueDate] everywhere. That staleness silently loses a charge dated
// on the first period's FromDate — OBSERVED, DEC-1 section 4.5.1 decision C-2b,
// capture FC-20 byte-identical to the zero-charge control while capture FC-11 (a
// FLAT charge, same date) pays 9,000.00.
//
// WHICH RULE GOVERNS WHICH FIELD: M1 the interest-period segmentation and the
// effective due date; M2 the related-period list and hence the level
// installment; M3 the disbursement row's emission, the interest model's
// registration and the ordering window key; M4 the fee and penalty columns.
// They are not interchangeable.
//""",
)

sub(
    """//	                        see "The THREE date-membership rules" above);""",
    """//	                        see "The FOUR date-membership rules" above);""",
)

guard.commit(s)
print("\n".join(LOG))
