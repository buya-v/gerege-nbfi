"""
T39 -- the three READINGS of the `rateFactorTillPeriodDueDate` multiplier, and a
FULL-CELL renderer for each.

*** NOTHING IN THIS FILE IS AN OBSERVATION.  Every value it computes is a
*** RE-DERIVATION, produced so that it can be compared against an observation.
*** The oracle decides; this file only says what each reading PREDICTS.

The readings
------------

R1  "DEC-1 revision 6 as written".  The multiplier on BOTH call sites is
    `RepaymentEvery`.
      DEC-1 4.3.2 (lines 486-490) and nexus/internal/apps/loanschedule/contract/
      contract.go:1455-1459:
        rateFactorTillPeriodDueDate = setScale( (rate x 30 x RepaymentEvery / 360)
                                                x actualDays / calculatedDays,
                                                RateFactorScale )
    Implemented by t34_model.generate(req) with multipliers=None.

R2  "the pinned source".  The multiplier on the `rateFactorTillPeriodDueDate`
    call site is `periodRatio`
      [ProgressiveEMICalculator.java:1404-1413 -- the switch computes periodRatio
       and passes it, together with a hard-coded BigDecimal.valueOf(30), into
       calculateRateFactorPerPeriodBasedOnRepaymentFrequency],
    where periodRatio = calculatePeriodRatio(..., ChronoUnit.MONTHS, mc)
      [:1419-1458], seeded by calculateSeedDate [:1460-1479].
    The recurrence's own entry point still passes `repaymentEvery`
      [:1536-1537].
    Implemented by t34_model.generate(req, multipliers=period_ratios_for(req)).

R3  "the pinned source, month-end special case OMITTED".  Identical to R2 except
    that calculatePeriodRatio's MONTHS arm

        int targetDateLastDay = lastDayOfMonth(repaymentPeriod.getFromDate());
        if (targetDateLastDay == targetDateDay && seedDateDay > targetDateDay) {
            yield getExactDifference(seedDate, fromDate.plusDays(1), MONTHS);
        } else {
            yield getExactDifference(seedDate, fromDate, MONTHS);
        }
                                        [ProgressiveEMICalculator.java:1426-1436]

    is written WITHOUT the special case (the `else` branch always).  This is the
    single most plausible mis-port of the routine: it is four lines of edge-case
    handling inside a switch arm, and no committed capture names it.  R3 exists
    so that the month-end special case can be TARGETED rather than sampled.

Sources copied VERBATIM into this directory and hashed in ATTESTATION.md:
  t34_model.py       -- T34's transcription of DEC-1 revision 6 from its text alone
  t34_periodratio.py -- T34's transcription of calculatePeriodRatio/calculateSeedDate

Exact arithmetic only: Decimal at explicit contexts, integer minor units.
NO float appears anywhere on a money path in this file.
"""

from __future__ import annotations

import calendar
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from t34_model import (MINOR, Request, add_months_clamped, generate, m2s,  # noqa: E402
                       repayment_boundaries, round_mc, totals)
from t34_periodratio import (calculate_seed_date, months_between,  # noqa: E402
                             period_ratios_for)


# --------------------------------------------------------------------------
# R3's period ratio: t34_periodratio.calculate_period_ratio with ONE marked edit
# --------------------------------------------------------------------------

def calculate_period_ratio_no_monthend(schedule_start: date, rp_from: date, rp_due: date,
                                       repay_every: int) -> Decimal:
    """calculatePeriodRatio [:1419-1458] MONTHS arm, with the month-end special
    case at :1429-1434 REMOVED.  Everything else is t34_periodratio's transcription
    character for character."""
    seed = calculate_seed_date(schedule_start, rp_from, rp_due, repay_every)

    # >>> MARKED EDIT (R3): the special case is omitted; the else branch always.
    n = months_between(seed, rp_from)
    # <<< END MARKED EDIT

    mult = n + 1
    from_date = rp_from
    while from_date < rp_due:
        from_date = add_months_clamped(seed, mult)
        if not (from_date > rp_due):
            mult += 1
        else:
            full_period_date = from_date
            mult = mult - n - 1
            from_date = add_months_clamped(seed, mult)
            difference = (rp_due - from_date).days
            full_difference = (full_period_date - from_date).days
            return round_mc(Decimal(difference) / Decimal(full_difference)) + Decimal(mult)
    mult = mult - n - 1
    return Decimal(mult)


