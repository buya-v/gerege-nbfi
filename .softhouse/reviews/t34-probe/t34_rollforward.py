"""
T34 (D): DEC-1 4.3.2 step 4's roll-forward against the committed capture P-03.

DEC-1 4.3.2 step 4 states, normatively:

    OutstandingPrincipalMinor = max(0, balance carried in
                                    + amounts disbursed in this period
                                    - PrincipalMinor)
                                    [RepaymentPeriod.java:389-403, clamp at :399]

The same subsection's segmentation table row 2 states, for a disbursement dated
on repayment period j's DueDate:

    "ONE, unchanged; the amount is recorded on it and enters period j+1's balance"

Those two sentences give DIFFERENT answers for period j's own row, and the
document never says which governs:

  reading A -- "in this period" is the repayment period CONTAINING the
               disbursement, under 4.3.1's membership rule ([From,Due] for the
               first period, (From,Due] for later ones).  Period j's outstanding
               is then the full principal.
  reading B -- the amount is not "in" period j at all because it enters period
               j+1's balance.  Period j's outstanding is then 0.

Committed capture P-03 (.softhouse/capture/out/capture-prod-raw.json) records
period 1's balance as "0.00" -- reading B.  NOTHING HERE IS A NEW OBSERVATION;
the expectation is transcribed from that committed file.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from t34_model import (Request, segment, apply_rate_factors, first_related,
                       level_installment, build, m2s, MINOR)


def reading_b_fix(req: Request, rows):
    """Reading B: zero the outstanding of the repayment period whose DueDate
    equals the disbursement date (and of every row before it)."""
    for p in rows:
        if p.due <= req.disb:
            p.outstanding_minor = 0
    return rows


def main():
    print("T34 (D) -- DEC-1 4.3.2 step 4's roll-forward vs the committed corpus.")
    print("NO ORACLE WAS CONTACTED.  The expectations are transcribed from")
    print(".softhouse/capture/out/capture-prod-raw.json.")
    print()

    data = json.load(open(".softhouse/capture/out/capture-prod-raw.json"))
    cap = next(c for c in data["captures"] if c["id"] == "P-03")
    obs = [p for p in cap["observed"]["periods"] if p["type"] == "REPAYMENT"]

    req = Request(start=date(2024, 1, 1), disb=date(2024, 2, 1),
                  principal_minor=100 * MINOR, n=6, rate_pct=Decimal("7.0"))
    periods, target = segment(req)
    apply_rate_factors(req, periods)
    fr = first_related(req, periods, target)
    emi = level_installment(periods, fr, req.principal_minor)
    a = build(req, emi, fr)

    print("  capture P-03: schedule start 2024-01-01, disbursement 2024-02-01,")
    print("                100.00 / 6 x 7.0%, (19, HALF_UP)")
    print()
    print(f"  {'period':>7} {'due':>11} {'principal':>10} {'interest':>10} "
          f"{'reading A':>10} {'reading B':>10} {'CAPTURE':>10}")
    mismatch_a = mismatch_b = 0
    for i, (o, r) in enumerate(zip(obs, a), start=1):
        ra = m2s(r.outstanding_minor)
        rb = m2s(0 if r.due <= req.disb else r.outstanding_minor)
        capv = f'{Decimal(o["balance"]):.2f}'
        if ra != capv:
            mismatch_a += 1
        if rb != capv:
            mismatch_b += 1
        print(f"  {i:>7} {str(r.due):>11} {m2s(r.principal_minor):>10} "
              f"{m2s(r.interest_minor):>10} {ra:>10} {rb:>10} {capv:>10}"
              f"   {'<-- DIVERGES' if ra != rb else ''}")
    print()
    print(f"  reading A (DEC-1 4.3.2 step 4 read literally): "
          f"{mismatch_a} row(s) disagree with the capture")
    print(f"  reading B (segmentation-table row 2 read literally): "
          f"{mismatch_b} row(s) disagree with the capture")
    print()
    print("  The divergence class is EVERY graded-domain request whose single")
    print("  disbursement falls on a repayment period's DueDate -- an entire row")
    print("  of DEC-1 4.3.1's own related-periods table ('on period j's due date,")
    print("  j < N').  The gap on that row is the WHOLE PRINCIPAL.")
    print()
    print("  Note also: the 13-observation check in DEC-1 4.3.1's Provenance")
    print("  paragraph compares three numbers per shape (level installment, final")
    print("  installment, total interest).  It does not compare")
    print("  OutstandingPrincipalMinor at all, so '13 of 13' could not have")
    print("  detected this.  The row-level capture P-03 does.")


if __name__ == "__main__":
    main()
