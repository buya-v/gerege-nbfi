#!/usr/bin/env python3
"""T275 -- read the q8 snapshots under out/ and print how acc_product_mapping row IDENTITY
moved between them.

This is a READER, not a capture. It re-derives nothing about money and decides nothing; it
parses the psql box-drawing output already committed under out/ and reports which mapping
row ids appeared, vanished or survived between consecutive snapshots. Every number it
prints is traceable to a line in a committed .txt.

  python3 t275-mapping-diff.py PRODUCT_ID SNAP [SNAP ...]

Numbers are compared as TEXT, never parsed to float. Nothing in acc_product_mapping is a
monetary amount, but the rule is the rule.
"""
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, "out")

COLS = ["mapping_id", "product_id", "accounting_type", "product_type",
        "financial_account_type", "payment_type", "charge_id", "charge_off_reason_id",
        "write_off_reason_id", "cap_inc_class_id", "buydown_class_id", "gl_account_id",
        "gl_code", "gl_name", "account_usage", "classification_enum"]


def rows(name):
    """Parse the first result set of a q8 snapshot into dicts keyed by COLS."""
    path = os.path.join(OUT, name + ".txt")
    out, maxid = [], None
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == len(COLS) and cells[0].isdigit():
                out.append(dict(zip(COLS, cells)))
            elif len(cells) == 2 and cells[0].isdigit() and cells[1].isdigit():
                maxid = cells[0]          # the max_mapping_id / mapping_rows tail query
    return out, maxid


def key(r):
    """The semantic key of a mapping, as ProductToGLAccountMapping's JPA @UniqueConstraint
    `financial_action` declares it -- product, product type, financial account type,
    payment type -- widened by the dimensions the DDL added later (charge, reasons,
    classifications), which that annotation does not mention."""
    return (r["financial_account_type"], r["payment_type"] or "-", r["charge_id"] or "-",
            r["charge_off_reason_id"] or "-", r["write_off_reason_id"] or "-",
            r["cap_inc_class_id"] or "-", r["buydown_class_id"] or "-")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    pid = sys.argv[1]
    snaps = sys.argv[2:]
    prev = None
    for name in snaps:
        rs, maxid = rows(name)
        mine = {r["mapping_id"]: r for r in rs if r["product_id"] == pid}
        print(f"\n=== {name}   product {pid}: {len(mine)} mapping row(s), "
              f"table max(id)={maxid}")
        for mid in sorted(mine, key=int):
            r = mine[mid]
            print(f"    id={mid:>3}  fat={r['financial_account_type']:>2}  "
                  f"payment_type={r['payment_type'] or '-':>2}  "
                  f"charge={r['charge_id'] or '-':>2}  "
                  f"gl={r['gl_account_id']:>2} ({r['gl_code']} {r['gl_name']})")
        if prev is not None:
            gone = sorted(set(prev) - set(mine), key=int)
            new = sorted(set(mine) - set(prev), key=int)
            kept = sorted(set(mine) & set(prev), key=int)
            print(f"    -> vs previous: {len(kept)} id(s) SURVIVED, "
                  f"{len(gone)} DELETED {gone or ''}, {len(new)} CREATED {new or ''}")
            for mid in kept:
                a, b = prev[mid], mine[mid]
                d = [c for c in COLS if a[c] != b[c]]
                if d:
                    print(f"       id={mid} MUTATED IN PLACE: "
                          + ", ".join(f"{c} {a[c]!r}->{b[c]!r}" for c in d))
            for mid in new:
                k = key(mine[mid])
                match = [m for m in gone if key(prev[m]) == k]
                if match:
                    print(f"       id={mid} REPLACES id={match[0]} at the same semantic key "
                          f"(gl {prev[match[0]]['gl_account_id']} -> {mine[mid]['gl_account_id']})")
        prev = mine
    return 0


if __name__ == "__main__":
    sys.exit(main())
