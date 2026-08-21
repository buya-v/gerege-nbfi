#!/usr/bin/env python3
"""T41 edit batch 17 — F-1 only: pin step B's whole-months function.

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
PRE-FIX bytes exited 1 at an anchor (`FAIL: found 0`)
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
  DEC-1        BEFORE_SHA256 = 123dc3c3ffde71ef6b206cb12dacb65fb99d1419de1372b01bcf3724fb5b114c
  DEC-1        AFTER_SHA256  = 2eb3092aad8064c6cfed6c8e4b19b611b012570afa23f1cb39bf598785ef4201

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


NAME = 'edit17'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT17-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '123dc3c3ffde71ef6b206cb12dacb65fb99d1419de1372b01bcf3724fb5b114c'
AFTER_SHA256 = \
    '2eb3092aad8064c6cfed6c8e4b19b611b012570afa23f1cb39bf598785ef4201'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.RATIFIED_ADR)

old = ("**Step B — the whole-period offset `k`** [`:1423-1439`]. `k` is the whole months from the "
       "seed to the repayment period's `FromDate` (`DateUtils.getExactDifference(seed, FromDate, "
       "MONTHS)`, truncated toward zero) [`:1435`], with an explicit **month-end special case** "
       "whose predicate revision 8 spells out literally,")

new = ("**Step B — the whole-period offset `k`** [`:1423-1439`].\n\n"
       "**First, WHICH whole-months function — because \"whole months, truncated toward zero\" "
       "names TWO different functions, and revision 8's own spec-check probe caught the ambiguity "
       "in revision 8's own draft** (finding **F-1**, `.softhouse/reviews/t41-probe/`). `k` is "
       "`DateUtils.getExactDifference(seed, FromDate, MONTHS)` [`:1435`], which is "
       "`ChronoUnit.MONTHS.between` [VERIFIED: `DateUtils.java:308-317` — `getExactDifference` "
       "→ `getDifference` → `unit.between(first, second)`], i.e. Java's `LocalDate.monthsUntil`:\n\n"
       "```\n"
       "packed(d) = (d.year × 12 + d.month − 1) × 32 + d.dayOfMonth\n"
       "k         = (packed(FromDate) − packed(seed)) ÷ 32        # truncated toward zero\n"
       "```\n\n"
       "**It is NOT \"the largest k with seed + k months ≤ FromDate\".** The two agree almost "
       "everywhere and differ **exactly** when `plusMonths` would have **clamped** — when "
       "`FromDate` is the last day of its month and the seed's day-of-month is strictly greater. "
       "`MONTHS.between(2024-01-31, 2024-02-29)` is **0** under the packed rule and **1** under "
       "the clamped-step rule. **That is precisely the condition the month-end special case below "
       "tests**, so the two readings coincide on every input *while the special case is present* "
       "and part company the moment it is dropped — which is why a model built on the wrong one "
       "reproduces every committed cell and still cannot see that the special case matters. "
       "(That is not hypothetical: this task's first transcription used the clamped-step reading, "
       "reproduced all 4,578 cells, and reported the special case as inert. The packed rule was "
       "adopted after reading `DateUtils.java`, and the same 4,578 cells still reproduce.) The "
       "JDK's packing is not a `file:line` in the pinned checkout, so the formula itself is "
       "`[UNVERIFIED in this checkout]` — but **which rule is in force is settled by "
       "observation**, because the special case is load-bearing only under the packed rule and "
       "T39 observed it load-bearing on 116 of 116 discriminating cells [VERIFIED: captures "
       "`T39-ME-A`…`T39-ME-D`]. **A port must implement the packed rule WITH the special case, or "
       "the clamped-step rule WITHOUT it; taking the packed rule and dropping the special case "
       "double-charges alternate periods, and that combination is the one a careless port "
       "lands on.**\n\n"
       "Then, `k` carries an explicit **month-end special case** whose predicate revision 8 spells "
       "out literally,")

if s.count(old) != 1:
    sys.exit("FAIL: found %d" % s.count(old))
guard.commit(s.replace(old, new))
print("ok: step B k function pinned")
