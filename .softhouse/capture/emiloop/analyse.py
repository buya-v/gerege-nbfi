#!/usr/bin/env python3
"""T57 -- derive the EmiAdjustment guard and the EMI-SMOOTHING-LOOP-OMITTED margin.

Three stages, in this order, because stage 1 is what makes stages 2 and 3 mean anything.

  STAGE 1  CONTROL. Run the no-loop model over the ELEVEN already-promoted pass-3b parity
           captures. T9 (review section 1.2) showed a loop-omitting re-derivation reproduces
           every cell of all eleven. If this model does the same, it IS a faithful model of
           "the oracle minus the smoothing loop" -- and any place it then DISAGREES with the
           oracle is attributable to the loop rather than to a modelling error.

  STAGE 2  GUARD. Evaluate EmiAdjustment.shouldBeAdjusted on the NO-LOOP model for the two
           new pass-3c shapes. The oracle evaluates it there too: the loop is called at
           ProgressiveEMICalculator.java:749, AFTER calculateLastUnpaidRepaymentPeriodEMI at
           :747, so the pre-adjustment state is exactly the no-loop schedule.
           The guard is ALSO reported on the OBSERVED post-loop schedule, for contrast.

  STAGE 3  MARGIN. The largest per-cell minor-unit distance between the oracle's OBSERVED
           schedule and the no-loop counterfactual, over principal, interest and outstanding
           balance -- plus the total-interest distance.
"""
import json
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noloop_model import noloop_schedule, guard  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CAP3B = os.path.join(ROOT, ".softhouse/capture/out/capture-prod3b-raw.json")
CAP3C = os.path.join(ROOT, ".softhouse/capture/out/capture-prod3c-raw.json")

PROMOTED = ["P-00", "P-01", "P-02", "P-02b", "P-04f", "P-04t",
            "P-MNT-5M", "P-MNT-1M2", "P-MNT-50M", "P-MNT-4M999"]
# P-03 is excluded from the control: its disbursement falls on repayment 1's due date, so
# n = 5 related periods over a 6-repayment schedule and row 1 is all-zero. The model below
# takes the simple in-domain shape (disbursement on the schedule start) on purpose.


def minor(text):
    ip, _, fp = text.partition(".")
    fp = (fp + "00")[:2]
    return int(ip) * 100 + int(fp)


def load(path):
    d = json.load(open(path))
    return {c["id"]: c for c in d["captures"]}


def rows_of(cap):
    return [p for p in cap["observed"]["periods"] if p["type"] == "REPAYMENT"]


def control(cases):
    print("STAGE 1 -- CONTROL: does the no-loop model reproduce the promoted corpus?")
    print("%-14s %4s %-22s %-12s %-12s %s" % ("case", "n", "r", "model EMI", "oracle EMI", "all cells"))
    allok = True
    for cid in PROMOTED:
        c = cases[cid]
        i = c["inputs"]
        n = int(i["numberOfRepayments"])
        m = noloop_schedule(i["disbursementAmount"], n, i["annualNominalInterestRate"])
        obs = rows_of(c)
        ok = True
        for k, (mr, orow) in enumerate(zip(m["rows"], obs)):
            if (mr["principal"] != Decimal(orow["principal"])
                    or mr["interest"] != Decimal(orow["interest"])
                    or mr["closing"] != Decimal(orow["balance"])
                    or mr["emi"] != Decimal(orow["total"])):
                ok = False
        allok = allok and ok
        print("%-14s %4d %-22s %-12s %-12s %s"
              % (cid, n, m["r"], m["emi"], obs[0]["total"], "REPRODUCED" if ok else "*** DIVERGES ***"))
    print("control verdict:", "ALL REPRODUCED" if allok else "*** MODEL IS NOT FAITHFUL ***")
    return allok


