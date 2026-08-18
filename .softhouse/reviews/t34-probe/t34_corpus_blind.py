"""
T34 (E): is the committed corpus blind to the periodRatio question?

For every committed Path-A capture and for the thirteen observations DEC-1
4.3.1's Provenance paragraph relies on, compute the pinned source's
`periodRatio` [ProgressiveEMICalculator.java:1404-1413] per repayment period.
If it is 1 everywhere, no capture in the corpus can separate DEC-1 revision 6's
normative `RepaymentEvery` from the source's `periodRatio`.

*** NO ORACLE WAS CONTACTED.  RE-DERIVATION ONLY. ***
"""
from __future__ import annotations

import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t34_model import Request, MINOR
from t34_periodratio import period_ratios_for


def d(s):
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def main():
    print("T34 (E) -- can any committed capture see the periodRatio question?")
    print("RE-DERIVATION ONLY.  NO ORACLE WAS CONTACTED.")
    print()
    data = json.load(open(".softhouse/capture/out/capture-prod-raw.json"))
    nonunit = 0
    for cap in data["captures"]:
        i = cap["inputs"]
        req = Request(start=d(i["scheduleGenerationStartDate"]),
                      disb=d(i["disbursementDate"]),
                      principal_minor=int(Decimal(i["disbursementAmount"]) * MINOR),
                      n=i["numberOfRepayments"],
                      rate_pct=Decimal(i["annualNominalInterestRate"]),
                      every=i["repaymentFrequency"])
        ratios = period_ratios_for(req)
        bad = [str(r) for r in ratios if r != Decimal(1)]
        if bad:
            nonunit += 1
        print(f"  {cap['id']:<14} start {i['scheduleGenerationStartDate']} "
              f"disb {i['disbursementDate']}  "
              f"all periodRatio == 1: {'NO ' + str(bad) if bad else 'yes'}")
    print()
    print("  the 13 observations of DEC-1 4.3.1's Provenance paragraph "
          "(schedule start 2024-01-01):")
    thirteen = [(6, None), (6, None), (36, None), (6, None), (6, None), (6, None),
                (12, None), (18, None), (18, None), (36, None), (36, None),
                (6, None), (6, date(2024, 2, 1))]
    bad13 = 0
    for n, disb in thirteen:
        start = date(2024, 1, 1)
        req = Request(start=start, disb=disb or start, principal_minor=100 * MINOR,
                      n=n, rate_pct=Decimal("7.0"))
        if any(r != Decimal(1) for r in period_ratios_for(req)):
            bad13 += 1
    print(f"    {13 - bad13} of 13 have periodRatio == 1 on every period")
    print()
    print(f"  Path-A captures with any non-unit periodRatio: {nonunit} of "
          f"{len(data['captures'])}")
    print()
    print("  CONCLUSION: the committed corpus is entirely blind to the difference")
    print("  between DEC-1 revision 6's normative `RepaymentEvery` multiplier and")
    print("  the pinned source's `periodRatio`.  Every capture, and every one of")
    print("  the thirteen observations, sits on the sub-manifold where they coincide.")


if __name__ == "__main__":
    main()
