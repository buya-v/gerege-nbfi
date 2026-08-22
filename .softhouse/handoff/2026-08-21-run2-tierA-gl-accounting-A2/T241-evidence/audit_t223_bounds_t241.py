#!/usr/bin/env python3
"""
T241 — audit of T223's scope-table BOUNDARY, at the commit T223 itself committed.

T223's `scope_table_t223.py` bounds the G-8 section as

    start = "## G-8 — TWO phenomena"      end = "## G-8-NOTICE"

This script replays T223's OWN enumeration logic (copied verbatim below, marked) against
`.softhouse/gates.md` AS IT STOOD AT T223's COMMIT `557ed0ee3e6dfa25f653121955304b1deff3fe5c`, and
against the correct boundary (the next `## G-<n>` gate heading), and reports both.

It reads a file dumped by `git show <commit>:.softhouse/gates.md`; the path is argv[1].
No float, no money, no `grep`, no `rg` (P-25, P-75).
"""
import re
import sys


# ------------------- verbatim from T223's scope_table_t223.py -------------------
def sentences(block):
    out = []
    for lineno, line in enumerate(block, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") or re.match(r"^[-*>#]", stripped):
            out.append((lineno, stripped))
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z*`\[])", stripped):
            if s.strip():
                out.append((lineno, s.strip()))
    return out
# --------------------------- end verbatim copy ----------------------------------


def main():
    lines = open(sys.argv[1]).read().split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## G-8 — TWO phenomena"))
    t223_end = next(i for i, l in enumerate(lines) if i > start and l.startswith("## G-8-NOTICE"))
    true_end = next(i for i, l in enumerate(lines) if i > start and re.match(r"^## G-\d", l))

    t223_block = lines[start:t223_end]
    true_block = lines[start:true_end]
    foreign = lines[true_end:t223_end]

    print("gates.md as at the commit given on the command line: %s" % sys.argv[1])
    print("  '## G-8 — TWO phenomena' at line          : %d" % (start + 1))
    print("  next '## G-<n>' gate heading at line      : %d  (%s)" % (true_end + 1, lines[true_end][:60]))
    print("  '## G-8-NOTICE' at line                   : %d" % (t223_end + 1))
    print()
    print("  T223's block  (G-8 .. G-8-NOTICE)         : %d lines, %d claim units"
          % (len(t223_block), len(sentences(t223_block))))
    print("  the ACTUAL G-8 live section               : %d lines, %d claim units"
          % (len(true_block), len(sentences(true_block))))
    print("  FOREIGN text T223 enumerated as G-8       : %d lines, %d claim units"
          % (len(foreign), len(sentences(foreign))))
    heads = [l for l in foreign if l.startswith("## ")]
    for h in heads:
        print("      foreign section: %s" % h[:90])
    n_t223 = len(sentences(t223_block))
    n_foreign = len(sentences(foreign))
    print()
    print("  DIRECTION OF THE ERROR: OVER-scoped, not under-scoped -- T223 enumerated"
          " %d units of which %d (%d%%) were NOT G-8." % (n_t223, n_foreign,
                                                          (100 * n_foreign) // n_t223))
    print("  So T223 MISSED no G-8 sentence by this boundary; its reported counts simply are"
          " not counts of G-8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
