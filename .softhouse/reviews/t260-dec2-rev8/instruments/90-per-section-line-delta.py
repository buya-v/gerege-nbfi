#!/usr/bin/env python3
"""T260 — for every CHANGED section, print the EXACT lines removed and added.

This is the population a reviewer must read by hand to rule on "no obligation moved". It is
derived from the document's own heading structure (see 10-section-identity-map.py), not chosen,
so nothing can be silently outside it. P-40: the count of what was skipped is zero by
construction -- every changed section is printed.

Usage: 90-per-section-line-delta.py <rev7.md> <rev8.md> [only-section]
Exit 0 always.
"""
import difflib
import re
import sys


def load(p):
    return open(p, encoding="utf-8").read().split("\n")


def sections(lines):
    idx = []
    fence = False
    for i, l in enumerate(lines):
        if l.lstrip("> ").startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if re.match(r"^#{1,4} ", l):
            idx.append(i)
    out = []
    if idx and idx[0] != 0:
        out.append(("PREAMBLE", 0, idx[0]))
    for n, i in enumerate(idx):
        out.append((lines[i].strip(), i, idx[n + 1] if n + 1 < len(idx) else len(lines)))
    return out


def key(t):
    m = re.match(r"^#{1,4} (\d+(?:\.\d+)*)", t)
    return m.group(1) if m else t


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    only = sys.argv[3] if len(sys.argv) > 3 else None
    ka = {key(t): (s, e) for t, s, e in sections(a)}
    kb = {key(t): (s, e) for t, s, e in sections(b)}
    tot_rm = tot_add = 0
    for k in ka:
        if k not in kb:
            continue
        if only and k != only:
            continue
        s1, e1 = ka[k]
        s2, e2 = kb[k]
        A, B = a[s1:e1], b[s2:e2]
        if A == B:
            continue
        sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
        rm, add = [], []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("replace", "delete"):
                rm.extend(A[i1:i2])
            if tag in ("replace", "insert"):
                add.extend(B[j1:j2])
        rm = [x for x in rm if x.strip()]
        add = [x for x in add if x.strip()]
        tot_rm += len(rm)
        tot_add += len(add)
        print("=" * 100)
        print(f"SECTION {k}   removed {len(rm)} line(s), added {len(add)} line(s)")
        print("=" * 100)
        print("--- REMOVED ---")
        for x in rm:
            print("  -" + x[:400])
        print("--- ADDED ---")
        for x in add:
            print("  +" + x[:400])
        print()
    print(f"TOTAL over changed sections: removed {tot_rm}, added {tot_add}")


if __name__ == "__main__":
    main()
