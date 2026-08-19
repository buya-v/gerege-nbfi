"""
T39 -- SHAPE SELECTION.  Run BEFORE the capture.

Asks, by RE-DERIVATION only, which candidate shapes actually SEPARATE the
readings, so that the capture does not spend a run landing where every reading
agrees.  A capture taken where the readings agree proves nothing, and this file
is what stops that happening by accident.

*** NO ORACLE IS CONTACTED HERE.  Nothing printed by this file is an observation.

Two separations are measured:
  R1 vs R2  -- DEC-1 revision 6's `RepaymentEvery` against the pinned source's
               `periodRatio`.  This is P0-T34-1.
  R2 vs R3  -- the pinned source against the same routine with calculatePeriodRatio's
               month-end special case [:1429-1434] omitted.  This is the sub-shape
               the brief asks to target deliberately.

Comparison is FULL-CELL: every column of every row plus the plan totals.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from t34_model import MINOR, Request  # noqa: E402
from t34_periodratio import period_ratios_for  # noqa: E402
from readings import (monthend_special_case_fires, period_ratios_no_monthend,  # noqa: E402
                      render_reading)


def disagree(a: dict[str, str], b: dict[str, str]) -> list[str]:
    keys = sorted(set(a) | set(b))
    return [k for k in keys if a.get(k) != b.get(k)]


def report(tag: str, req: Request) -> dict:
    r1 = render_reading(req, "R1")
    r2 = render_reading(req, "R2")
    r3 = render_reading(req, "R3")
    d12 = disagree(r1, r2)
    d23 = disagree(r2, r3)
    print(f"--- {tag}")
    print(f"    start={req.start} disb={req.disb} principal={req.principal_minor // MINOR}"
          f" n={req.n} rate={req.rate_pct}")
    print(f"    periodRatio (R2): {[str(x) for x in period_ratios_for(req)]}")
    print(f"    periodRatio (R3, no month-end case): {[str(x) for x in period_ratios_no_monthend(req)]}")
    print(f"    month-end special case fires on repayment periods (0-based): "
          f"{monthend_special_case_fires(req)}")
    print(f"    R1 vs R2: {len(d12)} differing cells; totalInterest "
          f"R1={r1['totals.totalInterestAmount']} R2={r2['totals.totalInterestAmount']}")
    print(f"    R2 vs R3: {len(d23)} differing cells; totalInterest "
          f"R2={r2['totals.totalInterestAmount']} R3={r3['totals.totalInterestAmount']}")
    return {"tag": tag, "d12": len(d12), "d23": len(d23)}


# The shapes actually taken to the oracle.  Ids and inputs are identical to
# ../src/CapturePeriodRatio.java; discriminate.py joins the two by id.
# T39-CAL is not listed here: it runs at (12, HALF_UP) against a shipped USD test
# literal and is a rig calibration, never a parity vector, so "which reading does
# it favour" is not a question about it.
SHAPES = {
    # ---- in-graded-domain CONTROLS, OUTSIDE the drift region.
    #      Both readings agree on every cell here.  That is the point: these
    #      shapes license the claim that the harness reproduces the oracle where
    #      nothing is in dispute.
    "T39-CTL-Q0a": Request(date(2024, 1, 1), date(2024, 1, 1), 1200000 * MINOR, 6, Decimal("21.6")),
    "T39-CTL-1": Request(date(2024, 1, 1), date(2024, 1, 1), 1014632 * MINOR, 6, Decimal("7.0")),
    "T39-CTL-2": Request(date(2024, 1, 15), date(2024, 1, 15), 1200000 * MINOR, 6, Decimal("21.6")),

    # ---- IN the drift region: schedule start near month end, disbursement LATER
    #      in the same month with a larger day, so DefaultScheduledDateGenerator's
    #      re-anchor seed (the DISBURSEMENT date) and calculateSeedDate's seed
    #      (the SCHEDULE START date) disagree and the boundaries leave the lattice.
    "T39-P0-A": Request(date(2024, 1, 28), date(2024, 1, 31), 1200000 * MINOR, 6, Decimal("21.6")),
    "T39-P0-B": Request(date(2024, 1, 28), date(2024, 1, 29), 1200000 * MINOR, 6, Decimal("21.6")),
    "T39-P0-C": Request(date(2024, 1, 29), date(2024, 1, 31), 5000000 * MINOR, 12, Decimal("16.8")),
    "T39-P0-D": Request(date(2024, 1, 28), date(2024, 1, 31), 50000000 * MINOR, 36, Decimal("21.6")),
    "T39-P0-E": Request(date(2025, 1, 28), date(2025, 1, 31), 1200000 * MINOR, 6, Decimal("21.6")),
    "T39-P0-F": Request(date(2024, 1, 28), date(2024, 1, 31), 100 * MINOR, 6, Decimal("21.6")),
    "T39-P0-G": Request(date(2024, 3, 28), date(2024, 3, 31), 2500000 * MINOR, 6, Decimal("16.8")),
    "T39-P0-H": Request(date(2024, 11, 28), date(2024, 11, 30), 3000000 * MINOR, 6, Decimal("16.8")),

    # ---- the MONTH-END SPECIAL CASE inside calculatePeriodRatio [:1429-1434].
    #      T39-ME-A is ALSO a reproduction control: its inputs are byte-identical
    #      to the committed capture T37-3b-2.
    "T39-ME-A": Request(date(2024, 1, 31), date(2024, 1, 31), 3924149 * MINOR, 6, Decimal("16.8")),
    "T39-ME-B": Request(date(2024, 1, 31), date(2024, 1, 31), 1200000 * MINOR, 6, Decimal("21.6")),
    "T39-ME-C": Request(date(2023, 1, 31), date(2023, 1, 31), 1200000 * MINOR, 6, Decimal("21.6")),
    "T39-ME-D": Request(date(2024, 1, 30), date(2024, 1, 30), 1200000 * MINOR, 6, Decimal("21.6")),
}

if __name__ == "__main__":
    print("T39 shape selection -- RE-DERIVATION ONLY, no oracle contacted.\n")
    rows = [report(tag, req) for tag, req in SHAPES.items()]
    print("\nsummary (differing cells)")
    print(f"{'shape':14} {'R1 vs R2':>10} {'R2 vs R3':>10}")
    for r in rows:
        print(f"{r['tag']:14} {r['d12']:>10} {r['d23']:>10}")
