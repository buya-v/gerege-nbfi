#!/usr/bin/env python3
"""T175 -- SUCCESSOR to `t44_float_roundtrip.py`.  De-vacuumed.

WHY THIS FILE EXISTS
--------------------
`t44_float_roundtrip.py` is COMMITTED EVIDENCE and is left byte-identical (T114's ruling).  It
carries one silent swallow, at its lines 26-30:

    for p in paths:
        try:
            json.load(open(p), parse_float=hook)
        except Exception:
            pass

A file the scan cannot parse is SKIPPED WITHOUT A WORD.  The report that follows -- "distinct
bare non-integer literals", "total occurrences", "literals whose float VALUE != the decimal" --
is then a statement about an INSPECTED denominator that the reader has no way to learn.  Handed
a glob that matches nothing parseable, the script prints `distinct: 0`, `occurrences: 0` and
then the reassurance "=> no literal changes VALUE on a float round-trip", which reads as a clean
bill of health for a scan that examined nothing.  That is a vacuous pass sitting directly on the
FIRST non-negotiable in CLAUDE.md: money is integer minor units, no floating point anywhere.

Its own sibling `t44_float_scan.py` gets this right -- `except Exception as e: print(f"  {p}:
UNPARSEABLE ({e})")` -- which is how we know the corpus really does contain unparseable inputs.

WHAT THIS SUCCESSOR CHANGES -- and NOTHING ELSE
-----------------------------------------------
1. SKIP REGISTER.  Every unparseable file is NAMED (path, exception type, exception message)
   and COUNTED, and the register is printed on EVERY run, including a run with zero skips.
2. A non-zero skip count FAILS the run by default.  If the skips are legitimate and expected,
   the caller must say so explicitly with `--expect-skips N`, where N must match EXACTLY; the
   count is still printed prominently, and it is never rendered as zero.
3. ZERO INSPECTED IS AN ERROR (P-35): zero files requested, zero files parsed, or zero literals
   seen each fail the run instead of producing a confident-looking report about nothing.
4. Every published figure is scoped to its denominator in the line that prints it -- "over N of
   M requested files" -- so a count can never be read as covering more than it did.

The arithmetic is UNCHANGED.  The `float()` calls below exist ONLY to characterise the hazard,
exactly as in the original, and are labelled; every VERDICT is computed on `decimal.Decimal`
built from exact text (CLAUDE.md non-negotiable 1; patterns.md P-25).

USAGE
    python3 t44_float_roundtrip_v2.py <glob> [<glob> ...] [--expect-skips N]

The recipe that reproduces the ORIGINAL committed output byte-for-byte, from the repo root
[VERIFIED by T175: diff against t44_float_roundtrip-output.txt was empty], is:

    python3 .../t44_float_roundtrip.py \
        '.softhouse/capture/periodratio/out/*.json' \
        '.softhouse/capture/mathcontext/out/*.json' \
        '.softhouse/capture/charges/out/fc/*.json' \
        '.softhouse/capture/charges/out/attested/*.json'

Exit 0 = something was inspected, and nothing was swallowed (or the skips matched
         --expect-skips exactly).
Exit 1 = nothing was inspected, or an unacknowledged file was swallowed.
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


def main(argv):
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

    print("T175 SUCCESSOR to t44_float_roundtrip.py -- float round-trip hazard, with every")
    print("skipped file NAMED and COUNTED.")
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
    print(f"  distinct bare non-integer literals : {len(seen)}")
    print(f"  total occurrences                  : {sum(seen.values())}")
    files_with_literals = sum(1 for v in per_file.values() if v)
    print(f"  files carrying at least one        : {files_with_literals} of {parsed} parsed")

    if parsed and not seen:
        failures.append(
            f"{parsed} file(s) parsed but ZERO bare non-integer literals were found. That may "
            f"be the honest answer, but this script exists to characterise literals it has "
            f"actually seen, so an empty sample is an ERROR here, not a clean bill of health "
            f"(P-35). Point it at a corpus that has some, or use t44_float_scan.py, which is "
            f"the script whose job is to report a genuine zero.")

    # HAZARD CHARACTERISATION ONLY - these floats never touch a verdict.
    lossy_text, lossy_value, max_scale = [], [], 0
    for s in seen:
        max_scale = max(max_scale, -Decimal(s).as_tuple().exponent)
        f = float(s)                      # deliberate: the thing a careless consumer would do
        if repr(f) != s:
            lossy_text.append((s, repr(f)))
        if Decimal(repr(f)) != Decimal(s):
            lossy_value.append((s, repr(f)))

    print()
    print(f"  max decimal scale seen                    : {max_scale}")
    print(f"  literals whose float repr() != the text   : {len(lossy_text)} of {len(seen)}")
    print(f"  literals whose float VALUE != the decimal : {len(lossy_value)} of {len(seen)}")
    print()
    for label, lst in (("text-lossy", lossy_text), ("VALUE-lossy", lossy_value)):
        if lst:
            print(f"  {label} examples:")
            for s, r in lst[:12]:
                print(f"    {s!r:>18}  ->  {r}")
            print()
    if seen and not lossy_value:
        print(f"  => over the {len(seen)} distinct literals actually inspected, in "
              f"{parsed} of {len(paths)} requested")
        print("     files, NO literal changes VALUE on a float round-trip at these magnitudes")
        print("     and scales. The hazard is structural: the wire format is float-shaped, so a")
        print("     consumer that does not force exact decimal parsing violates the money rule")
        print("     by construction, and would corrupt a value as soon as a magnitude or a")
        print("     scale grows. THIS SENTENCE IS SCOPED TO THE DENOMINATORS ABOVE and says")
        print(f"     nothing whatever about the {len(SKIPS)} file(s) in the SKIP REGISTER.")

    print()
    if failures:
        print(f"T175 SUCCESSOR: FAILED -- {len(failures)} breach(es):")
        for f in failures:
            print("  FAIL  " + f)
        return 1
    print(f"T175 SUCCESSOR: PASS -- {parsed} of {len(paths)} files scanned, "
          f"{len(SKIPS)} skipped, {len(seen)} distinct literals inspected.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
