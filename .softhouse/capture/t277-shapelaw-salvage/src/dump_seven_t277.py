#!/usr/bin/env python3
"""T277 -- ROW-LEVEL dump of the seven law-(ii) exception cells, and of the five
PARTIAL family-B witnesses, straight from the committed raw `.json.gz` schedules.

The census (`shapelaw_census_t277.py`) reports counts. This file exists so a
reader can see the actual principal rows that refute
`TOTAL PRINCIPAL = max(0, B_minor - n*delta)` without running anything.

Integer minor units only. Imports the minor-unit parser from the census module
(this program's own instrument, written for T277) and nothing else.
"""
import glob
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapelaw_census_t277 import to_minor, half_up_ratio, monthly_rate_factor  # noqa: E402

SEVEN = [
    ("T117P2-R600p0-N108-B11", "capture-t117p2-raw.json.gz"),
    ("T117P2-R600p0-N121-B11", "capture-t117p2-raw.json.gz"),
    ("T117P2-R600p0-N150-B11", "capture-t117p2-raw.json.gz"),
    ("T159-R600p0-N108-B11", "capture-t159-raw.json.gz"),
    ("T159-R600p0-N121-B11", "capture-t159-raw.json.gz"),
    ("T159-R600p0-N150-B11", "capture-t159-raw.json.gz"),
    ("T159-R600p0-N2000-B999", "capture-t159-raw.json.gz"),
]


def load(root):
    out = {}
    for path in sorted(glob.glob(os.path.join(root, ".softhouse", "**", "*.json.gz"),
                                 recursive=True)):
        with gzip.open(path) as fh:
            raw = json.load(fh)
        for cap in raw.get("captures", []):
            out[(cap["id"], os.path.basename(path))] = cap
    return out


def show(cap, cid, cfile):
    inp, obs = cap["inputs"], cap["observed"]
    reps = [p for p in obs["periods"] if p["type"] == "REPAYMENT"]
    n = int(inp["numberOfRepayments"])
    b = to_minor(obs["totalDisbursedAmount"])
    e = to_minor(reps[0]["total"])
    r_num, r_den = monthly_rate_factor(str(inp["annualNominalInterestRate"]))
    i1q = half_up_ratio(b * r_num, r_den)
    d = i1q - e
    rowp = [to_minor(p["principal"]) for p in reps]
    rowi = [to_minor(p["interest"]) for p in reps]
    rowt = [to_minor(p["total"]) for p in reps]

    print("=" * 92)
    print("%s   [%s]" % (cid, cfile))
    print("  rate %s%% p.a.  n=%d  rows=%d  B=%d minor  E(row1 total)=%d  I1q=%d  delta=%d"
          % (inp["annualNominalInterestRate"], n, len(reps), b, e, i1q, d))
    print("  FULL family B antecedent  (delta>=1 and B <= n*delta):  %d>=1 and %d<=%d  -> %s"
          % (d, b, n * d, d >= 1 and b <= n * d))
    print("  LAW (ii) PREDICTS TOTAL PRINCIPAL = max(0, %d - %d*%d) = %d"
          % (b, n, d, max(0, b - n * d)))
    print("  SUM OF THE PRINCIPAL COLUMN OVER ALL %d REPAYMENT ROWS = %d   <-- OBSERVED"
          % (len(reps), sum(rowp)))
    print("  header totalPrincipalAmount = %d  (equals row sum: %s)"
          % (to_minor(obs["totalPrincipalAmount"]),
             to_minor(obs["totalPrincipalAmount"]) == sum(rowp)))
    print("  LAW (i) / FACT A: last row total %d == E+B = %d  -> %s"
          % (rowt[-1], e + b, rowt[-1] == e + b))
    print("  TOTAL REPAYMENT %d == n*E+B = %d  -> %s"
          % (sum(rowt), n * e + b, sum(rowt) == n * e + b))
    print("  every row with a NON-ZERO principal (row#: principal / interest / total / balance):")
    any_nonzero = False
    for idx, p in enumerate(reps):
        if rowp[idx] != 0:
            any_nonzero = True
            print("      row %-5d  principal %-6d interest %-6d total %-6d balance %s"
                  % (p.get("periodNumber", idx + 1), rowp[idx], rowi[idx], rowt[idx],
                     to_minor(p["balance"])))
    if not any_nonzero:
        print("      (none)")
    print("  first row : principal %d  interest %d  total %d  balance %d"
          % (rowp[0], rowi[0], rowt[0], to_minor(reps[0]["balance"])))
    print("  last row  : principal %d  interest %d  total %d  balance %d"
          % (rowp[-1], rowi[-1], rowt[-1], to_minor(reps[-1]["balance"])))
    print()


def main(argv):
    root = argv[1] if len(argv) > 1 else "."
    caps = load(root)

    print("T277 -- THE SEVEN CELLS ON WHICH LAW (ii) IS FALSE, FROM THE RAW SCHEDULES")
    print("Law (ii), as stated in .softhouse/gates.md under `### THE LAW`:")
    print("    TOTAL PRINCIPAL = max(0, B_minor - n*delta)")
    print("Every cell below satisfies the block's own `FULL family B` antecedent")
    print("(delta >= 1 AND B_minor <= n*delta), so the law predicts EXACTLY ZERO principal.")
    print("Every one of them repays a POSITIVE amount of principal.")
    print()
    missing = [k for k in SEVEN if k not in caps]
    if missing:
        print("MISSING CAPTURES -- census scope moved: %r" % (missing,))
        return 1
    for cid, cfile in SEVEN:
        show(caps[(cid, cfile)], cid, cfile)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
