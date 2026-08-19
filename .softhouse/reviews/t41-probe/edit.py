#!/usr/bin/env python3
"""T41 — DEC-1 revision 7 -> revision 8. Exact-string edits with occurrence asserts.

Every replacement asserts its expected occurrence count, so a silent no-op or an
accidental multi-site edit is impossible. Run repeatedly is NOT safe; run once.
"""
import io
import sys

P = "docs/adr/DEC-1-schedule-generator-adapter.md"
s = io.open(P, encoding="utf-8").read()
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

io.open(P, "w", encoding="utf-8").write(s)
print("\n".join(LOG))
print("EDITS APPLIED: %d" % len(LOG))
