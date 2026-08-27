#!/usr/bin/env python3
"""T41 edit batch 9 — M4, the fourth date-membership rule (T40).

HARDENED BY T187 (21 August 2026) - P-22, P-48 rule 4.  This file REUSES T178's
shared guard verbatim (`../t47-probe/t178_guard.py`, itself T167's shape).  It
introduces no third guard shape and contains no copy of the guard.

AS SHIPPED BY TASK T41 this file ended in

    io.open(<a hard-wired repo-relative path>, "w", encoding="utf-8").write(s)

with no authorisation, no content gate, no atomicity and no trap.  `io.open(p,
"w")` opens with O_TRUNC, so the target was EMPTIED before a single byte of
replacement text was written, and any interruption from that instant until the
last flush left it truncated or half-edited.  Its target was the RATIFIED DEC-1.
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
  DEC-1        BEFORE_SHA256 = 3e475f1f313cee01e165a8783da54e658602ef49897dfeb5308e99fecd719bb2
  DEC-1        AFTER_SHA256  = 4e682455ed4e712f86f3c156db7a4af1891364dde47c58dd4060e649d11c1b7a

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


NAME = 'edit9'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT9-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '3e475f1f313cee01e165a8783da54e658602ef49897dfeb5308e99fecd719bb2'
AFTER_SHA256 = \
    '4e682455ed4e712f86f3c156db7a4af1891364dde47c58dd4060e649d11c1b7a'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.RATIFIED_ADR)

LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:260]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# --- heading + lead-in -------------------------------------------------------
sub(
    "##### The THREE date-membership rules, stated together (P0-T37-1, added in revision 7)\n\n"
    "The oracle uses **three different** date-membership conventions on the disbursement date, "
    "and they do not agree with one another. Revisions 1–6 stated two of them in §4.3.1 and the "
    "third in §4.6, in a different context and never reconciled with §4.3.2's roll-forward — "
    "which is exactly how §4.3.2 step 4 came to contradict this subsection's own segmentation "
    "table. **A port that assumes one convention throughout is wrong somewhere.** All three are "
    "normative:",

    "##### The FOUR date-membership rules, stated together (P0-T37-1, added in revision 7; **M4 "
    "added in revision 8** from task T40's charge observations)\n\n"
    "The oracle uses **four different** date-membership conventions when it decides which "
    "repayment period a dated thing belongs to, and they do not all agree with one another. "
    "Revisions 1–6 stated two of them in §4.3.1 and the third in §4.6, in a different context and "
    "never reconciled with §4.3.2's roll-forward — which is exactly how §4.3.2 step 4 came to "
    "contradict this subsection's own segmentation table. The fourth governs **charges** and was "
    "unobservable until task T40 captured the first non-zero fee in this program's history. "
    "**A port that assumes one convention throughout is wrong somewhere.** All four are "
    "normative, and this table is the one place they are reconciled:",
)

# --- the M4 row --------------------------------------------------------------
sub(
    "| **M3** | `[FromDate, DueDate)` — from-inclusive, **DUE-EXCLUSIVE** | "
    "`ProgressiveLoanScheduleGenerator.java:307-308`, guard at `:309` | during which repayment "
    "period's iteration `processDisbursements` runs — so **in which period's iteration the "
    "disbursement is registered into the interest model** [`:351`] and the disbursement row is "
    "emitted [`:318`], which §4.6 already uses as its ordering window key |",

    "| **M3** | `[FromDate, DueDate)` — from-inclusive, **DUE-EXCLUSIVE** | "
    "`ProgressiveLoanScheduleGenerator.java:307-308`, guard at `:309` | during which repayment "
    "period's iteration `processDisbursements` runs — so **in which period's iteration the "
    "disbursement is registered into the interest model** [`:351`] and the disbursement row is "
    "emitted [`:318`], which §4.6 already uses as its ordering window key |\n"
    "| **M4** | `[FromDate, DueDate]` for the **FIRST** repayment period and `(FromDate, DueDate]` "
    "for every later one — **the same predicate function as M1**, but reached with a **different "
    "source for the \"is first\" flag** | `LoanCharge.java:371-373` → "
    "`LoanRepaymentScheduleProcessingWrapper.java:251-254`, flag supplied by "
    "`LoanScheduleParams.isFirstPeriod()` [`LoanScheduleParams.java:533-535`] at "
    "`ProgressiveLoanScheduleGenerator.java:374`, `:377` (main loop) and `:479`, `:483` "
    "(separated path) | which repayment row a **CHARGE** lands on — the `feeChargesDue` / "
    "`penaltyChargesDue` columns and `totalDueForPeriod`. **Not carried by this contract** "
    "(§4.5, §4.5.1); stated because a port that later admits charges must not reuse M1, M2 or M3 "
    "for them |",
)

# --- the "M1 and M3 disagree" paragraph: extend to M4 -----------------------
sub(
    "**M1 and M3 disagree on exactly one date: a disbursement dated on a repayment period's "
    "`DueDate`.** M1 puts it in period *j*; M3 puts it in period *j+1*. Both are right about "
    "their own question, and the disagreement is the whole of P0-T37-1.",

    "**M1 and M3 disagree on exactly one date: a disbursement dated on a repayment period's "
    "`DueDate`.** M1 puts it in period *j*; M3 puts it in period *j+1*. Both are right about "
    "their own question, and the disagreement is the whole of P0-T37-1.\n\n"
    "**M4 shares M1's interval shape and is still a different rule, because the input that "
    "selects the shape is different — and on one path it is STALE** (revision 8, re-derived by "
    "this task from the pinned checkout and corroborated by observation). M1 passes the "
    "repayment period's **own structural property**, `period.isFirstRepaymentPeriod()` "
    "[`ProgressiveLoanInterestScheduleModel.java:243`], which is `previous == null` "
    "[`RepaymentPeriod.java:449-451`] — true of the first period and of nothing else, always. "
    "M4 passes `LoanScheduleParams.isFirstPeriod()`, which is `1 == instalmentNumber` "
    "[`LoanScheduleParams.java:533-535`] — a **mutable running counter**. Inside the main "
    "schedule loop the counter is correct, because `applyChargesForCurrentPeriod` runs at "
    "[`ProgressiveLoanScheduleGenerator.java:140`] and `incrementInstalmentNumber()` only at "
    "[`:143`], so during period 1's iteration the flag is `true` and M4 coincides with M1. "
    "On the **separated** path it is not: `updatePeriodsWithCharges` runs at [`:154`], **after** "
    "the `for` loop at [`:116-145`] has incremented the counter once per period, so "
    "`isFirstPeriod()` is **false for every period including period 1** [`:479`, `:483`] and M4 "
    "degenerates to `(FromDate, DueDate]` everywhere. **That staleness is a money-losing defect "
    "in the reference oracle and it is OBSERVED** — §4.5.1, capture `FC-20`. "
    "**Which rule governs which field:** M1 the interest-period segmentation and the effective "
    "due date; M2 the related-period list and hence the level installment; M3 the disbursement "
    "row's emission, the interest model's registration and §4.6's ordering window key; M4 the "
    "fee and penalty columns. **They are not interchangeable and this table is the only place "
    "they may be read from.**",
)

guard.commit(s)
print("\n".join(LOG))
