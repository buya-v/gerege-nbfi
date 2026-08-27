"""
T38 (H) -- direct check that NO committed capture carries a non-unit periodRatio.

The discrimination run (D) shows the two readings return the SAME MONEY on all
21 committed production-setting captures.  That is the operational fact, but it
could in principle be a coincidence.  This script checks the stronger, direct
statement DEC-1 4.1.1 makes: on every repayment period of every committed
capture, periodRatio == RepaymentEvery exactly.

RE-DERIVATION over committed capture inputs.  No oracle was contacted.
"""
import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t38_model import repayment_boundaries, period_ratio

SOURCES = [
    (".softhouse/capture/out/capture-prod-raw.json", "Path A pass 3"),
    (".softhouse/capture/out/capture-prod3b-raw.json", "Path A pass 3b"),
    (".softhouse/capture/dec1-binding/out/t37-binding.json", "T37 binding"),
]


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def main():
    print("=" * 78)
    print("H  Does ANY committed capture carry a repayment period whose")
    print("   periodRatio differs from RepaymentEvery?")
    print("=" * 78)
    total = 0
    drifted = 0
    for path, label in SOURCES:
        data = json.load(open(path), parse_float=Decimal, parse_int=int)
        for cap in data["captures"]:
            i = cap["inputs"]
            if i["daysInMonth"] != "DAYS_30" or i["daysInYear"] != "DAYS_360":
                print(f"{label}/{cap['id']:<14} SKIPPED (day count)")
                continue
            every = i.get("repaymentEvery", i.get("repaymentFrequency", 1))
            start = d(i["scheduleGenerationStartDate"])
            disb = d(i["disbursementDate"])
            bounds = repayment_boundaries(start, disb, i["numberOfRepayments"], every)
            ratios = [period_ratio(start, f, dd, every) for f, dd in bounds]
            bad = [r for r in ratios if r != Decimal(every)]
            total += 1
            if bad:
                drifted += 1
            print(f"{label}/{cap['id']:<14} start {start} disb {disb} "
                  f"prec {i['mathContextPrecision']:<3} "
                  f"periods {len(ratios):<3} non-unit periodRatio: "
                  f"{len(bad)}  {'<-- DRIFTED' if bad else ''}")
    print()
    print(f"captures checked: {total}   with any non-unit periodRatio: {drifted}")
    print()
    print("VERDICT:", "THE COMMITTED CORPUS IS BLIND TO periodRatio"
          if drifted == 0 else "at least one capture drifts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
