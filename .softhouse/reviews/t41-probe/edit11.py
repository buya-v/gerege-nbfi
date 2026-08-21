#!/usr/bin/env python3
"""T41 edit batch 11 — leak closure: three->four membership rules, 4.5, 6.1, 8, 9.

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
  DEC-1        BEFORE_SHA256 = 3da914cebede41a41fa095a1d0c49c4fdddc4ac844c988cfd2e820ca93b6a15a
  DEC-1        AFTER_SHA256  = ede0764bcc03da14cd84fc31c2760eac10a5743a46003c38fc5df50eb059c5bb

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


NAME = 'edit11'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT11-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '3da914cebede41a41fa095a1d0c49c4fdddc4ac844c988cfd2e820ca93b6a15a'
AFTER_SHA256 = \
    'ede0764bcc03da14cd84fc31c2760eac10a5743a46003c38fc5df50eb059c5bb'

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


# --- 4.3.1's spec-check description -----------------------------------------
sub(
    "§4.3.1 and §4.3.2 *including the three membership rules and step 4b* — from the document "
    "text alone,",
    "§4.3.1 and §4.3.2 *including the membership rules and step 4b* — from the document text "
    "alone,",
)

# --- 4.3.2 provenance --------------------------------------------------------
sub(
    "the `periodRatio` multiplier, the three membership rules and step 4b added in revision 7 and "
    "re-derived by task T38 from the same checkout",
    "the `periodRatio` multiplier, membership rules M1–M3 and step 4b added in revision 7 and "
    "re-derived by task T38 from the same checkout; **M4 added in revision 8 and re-derived by "
    "task T41** [`LoanCharge.java:371-373`, "
    "`LoanRepaymentScheduleProcessingWrapper.java:251-254`, `LoanScheduleParams.java:533-535`, "
    "`ProgressiveLoanScheduleGenerator.java:140`, `:143`, `:154`, `:374`, `:377`, `:400-403`, "
    "`:479`, `:483`, `ProgressiveLoanInterestScheduleModel.java:243`, "
    "`RepaymentPeriod.java:449-451`]",
)

# --- section 9 date-membership obligation -----------------------------------
sub(
    "- **The date-membership obligation** (added in revision 7, P0-T37-1). The Go module must "
    "implement **all three** of §4.3.2's membership rules and must not collapse them into one:",
    "- **The date-membership obligation** (added in revision 7, P0-T37-1; **widened to four rules "
    "in revision 8** from task T40's charge observations). The Go module must implement **all "
    "four** of §4.3.2's membership rules and must not collapse them into one:",
)

sub(
    "and which §4.6 already uses as the ordering window key. M1 and M3 disagree on exactly one "
    "date — a disbursement on a repayment period's `DueDate` — and that disagreement is the whole "
    "of the next obligation.",

    "and which §4.6 already uses as the ordering window key; and **M4** — `[From, Due]` for the "
    "first repayment period and `(From, Due]` thereafter, the **same predicate function as M1** "
    "[`LoanRepaymentScheduleProcessingWrapper.java:251-254`] reached through "
    "`LoanCharge.isDueInPeriod` [`LoanCharge.java:371-373`, "
    "`ProgressiveLoanScheduleGenerator.java:400-403`] but with the \"is first\" flag supplied by "
    "the **mutable counter** `LoanScheduleParams.isFirstPeriod()` "
    "[`LoanScheduleParams.java:533-535`] rather than by the period's own "
    "`isFirstRepaymentPeriod()` [`ProgressiveLoanInterestScheduleModel.java:243`, "
    "`RepaymentPeriod.java:449-451`] — which decides **which row a CHARGE lands on**. M1 and M3 "
    "disagree on exactly one date — a disbursement on a repayment period's `DueDate` — and that "
    "disagreement is the whole of the next obligation. **M4 is not carried by this contract "
    "today** (there is no charge field), and it is stated so that a port which later admits "
    "charges does not reuse M1, M2 or M3 for them, and so that the **staleness** of M4's flag on "
    "the separated charge path (§4.5.1, decision C-2b) is a recorded oracle defect rather than a "
    "surprise.",
)

# --- section 9 rounding-policy bullet's closing sentence --------------------
sub(
    "**Revision 7 also names, in one place, the three date-membership rules the oracle uses on "
    "the disbursement date (§4.3.2), because two of them disagree and revisions 1–6 stated them "
    "in three different sections and never reconciled them.**",

    "**Revision 7 also names, in one place, the date-membership rules the oracle uses on the "
    "disbursement date (§4.3.2), because two of them disagree and revisions 1–6 stated them in "
    "three different sections and never reconciled them. Revision 8 adds a FOURTH to that same "
    "one place** — the rule that decides which row a **charge** lands on, which shares M1's "
    "interval shape but takes its \"is first\" input from a mutable counter and is therefore "
    "stale on one path (§4.3.2 M4, §4.5.1). **Revision 8 also makes the multiplier decision "
    "OBSERVED rather than only specified** (task T39: `periodRatio` 415 of 415 discriminating "
    "cells, `RepaymentEvery` 0 of 415), and adds §4.1.2, which says **which `MathContext` is in "
    "force** — the threaded one on Path A, the ambient one on Path B — so that an attestation is "
    "read as evidence of the thing it actually witnesses.",
)

guard.commit(s)
print("\n".join(LOG))
