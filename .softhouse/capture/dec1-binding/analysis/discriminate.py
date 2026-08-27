#!/usr/bin/env python3
"""T37 step 2 -- DISCRIMINATION, run AFTER the capture.

For each captured shape, run DEC-1 revision 6's reading AND the wrong reading the
corresponding binding item exists to separate, and compare BOTH against the
OBSERVATION in ../out/t37-binding.json -- row by row, every money cell, not just
three summary figures.

The one sentence this script exists to produce, per item:
    "the observation separates the readings"  or  "it does not, and here is why".

The observation is the ONLY evidence here.  The readings are re-derivations; where a
reading agrees with the observation that is a fact about the reading, not a new
observation, and nothing computed by this file may enter the vector store.
"""
import json
import os
from datetime import date

import dec1_readings as m

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "..", "out", "t37-binding.json")

D = date

# capture id -> (principal, n, rate, start, disb, binding item,
#                wrong-reading label, wrong-reading kwargs)
SHAPES = {
    "T37-CAL": (100, 6, "7.0", D(2024, 1, 1), None, "-", None, None),
    "T37-CTL-Q0a": (1200000, 6, "21.6", D(2024, 1, 1), None, "-", None, None),
    "T37-3-A": (1014632, 6, "7.0", D(2024, 1, 1), None, "3",
                "EMI re-adjust loop never implemented", {"loop_reading": "absent"}),
    "T37-3-B": (127704, 36, "16.8", D(2024, 1, 1), None, "3",
                "EMI re-adjust loop never implemented", {"loop_reading": "absent"}),
    "T37-3a": (100025, 12, "16.8", D(2024, 1, 1), None, "3a",
               "loop implemented WITHOUT the strict adoption test", {"loop_reading": "no_adoption"}),
    "T37-3b": (13202, 6, "16.8", D(2024, 1, 1), None, "3b",
               "textbook `balance x rateFactor` interest", {"interest_reading": "textbook"}),
    "T37-3b-2": (3924149, 6, "16.8", D(2024, 1, 31), None, "3b",
                 "textbook `balance x rateFactor` interest", {"interest_reading": "textbook"}),
    "T37-3c": (10548069, 6, "16.8", D(2024, 1, 1), D(2024, 2, 1), "3c",
               "n = NumberOfRepayments instead of |relatedRepaymentPeriods|",
               {"n_reading": "numberofrepayments"}),
    "T37-3c-2": (13549647, 6, "21.6", D(2024, 1, 1), D(2024, 2, 1), "3c",
                 "n = NumberOfRepayments instead of |relatedRepaymentPeriods|",
                 {"n_reading": "numberofrepayments"}),
    "T37-3d": (1200000, 6, "21.6", D(2024, 1, 1), D(2024, 1, 15), "3d",
               "day-count ratio hard-coded to 1", {"day_counts": "ratio1"}),
    "T37-3d-2": (127704, 36, "16.8", D(2024, 1, 1), D(2024, 1, 20), "3d",
                 "day-count ratio hard-coded to 1", {"day_counts": "ratio1"}),
}

CELLS = ("principal", "interest", "total", "balance")


def observed_rows(cap):
    o = cap["observed"]
    reps = [p for p in o["periods"] if p["type"] == "REPAYMENT"]
    return {
        "totalInterestAmount": o["totalInterestAmount"],
        "totalRepaymentAmount": o["totalRepaymentAmount"],
        "periods": [{"periodNumber": p["periodNumber"], "fromDate": p["fromDate"],
                     "dueDate": p["dueDate"], "principal": p["principal"],
                     "interest": p["interest"], "total": p["total"],
                     "balance": p["balance"]} for p in reps],
    }


def cells(d):
    """Flatten a schedule into an addressable cell map."""
    out = {"totalInterestAmount": d["totalInterestAmount"],
           "totalRepaymentAmount": d["totalRepaymentAmount"]}
    for p in d["periods"]:
        for c in CELLS:
            out[f"p{p['periodNumber']}.{c}"] = p[c]
        out[f"p{p['periodNumber']}.window"] = f"{p['fromDate']}..{p['dueDate']}"
    return out


def compare(obs, rd):
    """Return (matches on EVERY cell, [mismatch descriptions])."""
    a, b = cells(obs), cells(rd)
    bad = [f"{k}: observed {a[k]} vs reading {b.get(k)}"
           for k in a if a[k] != b.get(k)]
    return (not bad), bad


