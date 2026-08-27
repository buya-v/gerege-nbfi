#!/usr/bin/env python3
"""T207 -- SCRATCH SUCCESSOR to `t44_float_roundtrip_v2.py`.  The verdict question, decided.

USAGE
    python3 t44_float_roundtrip_v3.py <glob> [<glob> ...] [--expect-skips N]
    python3 t44_float_roundtrip_v3.py --selftest

Exit 0 = something was inspected; nothing was swallowed unacknowledged; and NO inspected
         literal CHANGES VALUE under a binary-double round trip.
Exit 1 = any of those failed.

================================================================================================
WHY THIS FILE EXISTS -- three defects in `_v2`, one of which is a decision
================================================================================================

**D-1 (T185's F-1).  `_v2` DETECTS VALUE CORRUPTION AND THEN REPORTS `PASS`.**
`_v2:170-182` computes `lossy_value` -- the literals for which
`Decimal(repr(float(s))) != Decimal(s)`, i.e. the literals a float-shaped consumer would read
as A DIFFERENT AMOUNT OF MONEY.  It prints them under "VALUE-lossy examples".  It never appends
them to `failures`.  So `_v2:206` prints `T175 SUCCESSOR: PASS` and `main` returns 0 on a
corpus containing a value-corrupted money literal.  [VERIFIED: `_v2` read line by line this
fire; the string `lossy_value` occurs at `:170`, `:176`, `:177`, `:190` and NOWHERE inside any
`failures.append(...)`; driven RED in `T207-red/`.]

That is P-22 in its purest form: a detector that cannot fail is worse than no detector,
because it is believed.

**D-2.  THE PASS BANNER AND THE VERDICT MACHINERY ARE NEW IN THE SUCCESSOR.**
[VERIFIED: `t44_float_roundtrip.py` -- the original -- read in full this fire. It has NO
`failures` list, NO `main()`, NO `return`/`sys.exit`, NO PASS or FAIL banner, and its committed
transcript `t44_float_roundtrip-output.txt` contains no verdict word at all.  It is a pure
MEASUREMENT script whose exit status is whatever Python's happy path gives it.]  T175 added
`failures`, the exit codes and the `PASS` banner.

**D-3.  `_v2` CARRIES A STATEMENT ABOUT ITSELF THAT IS NO LONGER TRUE.**
`_v2:169` reads `# HAZARD CHARACTERISATION ONLY - these floats never touch a verdict.`,
inherited verbatim from the original's `:37`.  In the ORIGINAL that sentence was TRUE and
correct, because the original has no verdict.  In `_v2` there IS a verdict, and the comment is
the reason nobody wired the strongest measurement in the file to it.  A false self-description
is how D-1 survived review.

================================================================================================
THE RULING -- may a float-derived predicate reach a verdict here?  YES, AND HERE IT MUST.
================================================================================================
Full argument: `T207/RULING-float-derived-predicate.md`.  The load-bearing steps:

**1. WHICH REGION.  ZONE A -- the oracle-facing wire -- response leg.**  T186 §7: "*Path
decides the rule.*"  This instrument's corpus is `.softhouse/capture/**/out/*.json`: captured
oracle RESPONSES.  Not `nexus/**` (Zone B), not `.softhouse/vectors/**` (Zone C).

**2. ZONE A ALREADY GATES ON A FLOAT-DERIVED PREDICATE, BY RATIFIED DECISION.**  T186's own
enforcement rule A1 is `repr(float(tok)) == tok` -- a predicate that cannot be evaluated
without constructing the float -- and T186 records it as "*already implemented and wired*" in
`.softhouse/capture/lib/check_wire_float_roundtrip.py`, invoked from `conformance.sh`
[VERIFIED: invocation live at `conformance.sh:997`; T186 cites `:784`, which has drifted].
That guard's own docstring settles the principle in terms this file adopts verbatim:

    THE ONE DELIBERATE `float()` (P-25)
    The line marked SIMULATE calls `float()` on purpose: it SIMULATES THE DEFECT, which is
    the only way to measure it.  No money conclusion is drawn from it -- the comparison is
    between two STRINGS.
    [VERIFIED: check_wire_float_roundtrip.py, docstring]

So "may a float-derived predicate gate in Zone A" is not an open question.  It was answered
YES, it is answered YES *today*, on every conformance run.  Answering NO here would not be a
cautious reading of the non-negotiable; it would be an unlicensed reversal of A1.

**3. THE NON-NEGOTIABLE BANS FLOATS FROM CARRYING VALUE, NOT FROM BEING MEASURED.**
`CLAUDE.md`: "*no floating-point in any monetary code path, struct field, schema column, API
field, or test fixture -- including intermediate calculation.*"  Every one of those nouns names
a place a float would HOLD AN AMOUNT.  In this file no amount is ever a float: the recording
hook returns `Decimal(s)`, every comparison is `Decimal` against `Decimal` or `str` against
`str`, and the only thing a `float()` ever produces is a BOOLEAN.  Reading the rule the other
way is self-defeating -- it forbids the one mechanism that can detect a float hazard, leaving
the FIRST non-negotiable enforceable only by assertion, which is P-22 again one level up.

**4. WHICH predicate gates -- P3 (value), not P2 (bytes).**  T186 §6.3 measured 245 P2 failures
corpus-wide and found "*all 245 P2 failures are trailing-zero decimal forms ... scale-6
emissions by Fineract itself on the RESPONSE leg, matching DECIMAL(19,6). The value is intact
in every one*", and T186's rule A4 says of responses: "*never rewrite, never re-emit through a
float, never normalise scale. `1200000.000000` is not a typo for `1200000.0`; the scale
witnesses `DECIMAL(19,6)`.*"  So on THIS corpus P2 has 41 legitimate failures already
[VERIFIED: `t44_float_roundtrip-output.txt:6`] and CANNOT be the gate -- gating on it would
refuse the oracle's own correct output.  P3 -- value change -- is what remains, and P3 failure
strictly implies P2 failure (if the text round-trips, the values are equal), so P3 is the
narrower, stronger event.

**5. THE ONE COUNTER-ARGUMENT, ANSWERED RATHER THAN OMITTED.**  T186 §6.4 says: "*it is also
why P3 should not be adopted as the guard property: it would pass a corpus that had already
drifted badly, and it will keep passing right up until it doesn't.*"  That sentence is about
A1, the REQUEST-BODY guard, where P2 is available and is strictly stronger; there, P3 is
redundant.  It is not a ruling that P3 must be SILENT when it fires, and no reading of it makes
`detect -> print PASS` correct.  "Too weak to be the only alarm" is not "must not ring".
[This is T207's reading of a T186 sentence written in a narrower context.  T186 did not rule on
the response leg.  Marked as inference, not as T186's words.]

================================================================================================
WHAT CHANGED FROM `_v2`, EACH CHANGE NAMED (T163's declared-widenings discipline)
================================================================================================
R1  VALUE-LOSS NOW FAILS THE RUN.  `lossy_value` is appended to `failures`, naming every
    literal and its residue in exact `Decimal`.  This is D-1's fix and step 1-5's consequence.
R2  TEXT-LOSS EXPLICITLY DOES NOT GATE, and the reason is printed on every run, so no later
    reader "tightens" it into a rejection of the oracle's own scale-6 emissions (T186 A4).
R3  THE FALSE SELF-DESCRIPTION IS GONE.  `_v2:169`'s comment is replaced by an accurate one.
R4  THE BARE WORD `PASS` IS GONE FROM THE SUCCESS BANNER.  A green run of this instrument
    establishes something narrow, and the banner now says what, and says what it does not
    (P-3: a green run says nothing about unexercised behaviours).
R5  POPULATION INSPECTED IS STATED, in the shape `guard_ledger_invariants` uses -- including
    the `NIL-COVERAGE — ... inspected an empty population` line when a stage inspects nothing
    [VERIFIED shape: `.softhouse/guards/ledgerguard/main.go:840,847,852`].
R6  `--selftest`.  P-22 forbids shipping a guard nobody has driven red.  The selftest asserts
    the value predicate fires on constructed literals and stays quiet on the ones that
    genuinely round-trip, and it FAILS if either half is silent.
R7  A ZERO-LITERAL corpus stays an error, and a nonzero-skip corpus still needs
    `--expect-skips N` -- `_v2`'s behaviours, kept, not re-litigated.

WHAT IS UNCHANGED: the arithmetic.  Every amount is `decimal.Decimal` from exact text.  The
recording hook returns `Decimal(s)` and never a float.  Over the legitimate corpus this file
reports the same 245 / 9,122 / max-scale-6 / 41 text-lossy / 0 value-lossy as `_v2` and as the
original -- see `T207-red/`.

T114: `t44_float_roundtrip.py` and `t44_float_roundtrip_v2.py` BOTH produced committed
evidence and are left byte-identical.  See `T207/T207-SUPERSEDES.md`.
"""
import glob
import json
import sys
from decimal import Decimal