def period_ratios_no_monthend(req: Request) -> list[Decimal]:
    bounds = repayment_boundaries(req.start, req.disb, req.n, req.every)
    return [calculate_period_ratio_no_monthend(req.start, f, d, req.every) for f, d in bounds]


def monthend_special_case_fires(req: Request) -> list[int]:
    """Indices of the repayment periods on which calculatePeriodRatio's month-end
    special case [:1429-1434] evaluates TRUE.  A re-derivation from the pinned
    source, used only to choose shapes."""
    out = []
    bounds = repayment_boundaries(req.start, req.disb, req.n, req.every)
    for i, (f, d) in enumerate(bounds):
        seed = calculate_seed_date(req.start, f, d, req.every)
        last_day = calendar.monthrange(f.year, f.month)[1]
        if last_day == f.day and seed.day > f.day:
            out.append(i)
    return out


# --------------------------------------------------------------------------
# the three readings, as row lists
# --------------------------------------------------------------------------

def rows_R1(req: Request):
    return generate(req)


def rows_R2(req: Request):
    return generate(req, multipliers=period_ratios_for(req))


def rows_R3(req: Request):
    return generate(req, multipliers=period_ratios_no_monthend(req))


READINGS = {"R1": rows_R1, "R2": rows_R2, "R3": rows_R3}


# --------------------------------------------------------------------------
# FULL-CELL renderer
# --------------------------------------------------------------------------
# Every column the Path-A harness emits, for every row, plus the plan totals.
# NOT the three headline scalars -- that shape is what let F-1 hide through five
# reviews (.softhouse/patterns.md).

def render(req: Request, rows) -> dict[str, str]:
    """Cell map: address -> exact decimal string, addressed the same way the
    observation is addressed by discriminate.py."""
    cells: dict[str, str] = {}

    total_principal_minor, total_interest_minor, total_repay_minor = totals(rows)

    first_from = rows[0].frm
    last_due = rows[-1].due
    cells["totals.loanTermInDays"] = str((last_due - first_from).days)
    cells["totals.totalDisbursedAmount"] = m2s(req.principal_minor)
    cells["totals.totalInterestAmount"] = m2s(total_interest_minor)
    cells["totals.totalRepaymentAmount"] = m2s(total_repay_minor)

    # The DISBURSEMENT row.  The harness prints periodFromDate, periodDueDate and
    # principal for it.
    cells["disbursement.fromDate"] = req.disb.isoformat()
    cells["disbursement.dueDate"] = req.disb.isoformat()
    cells["disbursement.principal"] = m2s(req.principal_minor)

    # totalOutstandingBalance on repayment row i is, on every committed capture,
    # that row's outstanding principal plus the interest still to fall due.
    remaining_interest = total_interest_minor
    for i, p in enumerate(rows, start=1):
        remaining_interest -= p.interest_minor
        k = f"period[{i}]"
        cells[k + ".fromDate"] = p.frm.isoformat()
        cells[k + ".dueDate"] = p.due.isoformat()
        cells[k + ".principal"] = m2s(p.principal_minor)
        cells[k + ".interest"] = m2s(p.interest_minor)
        cells[k + ".fee"] = "0.00"
        cells[k + ".penalty"] = "0.00"
        cells[k + ".balance"] = m2s(p.outstanding_minor)
        cells[k + ".total"] = m2s(p.emi_minor)
        cells[k + ".totalOutstandingBalance"] = m2s(p.outstanding_minor + remaining_interest)
    return cells


def render_reading(req: Request, name: str) -> dict[str, str]:
    return render(req, READINGS[name](req))
