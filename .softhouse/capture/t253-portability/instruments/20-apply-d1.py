#!/usr/bin/env python3
"""T253b — apply the D1 fix to EVERY `mktemp -t` site in conformance.sh.

SELECTOR FIRST (P-76 addendum). The population is defined as "every line in
.softhouse/conformance.sh containing the word mktemp", enumerated with python's
re — never a bare `grep`, never `rg` (P-75). Both terms are then reported:
  population  = all mktemp sites in the file
  rewritten   = the subset carrying the non-portable `-t NAME` form
and the script REFUSES if population != rewritten, because a leftover site is
exactly the "fixed only the one that fired" failure this task exists to avoid.

The rewrite is LINE-FOR-LINE: no line is added or removed, so no downstream
line number in conformance.sh moves (T255 is landing citations into this same
file in this same fire).

Exit: 0 rewritten (or already clean), 1 refusal.
"""
import re
import sys

PATH = ".softhouse/conformance.sh"

# `mktemp [-d] -t NAME`  ->  `mktemp [-d] "${TMPDIR:-/tmp}/NAME.XXXXXXXXXX"`
SITE = re.compile(r'mktemp(?P<opts>(?:\s+-[A-Za-z]+)*?)\s+-t\s+(?P<name>[A-Za-z0-9._-]+)')
ANY = re.compile(r'\bmktemp\b')


def rewrite(line: str) -> str:
    def sub(m: re.Match) -> str:
        opts = m.group("opts")
        name = m.group("name")
        return 'mktemp%s "${TMPDIR:-/tmp}/%s.XXXXXXXXXX"' % (opts, name)
    return SITE.sub(sub, line)


def main() -> int:
    src = open(PATH, encoding="utf-8").read()
    lines = src.split("\n")

    population, targets = [], []
    for i, line in enumerate(lines, 1):
        if ANY.search(line):
            population.append(i)
            if SITE.search(line):
                targets.append(i)

    print("SELECTOR : every line matching \\bmktemp\\b in %s" % PATH)
    print("population (all mktemp sites)        : %d  %s" % (len(population), population))
    print("rewritten (non-portable `-t NAME`)   : %d  %s" % (len(targets), targets))

    residual = sorted(set(population) - set(targets))
    if residual:
        print("RESIDUAL mktemp sites NOT rewritten  : %d  %s" % (len(residual), residual))
        for n in residual:
            print("   %d: %s" % (n, lines[n - 1].strip()))
        print("REFUSING: a residual `-t` site would keep the harness dead on GNU. "
              "Inspect each residual and either rewrite it or justify it explicitly.")
        return 1

    changed = 0
    for n in targets:
        before = lines[n - 1]
        after = rewrite(before)
        if after == before:
            print("REFUSING: site %d matched the selector but the rewrite was a no-op:" % n)
            print("   %s" % before.strip())
            return 1
        if SITE.search(after):
            print("REFUSING: site %d still carries `-t NAME` after rewrite:" % n)
            print("   %s" % after.strip())
            return 1
        lines[n - 1] = after
        changed += 1
        print("  %4d - %s" % (n, before.strip()))
        print("  %4d + %s" % (n, after.strip()))

    out = "\n".join(lines)
    if len(out.split("\n")) != len(src.split("\n")):
        print("REFUSING: line count moved (%d -> %d); the rewrite must be line-for-line."
              % (len(src.split("\n")), len(out.split("\n"))))
        return 1

    open(PATH, "w", encoding="utf-8").write(out)
    print("REWROTE %d/%d site(s). Line count unchanged at %d."
          % (changed, len(population), len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
