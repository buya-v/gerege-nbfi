#!/usr/bin/env python3
"""T41 edit batch 7 — discriminate-table header and its lead-in; 4.3.2 status table.

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
  DEC-1        BEFORE_SHA256 = 6ae9a163512e617f201307c40bd6c54ad4c47ce536eee4616a72836a5ade5d22
  DEC-1        AFTER_SHA256  = 61b4d2e32c43e9e9ab2e2381606e1b617185ae6421655b8c02e50dae236ffa99

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


NAME = 'edit7'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT7-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '6ae9a163512e617f201307c40bd6c54ad4c47ce536eee4616a72836a5ade5d22'
AFTER_SHA256 = \
    '61b4d2e32c43e9e9ab2e2381606e1b617185ae6421655b8c02e50dae236ffa99'

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
    "| wrong reading | captures failed, of 21 | first witness |",
    "| wrong reading | captures failed | first witness |",
)

sub(
    "- **discriminates**, cell by cell, every wrong reading the corpus can see. Of the seven "
    "readings put to it, six fail at least one committed capture and one does not "
    "[`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`]:",

    "- **discriminates**, cell by cell, every wrong reading the corpus can see. Of the seven "
    "readings T38 put to it, six failed at least one of the 21 committed captures of that era and "
    "one did not [`.softhouse/reviews/t38-probe/t38-discriminate-output.txt`]. **Revision 8 "
    "extends the table with the readings T39's 16 and T40's 21 captures can now see**, and the "
    "\"captures failed\" column therefore names its denominator per row rather than assuming 21:",
)

# --- 4.3.2 status table ------------------------------------------------------
sub(
    "| the **`periodRatio` multiplier** of §4.1.1 | **NOT OBSERVED, and the corpus cannot see "
    "it** | §8 item **3e**, no capture exists |",

    "| the **`periodRatio` multiplier** of §4.1.1 | **OBSERVED** (revision 8), and the "
    "`RepaymentEvery` reading refuted on 415 of 415 discriminating cells across 8 shapes | "
    "captures `T39-P0-A`…`T39-P0-H` (§8 item **3e**) |\n"
    "| §4.1.1 step B's **month-end special case** | **OBSERVED** (revision 8), and its omission "
    "refuted on 116 of 116 discriminating cells across 4 shapes | captures `T39-ME-A`…`T39-ME-D` "
    "(§8 item **3f**) |",
)

sub(
    "**What is graded, and what is not — restated in revision 7, because the evidence base "
    "moved.** Until T37 every committed observation fell in the first two rows of the "
    "segmentation table. That is no longer true:",

    "**What is graded, and what is not — restated in revision 7 and again in revision 8, because "
    "the evidence base moved twice.** Until T37 every committed observation fell in the first two "
    "rows of the segmentation table; T37 broke that, and T39 then closed the last **NOT "
    "OBSERVED** row in this table. **Every rule §4.3.2 and §4.1.1 state normatively is now "
    "witnessed by at least one attested capture** — which is a statement about *evidence*, not "
    "about the binding, and §8 item 1's promotion step is still what stands between a capture and "
    "a graded rule:",
)

# --- 4.3.2's two honest qualifications --------------------------------------
sub(
    "Second, item **3e** has no capture at all, so **the `periodRatio` rule above remains "
    "specified-from-source and ungraded** on exactly the terms §4.3.1 states for the loop, and "
    "**no conformance PASS for `loanschedule` may be read as evidence that a port implements "
    "it.**",

    "Second — **and revision 8 changes only the first half of this sentence** — item **3e** now "
    "has captures (`T39-P0-A`…`T39-P0-H`) and its sibling **3f** has captures "
    "(`T39-ME-A`…`T39-ME-D`), so the `periodRatio` rule and its month-end special case are "
    "**observed**; but they are observed by attested raw captures, not by admissible vectors, so "
    "they remain **ungraded** on exactly the terms §4.3.1 states for the loop, and **no "
    "conformance PASS for `loanschedule` may be read as evidence that a port implements them.** "
    "**Captured is not promoted, and promoted is not cut over** — that sentence is now true of "
    "all seven binding items rather than five of six.",
)

guard.commit(s)
print("\n".join(LOG))
