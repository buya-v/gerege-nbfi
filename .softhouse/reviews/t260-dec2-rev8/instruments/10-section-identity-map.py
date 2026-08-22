#!/usr/bin/env python3
"""T260 LEG A — whole-document section identity map.

INDEPENDENT of T255's method. T255 chose six "obligation-bearing blocks" and proved those
byte-identical. That is a CHOSEN population and it does not prove exhaustiveness (T255 says so
itself, [UNVERIFIED] item 1). This instrument inverts the question: partition the WHOLE document
into sections and report, for every section, IDENTICAL / CHANGED / ADDED / REMOVED. Sections that
are byte-identical need no obligation analysis at all; what remains is the exact population a
reviewer must read by hand, and it is derived from the document rather than chosen.

P-67: both terms are printed — lines inside changed sections AND lines inside identical sections,
summing to the document.

Usage: 10-section-identity-map.py <rev7.md> <rev8.md>
Exit 0 always (this is a census, not a gate).
"""
import re
import sys
import hashlib


def load(p):
    with open(p, encoding="utf-8") as f:
        return f.read().split("\n")


def sections(lines):
    """Partition on ATX headings h1-h4 that are NOT inside a fenced code block.

    Everything before the first heading is a synthetic PREAMBLE section (the banner + status
    block), which is where DEC-2 keeps a great deal of its load-bearing prose.
    """
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
    if not idx:
        return [("PREAMBLE", 0, len(lines))]
    if idx[0] != 0:
        out.append(("PREAMBLE (banner + status block)", 0, idx[0]))
    for n, i in enumerate(idx):
        end = idx[n + 1] if n + 1 < len(idx) else len(lines)
        out.append((lines[i].strip(), i, end))
    return out


def sha(ls):
    return hashlib.sha256("\n".join(ls).encode()).hexdigest()[:16]


def key(t):
    """Match sections across revisions by their SECTION NUMBER, not their title -- several
    headings had their trailing state-claim reworded, and matching on the full title would
    report those as REMOVED+ADDED and hide the real comparison."""
    m = re.match(r"^#{1,4} (\d+(?:\.\d+)*)", t)
    if m:
        return m.group(1)
    return t


def main():
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    sa = sections(a)
    sb = sections(b)

    ka, kb = {}, {}
    for t, s, e in sa:
        ka.setdefault(key(t), []).append((t, s, e))
    for t, s, e in sb:
        kb.setdefault(key(t), []).append((t, s, e))

    order = []
    seen = set()
    for t, s, e in sa:
        k = key(t)
        if k not in seen:
            order.append(k)
            seen.add(k)
    for t, s, e in sb:
        k = key(t)
        if k not in seen:
            order.append(k)
            seen.add(k)

    changed_a = 0
    identical_a = 0
    print(f"{'SECTION':<9} {'STATUS':<10} {'A':>6} {'B':>6}  {'sha(A)':<17} heading (rev8 text)")
    print("-" * 118)
    for k in order:
        A = ka.get(k)
        B = kb.get(k)
        if A and B:
            ta, s1, e1 = A[0]
            tb, s2, e2 = B[0]
            h1, h2 = sha(a[s1:e1]), sha(b[s2:e2])
            st = "IDENTICAL" if h1 == h2 else "CHANGED"
            if st == "CHANGED":
                changed_a += e1 - s1
            else:
                identical_a += e1 - s1
            print(f"{k:<9} {st:<10} {e1-s1:>6} {e2-s2:>6}  {h1:<17} {tb[:60]}")
        elif A:
            ta, s1, e1 = A[0]
            changed_a += e1 - s1
            print(f"{k:<9} {'REMOVED':<10} {e1-s1:>6} {0:>6}  {sha(a[s1:e1]):<17} {ta[:60]}")
        else:
            tb, s2, e2 = B[0]
            print(f"{k:<9} {'ADDED':<10} {0:>6} {e2-s2:>6}  {'-':<17} {tb[:60]}")

    tot_a = len(a)
    print()
    print(f"rev7 lines total                        : {tot_a}")
    print(f"rev7 lines in CHANGED/REMOVED sections  : {changed_a} ({100.0*changed_a/tot_a:.1f}%)")
    print(f"rev7 lines in IDENTICAL sections        : {identical_a} ({100.0*identical_a/tot_a:.1f}%)")
    assert changed_a + identical_a == tot_a, "P-67: the two terms must sum to the document"
    print("P-67 check: the two terms sum to the document. OK")


if __name__ == "__main__":
    main()
