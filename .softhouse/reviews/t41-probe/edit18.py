#!/usr/bin/env python3
"""T41 edit batch 18 — F-1/F-2 leak closure: contract.go, section 9, revision history.

HARDENED BY T187 (21 August 2026) - P-22, P-48 rule 4.  This file REUSES T178's
shared guard verbatim (`../t47-probe/t178_guard.py`, itself T167's shape).  It
introduces no third guard shape and contains no copy of the guard.

AS SHIPPED BY TASK T41 this file ended in

    io.open(<a hard-wired repo-relative path>, "w", encoding="utf-8").write(s)

with no authorisation, no content gate, no atomicity and no trap.  `io.open(p,
"w")` opens with O_TRUNC, so the target was EMPTIED before a single byte of
replacement text was written, and any interruption from that instant until the
last flush left it truncated or half-edited.  Its target was the RATIFIED DEC-1 and the FROZEN adapter contract.
Amending a ratified DEC-n, or the frozen adapter contract that gate G-3 forbids
even `gofmt -w` from touching, is a hard `user` gate under CLAUDE.md.  An unguarded
rewriter aimed at either is a GATE BYPASS whether or not anybody runs it.

MEASURED BY T187 ON SCRATCH COPIES, NOT ASSERTED.  INERT TODAY.  Against byte-identical scratch copies of the CURRENT artefacts the
PRE-FIX bytes exited 1 at an anchor (`FAIL in nexus/internal/apps/loanschedule/contract/contract.go: found 0 for:`)
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
  DEC-1        BEFORE_SHA256 = 2eb3092aad8064c6cfed6c8e4b19b611b012570afa23f1cb39bf598785ef4201
  DEC-1        AFTER_SHA256  = 4bc1dfb9ff513c4e70d0cb0501b33fe04794a969a96d887d8d0dba4f8afd2114
  contract.go  BEFORE_SHA256 = 0e5468c470363914d2b50ddd4f0b800b64f363b961d4b8fb8846d916fb588097
  contract.go  AFTER_SHA256  = 4f986bb157b3ec95ae16d1a7c8509d7d1c10d521060091195e35203361e01b83

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


NAME = 'edit18'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT18-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1-OR-THE-FROZEN-CONTRACT')

BEFORE_ADR = \
    '2eb3092aad8064c6cfed6c8e4b19b611b012570afa23f1cb39bf598785ef4201'
AFTER_ADR = \
    '4bc1dfb9ff513c4e70d0cb0501b33fe04794a969a96d887d8d0dba4f8afd2114'
BEFORE_GO = \
    '0e5468c470363914d2b50ddd4f0b800b64f363b961d4b8fb8846d916fb588097'
AFTER_GO = \
    '4f986bb157b3ec95ae16d1a7c8509d7d1c10d521060091195e35203361e01b83'

LOG = []


# --------------------------------------------------------------------------
# TWO-TARGET DEMUX.  This script rewrites TWO artefacts and t178_guard's API is
# one guarded session per target, so argv has to be split before the guard sees
# it.  The demux below ONLY SPLITS: every authorisation check, every target
# policy check and every content gate still happens inside the guard, once per
# target.  A missing flag is not defaulted - it reaches the guard as a MISSING
# target, and the guard refuses with its own usage text and exit 2.  So
# default-deny remains the guard's property, not this file's.
#
# NOT ATOMIC ACROSS THE TWO FILES, stated rather than implied.  Each file is
# replaced atomically by guard.commit(); a run that commits the first target and
# then refuses on the second leaves the first at AFTER and the second at BEFORE.
# That is the PRE-FIX behaviour, preserved deliberately, and it is fail-closed:
# a re-run then refuses at the first target's content gate (exit 3) rather than
# doubling the edit.  Both targets are scratch copies outside the repository
# working tree in any case - the guard admits nothing else.
# --------------------------------------------------------------------------
_ARGS = {}
for _a in sys.argv[1:]:
    if _a.startswith("--target-adr="):
        _ARGS["adr"] = _a.split("=", 1)[1]
    elif _a.startswith("--target-go="):
        _ARGS["go"] = _a.split("=", 1)[1]
    elif _a.startswith("--authorise="):
        _ARGS["tok"] = _a.split("=", 1)[1]
    elif _a == "--dry-run":
        _ARGS["dry"] = True
    else:
        sys.stderr.write(
            "%s: REFUSED (2): unknown argument %r\n"
            "  usage: %s.py --target-adr=<path to a SCRATCH copy> \\\n"
            "               --target-go=<path to a SCRATCH copy> \\\n"
            "               --authorise=%s [--dry-run]\n"
            % (NAME, _a, NAME, AUTHORISE_TOKEN))
        sys.exit(2)

_GATE = {"adr": (BEFORE_ADR, AFTER_ADR, guard.RATIFIED_ADR),
         "go": (BEFORE_GO, AFTER_GO, guard.FROZEN_CONTRACT)}


def patch(kind, pairs):
    """One guarded session for one target: load (authorise + policy + content
    gate), apply T41's pairs unchanged, commit atomically."""
    before, after, prot = _GATE[kind]
    argv = [sys.argv[0]]
    if kind in _ARGS:
        argv.append("--target=" + _ARGS[kind])
    argv.append("--authorise=" + _ARGS.get("tok", ""))
    if _ARGS.get("dry"):
        argv.append("--dry-run")
    sys.argv = argv
    s = guard.load(NAME + ":" + kind, __file__, AUTHORISE_TOKEN, before, after,
                   prot)
    for old, new in pairs:
        c = s.count(old)
        if c != 1:
            sys.exit("FAIL in %s: found %d for:\n%s" % (kind, c, old[:240]))
        s = s.replace(old, new)
        LOG.append("ok %s: %s" % (kind, old[:60].replace("\n", " ")))
    guard.commit(s)


