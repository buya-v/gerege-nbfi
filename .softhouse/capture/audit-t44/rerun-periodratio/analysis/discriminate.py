"""
T39 -- DISCRIMINATION.  The observation against each reading, cell by cell.

Method (the one T37 proved, .softhouse/capture/dec1-binding/analysis/discriminate.py):
for a pair of readings, take the set of cells on which THE TWO READINGS DISAGREE --
those are the only cells that carry information about the question -- and ask which
reading the OBSERVATION agrees with on exactly those cells.  A cell where both
readings agree tells you nothing about them, and counting it inflates the verdict.

Comparison is FULL-CELL: fromDate, dueDate, principal, interest, fee, penalty,
outstanding balance, total due and total outstanding balance on EVERY row, plus the
plan totals and the disbursement row.  Not the three headline scalars -- that shape is
what let defect F-1 hide through five reviews (.softhouse/patterns.md).

Inputs:
  ../out/t39-periodratio.json  -- the OBSERVATION, taken from the pinned oracle
  ./readings.py                -- R1/R2/R3, RE-DERIVED, no oracle contacted
  ./select_shapes.py           -- the shape table, joined to the observation by id

Exact decimal strings throughout.  No float anywhere.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from readings import monthend_special_case_fires, render_reading  # noqa: E402
from select_shapes import SHAPES  # noqa: E402
from t34_periodratio import period_ratios_for  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = os.path.join(HERE, "..", "out", "t39-periodratio.json")


def observed_cells(cap: dict) -> dict[str, str]:
    """The observation, flattened to the same addressable cell map render() produces."""
    o = cap["observed"]
    cells: dict[str, str] = {
        "totals.loanTermInDays": str(o["loanTermInDays"]),
        "totals.totalDisbursedAmount": o["totalDisbursedAmount"],
        "totals.totalInterestAmount": o["totalInterestAmount"],
        "totals.totalRepaymentAmount": o["totalRepaymentAmount"],
    }
    for p in o["periods"]:
        if p["type"] == "DISBURSEMENT":
            cells["disbursement.fromDate"] = p["fromDate"]
            cells["disbursement.dueDate"] = p["dueDate"]
            cells["disbursement.principal"] = p["principal"]
        elif p["type"] == "REPAYMENT":
            k = f"period[{p['periodNumber']}]"
            for col in ("fromDate", "dueDate", "principal", "interest", "fee", "penalty",
                        "balance", "total", "totalOutstandingBalance"):
                cells[k + "." + col] = p[col]
        else:
            cells["UNEXPECTED_ROW_TYPE." + p["type"]] = "present"
    return cells


def disagree(a: dict[str, str], b: dict[str, str]) -> list[str]:
    return [k for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def agreement(obs: dict[str, str], reading: dict[str, str], keys: list[str]) -> int:
    return sum(1 for k in keys if obs.get(k) == reading.get(k))


def main() -> int:
    doc = json.load(open(PAYLOAD))
    caps = {c["id"]: c for c in doc["captures"]}

    print("T39 -- observation vs readings, FULL-CELL.")
    print(f"payload: out/t39-periodratio.json  (oracle commit {doc['fineractCommit']}, "
          f"MoneyHelper.PRECISION={doc['moneyHelperPrecisionConstant']})")
    print()
    print("R1 = DEC-1 revision 6 as written        (multiplier = RepaymentEvery)")
    print("R2 = the pinned source                  (multiplier = periodRatio)          [:1404-1413]")
    print("R3 = the pinned source, month-end special case OMITTED                      [:1426-1436]")
    print()

    verdicts = []
    for cid, req in SHAPES.items():
        cap = caps.get(cid)
        if cap is None:
            print(f"!! {cid}: NOT PRESENT IN THE PAYLOAD")
            continue
        obs = observed_cells(cap)
        r = {name: render_reading(req, name) for name in ("R1", "R2", "R3")}

        d12 = disagree(r["R1"], r["R2"])
        d23 = disagree(r["R2"], r["R3"])

        full = {name: (len(disagree(obs, r[name])), len(obs)) for name in ("R1", "R2", "R3")}

        print(f"--- {cid}   start={req.start} disb={req.disb} n={req.n} rate={req.rate_pct}")
        print(f"    periodRatio per repayment period: {[str(x) for x in period_ratios_for(req)]}")
        print(f"    month-end special case fires on (0-based): {monthend_special_case_fires(req)}")
        print(f"    observed totalInterest = {obs['totals.totalInterestAmount']}   "
              f"(R1 {r['R1']['totals.totalInterestAmount']} / "
              f"R2 {r['R2']['totals.totalInterestAmount']} / "
              f"R3 {r['R3']['totals.totalInterestAmount']})")
        for name in ("R1", "R2", "R3"):
            diff, tot = full[name]
            print(f"    FULL-CELL: observation vs {name}: {tot - diff}/{tot} cells reproduce"
                  + ("" if diff == 0 else f"  ({diff} differ)"))

        row = {"id": cid,
               "d12": len(d12), "d23": len(d23),
               "full_R1": full["R1"], "full_R2": full["R2"], "full_R3": full["R3"]}

        if d12:
            a1, a2 = agreement(obs, r["R1"], d12), agreement(obs, r["R2"], d12)
            print(f"    R1 vs R2 DISAGREE on {len(d12)} cells -> observation agrees with "
                  f"R1 on {a1}/{len(d12)}, with R2 on {a2}/{len(d12)}")
            row["p0"] = (a1, a2, len(d12))
        else:
            print("    R1 vs R2 disagree on 0 cells -> this shape CANNOT separate them "
                  "(it grades nothing about P0-T34-1)")
            row["p0"] = None

        if d23:
            b2, b3 = agreement(obs, r["R2"], d23), agreement(obs, r["R3"], d23)
            print(f"    R2 vs R3 DISAGREE on {len(d23)} cells -> observation agrees with "
                  f"R2 on {b2}/{len(d23)}, with R3 on {b3}/{len(d23)}")
            row["me"] = (b2, b3, len(d23))
        else:
            print("    R2 vs R3 disagree on 0 cells -> this shape CANNOT separate the "
                  "month-end special case")
            row["me"] = None
        print()
        verdicts.append(row)

    print("=" * 100)
    print(f"{'capture':14} {'P0: R1/R2 cells':>16} {'obs=R1':>8} {'obs=R2':>8}"
          f" {'ME: R2/R3 cells':>16} {'obs=R2':>8} {'obs=R3':>8} {'full-cell vs R2':>18}")
    for v in verdicts:
        p0 = v["p0"]
        me = v["me"]
        d, t = v["full_R2"]
        print(f"{v['id']:14} {v['d12']:>16} "
              f"{(str(p0[0]) if p0 else '-'):>8} {(str(p0[1]) if p0 else '-'):>8} "
              f"{v['d23']:>16} "
              f"{(str(me[0]) if me else '-'):>8} {(str(me[1]) if me else '-'):>8} "
              f"{f'{t - d}/{t}':>18}")
    print("=" * 100)

    p0_shapes = [v for v in verdicts if v["p0"]]
    me_shapes = [v for v in verdicts if v["me"]]
    p0_cells = sum(v["p0"][2] for v in p0_shapes)
    p0_r2 = sum(v["p0"][1] for v in p0_shapes)
    p0_r1 = sum(v["p0"][0] for v in p0_shapes)
    me_cells = sum(v["me"][2] for v in me_shapes)
    me_r2 = sum(v["me"][0] for v in me_shapes)
    me_r3 = sum(v["me"][1] for v in me_shapes)
    print(f"P0-T34-1: {len(p0_shapes)} separating shapes, {p0_cells} discriminating cells; "
          f"observation agrees with R1 (RepaymentEvery) on {p0_r1}, "
          f"with R2 (periodRatio) on {p0_r2}.")
    print(f"MONTH-END special case: {len(me_shapes)} separating shapes, {me_cells} discriminating "
          f"cells; observation agrees with R2 (special case PRESENT) on {me_r2}, "
          f"with R3 (OMITTED) on {me_r3}.")
    full_bad = [v for v in verdicts if v["full_R2"][0] != 0]
    if full_bad:
        print("NOTE -- R2 does not reproduce every cell on: "
              + ", ".join(f"{v['id']} ({v['full_R2'][0]} cells)" for v in full_bad))
    else:
        print("R2 reproduces EVERY cell of EVERY capture end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
