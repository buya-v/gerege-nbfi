"""
T38 (D) -- the from-text DISCRIMINATION check.

A specification that cannot tell the wrong answer from the right one has not
been fixed.  For each WRONG reading, this script asks two questions against the
committed corpus (12 Path-A pass-3 captures + 11 T37 binding captures, all read
from files already on main):

  1. does revision 7's text reproduce every capture?          (must be YES)
  2. does the wrong reading FAIL at least one capture?         (want YES)

Where the answer to 2 is NO the corpus is BLIND to that reading, and the script
says so rather than pretending otherwise; for the blind one it then shows, on
the DEC-1 8 item 3e candidate shape, that the two readings return DIFFERENT
money -- a RE-DERIVATION, recorded as a candidate shape to capture and never as
an observation.

NO ORACLE WAS CONTACTED.  Nothing here may be promoted to the vector store.
"""
import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t38_model import Request, generate, totals, m2s, MINOR, period_ratio

SOURCES = [
    (".softhouse/capture/out/capture-prod-raw.json", "Path A pass 3"),
    (".softhouse/capture/dec1-binding/out/t37-binding.json", "T37 binding"),
]

READINGS = {
    "ratio-is-always-1            (P0-T32-1)": dict(ratio_one=True),
    "textbook balance x rateFactor(P0-T29-2)": dict(textbook=True),
    "n = NumberOfRepayments       (P0-T29-1)": dict(wrong_n=True),
    "RepaymentEvery not periodRatio(P0-T34-1)": dict(till_multiplier="repaymentEvery"),
    "whole-principal pre-disb row (P0-T37-1)": dict(whole_principal_prerow=True),
    "EMI re-adjust loop ABSENT    (item 3)  ": dict(run_loop=False),
    "loop without the ADOPTION test(item 3a)": dict(no_adoption=True),
}


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def load_cases():
    cases = []
    for path, label in SOURCES:
        data = json.load(open(path), parse_float=Decimal, parse_int=int)
        for cap in data["captures"]:
            i = cap["inputs"]
            if i["mathContextPrecision"] != 19:
                continue
            if i["daysInMonth"] != "DAYS_30" or i["daysInYear"] != "DAYS_360":
                continue
            req = Request(start=d(i["scheduleGenerationStartDate"]),
                          disb=d(i["disbursementDate"]),
                          principal_minor=int(Decimal(str(i["disbursementAmount"])) * MINOR),
                          n=i["numberOfRepayments"],
                          rate_pct=Decimal(str(i["annualNominalInterestRate"])),
                          every=i.get("repaymentEvery", i.get("repaymentFrequency", 1)))
            cells = {}
            k = 0
            for p in cap["observed"]["periods"]:
                if p["type"] != "REPAYMENT":
                    continue
                k += 1
                cells[f"R{k}.dueDate"] = p["dueDate"]
                cells[f"R{k}.principal"] = f'{Decimal(str(p["principal"])):.2f}'
                cells[f"R{k}.interest"] = f'{Decimal(str(p["interest"])):.2f}'
                cells[f"R{k}.balance"] = f'{Decimal(str(p["balance"])):.2f}'
            cells["totalInterest"] = f'{Decimal(str(cap["observed"]["totalInterestAmount"])):.2f}'
            cases.append((f"{label}/{cap['id']}", req, cells))
    return cases


def model_cells(req, **opts):
    rows = generate(req, **opts)
    out = {}
    for i, r in enumerate(rows, start=1):
        out[f"R{i}.dueDate"] = str(r.due)
        out[f"R{i}.principal"] = m2s(r.principal_minor)
        out[f"R{i}.interest"] = m2s(r.interest_minor)
        out[f"R{i}.balance"] = m2s(r.outstanding_minor)
    out["totalInterest"] = m2s(totals(rows)[1])
    return out


def main():
    cases = load_cases()
    print("=" * 78)
    print("D  From-text DISCRIMINATION over the committed corpus")
    print(f"   {len(cases)} captures at (19, HALF_UP), 30/360, compared CELL BY CELL")
    print("   (due date, principal, interest, outstanding balance, total interest)")
    print("=" * 78)

    # 1. revision 7 itself
    fails = []
    for name, req, exp in cases:
        got = model_cells(req)
        bad = [k for k, v in exp.items() if got.get(k) != v]
        if bad:
            fails.append((name, bad))
    print(f"\nrevision 7 (as written): {len(cases) - len(fails)} of {len(cases)} "
          f"captures reproduce")
    for n, b in fails:
        print(f"    FAIL {n}: {b[:6]}")

    print()
    print(f"{'wrong reading':<42} {'captures failed':>16}  {'first witness':<24}")
    print("-" * 78)
    blind = []
    for label, opts in READINGS.items():
        failed = []
        for name, req, exp in cases:
            got = model_cells(req, **opts)
            bad = [k for k, v in exp.items() if got.get(k) != v]
            if bad:
                failed.append((name, bad[0], got.get(bad[0]), exp[bad[0]]))
        witness = failed[0][0] if failed else "-- NONE: CORPUS IS BLIND --"
        print(f"{label:<42} {len(failed):>7} of {len(cases):<6}  {witness:<24}")
        if failed:
            n, cell, g, e = failed[0]
            print(f"{'':<42} {'':>16}  cell {cell}: reading gives {g}, "
                  f"oracle observed {e}")
        else:
            blind.append((label, opts))

    # 2. for any reading the corpus cannot see, show it moves money anyway
    if blind:
        print()
        print("=" * 78)
        print("D2  Readings the committed corpus CANNOT separate -- shown to move")
        print("    money on the DEC-1 8 item 3e candidate shape.")
        print("    EVERY FIGURE BELOW IS A RE-DERIVATION, NOT AN OBSERVATION.")
        print("=" * 78)
        cands = [
            ("3e candidate: MNT 1,200,000 / 6 x 21.6 %, start 2024-01-28, "
             "disbursement 2024-01-31",
             Request(start=date(2024, 1, 28), disb=date(2024, 1, 31),
                     principal_minor=1_200_000 * 100, n=6, rate_pct=Decimal("21.6"))),
            ("3e sibling:   MNT 50,000,000 / 36 x 21.6 %, start 2024-01-28, "
             "disbursement 2024-01-31",
             Request(start=date(2024, 1, 28), disb=date(2024, 1, 31),
                     principal_minor=50_000_000 * 100, n=36, rate_pct=Decimal("21.6"))),
        ]
        for label, opts in blind:
            for desc, req in cands:
                a = model_cells(req)
                b = model_cells(req, **opts)
                diff = [k for k in a if a[k] != b[k]]
                print(f"\n  reading: {label.strip()}")
                print(f"  shape:   {desc}")
                print(f"  cells differing: {len(diff)} of {len(a)}")
                print(f"  total interest: revision 7 {a['totalInterest']}   "
                      f"wrong reading {b['totalInterest']}")
                print(f"  period-1 interest: revision 7 {a['R1.interest']}   "
                      f"wrong reading {b['R1.interest']}")
                pr = period_ratio(req.start, req.start,
                                  # period 1's own window, recomputed for display
                                  __import__("t38_model").repayment_boundaries(
                                      req.start, req.disb, req.n, req.every)[0][1],
                                  req.every)
                print(f"  periodRatio of repayment period 1: {pr}")

    print()
    print("=" * 78)
    print("VERDICT:", "revision 7 reproduces the whole corpus"
          if not fails else "revision 7 FAILS the corpus")
    print("=" * 78)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