seen = {}          # exact literal text -> occurrence count
per_file = {}      # path -> literals contributed
SKIPS = []         # (path, exception type, exception message)


def make_hook(path):
    def hook(s):
        seen[s] = seen.get(s, 0) + 1
        per_file[path] = per_file.get(path, 0) + 1
        return Decimal(s)            # NEVER a float on the recording path
    return hook


# ---------------------------------------------------------------------------------------------
# THE TWO PREDICATES.
#
# Each one deliberately constructs a binary double, for the same reason
# check_wire_float_roundtrip.py does: SIMULATING the defect is the only way to measure it.
# Neither returns a number.  Both return a bool, and every value they compare is a str or a
# Decimal built from exact text.  No amount in this program is ever held in a float.
# ---------------------------------------------------------------------------------------------
def p2_text_lossy(s):
    """Would a float round trip change the CHARACTERS?  On the RESPONSE leg this is EXPECTED
    and LEGITIMATE (T186 A4: `1200000.000000` is a DECIMAL(19,6) scale witness, not a typo),
    so it is REPORTED and never gated on here.  It IS the gate for REQUEST bodies, enforced
    elsewhere by check_wire_float_roundtrip.py -- not duplicated here."""
    return repr(float(s)) != s


def p3_value_lossy(s):
    """Would a float round trip change the AMOUNT?  This is the gate.  P3 implies P2."""
    return Decimal(repr(float(s))) != Decimal(s)


