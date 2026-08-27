#!/usr/bin/env python3
"""T41 edit batch 22 — contract.go half of the T42 fold-in (em-dash corrected).

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
PRE-FIX bytes exited 1 at an anchor (`FAIL: found 0 for:`)
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

THIS SCRIPT APPLIES TO NO STATE OF contract.go THAT HAS EVER EXISTED HERE.
T187 ran the PRE-FIX bytes against all 21 DISTINCT historical blobs of
`nexus/internal/apps/loanschedule/contract/contract.go` reachable from every
ref in this repository.  All 21 refused at the FIRST anchor with `found 0`.
The reason is visible in the text: the anchor wraps `... no deployment / can
produce ...` while every state of the file that contains the surrounding
sentence wraps it `... no deployment can / produce ...` - the wrap that
edit_go1.py itself writes.  The anchor was hand-mangled and the corresponding
contract.go hunk in commit 0881cc0 was applied by hand, not by this file.

CONSEQUENCE FOR THE PINNED PAIR, STATED RATHER THAN PAPERED OVER.  BEFORE is
the contract.go state at this script's position in the chain (identical to the
COMMITTED blob at 0881cc0^, which is what makes it the right gate).  AFTER is
the 64-`f` sentinel: `guard.commit` is UNREACHABLE from here because the first
anchor cannot match, so no candidate digest exists to pin and none was invented.
An authorised run on a scratch copy at BEFORE reaches the anchor check and
exits 1 with the scratch file byte-identical - which is the whole of the green
half available for this file, and it is reported as such rather than dressed up
as a successful reproduction.
PINNED CONTENT GATE, AND THIS IS WHAT ACTUALLY CLOSES THE BYPASS.
  contract.go  BEFORE_SHA256 = 4f986bb157b3ec95ae16d1a7c8509d7d1c10d521060091195e35203361e01b83
  contract.go  AFTER_SHA256  = ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff

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


NAME = 'edit22'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT22-ON-A-SCRATCH-COPY-NOT-THE-FROZEN-CONTRACT')

BEFORE_SHA256 = \
    '4f986bb157b3ec95ae16d1a7c8509d7d1c10d521060091195e35203361e01b83'
AFTER_SHA256 = \
    'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.FROZEN_CONTRACT)

LOG = []


def sub(old, new):
    global s
    c = s.count(old)
    if c != 1:
        sys.exit("FAIL: found %d for:\n%s" % (c, old[:240]))
    s = s.replace(old, new)
    LOG.append("ok: %s" % old[:60].replace("\n", " "))


sub("""	// Every one of those sits on the installment-multiple or
	// multipliedBy(double) path, which the graded domain excludes.
	// Independently settable modes would admit combinations no deployment
	// can produce and would double the vector matrix.""",
    """	// Every one of those sits on the installment-multiple or
	// multipliedBy(double) path, which the graded domain excludes -- AND ONE
	// MORE SITE THAT IS HANDED A CONTEXT AND IGNORES IT (revision 8, task
	// T42): Money's constructor calls the TWO-argument roundToMultiplesOf at
	// Money.java:50, which hard-codes MoneyHelper.getRoundingMode()
	// (Money.java:154) and never looks at the mc assigned at :42. It is gated
	// on currency.getInMultiplesOf() != null && getDecimalPlaces() == 0 &&
	// inMultiplesOf > 0 (Money.java:48-51). Currency.MinorUnitDigits == 2 is a
	// graded-domain predicate and MNT has two decimal places, so a ratified
	// request NEVER reaches it -- but a Go port that threads its context
	// correctly everywhere will be MORE consistent than the reference oracle
	// and WILL DIVERGE on a 0-decimal-place currency with an inMultiplesOf.
	// Observed, not read: T42 reached it by giving the tenant no rounding mode
	// and catching the IllegalStateException from MoneyHelper.java:79.
	// Independently settable modes would admit combinations no deployment
	// can produce and would double the vector matrix.""")

sub("""	// converse holds — nothing threads a context, getMc() takes its null
	// branch, and the ambient mode IS the arithmetic, which is why the same
	// request on two tenants differing only in mode returns 20,925.05 under
	// HALF_UP and 20,925.04 under HALF_EVEN. A CAPTURE ATTESTATION MUST
	// RECORD THE TWO CONTEXTS AS TWO LABELLED FIELDS; "captured at
	// (19, HALF_UP)" does not say which, and on Path A only the threaded one
	// is evidence about the money.""",
    """	// converse holds, and the reason is NOT that nothing is threaded: the
	// caller SOURCES the threaded context from the ambient one.
	// LoanScheduleAssembler does
	//     final MathContext mc = MoneyHelper.getMathContext();   (:753)
	// and hands THAT SAME OBJECT to generate(mc, ...) (:765), so on Path B the
	// two contexts are one reference — which is why the same request on two
	// tenants differing only in mode returns 20,925.05 under HALF_UP and
	// 20,925.04 under HALF_EVEN. Task T42 read that wiring off the DEPLOYED
	// bytecode of the running server and measured it: an ambient-only change
	// moves 0 cells on the Path A wiring and 22-28 on the Path B wiring, in
	// one payload. A CAPTURE ATTESTATION MUST RECORD THE TWO CONTEXTS AS TWO
	// LABELLED FIELDS AND THE WIRING; "captured at (19, HALF_UP)" does not
	// say which, and on Path A only the threaded one is evidence about the
	// money. THE RULE IS PER SITE, NOT A SLOGAN: on a 0-dp / inMultiplesOf
	// shape it INVERTS -- the ambient mode moves 23 cells and the threaded
	// mode moves none.""")

guard.commit(s)
print("\n".join(LOG))