# --- contract.go -------------------------------------------------------------
patch("go", [
    ("""	//	k     := whole months from seed to FromDate, EXCEPT that when FromDate is
	//	         the last day of its month and seed's day > FromDate's day, it is
	//	         measured to FromDate.plusDays(1)               (:1430-1433)""",
     """	//	k     := MONTHS.between(seed, FromDate)  -- Java LocalDate.monthsUntil,
	//	         i.e. packed = (year*12 + month-1)*32 + day; k = (p2-p1)/32
	//	         truncated toward zero (DateUtils.java:308-317).  THIS IS NOT
	//	         "the largest k with seed + k months <= FromDate": the two differ
	//	         exactly when plusMonths would have CLAMPED, which is exactly the
	//	         condition the special case below tests, so they coincide WHILE the
	//	         special case is present and part company the moment it is dropped.
	//	         EXCEPT that when FromDate is the last day of its month and seed's
	//	         day > FromDate's day, k is measured to FromDate.plusDays(1)
	//	                                                        (:1426-1436, :1432)
	//	         Implement the packed rule WITH the special case, or the
	//	         clamped-step rule WITHOUT it; the packed rule minus the special
	//	         case DOUBLE-CHARGES alternate periods (an observed MNT 83,959.76
	//	         on one six-month MNT 3,924,149 loan)."""),
])

# --- DEC-1 section 9 obligation (c) -----------------------------------------
patch("adr", [
    ("the month-end special case in the whole-period offset [`:1430-1433`], the forward walk and "
     "its fractional branch [`:1441-1458`], with the **division at `:1453` as the only "
     "`MathContext`-rounded step** and the addition at `:1454` **exact**;",

     "the whole-period offset `k` as **`ChronoUnit.MONTHS.between`'s packed rule** "
     "[`:1435`, `DateUtils.java:308-317`] **together with** the month-end special case "
     "[`:1426-1436`, predicate at `:1432`, effect at `:1433`] — the two must be implemented as a "
     "pair, because the packed rule without the special case double-charges alternate periods "
     "and the clamped-step reading of \"whole months\" silently absorbs the special case (§4.1.1 "
     "step B, finding F-1); the forward walk and its fractional branch [`:1441-1458`], with the "
     "**division at `:1453` as the only `MathContext`-rounded step** and the addition at `:1454` "
     "**exact**;"),

    # revision-history: record the probe's own two findings
    ("  **What revision 8 does NOT do.** It does not admit charges to the contract,",

     "  **Two findings revision 8's OWN spec-check probe produced, recorded because a probe that "
     "finds nothing has not been run** (`.softhouse/reviews/t41-probe/`). **F-1 (§4.1.1 step B, "
     "§9, `contract.go`):** \"whole months, truncated toward zero\" names **two** functions — "
     "`ChronoUnit.MONTHS.between`'s packed rule and \"the largest `k` with seed + k months ≤ "
     "FromDate\" — which differ exactly when `plusMonths` would have clamped, i.e. exactly where "
     "the month-end special case fires. They therefore coincide **while the special case is "
     "present** and diverge the instant it is dropped, so a model built on the wrong one "
     "reproduces every committed cell *and reports the special case as inert*. This task's first "
     "transcription did exactly that. Step B now pins the packed rule with its citation and says "
     "the two must be implemented as a pair. **F-2 (§4.1.1 step B, §4.3.1, §4.3.2, §8 item 3f):** "
     "the pre-T39 corpus was **never blind** to the month-end special case — the omitted reading "
     "fails `P-02`, `P-02b` and `T37-3b-2` as well as T39's four, so **seven** committed captures "
     "separate it, more than any other binding item, and it is *still* undischarged because none "
     "is promoted.\n"
     "  **Spec-check result.** A model transcribed from revision 8's text alone reproduces "
     "**4,578 cells** across four corpora — the 13 observation triples, the 11 Path-A pass-3 "
     "captures (712 cells), the 10 T37 binding captures (776 cells), the 15 parity-setting T39 "
     "captures (1,224 cells, full-cell including fee, penalty and `totalOutstandingBalance`) and "
     "the schedule core of all 21 T40 charge captures (1,827 cells) — with **zero mismatches**, "
     "and it discriminates every known corpus-invisible wrong reading plus the three revision 8 "
     "adds. **The T40 result is the executable form of decision C-1/C-2's premise**: a model that "
     "computes no charge at all reproduces the principal split, the interest, the outstanding "
     "principal and the level installment of twenty-one charge-bearing schedules exactly.\n"
     "  **What revision 8 does NOT do.** It does not admit charges to the contract,"),
])

print("\n".join(LOG))
