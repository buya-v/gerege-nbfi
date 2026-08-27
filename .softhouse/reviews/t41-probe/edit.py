#!/usr/bin/env python3
"""T41 — DEC-1 revision 7 -> revision 8. Exact-string edits with occurrence asserts.

Every replacement asserts its expected occurrence count, so a silent no-op or an
accidental multi-site edit is impossible. Run repeatedly is NOT safe; run once.

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
PRE-FIX bytes exited 1 at an anchor (`FAIL: expected 1 occurrence(s), found 0 for:`)
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
  DEC-1        BEFORE_SHA256 = 35e513cdec69913caed759daee92626f2248c5c6fe2ca9ead6ed9968dc5f78e2
  DEC-1        AFTER_SHA256  = 803aa922560581b03fffaa3c3b91a1b292ce8245ce0c31308b85105703d83c71

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


NAME = 'edit'

# The exact phrase that authorises a run.  Long, self-describing, argv-only -
# never an environment variable: an env var is exported once in a wrapper,
# inherited by every child and then forgotten, whereas an argv word must be
# retyped at every invocation and is recorded in the process table.
AUTHORISE_TOKEN = (
    'I-AM-REPRODUCING-T41-EDIT-ON-A-SCRATCH-COPY-NOT-THE-RATIFIED-DEC-1')

BEFORE_SHA256 = \
    '35e513cdec69913caed759daee92626f2248c5c6fe2ca9ead6ed9968dc5f78e2'
AFTER_SHA256 = \
    '803aa922560581b03fffaa3c3b91a1b292ce8245ce0c31308b85105703d83c71'

s = guard.load(NAME, __file__, AUTHORISE_TOKEN, BEFORE_SHA256,
               AFTER_SHA256, guard.RATIFIED_ADR)

LOG = []


def sub(old, new, n=1):
    global s
    c = s.count(old)
    if c != n:
        sys.exit("FAIL: expected %d occurrence(s), found %d for:\n%s" % (n, c, old[:200]))
    s = s.replace(old, new)
    LOG.append("ok (%d): %s" % (n, old[:80].replace("\n", " ")))


# =============================================================================
# CORRECTION 3 (T39 N-3) — ambient vs threaded MathContext, in section 4.1
# =============================================================================

sub(
    "**Revision 7 replaces the source inference with an ATTESTATION, because one now exists.** "
    "Both halves of `(19, HALF_UP)` have been measured against the *deployed artefact* rather than "
    "only read in the source tree:",

    "**Revision 7 replaced the source inference with an ATTESTATION, because one now exists. "
    "Revision 8 states precisely WHAT each half of that attestation is evidence OF** (P1-T39-1, "
    "from task T39's finding N-3, plus a re-derivation this task added to explain it). Both halves "
    "of `(19, HALF_UP)` have been measured against the *deployed artefact* rather than only read "
    "in the source tree. **But an attestation of the AMBIENT `MoneyHelper` context and an "
    "attestation of the THREADED `MathContext` are two different claims, and on the Path-A seam "
    "only the second is evidence about the money** — §4.1.2 states the rule, its mechanism and "
    "its falsification test. Each bullet below is tagged with which context it witnesses:",
)

sub(
    "- **Precision.** `javap -p -constants` over `BOOT-INF/lib/fineract-core-1.16.0-SNAPSHOT.jar` "
    "**inside the running container** prints `public static final int PRECISION = 19;` "
    "[VERIFIED: task T36, `.softhouse/capture/pathb/t36/out/recapture-gerege/attestation.json`]. "
    "Task T35 read the same constant at runtime on the Path-A rig.",

    "- **Precision — witnesses the AMBIENT context, and the code constant behind it.** "
    "`javap -p -constants` over `BOOT-INF/lib/fineract-core-1.16.0-SNAPSHOT.jar` **inside the "
    "running container** prints `public static final int PRECISION = 19;` [VERIFIED: task T36, "
    "`.softhouse/capture/pathb/t36/out/recapture-gerege/attestation.json`; independently by task "
    "T40, `.softhouse/capture/charges/out/attested/attestation.json`]. Task T35 read the same "
    "constant at runtime on the Path-A rig. `PRECISION` is the compile-time constant "
    "`MoneyHelper.getMathContext()` builds its `MathContext` from [`MoneyHelper.java:35`, "
    "`:91-93`], so this is an attestation of **`MoneyHelper`'s** precision. On Path A the harness "
    "threads its own `MathContext` and the two coincide by construction of the rig, not by "
    "inference — the capture asserts the threaded precision separately [VERIFIED: T39, "
    "`.softhouse/capture/periodratio/ATTESTATION.md`, threaded `(19, HALF_UP)` on fifteen of "
    "sixteen, `(12, HALF_UP)` on the labelled calibration only].",
)

sub(
    "- **Mode.** Read three independent ways on the `gerege` tenant: the "
    "`c_configuration.rounding-mode` row (**4**, enabled), **this JVM run's own** `MoneyHelper` "
    "initialisation line, and a **behavioural canary** — `1,162,502.50 × 0.018 = 20,925.045` comes "
    "back `20925.05` on `gerege` and `20925.04` on the stock `default` tenant in the same run "
    "[VERIFIED: T36; and T37's Path-A log, 11 of 11 lines `HALF_UP`].",

    "- **Mode — two of the three readings witness the AMBIENT context; the third witnesses "
    "arithmetic, on the path it ran on.** Read three independent ways on the `gerege` tenant: the "
    "`c_configuration.rounding-mode` row (**4**, enabled) and **this JVM run's own** `MoneyHelper` "
    "initialisation line are both statements about the **tenant configuration**, i.e. about what "
    "`MoneyHelper.getMathContext()` returns; the **behavioural canary** — "
    "`1,162,502.50 × 0.018 = 20,925.045` comes back `20925.05` on `gerege` and `20925.04` on the "
    "stock `default` tenant in the same run — is a statement about **arithmetic**, and it is a "
    "**Path-B** statement, taken through the running server where no caller threads a "
    "`MathContext` [VERIFIED: T36; T40 re-ran the same canary and got `20925.05`, "
    "`.softhouse/capture/charges/out/attested/`; and T37's Path-A log, 11 of 11 lines `HALF_UP`]. "
    "**None of the three is, by itself, evidence about the mode in force on a Path-A capture** "
    "— §4.1.2.",
)

sub(
    "So where this document says \"the production `MathContext` is `(19, HALF_UP)`\" it is now "
    "citing an attestation of the artefact that produced the captures, not an inference from "
    "source.",

    "So where this document says \"the production `MathContext` is `(19, HALF_UP)`\" it is citing "
    "an attestation of the artefact that produced the captures, not an inference from source. "
    "**Revision 8 adds the scope that attestation carries:** it attests the ambient "
    "`MoneyHelper` context and, separately and by its own assertions, the threaded context each "
    "capture ran at. Where a claim in this document is about **money**, the threaded reading is "
    "the citation; where it is about **provenance or tenant configuration**, the ambient reading "
    "is. §4.1.2 makes that split normative and falsifiable.",
)

# --- 4.1's "One mode, not three" -------------------------------------------
sub(
    "**One mode, not three.** The oracle takes every tie rule from one of two places — the "
    "threaded `MathContext` where one is passed, and the tenant-global one where one is not "
    "[`Money.java:52`; `:102-104`; `:150-157`; `:159-161` and `:163-170`, whose return path goes "
    "through the two-argument `Money.of` and therefore reads tenant-global state even though its "
    "own division used the threaded context]. Independently settable modes would admit "
    "combinations no deployment can produce.",

    "**One mode, not three.** The oracle takes every tie rule from one of two places — the "
    "threaded `MathContext` where one is passed, and the tenant-global one where one is not. "
    "**Which of the two applies is decided by one line, and revision 8 cites it rather than "
    "leaving it to `Money.java:52` to imply:** `Money` carries its own `MathContext` field "
    "[`Money.java:32`] and `getMc()` returns **that field when it is non-null**, falling back to "
    "`MoneyHelper.getMathContext()` only when it is null [`Money.java:494-496`]. So the "
    "constructor's own currency-scale `setScale(decimalPlaces, getMc().getRoundingMode())` "
    "[`Money.java:52`] reads the **threaded** mode whenever one was threaded — `this.mc` is "
    "assigned at `:42`, before `:52` runs — and the **tenant-global** mode only where no context "
    "was threaded: the two-argument `Money.of` [`:102-104`, `:114-116`], `Money.zero(currency)` "
    "[`:118-120`], the static `roundToMultiplesOf(BigDecimal, Integer)` [`:150-157`], "
    "`roundToMultiplesOf(Money, Integer)` [`:159-161`] and the three-argument form's return path "
    "[`:163-170`, which goes through the two-argument `Money.of` at `:169` even though its own "
    "division used the threaded context], and `multipliedBy(double)` [`:372-378`, the "
    "two-argument `Money.of` at `:377`]. Independently settable modes would admit combinations no "
    "deployment can produce. **Revision 7 cited `:52` as the tenant-global source; that was "
    "imprecise, and §4.1.2 records what the imprecision cost.**",
)

# --- 4.1's adapter obligation ----------------------------------------------
sub(
    "and the `Money` constructor reads only the **rounding mode** from `getMc()` "
    "[`Money.java:52`], never the precision. The call sites that do read the tenant-global "
    "precision [`Money.java:103`, `:115`, `:160`, `:377`] all sit on the installment-multiple and "
    "`multipliedBy(double)` paths, which the graded domain excludes (§4.7). So no reached call "
    "site consults the tenant-global precision — established from source, not inferred from a "
    "precision-insensitive capture.",

    "and the `Money` constructor reads only the **rounding mode** from `getMc()` "
    "[`Money.java:52`], never the precision — and, revision 8 adds, on a `Money` built through "
    "the three-argument form `getMc()` **is the threaded context** [`Money.java:494-496`], so "
    "that read is not a tenant-global read at all. The call sites that do reach the tenant-global "
    "context [`Money.java:103`, `:115`, `:160`, `:377`] all sit on the installment-multiple and "
    "`multipliedBy(double)` paths, which the graded domain excludes (§4.7). So no reached call "
    "site consults the tenant-global precision **or the tenant-global mode** — established from "
    "source, not inferred from a precision-insensitive capture, and now **confirmed by a negative "
    "test**: forcing the tenant mode to `DOWN` left all sixteen T39 capture blocks byte-identical "
    "[VERIFIED: T39 N-3, `.softhouse/capture/periodratio/out/t39-neg5.json` versus "
    "`out/t39-periodratio.json`, 0 of 16 differ]. **The obligation to initialise the tenant mode "
    "before every call therefore does NOT rest on that mode changing the answer inside the graded "
    "domain — observation says it does not. It rests on the fact that an uninitialised tenant "
    "THROWS** [`MoneyHelper.java:74-82`, `:91-93`], which turns a silently different number into "
    "a loud failure and is the stronger reason of the two.",
)

# --- 4.1 mode value domain ---------------------------------------------------
sub(
    "The mode is demonstrably live, not a dead knob: *observed*, the same request put to two "
    "tenants of one running oracle differing only in rounding mode returned period-1 interest "
    "**20,925.05** under HALF_UP and **20,925.04** under HALF_EVEN on principal MNT 1,162,502.50, "
    "the tie taken at `Money.java:52`.",

    "The mode is demonstrably live, not a dead knob: *observed*, the same request put to two "
    "tenants of one running oracle differing only in rounding mode returned period-1 interest "
    "**20,925.05** under HALF_UP and **20,925.04** under HALF_EVEN on principal MNT 1,162,502.50, "
    "the tie taken at `Money.java:52`. **That observation is a PATH-B one and revision 8 says so** "
    "(§4.1.2): through the running server nothing threads a `MathContext`, so `getMc()` takes "
    "the null branch [`Money.java:494-496`] and the tenant-global mode **is** the arithmetic. On "
    "**Path A** the same tenant-mode change moves nothing, because a context is threaded "
    "[VERIFIED: T39 N-3, 0 of 16 blocks differ] — the two results are consistent, not "
    "contradictory, and §4.1.2 is why.",
)

guard.commit(s)
print("\n".join(LOG))
print("EDITS APPLIED: %d" % len(LOG))
