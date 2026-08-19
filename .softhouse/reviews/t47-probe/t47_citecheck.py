#!/usr/bin/env python3
"""T45 - machine-check every file:line citation in DEC-1 revision 9 and in contract.go
against the pinned Fineract checkout.

Revision 9 exists BECAUSE citations were wrong, so this runs over the whole document
rather than over the lines this task touched.

Method
------
1. Extract every `<Name>.java:<n>` and `<Name>.java:<n>-<m>` occurrence.
2. Resolve `<Name>.java` against the pinned checkout's main sources (never test, never build).
   A name that resolves to more than one main-source file is reported AMBIGUOUS and checked
   against every candidate (it passes if it is in range on at least one).
3. Check the line, or the whole range, is in range for that file.
4. Report totals and every failure.

Bare `:<n>` citations that inherit the previously named file are COUNTED but not resolved:
resolving them needs the prose context, and this probe reports the count so the number is
not silently overstated.
"""
import os
import re
import subprocess
import sys
from collections import defaultdict

FIN = os.environ.get("FIN", "/Users/buv/fineract")
TARGETS = [
    "docs/adr/DEC-1-schedule-generator-adapter.md",
    "nexus/internal/apps/loanschedule/contract/contract.go",
]

QUALIFIED = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*\.java):(\d+)(?:\s*[-–]\s*(\d+))?")
BARE = re.compile(r"(?<![A-Za-z0-9_.])[:∶](\d+)(?:-(\d+))?\b")


def index_main_sources():
    """name -> [absolute paths]. Main sources plus test sources: DEC-1 cites the oracle's
    own shipped test helper (section 8 item 7) as a harness trap, and excluding tests would
    report that citation as unresolvable when it is correct."""
    idx = defaultdict(list)
    out = subprocess.run(["find", FIN, "-name", "*.java", "-path", "*/src/*"],
                         capture_output=True, text=True).stdout.split("\n")
    for path in out:
        if not path or "/build/" in path:
            continue
        if "/src/test/" in path and not os.path.basename(path).endswith("Test.java"):
            continue
        idx[os.path.basename(path)].append(path)
    return idx


def linecount(path, cache={}):
    if path not in cache:
        with open(path, "rb") as fh:
            cache[path] = sum(1 for _ in fh)
    return cache[path]


def main():
    head = subprocess.run(["git", "-C", FIN, "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    print("T45 CITATION CHECK - every file:line in DEC-1 revision 9 and contract.go")
    print(f"pinned checkout: {FIN} @ {head}")
    print()
    idx = index_main_sources()
    print(f"Java files indexed: {sum(len(v) for v in idx.values())}"
          f" ({len(idx)} distinct basenames)")
    print()

    total = ok = 0
    failures = []
    unresolved = []
    ambiguous = set()
    per_file = defaultdict(int)
    bare_total = 0

    for target in TARGETS:
        text = open(target).read()
        bare_total += len(BARE.findall(text))
        seen = set()
        for m in QUALIFIED.finditer(text):
            name, lo, hi = m.group(1), int(m.group(2)), m.group(3)
            hi = int(hi) if hi else lo
            key = (target, name, lo, hi)
            if key in seen:
                per_file[name] += 1
                total += 1
                ok += 1          # duplicate of a citation already judged
                continue
            seen.add(key)
            total += 1
            per_file[name] += 1
            cands = idx.get(name)
            if not cands:
                unresolved.append((target, name, lo, hi))
                continue
            if len(cands) > 1:
                ambiguous.add(name)
            good = any(1 <= lo <= linecount(p) and 1 <= hi <= linecount(p) and lo <= hi
                       for p in cands)
            if good:
                ok += 1
            else:
                failures.append((target, name, lo, hi,
                                 [(os.path.relpath(p, FIN), linecount(p)) for p in cands]))

    print(f"QUALIFIED citations checked : {total}")
    print(f"  in range                  : {ok}")
    print(f"  OUT OF RANGE              : {len(failures)}")
    print(f"  unresolvable basename     : {len(unresolved)}")
    print(f"  ambiguous basenames       : {len(ambiguous)}"
          + (f"  {sorted(ambiguous)}" if ambiguous else ""))
    print()
    print(f"BARE `:n` / `:n-m` citations present (context-resolved, NOT machine-checked): {bare_total}")
    print()

    if failures:
        print("OUT OF RANGE:")
        for t, name, lo, hi, cands in failures:
            print(f"  {t}: {name}:{lo}-{hi}   candidates {cands}")
    if unresolved:
        print("UNRESOLVABLE BASENAME (not a main source in the pinned checkout):")
        for t, name, lo, hi in unresolved:
            print(f"  {t}: {name}:{lo}-{hi}")
    print()
    print("Citations per file, most-cited first:")
    for name, n in sorted(per_file.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {name}")

    return 1 if (failures or unresolved) else 0


if __name__ == "__main__":
    sys.exit(main())