def analyse(cases3c, cid):
    c = cases3c[cid]
    i = c["inputs"]
    n = int(i["numberOfRepayments"])
    m = noloop_schedule(i["disbursementAmount"], n, i["annualNominalInterestRate"])
    obs = rows_of(c)

    print()
    print("=" * 100)
    print("%s -- %s / %s x %s%%  currency %s" % (cid, i["disbursementAmount"], n,
                                                 i["annualNominalInterestRate"], i["currencyCode"]))
    print("=" * 100)
    print("  rate factor r (setScale 19, HALF_UP)   = %s" % m["r"])
    print("  rateFactorPlus1N (folded, mc 19)       = %s" % m["rateFactorPlus1N"])
    print("  fnResult (folded, mc 19)               = %s" % m["fnResult"])
    print("  raw EMI, Money 2dp HALF_UP             = %s" % m["emi"])

    # --- STAGE 2: the guard, on the NO-LOOP (pre-adjustment) model ---
    g = guard(n, m["lastEmi"], m["penultEmi"])
    print()
    print("  STAGE 2 -- EmiAdjustment.shouldBeAdjusted on the PRE-ADJUSTMENT (no-loop) model")
    print("    lastEMI (after last-period balancing) = %s" % g["lastEmi"])
    print("    penultimate EMI                       = %s" % g["penultimateEmi"])
    print("    emiDifference                         = %s" % g["emiDifference"])
    print("    |emiDifference| in minor units        = %d" % g["absDiffMinorUnits"])
    print("    lowerHalfOfRelatedPeriods floor(%d/2)  = %d" % (n, g["lowerHalfOfRelatedPeriods"]))
    print("    guard: |diff| * 100 = %s  >  %s ?     = %s"
          % (g["lhs_absDiffTimes100"], g["rhs_threshold"], "TRIPS" if g["trips"] else "does not trip"))

    og = guard(n, Decimal(obs[-1]["total"]), Decimal(obs[-2]["total"]))
    print("    (for contrast, on the OBSERVED post-loop schedule: |diff| = %d minor units vs "
          "threshold %d -> %s)"
          % (og["absDiffMinorUnits"], og["lowerHalfOfRelatedPeriods"],
             "still trips" if og["trips"] else "does not trip"))

    # --- STAGE 3: the margin ---
    print()
    print("  STAGE 3 -- observed vs no-loop counterfactual, minor units")
    print("    %3s %14s %14s %6s | %12s %12s %6s | %14s %14s %6s"
          % ("k", "obs principal", "cf principal", "d", "obs int", "cf int", "d",
             "obs balance", "cf balance", "d"))
    worst = (0, None, None)
    diffcount = 0
    for k, (mr, orow) in enumerate(zip(m["rows"], obs), start=1):
        dp = minor(orow["principal"]) - int(mr["principal"] * 100)
        di = minor(orow["interest"]) - int(mr["interest"] * 100)
        db = minor(orow["balance"]) - int(mr["closing"] * 100)
        if dp or di or db:
            diffcount += 1
        for label, d in (("principal", dp), ("interest", di), ("outstanding", db)):
            if abs(d) > worst[0]:
                worst = (abs(d), k, label)
        print("    %3d %14s %14s %6d | %12s %12s %6d | %14s %14s %6d"
              % (k, orow["principal"], mr["principal"], dp,
                 orow["interest"], mr["interest"], di,
                 orow["balance"], mr["closing"], db))
    obs_ti = minor(c["observed"]["totalInterestAmount"])
    cf_ti = int(m["totalInterest"] * 100)
    print("    total interest: observed %s (%d minor) vs counterfactual %s (%d minor), delta %d"
          % (c["observed"]["totalInterestAmount"], obs_ti, m["totalInterest"], cf_ti, obs_ti - cf_ti))
    print("    rows differing in at least one cell: %d of %d" % (diffcount, len(obs)))
    print("    WIDEST CELL MARGIN: %d minor units, at paying period %s, column %s"
          % (worst[0], worst[1], worst[2]))
    return {"guard": g, "observed_guard": og, "model": m, "worst": worst,
            "obs_total_interest_minor": obs_ti, "cf_total_interest_minor": cf_ti,
            "rows_differing": diffcount, "n_rows": len(obs)}


def main():
    cases3b = load(CAP3B)
    cases3c = load(CAP3C)
    ok = control(cases3b)
    if not ok:
        sys.exit("STOP: the no-loop model does not reproduce the promoted corpus, so nothing "
                 "derived from it below may be attributed to the smoothing loop.")
    for cid in ("P-EMI-6-1M014632", "P-EMI-36-127704"):
        analyse(cases3c, cid)


if __name__ == "__main__":
    main()
