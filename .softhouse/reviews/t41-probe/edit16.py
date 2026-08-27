#!/usr/bin/env python3
"""T41 edit batch 16 — F-2 corrections at their actual wording.

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
  DEC-1        BEFORE_SHA256 = 1644db02cc3a311cb699b1eb3543e5c4525aa2942de22a8f58264642586385b0
  DEC-1        AFTER_SHA256  = 123dc3c3ffde71ef6b206cb12dacb65fb99d1419de1372b01bcf3724fb5b114c

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


NAME = 'edit16'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT16-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '1644db02cc3a311cb699b1eb3543e5c4525aa2942de22a8f58264642586385b0'
AFTER_SHA256 = \
    '123dc3c3ffde71ef6b206cb12dacb65fb99d1419de1372b01bcf3724fb5b114c'

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


sub(
    "with the oracle agreeing with the special-case-present routine on **116 of 116** disagreeing "
    "cells and with the omitted routine on **0 of 116** [VERIFIED: captures "
    "`T39-ME-A`…`T39-ME-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. "
    "**Reproducing this case is a Go-module obligation (§9) and it needs its own vector (§8 item "
    "3f), because no shape grades it and the multiplier together.**",

    "with the oracle agreeing with the special-case-present routine on **116 of 116** disagreeing "
    "cells and with the omitted routine on **0 of 116** [VERIFIED: captures "
    "`T39-ME-A`…`T39-ME-D`, `.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. "
    "**And the OLDER corpus was never blind to this one** (revision 8's own spec-check probe, "
    "finding **F-2**): the special-case-omitted reading also fails **3 of the 21 pre-T39 "
    "production-setting captures** — `P-02`, `P-02b` and `T37-3b-2`, the three whose "
    "`ScheduleStartDate` sits on a month end [VERIFIED: "
    "`.softhouse/reviews/t41-probe/t41-discriminate-output.txt`]. §5 credits `P-02` and `P-02b` "
    "with grading §4.2's **re-anchor**; they grade step B's special case as well, which no "
    "previous revision had measured. **Reproducing this case is a Go-module obligation (§9) and "
    "it still needs its own vector (§8 item 3f), because no shape grades it and the multiplier "
    "together — but its evidence is older and wider than T39, which makes 3f the best-witnessed "
    "of the seven binding items.**",
)

# --- 4.3.2's status table row -----------------------------------------------
sub(
    "| §4.1.1 step B's **month-end special case** | **OBSERVED** (revision 8), and its omission "
    "refuted on 116 of 116 discriminating cells across 4 shapes | captures `T39-ME-A`…`T39-ME-D` "
    "(§8 item **3f**) |",

    "| §4.1.1 step B's **month-end special case** | **OBSERVED** (revision 8), and its omission "
    "refuted on 116 of 116 discriminating cells across 4 shapes — **and separately refuted by 3 "
    "of the 21 pre-T39 captures**, which no previous revision had measured | captures "
    "`T39-ME-A`…`T39-ME-D`; also `P-02`, `P-02b`, `T37-3b-2` (§8 item **3f**) |",
)

# --- 4.3.1's discriminate table: add the month-end row and correct denominators
sub(
    "| **`periodRatio` with the month-end special case omitted (T39 N-2)** | 0 of those 21; "
    "**4 of T39's 16**, on 116 discriminating cells | `T39-ME-B`, cell `R2.interest` |",

    "| **`periodRatio` with the month-end special case omitted (T39 N-2)** | **3 of those 21** "
    "(`P-02`, `P-02b`, `T37-3b-2`) and **4 of T39's 15** parity-setting captures, on 116 "
    "discriminating cells | `P-02`, cell `R1.balance` |",
)

# --- section 8 item 3f: correct "no shape grades it" and add the older evidence
sub(
    "Across 4 shapes and **116 disagreeing cells** the oracle agrees **116 of 116** with the "
    "special case present and **0 of 116** with it omitted [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`].",

    "Across 4 shapes and **116 disagreeing cells** the oracle agrees **116 of 116** with the "
    "special case present and **0 of 116** with it omitted [VERIFIED: "
    "`.softhouse/capture/periodratio/analysis/discriminate-output.txt`]. **Revision 8's own "
    "probe adds three more witnesses, from the OLDER corpus** (finding F-2): the omitted reading "
    "also fails `P-02`, `P-02b` and `T37-3b-2` [VERIFIED: "
    "`.softhouse/reviews/t41-probe/t41-discriminate-output.txt`]. So **seven** committed captures "
    "separate this rule, which is more than any other binding item has — and it is still "
    "undischarged, because none of the seven is promoted. **That contrast is the clearest "
    "statement available of what item 1 is for.**",
)

guard.commit(s)
print("\n".join(LOG))