def separation(obs, spec, wrong):
    """The correct discrimination test.

    Compare the two readings to each other first; the cells where THEY differ are
    the only cells that can carry information about the question this capture was
    taken to settle.  On exactly those cells, ask which reading the OBSERVATION
    agrees with.  A cell where both readings agree tells us nothing about them --
    a disagreement there is a defect in BOTH, i.e. a different finding entirely.
    """
    a, s, w = cells(obs), cells(spec), cells(wrong)
    disc = [k for k in s if s[k] != w.get(k)]
    obs_is_spec = [k for k in disc if a.get(k) == s[k]]
    obs_is_wrong = [k for k in disc if a.get(k) == w[k]]
    neither = [k for k in disc if a.get(k) not in (s[k], w[k])]
    return disc, obs_is_spec, obs_is_wrong, neither


def main():
    cap = json.load(open(CAP))
    print("T37 DISCRIMINATION -- observation vs the two readings")
    print(f"capture file : {os.path.normpath(CAP)}")
    print(f"oracle commit: {cap['fineractCommit']}   JVM {cap['javaVmVersion']}")
    print(f"MoneyHelper.PRECISION constant as the oracle reports it: "
          f"{cap['moneyHelperPrecisionConstant']}\n")

    verdicts = []
    for c in cap["captures"]:
        cid = c["id"]
        p, n, r, start, disb, item, wlabel, wkw = SHAPES[cid]
        obs = observed_rows(c)
        spec = m.reading(p, n, r, start, disb)
        ok_spec, bad_spec = compare(obs, spec)

        ds = f" disb={disb}" if disb else ""
        print(f"--- {cid}  (DEC-1 8/{item})  MNT {p:,} / {n} x {r}%  start={start}{ds}")
        print(f"    ambient MathContext the oracle reported: "
              f"{c['inputs']['ambientMoneyHelperMathContext']}")
        print(f"    threaded MathContext: ({c['inputs']['mathContextPrecision']}, "
              f"{c['inputs']['mathContextRoundingMode']})")
        print(f"    OBSERVED  total interest {obs['totalInterestAmount']:>15}   "
              f"final installment {obs['periods'][-1]['total']:>15}")
        print(f"    FIDELITY -- DEC-1 rev 6 reading reproduces the observation on "
              f"EVERY cell: {'YES' if ok_spec else 'NO'}")
        if not ok_spec:
            for line in bad_spec[:8]:
                print(f"        MISMATCH {line}")

        if wkw is None:
            print("    (control case -- no wrong reading attached)\n")
            verdicts.append((cid, item, ok_spec, None, None, 0))
            continue

        wrong = m.reading(p, n, r, start, disb, **wkw)
        ok_wrong, _ = compare(obs, wrong)
        disc, is_spec, is_wrong, neither = separation(obs, spec, wrong)
        print(f"    WRONG reading ({wlabel})")
        print(f"        total interest {wrong['totalInterestAmount']:>15}   "
              f"final installment {wrong['periods'][-1]['total']:>15}")
        print(f"        reproduces the observation on every cell: {'YES' if ok_wrong else 'NO'}")
        print(f"    DISCRIMINATION -- cells on which the two readings DISAGREE: {len(disc)}")
        print(f"        observation agrees with DEC-1 rev 6 on {len(is_spec)}/{len(disc)}"
              f"   with the wrong reading on {len(is_wrong)}/{len(disc)}"
              f"   with neither on {len(neither)}/{len(disc)}")
        for k in disc[:4]:
            print(f"        {k}: observed {cells(obs).get(k)} | rev 6 {cells(spec)[k]}"
                  f" | wrong {cells(wrong)[k]}")
        sep = bool(disc) and len(is_spec) == len(disc) and len(is_wrong) < len(disc)
        print(f"    => THE OBSERVATION {'SEPARATES' if sep else 'DOES NOT SEPARATE'} THE READINGS\n")
        verdicts.append((cid, item, ok_spec, ok_wrong, sep, len(disc)))

    print("=" * 92)
    print(f"{'capture':<14}{'item':<6}{'rev6 all cells':<16}{'wrong all cells':<17}"
          f"{'disc cells':<12}separates?")
    for cid, item, ok_spec, ok_wrong, sep, nd in verdicts:
        a = "reproduces" if ok_spec else "FAILS"
        b = "-" if ok_wrong is None else ("reproduces" if ok_wrong else "FAILS")
        s = "-" if sep is None else ("YES" if sep else "NO")
        print(f"{cid:<14}{item:<6}{a:<16}{b:<17}{nd:<12}{s}")
    print("=" * 92)


if __name__ == "__main__":
    main()
