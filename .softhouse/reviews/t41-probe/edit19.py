#!/usr/bin/env python3
"""T41 edit batch 19 — scope section 5's and section 8's attestation phrasing to 4.1.2.

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
  DEC-1        BEFORE_SHA256 = 4bc1dfb9ff513c4e70d0cb0501b33fe04794a969a96d887d8d0dba4f8afd2114
  DEC-1        AFTER_SHA256  = e07d5f807f557a9c36a8ed74b196a26357f9fecfcbb3b4d8e551c252191960bc

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


NAME = 'edit19'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT19-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '4bc1dfb9ff513c4e70d0cb0501b33fe04794a969a96d887d8d0dba4f8afd2114'
AFTER_SHA256 = \
    'e07d5f807f557a9c36a8ed74b196a26357f9fecfcbb3b4d8e551c252191960bc'

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


# --- section 5, the Rounding.SignificantDigits row --------------------------
sub(
    "| `Rounding.SignificantDigits` | 19 | 12-vs-19 pair, all 18 periods divergent (§4.1). |",
    "| `Rounding.SignificantDigits` | 19 | 12-vs-19 pair, all 18 periods divergent (§4.1). "
    "**Read as the THREADED context** (§4.1.2): the corpus discriminates threaded precision on "
    "that 18 × 18.5 % shape, and T39 measured it **indiscriminable on all sixteen of its own** "
    "(N-4), so \"captured at 19\" is a provenance claim on that family and a discrimination "
    "claim on this one. |",
)

# --- section 5, the Rounding.Mode row ---------------------------------------
sub(
    "| `Rounding.Mode` | HALF_UP | HALF_EVEN *observed* live on a running oracle (20,925.05 vs "
    "20,925.04) but **uncaptured in the corpus** → refused. |",
    "| `Rounding.Mode` | HALF_UP | HALF_EVEN *observed* live on a running oracle (20,925.05 vs "
    "20,925.04) but **uncaptured in the corpus** → refused. **That observation is a PATH-B one** "
    "(§4.1.2): it varies the **ambient** tenant mode, which is the arithmetic there. On Path A "
    "the same ambient change moves nothing and only the **threaded** mode does — 0 of 16 against "
    "15 of 16 [VERIFIED: T39 N-3]. |",
)

# --- section 5's admissibility paragraph ------------------------------------
sub(
    "Second, the server-path captures were taken on a tenant running HALF_EVEN; **that is now "
    "fixed rather than argued around**: task T36 re-captured all four on the `gerege` tenant "
    "(`Asia/Ulaanbaatar`, rounding-mode 4, attested `MathContext(19, HALF_UP)`), with a "
    "preconditions script proven to *fail* on the stock tenant, and got **byte-identical** "
    "results across two independent product fixtures. **Path B is now admissible as a capture "
    "path.** Nothing is promoted, on either path.",

    "Second, the server-path captures were taken on a tenant running HALF_EVEN; **that is now "
    "fixed rather than argued around**: task T36 re-captured all four on the `gerege` tenant "
    "(`Asia/Ulaanbaatar`, rounding-mode 4, attested `MathContext(19, HALF_UP)`), with a "
    "preconditions script proven to *fail* on the stock tenant, and got **byte-identical** "
    "results across two independent product fixtures. **Path B is now admissible as a capture "
    "path**, and revision 8 adds that on **Path B the attested AMBIENT context is exactly the "
    "right thing to attest**, because nothing threads a context there (§4.1.2) — T40 re-ran the "
    "same preconditions 21 of 21 five times and re-observed the half-cent canary. **On Path A "
    "the ambient attestation is provenance, not arithmetic**, and every Path-A record must state "
    "its **threaded** context separately; T39's does, and the pre-T39 ones conflate the two. "
    "Nothing is promoted, on either path. **Revision 8 also adds a third fact a ratifier should "
    "know:** the corpus is no longer 21 captures — T39 added 15 parity-setting ones and T40 "
    "added 21 charge-bearing ones, and revision 8's from-text model reproduces **4,578 cells** "
    "across all four sets with zero mismatches [`.softhouse/reviews/t41-probe/`].",
)

guard.commit(s)
print("\n".join(LOG))
