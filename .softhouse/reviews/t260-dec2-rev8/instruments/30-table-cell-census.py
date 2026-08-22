#!/usr/bin/env python3
"""T260 LEG C — EXHAUSTIVE table-cell census over the WHOLE document.

T255 proved cell-by-cell identity for the seven rows of ONE table (§4.4) and byte identity for
§5.3's ten-row table as a block. DEC-2 states a great deal of its normative content in table cells
(the §4.2 predicate rows, §4.4's invariants, §4.9's refusal taxonomy, §4.10's registry, §5.3's
preconditions, §5.2's requirement matrices). A table cell that states a rule is an obligation with
no modal verb in it a good fraction of the time.

So: extract EVERY table row in both revisions, key each row by its FIRST cell (the row's
identifier), and report per-cell identity. Nothing is chosen; the population is every pipe-table
row in the file.

Usage: 30-table-cell-census.py <rev7.md> <rev8.md>
Exit 0 always.
"""
import re
import sys
import hashlib


def rows(path):
    """Return list of (section, row_index_in_table, cells[]) for every pipe-table row."""
    out = []
    section = "PREAMBLE"
    fence = False
    tbl = 0
    prev_was_row = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            l = line.rstrip("\n")
            if l.lstrip("> ").startswith("```"):
                fence = not fence
                continue
            if fence:
                continue
            m = re.match(r"^(#{1,4}) (.*)$", l)
            if m:
                section = m.group(2).strip()
                prev_was_row = False
                continue
            s = l.strip()
            if s.startswith("|") and s.endswith("|") and s.count("|") >= 2:
                if not prev_was_row:
                    tbl += 1
                prev_was_row = True
                cells = [c.strip() for c in s.strip("|").split("|")]
                out.append((section, tbl, cells))
            else:
                prev_was_row = False
    return out


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()[:12]


def keyof(section, cells):
    # match on section-number prefix + first cell, so a heading reword does not break matching
    m = re.match(r"(\d+(?:\.\d+)*)", section)
    sec = m.group(1) if m else section[:24]
    return (sec, cells[0])


def main():
    A = rows(sys.argv[1])
    B = rows(sys.argv[2])
    print("T260 LEG C — exhaustive pipe-table cell census")
    print("=" * 100)
    print(f"rev7 table rows: {len(A)}    rev8 table rows: {len(B)}")

    da, db = {}, {}
    dupa, dupb = [], []
    for sec, t, c in A:
        k = keyof(sec, c)
        if k in da:
            dupa.append(k)
        da.setdefault(k, (sec, c))
    for sec, t, c in B:
        k = keyof(sec, c)
        if k in db:
            dupb.append(k)
        db.setdefault(k, (sec, c))
    print(f"duplicate first-cell keys (rev7 {len(dupa)}, rev8 {len(dupb)}) — reported, first wins")

    only_a = [k for k in da if k not in db]
    only_b = [k for k in db if k not in da]
    both = [k for k in da if k in db]

    changed = []
    for k in both:
        ca = da[k][1]
        cb = db[k][1]
        if ca != cb:
            changed.append(k)

    print(f"rows present in BOTH: {len(both)}   IDENTICAL: {len(both)-len(changed)}   "
          f"CHANGED: {len(changed)}")
    print(f"rows only in rev7 (REMOVED): {len(only_a)}   only in rev8 (ADDED): {len(only_b)}")
    print()
    print("### ROWS REMOVED (present rev7, absent rev8) — every one must be justified")
    for k in only_a:
        print(f"  [{k[0]}] {da[k][1][0][:90]}")
        print(f"       full: {' | '.join(da[k][1])[:300]}")
    print()
    print("### ROWS ADDED")
    for k in only_b:
        print(f"  [{k[0]}] {db[k][1][0][:90]}")
    print()
    print("### ROWS CHANGED — per-cell verdict")
    for k in changed:
        ca, cb = da[k][1], db[k][1]
        n = max(len(ca), len(cb))
        print(f"\n  ROW {k[0]} :: {ca[0][:70]}   (rev7 {len(ca)} cells, rev8 {len(cb)} cells)")
        for i in range(n):
            x = ca[i] if i < len(ca) else "<<MISSING>>"
            y = cb[i] if i < len(cb) else "<<MISSING>>"
            v = "SAME" if x == y else "DIFF"
            print(f"    cell[{i}] {v}  sha7={h(x)} sha8={h(y)}  len7={len(x)} len8={len(y)}")
            if v == "DIFF":
                print(f"      -7: {x[:600]}")
                print(f"      +8: {y[:600]}")


if __name__ == "__main__":
    main()
