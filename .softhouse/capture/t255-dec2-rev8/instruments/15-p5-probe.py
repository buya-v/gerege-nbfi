#!/usr/bin/env python3
"""T255 — re-measure the P-5 claim revision 8 repeats in §5.3, rather than
inheriting it from T247 or T251 (P-69: stamp what you measured, at your commit).

CLAIM UNDER TEST: `P-5` is the one §5.3 precondition the ledger package names
nowhere, while its nine siblings are all named.

A NON-EXISTENCE IS A CLAIM ABOUT THE SEARCH (P-66/P-70), so this prints:
  * the exact population searched, file by file;
  * a POSITIVE control -- the nine siblings, which must be found;
  * a NEGATIVE control -- `P-99`, which must not be;
  * and a discrimination check that the word boundary really discriminates,
    run in a population that contains both `P-5` and `P-50`.

No `cd`. No `|| true`. No bare `grep`, no `rg` -- `python3 re` only (P-75).
Exit 0 = the claim reproduces; 1 = it does not; 2 = could not run.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
PKG = "nexus/internal/apps/ledger"


def tracked(prefix):
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "--", prefix],
                         capture_output=True, text=True, check=True)
    return [p for p in out.stdout.split("\n") if p]


def count(paths, token):
    pat = re.compile(r"\b" + re.escape(token) + r"\b")
    total = 0
    for rel in paths:
        full = os.path.join(ROOT, rel)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as fh:
            total += len(pat.findall(fh.read()))
    return total


def main():
    files = tracked(PKG)
    if not files:
        print("REFUSE (exit 2): zero tracked files under %s -- the population is empty, so no" % PKG)
        print("                 statement about it would be a measurement.")
        return 2
    print("POPULATION: %d tracked files under %s (P-66: this is WHERE I looked)" % (len(files), PKG))
    for rel in files:
        print("    %s" % rel)
    print("")

    siblings = ["P-1", "P-2", "P-3", "P-4", "P-6", "P-7", "P-8", "P-9", "P-10"]
    print("=== word-anchored counts over that population ===")
    results = {}
    for tok in ["P-1", "P-2", "P-3", "P-4", "P-5", "P-6", "P-7", "P-8", "P-9", "P-10", "P-99"]:
        results[tok] = count(files, tok)
        print("    %-5s %d" % (tok, results[tok]))
    print("")

    ok = True
    if results["P-5"] != 0:
        ok = False
        print("CLAIM FAILS: P-5 is named %d time(s) in the package." % results["P-5"])
    missing = [s for s in siblings if results[s] == 0]
    if missing:
        ok = False
        print("POSITIVE CONTROL FAILS: these siblings were not found either: %s" % ", ".join(missing))
        print("  -> a probe that finds none of them says nothing about P-5.")
    if results["P-99"] != 0:
        ok = False
        print("NEGATIVE CONTROL FAILS: P-99 was found, so the probe matches things that are not there.")

    # Discrimination: does \b actually separate P-5 from P-50? Measured in a
    # population known to contain both, because inside the ledger package all
    # three counts are 0 and the test would be vacuous there (P-35).
    pats = tracked(".softhouse/patterns.md")
    if pats:
        p5 = count(pats, "P-5")
        p50 = count(pats, "P-50")
        raw = 0
        for rel in pats:
            with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
                raw += fh.read().count("P-5")
        print("")
        print("=== \\b discrimination, measured where both needles EXIST (.softhouse/patterns.md) ===")
        print("    \\bP-5\\b  %d      \\bP-50\\b %d      unanchored 'P-5' %d" % (p5, p50, raw))
        if not (p5 > 0 and p50 > 0 and raw > p5):
            ok = False
            print("    DISCRIMINATION CHECK FAILS: the anchoring is not shown to separate them.")
    else:
        print("")
        print("NOTE: .softhouse/patterns.md not tracked; the discrimination check did not run.")

    print("")
    print("VERDICT: %s" % ("the claim reproduces at this commit" if ok else "the claim does NOT reproduce"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