def residue(s):
    """How much money the round trip would invent or destroy, exactly."""
    return Decimal(repr(float(s))) - Decimal(s)


# ---------------------------------------------------------------------------------------------
def selftest():
    """P-22: a guard nobody has driven red has not been tested. Both halves are asserted."""
    print("T207 t44_float_roundtrip_v3 --selftest")
    print()
    # (literal, expect_p2, expect_p3, why)
    CASES = [
        # -- must NOT fire P3: real corpus shapes. Scale witnesses fail P2 on purpose.
        ("1200000.00",            True,  False, "MNT stored to 2 dp; observed in the corpus"),
        ("1200000.000000",        True,  False, "exactly what DECIMAL(19,6) emits (T186 A4)"),
        ("0.10",                  True,  False, "ten mongo"),
        ("21.6",                  False, False, "the corpus's only real rate literal"),
        ("1162502.5",             False, False, "the T149/T153 half-cent TIE probe principal"),
        ("13158.1",               False, False, "from t44_float_roundtrip-output.txt"),
        # -- must fire P3: value really changes.
        ("1234567890123.456789",  True,  True,  "an ordinary numeric(19,6) value, 19 sig digits"),
        ("9999999999999.999999",  True,  True,  "numeric(19,6) near its own maximum"),
        ("12345678901234567890.12", True, True, "past binary64; T163 measured residue -890.12"),
        ("9007199254740993.00",   True,  True,  "2**53+1: the textbook binary64 cliff"),
    ]
    fails = []
    n_p2 = n_p3 = 0
    for s, want2, want3, why in CASES:
        got2, got3 = p2_text_lossy(s), p3_value_lossy(s)
        n_p2 += got2
        n_p3 += got3
        ok = (got2 == want2) and (got3 == want3)
        print("  %-6s %-26s P2=%-5s(want %-5s) P3=%-5s(want %-5s) residue=%-12s %s"
              % ("OK" if ok else "WRONG", s, got2, want2, got3, want3, residue(s), why))
        if not ok:
            fails.append(s)
    print()
    print("  cases                    : %d" % len(CASES))
    print("  cases that fired P2      : %d" % n_p2)
    print("  cases that fired P3      : %d" % n_p3)
    # P-35 shape: POSITIVE assertions, both directions, and a count that cannot be zero.
    if n_p3 == 0:
        fails.append("NO case fired the value predicate -- the gate is unfalsifiable (P-22)")
        print("  *** NO case fired P3. A gate no case can trip is not a gate.")
    if n_p3 == len(CASES):
        fails.append("EVERY case fired the value predicate -- the gate refuses everything")
        print("  *** EVERY case fired P3. A gate that refuses everything is not a gate.")
    if not any(p2_text_lossy(s) and not p3_value_lossy(s) for s, _, _, _ in CASES):
        fails.append("no case separates P2 from P3 -- the two predicates are not shown distinct")
    print()
    if fails:
        print("SELFTEST FAILED -- %d:" % len(fails))
        for f in fails:
            print("  FAIL  %s" % f)
        return 1
    print("SELFTEST OK -- %d cases, %d fire the value gate, %d fire only the text predicate."
          % (len(CASES), n_p3, n_p2 - n_p3))
    print("Both directions exercised, and P2 and P3 are shown to be DIFFERENT predicates.")
    return 0


