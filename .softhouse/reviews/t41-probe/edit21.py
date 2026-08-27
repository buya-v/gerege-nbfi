#!/usr/bin/env python3
"""T41 edit batch 21 — T42 leak closure: 4.1, 4.4, 5, 8, 9, contract.go, history.

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
PRE-FIX bytes exited 1 at an anchor (`FAIL in docs/adr/DEC-1-schedule-generator-adapter.md: found 0 for:`)
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

THE contract.go HALF OF THIS SCRIPT APPLIES TO NO STATE OF contract.go THAT HAS
EVER EXISTED HERE.  T187 ran the PRE-FIX bytes against all 21 DISTINCT
historical blobs of `nexus/internal/apps/loanschedule/contract/contract.go`
reachable from every ref in this repository: the FIRST pair of the `go` list
matches, a later pair does not, and the run dies with `found 0` on the anchor
beginning `// converse holds -- nothing threads a context`.  That anchor spells
the dash `--` where every state of the file spells it `—`; `edit22.py` is the
same edit with the em-dash corrected, which is why both exist.  The contract.go
hunk in commit 0881cc0 was applied by hand, not by this file.

CONSEQUENCE FOR THE PINNED PAIR, STATED RATHER THAN PAPERED OVER.  AFTER_GO is
the 64-`f` sentinel: `guard.commit` is UNREACHABLE on the `go` session, so no
candidate digest exists to pin and none was invented.  AFTER_ADR is real - the
DEC-1 half DOES apply, and the pre-fix script wrote it before dying on the
contract.go half, which is precisely the partial-application hazard the
two-target note below records.
PINNED CONTENT GATE, AND THIS IS WHAT ACTUALLY CLOSES THE BYPASS.
  DEC-1        BEFORE_SHA256 = 6bc401b4b8c77e917a06b81ec6bd60f6c675dd94cf1748981e35bcd72e6f6173
  DEC-1        AFTER_SHA256  = 5798acc94860f3ce06c1dd14e541b0709535151c530ade53cca6e44a8b2ae70f
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


NAME = 'edit21'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT21-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1-OR-THE-FROZEN-CONTRACT')

BEFORE_ADR = \
    '6bc401b4b8c77e917a06b81ec6bd60f6c675dd94cf1748981e35bcd72e6f6173'
AFTER_ADR = \
    '5798acc94860f3ce06c1dd14e541b0709535151c530ade53cca6e44a8b2ae70f'
BEFORE_GO = \
    '4f986bb157b3ec95ae16d1a7c8509d7d1c10d521060091195e35203361e01b83'
AFTER_GO = \
    'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'

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



patch("adr", [
    # --- 4.1's "no size threshold" paragraph gains T42's precision result ----
    ("**There is no size threshold.** *Observed*: the oracle's own 12-vs-19 pair diverges at a "
     "principal of **4.00** on a 36-period 16.8 % shape and is **identical** at 50,000,000 on that "
     "same shape and at 87,654,321 on a 6-period 7.0 % shape. Sensitivity is a rounding-boundary "
     "property of the `(principal, term, rate)` triple, not a magnitude property of the principal. "
     "All four MNT captures in the corpus are 12/19-identical, so nothing in the corpus shows "
     "Mongolian sizes are precision-sensitive either. **Any implementation shortcut justified by "
     "loan size is unfounded.**",

     "**There is no size threshold.** *Observed*: the oracle's own 12-vs-19 pair diverges at a "
     "principal of **4.00** on a 36-period 16.8 % shape and is **identical** at 50,000,000 on that "
     "same shape and at 87,654,321 on a 6-period 7.0 % shape. Sensitivity is a rounding-boundary "
     "property of the `(principal, term, rate)` triple, not a magnitude property of the principal. "
     "**Revision 8 upgrades the last clause from a corpus limitation to a MEASUREMENT** (task "
     "T42): the four MNT captures of the Run-1 corpus are 12/19-identical, but a 110-shape sweep "
     "to 360 periods found separating ones and they are **ordinary Mongolian retail loans** — MNT "
     "**50,000,000 / 360 × 21.6 %** differs by **MNT 2.05** in total interest across **861 cells**, "
     "MNT **25,000,000 / 360 × 7.7 %** across 610 — and **separation is not monotone in the "
     "principal**, so 25 M separates while 30–70 M do not and 80 M does again [VERIFIED: task T42, "
     "`.softhouse/capture/mathcontext/analysis/discriminate2-output.txt`]. **Any implementation "
     "shortcut justified by loan size is unfounded, and that is now observed at both ends of the "
     "scale rather than argued.**"),

    # --- 4.4's currency.inMultiplesOf row ------------------------------------
    ("| `currency.inMultiplesOf` | `null` | Inert because the oracle applies it only when the "
     "currency has **zero** decimal places [`Money.java:48-51`] and MNT has two. *Observed* at "
     "zero decimal places it moves money (total interest 763,994 versus 764,100 on an 18 × 18.5 % "
     "MNT 5,000,000 loan), which is a second reason `Currency.MinorUnitDigits == 2` is in the "
     "graded domain. It is a **different thing** from `InstallmentRoundingMultipleMinor`, which is "
     "the loan-product rounding and *is* in the contract. |",

     "| `currency.inMultiplesOf` | `null` | Inert because the oracle applies it only when the "
     "currency has **zero** decimal places [`Money.java:48-51`] and MNT has two. *Observed* at "
     "zero decimal places it moves money (total interest 763,994 versus 764,100 on an 18 × 18.5 % "
     "MNT 5,000,000 loan), which is a second reason `Currency.MinorUnitDigits == 2` is in the "
     "graded domain. **Revision 8 adds a THIRD reason, and it is the sharpest** (task T42): that "
     "same guard is the **only** gate on the one Path-A site where the AMBIENT `MoneyHelper` "
     "context reaches the money — `Money`'s constructor calls the two-argument "
     "`roundToMultiplesOf` at [`Money.java:50`], which hard-codes `MoneyHelper.getRoundingMode()` "
     "[`:154`] and ignores the `MathContext` the constructor was handed. *Observed*: on a 0-dp / "
     "`inMultiplesOf` 100 shape the **ambient** mode moves 23 cells and the **threaded** mode "
     "moves **none** — the exact inversion of the graded domain's behaviour [VERIFIED: task T42, "
     "`.softhouse/capture/mathcontext/analysis/discriminate-output.txt`]. So admitting a 0-dp "
     "currency would not merely switch on a second rounding channel; it would change **which "
     "`MathContext` governs** (§4.1.2), and §4.1.2's whole argument would have to be re-run rather "
     "than inherited. It is a **different thing** from `InstallmentRoundingMultipleMinor`, which "
     "is the loan-product rounding and *is* in the contract. |"),

    # --- section 8 item 1: the attestation block gains T42's rule ------------
    ("**Revision 8 adds one more field to that machine-readable block**: the **threaded** "
     "`MathContext` and the **ambient** `MoneyHelper` context as two separately labelled values, "
     "never one conflated \"captured at (19, HALF_UP)\" — §4.1.2.",

     "**Revision 8 adds two more requirements to that machine-readable block, both from task T42's "
     "attestation rule.** (i) The **threaded** `MathContext` and the **ambient** `MoneyHelper` "
     "context as two separately labelled values, never one conflated \"captured at "
     "(19, HALF_UP)\"; the threaded value must be echoed **off the object handed to the callee**, "
     "not off the intent. (ii) The **WIRING**, per capture path — on **Path B** the ambient "
     "reading *is* the threaded context and the record must cite "
     "[`LoanScheduleAssembler.java:753`, `:765`]; on **Path A** the two are independent variables "
     "and the ambient reading witnesses the tenant configuration only. A **behavioural canary** "
     "must accompany whichever context the record claims governs — a configuration echo is not a "
     "discriminator (§4.1.2). **Revision 8 also records that three committed attestations need "
     "re-wording and none needs re-capturing**: T35's and T37's \"the `MathContext` in force\" "
     "phrasing reads the ambient context and is wrong about Path A; T36's is substantially sound, "
     "because on Path B it is right by the wiring. **No committed value changes** — every one of "
     "those captures echoed and asserted its threaded context separately [VERIFIED: task T42 §4]."),

    # --- section 8 item 6: add the precision vector --------------------------
    ("6. **Vectors for the uncaptured frequency and cardinality corners**: `FrequencyDays`, "
     "`FrequencyWeeks`, `RepaymentEvery > 1`, zero interest rate, `HALF_EVEN`.",

     "6. **Vectors for the uncaptured frequency and cardinality corners**: `FrequencyDays`, "
     "`FrequencyWeeks`, `RepaymentEvery > 1`, zero interest rate, `HALF_EVEN`.\n"
     "   **6c. A vector that discriminates threaded PRECISION 19 from 12** — added in revision 8 "
     "from task T42, superseding T39's N-4. Until T42 no captured shape could tell the ratified "
     "precision from any other, so `SignificantDigits == 19` was a **transcription** claim wearing "
     "a graded-domain predicate. T42 found separating shapes and they are ordinary: **MNT "
     "50,000,000 / 360 × 21.6 %** (MNT 2.05 in total interest, 861 cells) and **MNT 25,000,000 / "
     "360 × 7.7 %** (610 cells), with separation **not monotone in the principal** [VERIFIED: "
     "`.softhouse/capture/mathcontext/analysis/discriminate2-output.txt`]. Promote one 360-period "
     "shape **once G-1 closes**, labelled as the precision-discriminating vector, alongside a "
     "`(12, HALF_UP)` sibling kept explicitly as a **discrimination probe and never a parity "
     "vector**. **That pair is the only thing in this program that would make Buyan's ratified "
     "precision-19 parameter falsifiable**, and until it is promoted §5's `SignificantDigits` row "
     "grades the parameter on one 18 × 18.5 % shape and nothing Mongolian-sized."),
])

# --- contract.go: the ambient-site enumeration and the Path-B mechanism -----
patch("go", [
    ("	// Every one of those sits on the installment-multiple or\n"
     "	// multipliedBy(double) path, which the graded domain excludes.\n"
     "	// Independently settable modes would admit combinations no deployment can\n"
     "	// produce and would double the vector matrix.",

     "	// Every one of those sits on the installment-multiple or\n"
     "	// multipliedBy(double) path, which the graded domain excludes -- AND ONE\n"
     "	// MORE SITE THAT IS HANDED A CONTEXT AND IGNORES IT (revision 8, task\n"
     "	// T42): Money's constructor calls the TWO-argument roundToMultiplesOf at\n"
     "	// Money.java:50, which hard-codes MoneyHelper.getRoundingMode()\n"
     "	// (Money.java:154) and never looks at the mc assigned at :42. It is gated\n"
     "	// on currency.getInMultiplesOf() != null && getDecimalPlaces() == 0 &&\n"
     "	// inMultiplesOf > 0 (Money.java:48-51). Currency.MinorUnitDigits == 2 is a\n"
     "	// graded-domain predicate and MNT has two decimal places, so a ratified\n"
     "	// request NEVER reaches it -- but a Go port that threads its context\n"
     "	// correctly everywhere will be MORE consistent than the reference oracle\n"
     "	// and WILL DIVERGE on a 0-decimal-place currency with an inMultiplesOf.\n"
     "	// Observed, not read: T42 reached it by giving the tenant no rounding mode\n"
     "	// and catching the IllegalStateException from MoneyHelper.java:79.\n"
     "	// Independently settable modes would admit combinations no deployment can\n"
     "	// produce and would double the vector matrix."),

    ("	// converse holds -- nothing threads a context, getMc() takes its null\n"
     "	// branch, and the ambient mode IS the arithmetic, which is why the same\n"
     "	// request on two tenants differing only in mode returns 20,925.05 under\n"
     "	// HALF_UP and 20,925.04 under HALF_EVEN. A CAPTURE ATTESTATION MUST\n"
     "	// RECORD THE TWO CONTEXTS AS TWO LABELLED FIELDS; \"captured at\n"
     "	// (19, HALF_UP)\" does not say which, and on Path A only the threaded one\n"
     "	// is evidence about the money.",

     "	// converse holds, and the reason is NOT that nothing is threaded: the\n"
     "	// caller SOURCES the threaded context from the ambient one.\n"
     "	// LoanScheduleAssembler does\n"
     "	//     final MathContext mc = MoneyHelper.getMathContext();   (:753)\n"
     "	// and hands THAT SAME OBJECT to generate(mc, ...) (:765), so on Path B the\n"
     "	// two contexts are one reference -- which is why the same request on two\n"
     "	// tenants differing only in mode returns 20,925.05 under HALF_UP and\n"
     "	// 20,925.04 under HALF_EVEN. Task T42 read that wiring off the DEPLOYED\n"
     "	// bytecode of the running server and measured it: an ambient-only change\n"
     "	// moves 0 cells on the Path A wiring and 22-28 on the Path B wiring, in\n"
     "	// one payload. A CAPTURE ATTESTATION MUST RECORD THE TWO CONTEXTS AS TWO\n"
     "	// LABELLED FIELDS AND THE WIRING; \"captured at (19, HALF_UP)\" does not\n"
     "	// say which, and on Path A only the threaded one is evidence about the\n"
     "	// money. The rule is PER SITE, not a slogan: on a 0-dp / inMultiplesOf\n"
     "	// shape it inverts -- the ambient mode moves 23 cells and the threaded\n"
     "	// mode moves none."),
])

print("\n".join(LOG))
