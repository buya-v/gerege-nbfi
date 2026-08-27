#!/usr/bin/env python3
"""T41 edit batch 3 — T39 N-1: the days-in-month argument, re-derived precisely.

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
  DEC-1        BEFORE_SHA256 = 2144cff350c350035a50ccb4ab1bb7846d590f231e047017744f6a3eaa229d61
  DEC-1        AFTER_SHA256  = 916887a75e1e57a03e7444b16aff115fb8c314aca650fda043588b9ea87fd9db

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


NAME = 'edit3'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT3-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '2144cff350c350035a50ccb4ab1bb7846d590f231e047017744f6a3eaa229d61'
AFTER_SHA256 = \
    '916887a75e1e57a03e7444b16aff115fb8c314aca650fda043588b9ea87fd9db'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.RATIFIED_ADR)

LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d, found %d for:\n%s" % (n, c, old[:220]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:70].replace("\n", " "))


# --- 4.1.1: the heading claim ------------------------------------------------
sub(
    "**The two call sites differ in TWO arguments, not one** (P0-T34-1, corrected in revision 7). "
    "Revision 6's table named only the *span*; independent re-review T34 found the second "
    "difference, and **in money it is the larger of the two**.",

    "**The two call sites differ in two arguments SYNTACTICALLY, and in exactly ONE of them "
    "numerically — the multiplier** (P0-T34-1, corrected in revision 7; the framing **narrowed** "
    "in revision 8 on task T39's finding N-1, and the narrowing is in this document's favour). "
    "Revision 6's table named only the *span*; independent re-review T34 found the second "
    "difference and called it live; revision 7 said only the multiplier moves money **inside the "
    "graded domain**; revision 8 re-derives that the days-in-month argument is `30` at both call "
    "sites on **every path either call site is reachable on**, graded or not, so there is "
    "**exactly one numeric difference between them, unconditionally**.",
)

# --- 4.1.1: the "of those two argument differences" paragraph ---------------
sub(
    "**Of those two argument differences exactly one is live inside the graded domain, and "
    "revision 7 says which.** The days-in-month argument is a literal `30` on the interest call "
    "site [`:1413`] and the local `daysInMonth` on the recurrence call site [`:1537`], where "
    "`daysInMonth = daysInMonthType.isDaysInMonth_30() ? BigDecimal.valueOf(30) : "
    "calculatedDaysInRepaymentPeriod` [`:1508`] — so under `DayCountFixed30Over360` **both are "
    "exactly 30** and that difference is numerically inert. It can only become live under "
    "`DaysInMonthType.ACTUAL`, which §4.9 refuses and on which the interest call site takes a "
    "different branch entirely [`:1400-1402`]. **The multiplier is the live difference**: "
    "`RepaymentEvery` on the recurrence, `periodRatio` on the interest. Revisions 1–6 wrote "
    "`RepaymentEvery` for both.",

    "**Of those two argument differences exactly ONE moves money, and revision 8 states the "
    "stronger form of the reason.** The days-in-month argument is a literal `30` on the interest "
    "call site [`:1413`] and the local `daysInMonth` on the recurrence call site [`:1537`], where "
    "`daysInMonth = daysInMonthType.isDaysInMonth_30() ? BigDecimal.valueOf(30) : "
    "calculatedDaysInRepaymentPeriod` [`:1508`]. **So under `DayCountFixed30Over360` both are "
    "exactly 30.**\n\n"
    "**Revision 7 stopped there and said the difference \"can only become live under "
    "`DaysInMonthType.ACTUAL`\". Re-derived here in full, it cannot become live at all** — "
    "`daysInMonth` is consumed at exactly one place, `:1537`, and `:1537` sits inside the "
    "`case DAYS_30 ->` arm of the `switch (daysInMonthType)` at `:1533-1539`. `DAYS_30` is "
    "precisely the branch in which `:1508`'s ternary yields `BigDecimal.valueOf(30)`, so wherever "
    "the recurrence call site is reached its fourth argument **is** the literal 30, exactly as the "
    "interest call site's is. On the other two enum values neither call site is reached with a "
    "days-in-month argument at all: under `ACTUAL` the recurrence takes `:1534-1535` "
    "(`rateFactorByRepaymentPeriod` directly, no `daysInMonth`) and the interest site takes "
    "`:1400-1402` (likewise); under `INVALID` [`DaysInMonthType.java:34`] the recurrence throws at "
    "`:1538` and the interest site throws at `:1415-1416`. **There is therefore no configuration, "
    "inside the graded domain or outside it, in which the two call sites pass different "
    "days-in-month arguments to `calculateRateFactorPerPeriodBasedOnRepaymentFrequency`** — "
    "confirmed by grep: those are its only two call sites, and `daysInMonth` has only the one use "
    "[VERIFIED: `ProgressiveEMICalculator.java:1412-1413`, `:1508`, `:1533-1539`, `:1400-1402`, "
    "`:1415-1416`, `:1598-1607`; `DaysInMonthType.java:34-36`, `:71-73`].\n\n"
    "**The multiplier is the one and only live difference**: `RepaymentEvery` on the recurrence, "
    "`periodRatio` on the interest. Revisions 1–6 wrote `RepaymentEvery` for both. "
    "**A revision that also \"corrected\" the days-in-month argument would be wrong**, and task "
    "T39 raised exactly that as its finding N-1 [VERIFIED: "
    "`.softhouse/handoff/T39-periodratio-observation.md` §3 N-1]. Revision 8 records one "
    "divergence from T39: T39's prose locates the `daysInMonth` assignment at `:1509` while its "
    "own `[VERIFIED]` tag and this document say `:1508`; **`:1508` is correct**, re-read in the "
    "pinned checkout by this task. Revision 8 also goes one step beyond T39, which scoped the "
    "inertness to the graded domain: it is unconditional, for the reason above.",
)

guard.commit(s)
print("\n".join(LOG))