# ---------------------------------------------------------------------------------------------
def main(argv):
    if argv and argv[0] == "--selftest":
        return selftest()

    expect_skips = None
    pats = []
    i = 0
    while i < len(argv):
        if argv[i] == "--expect-skips":
            expect_skips = int(argv[i + 1])
            i += 2
            continue
        pats.append(argv[i])
        i += 1

    paths = []
    for pat in pats:
        paths.extend(sorted(glob.glob(pat, recursive=True)))

    print("T207 v3 of t44_float_roundtrip -- float round-trip hazard on captured ORACLE")
    print("RESPONSES, with every skipped file NAMED and COUNTED, and with VALUE CORRUPTION")
    print("WIRED TO THE VERDICT (T185 F-1; ruling in T207/RULING-float-derived-predicate.md).")
    print()
    print(f"  glob patterns given : {len(pats)}")
    for pat in pats:
        print(f"      {pat}   -> {len(sorted(glob.glob(pat, recursive=True)))} file(s)")
    print(f"  files REQUESTED     : {len(paths)}")

    failures = []
    if not pats:
        failures.append("no glob pattern was given -- a scan with no input is an ERROR, not a "
                        "clean report (P-35)")
    if not paths:
        failures.append("the globs matched ZERO files -- a scan that inspects nothing is an "
                        "ERROR, not a pass (P-35)")

    parsed = 0
    for p in paths:
        try:
            json.load(open(p), parse_float=make_hook(p))
        except Exception as exc:              # NAMED AND COUNTED -- never a bare `pass`
            SKIPS.append((p, type(exc).__name__, str(exc)))
            continue
        parsed += 1
        per_file.setdefault(p, 0)

    print(f"  files PARSED        : {parsed}")
    print(f"  files SKIPPED       : {len(SKIPS)}      <-- t44_float_roundtrip.py:29 discarded "
          f"these silently")
    print()

    # ---------------------------------------------------------------- SKIP REGISTER
    print("=" * 96)
    print(f"SKIP REGISTER -- {len(SKIPS)} file(s) could not be parsed and were NOT scanned.")
    print("Printed on EVERY run, including a clean one, so a reader never has to infer a zero")
    print("from a silence.")
    print("=" * 96)
    if not SKIPS:
        print("  0 files skipped.  Every one of the "
              f"{len(paths)} requested files was parsed and scanned.")
    else:
        for p, etype, emsg in SKIPS:
            print(f"  UNSCANNED  {p}")
            print(f"             {etype}: {emsg}")
        if expect_skips is None:
            failures.append(
                f"{len(SKIPS)} file(s) were skipped and no --expect-skips was given. A skipped "
                f"file is an UNSCANNED file; the report below covers {parsed} of {len(paths)} "
                f"requested files, NOT all of them.")
        elif expect_skips != len(SKIPS):
            failures.append(
                f"--expect-skips {expect_skips} was given but {len(SKIPS)} file(s) were "
                f"skipped -- the acknowledged set and the actual set differ.")
        else:
            print()
            print(f"  ACKNOWLEDGED: --expect-skips {expect_skips} matches. The {len(SKIPS)} "
                  f"file(s) above were NOT scanned;")
            print(f"  every figure below is over {parsed} of {len(paths)} requested files.")

    # ---------------------------------------------------------------- the measurement
    print()
    print("=" * 96)
    print(f"FLOAT ROUND-TRIP HAZARD -- over {parsed} of {len(paths)} requested file(s)")
    print("=" * 96)
    print("  POPULATION INSPECTED : "
          f"{parsed} file(s) parsed of {len(paths)} requested; {len(SKIPS)} unscanned; "
          f"{sum(seen.values())} numeric token(s) seen.")
    print(f"  distinct bare non-integer literals : {len(seen)}")
    print(f"  total occurrences                  : {sum(seen.values())}")
    files_with_literals = sum(1 for v in per_file.values() if v)
    print(f"  files carrying at least one        : {files_with_literals} of {parsed} parsed")

    if parsed and not seen:
        # R5: the NIL-COVERAGE shape used by guard_ledger_invariants.
        print()
        print(f"  NIL-COVERAGE — {parsed} file(s) parsed but ZERO bare non-integer literals "
              f"exist in them, so the value")
        print("  gate below inspected an empty population and establishes NOTHING about this "
              "corpus.")
        failures.append(
            f"{parsed} file(s) parsed but ZERO bare non-integer literals were found. That may "
            f"be the honest answer, but this script exists to characterise literals it has "
            f"actually seen, so an empty sample is an ERROR here, not a clean bill of health "
            f"(P-35). Point it at a corpus that has some, or use t44_float_scan.py, which is "
            f"the script whose job is to report a genuine zero.")

    # -----------------------------------------------------------------------------------------
    # R3: what the floats below DO and DO NOT do.
    #
    # They are constructed ON PURPOSE, and one of them DOES reach the verdict -- see R1 and the
    # ruling in the module docstring.  What they never do is HOLD AN AMOUNT: `seen` is keyed by
    # exact source text, the parse hook returns Decimal, and every comparison below is between
    # two strings or two Decimals.  `_v2:169` claimed "these floats never touch a verdict",
    # which was true of the ORIGINAL (it has no verdict) and false of `_v2` the moment T175 gave
    # it one.
    # -----------------------------------------------------------------------------------------
    lossy_text, lossy_value, max_scale = [], [], 0
    for s in seen:
        max_scale = max(max_scale, -Decimal(s).as_tuple().exponent)
        if p2_text_lossy(s):
            lossy_text.append((s, repr(float(s))))
        if p3_value_lossy(s):
            lossy_value.append((s, repr(float(s)), residue(s), seen[s]))

    print()
    print(f"  max decimal scale seen                    : {max_scale}")
    print(f"  literals whose float repr() != the text   : {len(lossy_text)} of {len(seen)}"
          f"   [REPORTED, NOT GATED -- see below]")
    print(f"  literals whose float VALUE != the decimal : {len(lossy_value)} of {len(seen)}"
          f"   [*** THIS IS THE GATE ***]")
    print()
    if lossy_text:
        print("  text-lossy examples:")
        for s, r in lossy_text[:12]:
            print(f"    {s!r:>18}  ->  {r}")
        print()
    print("  WHY TEXT-LOSS DOES NOT FAIL THIS RUN, stated every time so nobody 'tightens' it:")
    print("    these are scale witnesses on the RESPONSE leg. T186 rule A4 -- a response is an")
    print("    OBSERVATION: never rewrite it, never normalise its scale; `1200000.000000` is")
    print("    not a typo for `1200000.0`, it witnesses DECIMAL(19,6). Gating on text-loss here")
    print("    would refuse the oracle's own correct output. Byte-fidelity IS the gate for")
    print("    REQUEST BODIES, enforced by .softhouse/capture/lib/check_wire_float_roundtrip.py")
    print("    from conformance.sh -- and is NOT duplicated here.")

    # ---------------------------------------------------------------- R1: THE GATE
    if lossy_value:
        print()
        print("  " + "!" * 92)
        print("  VALUE-CORRUPTED MONEY LITERALS -- each of these is read as a DIFFERENT AMOUNT")
        print("  by any consumer that parses this capture through a binary double:")
        for s, r, res, occ in lossy_value[:24]:
            print(f"    {s!r:>26}  ->  {r:<26} residue {res}   ({occ} occurrence(s))")
        if len(lossy_value) > 24:
            print(f"    ... {len(lossy_value) - 24} more")
        print("  " + "!" * 92)
        failures.append(
            f"{len(lossy_value)} of {len(seen)} distinct literal(s) CHANGE VALUE under a "
            f"binary-double round trip, across {sum(o for _, _, _, o in lossy_value)} "
            f"occurrence(s). The capture wire is float-shaped, so this corpus can no longer "
            f"be consumed by any float-shaped reader without corrupting money. Largest "
            f"residue: {max((abs(res) for _, _, res, _ in lossy_value))}.")

    if seen and not lossy_value:
        print()
        print(f"  => over the {len(seen)} distinct literals actually inspected, in "
              f"{parsed} of {len(paths)} requested")
        print("     files, NO literal changes VALUE on a float round-trip at these magnitudes")
        print("     and scales. The hazard is structural: the wire format is float-shaped, so a")
        print("     consumer that does not force exact decimal parsing violates the money rule")
        print("     by construction, and would corrupt a value as soon as a magnitude or a")
        print("     scale grows. THIS SENTENCE IS SCOPED TO THE DENOMINATORS ABOVE and says")
        print(f"     nothing whatever about the {len(SKIPS)} file(s) in the SKIP REGISTER.")
        print("     T186 §6.4: this margin is enormous, not marginal -- which is exactly why a")
        print("     zero here is weak evidence, and why it is nevertheless WIRED: it costs")
        print("     nothing while green and is the only alarm available on the response leg.")

    print()
    if failures:
        print(f"T207 v3: FAILED -- {len(failures)} breach(es):")
        for f in failures:
            print("  FAIL  " + f)
        return 1
    # R4: no bare "PASS". Say what was established and what was not.
    print(f"T207 v3: NO VALUE CORRUPTION DETECTED -- {parsed} of {len(paths)} files scanned, "
          f"{len(SKIPS)} skipped, {len(seen)} distinct literals inspected.")
    print("  ESTABLISHES: none of those literals changes VALUE under a binary-double round")
    print("               trip, and no requested file went unscanned unacknowledged.")
    print("  DOES NOT ESTABLISH: that the corpus is float-safe (it is not -- the wire is")
    print("               float-shaped by design, T186 Zone A); that any Go code is correct;")
    print("               that any vector is admissible; or anything at all about a file")
    print("               outside the globs above.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
