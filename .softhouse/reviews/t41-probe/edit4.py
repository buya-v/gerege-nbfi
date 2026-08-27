#!/usr/bin/env python3
"""T41 edit batch 4 — leak-grep closure for the N-1 correction: 4.3.2 and section 9.

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
  DEC-1        BEFORE_SHA256 = 916887a75e1e57a03e7444b16aff115fb8c314aca650fda043588b9ea87fd9db
  DEC-1        AFTER_SHA256  = ad51e78d8bf5e3d1007ff60d5eb26a23ef958d075236b0e49bf1cc8e28459644

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


NAME = 'edit4'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT4-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '916887a75e1e57a03e7444b16aff115fb8c314aca650fda043588b9ea87fd9db'
AFTER_SHA256 = \
    'ad51e78d8bf5e3d1007ff60d5eb26a23ef958d075236b0e49bf1cc8e28459644'

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


# --- 4.3.2 restatement -------------------------------------------------------
sub(
    "The `30` above is the days-in-month multiplier. On this call site it is the literal "
    "`BigDecimal.valueOf(30)` [`:1413`]; on the recurrence call site it is `daysInMonth` "
    "[`:1508`, `:1537`], which is also exactly 30 under `DayCountFixed30Over360` — see §4.1.1 for "
    "why that second difference is inert inside the graded domain.",

    "The `30` above is the days-in-month multiplier, and it is **the same 30 on both call sites, "
    "unconditionally** (revision 8, narrowing revision 7 on task T39's N-1). On this call site it "
    "is the literal `BigDecimal.valueOf(30)` [`:1413`]; on the recurrence call site it is "
    "`daysInMonth` [`:1508`, passed at `:1537`], and `:1537` is reachable **only** from the "
    "`case DAYS_30 ->` arm at `:1536`, in which `:1508`'s ternary yields `BigDecimal.valueOf(30)`. "
    "So the two arguments are numerically identical wherever either call site is reached — see "
    "§4.1.1 for the full derivation, including why the difference cannot become live outside the "
    "graded domain either. **The multiplier is the one live difference between the two call "
    "sites.**",
)

# --- section 9 obligation (e) ------------------------------------------------
sub(
    "and (e) the days-in-month multiplier as **30** on both call sites under "
    "`DayCountFixed30Over360` [`:1413`, `:1508`, `:1537`].",

    "and (e) the days-in-month multiplier as **30** on both call sites [`:1413`, `:1508`, "
    "`:1537`] — under `DayCountFixed30Over360` and, revision 8 adds, on **every** path either "
    "call site is reachable on, because `:1537` is consumed only from the `case DAYS_30 ->` arm "
    "at `:1536` where `:1508` yields the literal 30 (§4.1.1). **A port must NOT \"correct\" this "
    "second argument to differ between the call sites**; only the multiplier differs.",
)

guard.commit(s)
print("\n".join(LOG))
