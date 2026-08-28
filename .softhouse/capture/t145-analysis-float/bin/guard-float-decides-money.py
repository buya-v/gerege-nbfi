#!/usr/bin/env python3
"""T145 GUARD -- a binary-float comparison must not DECIDE a money claim.

WHAT IT DETECTS, and why this shape and not "an unguarded json.load".
T207 ruled that a float-derived predicate MAY gate on the oracle-facing wire, response leg,
because the first non-negotiable bans a float from CARRYING a value, not from being MEASURED,
and T186 rule A1 already ships a ratified float-derived guard
(`repr(float(tok)) == tok`, live at conformance.sh:997). A guard that simply banned
`json.load` without `parse_float=` would therefore fire on 362 sites, 3 of which this task
MEASURED to be places where the "fix" is destructive, and would be reverted within a fire.

So this guard is narrow and it is the shape the ruling actually forbids:

    A CONTAINMENT WHERE BOTH SIDES OF A COMPARISON ARE float(), i.e. the amounts
    themselves are carried across the comparison as binary doubles.

That is the exact shape of `.softhouse/capture/actualactual/analysis/discriminate.py:160`

    if [float(g) for g in got] != [float(w) for w in want]:

which then prints "ALL n PERIODS REPRODUCED DIGIT FOR DIGIT". Under T207's own test --
"every amount ... is a Decimal built from exact text and the only thing float() yields is a
bool" -- this FAILS the first clause: nothing here is a Decimal and no exact text survives.

It is distinguished from the RATIFIED A1 guard, which this guard must not fire on:
A1 compares `repr(float(tok))` against `tok`, a STRING -- exactly ONE side is a float, and
the float is the simulated defect. One-sided float comparisons are PERMITTED and are not
reported as breaches.

BASELINE. Known sites are DECLARED below with their ruling, not silenced: a declared site
that has DISAPPEARED is also a failure, so this list cannot rot into a blanket suppressor
(the mechanism patterns.md uses for PNUMBER-REGISTER-DECLARED-COLLISIONS).

EXIT 0 clean / 2 a breach (a NEW two-sided float money comparison, or a declared one that
has silently vanished) / 3 the guard could not run.
"""
import ast
import os
import subprocess
import sys

# file -> (line, one-line ruling). A declared site is EXPECTED to be present.
DECLARED = {
    ".softhouse/capture/actualactual/analysis/discriminate.py": (
        160,
        "T145 verdict: CARRIES VALUE, not permitted measurement. Left BYTE-IDENTICAL under "
        "T114 (it produced analysis/DISCRIMINATION-OUTPUT.txt, cited by REPRODUCE.md:68); "
        "the repair is in the T145 scratch copy and filed as FU-T145-1.",
    ),
    ".softhouse/capture/t145-analysis-float/bin/selftest-discriminate-predicate.py": (
        35,
        "T145's own RED/GREEN battery. The predicate is TRANSCRIBED CHARACTER FOR CHARACTER "
        "from discriminate.py:160 in order to drive it red; it is the SIMULATED DEFECT, in "
        "the sense check_wire_float_roundtrip.py's docstring uses (P-25). Declaring it here "
        "rather than exempting the path is deliberate: the guard must stay able to fail on "
        "this file if the line ever moves.",
    ),
}


def has_float_call(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "float":
            return True
    return False


def scan(path, src):
    """Report Compare nodes where BOTH sides construct a float."""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if not isinstance(n, ast.Compare):
            continue
        if not isinstance(n.ops[0], (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
            continue
        left = has_float_call(n.left)
        right = any(has_float_call(c) for c in n.comparators)
        if left and right:
            out.append(n.lineno)
    return out


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    try:
        files = subprocess.run(["git", "ls-files", "--", ".softhouse"], cwd=root,
                               capture_output=True, text=True, check=True).stdout.split("\n")
    except Exception as e:                                        # noqa: BLE001
        print("GUARD COULD NOT RUN: %s" % e)
        return 3
    pys = sorted(p for p in files if p.endswith(".py"))

    print("T145 GUARD -- two-sided float() comparison deciding a money claim")
    print("SELECTOR: ast.Compare where BOTH the left operand and at least one comparator")
    print("          contain a float(...) call. One-sided float comparisons are PERMITTED")
    print("          (T186 rule A1: repr(float(tok)) == tok) and are NOT reported.")
    print("POPULATION: %d tracked .py under .softhouse" % len(pys))
    print()

    found = {}
    for rel in pys:
        try:
            src = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for ln in scan(rel, src):
            found.setdefault(rel, []).append(ln)

    breaches = []
    for rel, lns in sorted(found.items()):
        if rel in DECLARED and DECLARED[rel][0] in lns:
            print("DECLARED  %s:%d" % (rel, DECLARED[rel][0]))
            print("          %s" % DECLARED[rel][1])
            extra = [l for l in lns if l != DECLARED[rel][0]]
            for l in extra:
                breaches.append((rel, l, "UNDECLARED line in a declared file"))
        else:
            for l in lns:
                breaches.append((rel, l, "NEW two-sided float money comparison"))

    for rel, (ln, why) in DECLARED.items():
        if ln not in found.get(rel, []):
            breaches.append((rel, ln, "DECLARED SITE HAS VANISHED -- the declaration is now "
                                      "a silencer for a site that no longer exists; remove it"))

    print()
    print("two-sided float comparisons found : %d in %d files"
          % (sum(len(v) for v in found.values()), len(found)))
    print("declared                          : %d" % len(DECLARED))
    print("BREACHES                          : %d" % len(breaches))
    for rel, ln, why in breaches:
        print("  BREACH %s:%s -- %s" % (rel, ln, why))
    if breaches:
        print()
        print("GUARD FAILED -- a binary float is deciding a money claim. This is the first")
        print("non-negotiable: 'No floating-point in any monetary code path ... including")
        print("intermediate calculation.'")
        return 2
    print()
    print("GUARD CLEAN")
    return 0


sys.exit(main())
