#!/usr/bin/env python3
"""
T21 AUDIT PROBE — INDEPENDENT re-derivation of the Fineract progressive-loan
amortization, written from the pinned source at /Users/buv/fineract
(commit 426a23544e8426a38ae43ae404670a0a7e85b9eb) and NOT from any capture output.

This is not a transcription of Capture3.java; it is a from-source reimplementation
of the arithmetic in exact decimal, used to check the observed captures to the last
minor unit.

Source anchors (file:line, pinned checkout):
  ProgressiveEMICalculator.java:1318-1320  calcNominalInterestRatePercentage = rate/100 (mc)
  ProgressiveEMICalculator.java:1950-1964  rateFactorByRepaymentPeriod
                                           ifpp = mult.multiply(every,mc).divide(daysInYear,mc)
                                           r = rate*ifpp*actual/calc  then .setScale(mc.getPrecision(), mode)
  ProgressiveEMICalculator.java:1922-1927  rateFactorByRepaymentEveryMonth -> above with mult=daysInMonth=30
  RepaymentPeriod.java:212-214             rateFactorPlus1 = ONE + sum(IP.rateFactor)  [EXACT add, no mc]
  ProgressiveEMICalculator.java:1816-1820  rateFactorPlus1N = prod(rateFactorPlus1, mc)
  ProgressiveEMICalculator.java:1822-1828  fnResult = fold over periods[1:]; fn = 1 + prev*cur (mc)
  ProgressiveEMICalculator.java:1838-1841  EMI = rateFactorPlus1N * balance (mc) / fnResult (mc)
  Money.java:41-53                         Money = value.setScale(currency.decimalPlaces, mode)
  InterestPeriod.java:145-158              dueInterest = balance * rateFactorTill (mc) / lenTillDue (mc) * len (mc)
  RepaymentPeriod.java:413-427             initial EMI balance = prevOutstanding + disbursements
  InterestPeriod.java:168-188              outstanding balance roll-forward
  ProgressiveEMICalculator.java:1160-1215  calculateLastUnpaidRepaymentPeriodEMI (final-period true-up)
  EmiAdjustment.java (record)              shouldBeAdjusted: |diff|*100 > originalEmi * floor(n/2)
"""
from decimal import Decimal, Context, ROUND_HALF_UP, localcontext
import json, sys, datetime

PREC = None  # set per run
EXACT = Context(prec=200, rounding=ROUND_HALF_UP)


def mc_ctx(prec):
    return Context(prec=prec, rounding=ROUND_HALF_UP)


def money(x, digits=2):
    """Money.java:52 — setScale(decimalPlaces, HALF_UP)."""
    q = Decimal(1).scaleb(-digits)
    return x.quantize(q, rounding=ROUND_HALF_UP)


def add_months(d, n):
    """java.time.LocalDate.plusMonths — clamps day to target month length."""
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    import calendar
    day = min(d.day, calendar.monthrange(y, m)[1])
    return datetime.date(y, m, day)


def days(a, b):
    return (b - a).days


def rate_factor(annual_rate, prec, actual_days, calc_days, days_in_month=30, days_in_year=360, every=1):
    """ProgressiveEMICalculator.java:1950-1964 via :1922-1927."""
    ctx = mc_ctx(prec)
    if calc_days == 0:
        return Decimal(0)
    rate = ctx.divide(Decimal(annual_rate), Decimal(100))          # :1319
    ifpp = ctx.divide(ctx.multiply(Decimal(days_in_month), Decimal(every)), Decimal(days_in_year))
    v = ctx.multiply(rate, ifpp)
    v = ctx.multiply(v, Decimal(actual_days))
    v = ctx.divide(v, Decimal(calc_days))
    # NOTE: setScale(mc.getPrecision(), ...) — precision used as SCALE. This is the
    # precision-vs-scale seam T5 identified. Reproduced here exactly as written.
    return v.quantize(Decimal(1).scaleb(-prec), rounding=ROUND_HALF_UP)


def derive(principal, n, annual_rate, prec, start, digits=2):
    """Single disbursement on the first period's fromDate, monthly, DAYS_30/DAYS_360,
    DECLINING_BALANCE, no payments, no charges, no down payment."""
    ctx = mc_ctx(prec)
    dates = [start] + [add_months(start, i) for i in range(1, n + 1)]

    # --- interest periods -------------------------------------------------
    # Period 1 is split by insertInterestPeriod (ProgressiveLoanInterestScheduleModel:279-296):
    #   IP0 = [start, start] length 0, holds the disbursement
    #   IP1 = [start, due1]
    # Periods 2..n hold a single IP spanning the whole repayment period.
    periods = []
    for i in range(n):
        f, d = dates[i], dates[i + 1]
        calc = days(f, d)
        if i == 0:
            ips = [
                {"from": f, "due": f, "disb": money(Decimal(principal), digits)},
                {"from": f, "due": d, "disb": money(Decimal(0), digits)},
            ]
        else:
            ips = [{"from": f, "due": d, "disb": money(Decimal(0), digits)}]
        for ip in ips:
            ip["rf"] = rate_factor(annual_rate, prec, days(ip["from"], ip["due"]), calc)
            ip["rf_till"] = rate_factor(annual_rate, prec, days(ip["from"], d), calc)
            ip["bal"] = money(Decimal(0), digits)
        periods.append({"from": f, "due": d, "ips": ips, "calc": calc})

    # --- rateFactorPlus1 (RepaymentPeriod.java:212-214, EXACT addition) ---
    for p in periods:
        s = Decimal(1)
        for ip in p["ips"]:
            s = EXACT.add(s, ip["rf"])
        p["rfp1"] = s

    # --- EMI (ProgressiveEMICalculator.java:1722-1742) --------------------
    rfN = Decimal(1)
    for p in periods:
        rfN = ctx.multiply(rfN, p["rfp1"])
    fn = Decimal(1)
    for p in periods[1:]:
        fn = ctx.add(Decimal(1), ctx.multiply(fn, p["rfp1"]))
    # initial balance for EMI recalculation = prevOutstanding(0) + disbursements in period 1
    ob = money(Decimal(principal), digits)
    emi_raw = ctx.divide(ctx.multiply(rfN, ob), fn)
    emi = money(emi_raw, digits)
    for p in periods:
        p["emi"] = emi

    def roll():
        """calculateOutstandingBalance + per-period due amounts."""
        prev_out = None
        for p in periods:
            for j, ip in enumerate(p["ips"]):
                if j == 0:
                    ip["bal"] = prev_out if prev_out is not None else money(Decimal(0), digits)
                else:
                    prevd = p["ips"][j - 1]
                    ip["bal"] = money(prevd["bal"] + prevd["disb"], digits)
            # calculated due interest (InterestPeriod.java:145-158, RepaymentPeriod.java:246-260)
            tot = Decimal(0)
            for ip in p["ips"]:
                L = days(ip["from"], ip["due"])
                Ltill = days(ip["from"], p["due"])
                if Ltill == 0 or L == 0:
                    v = Decimal(0)
                else:
                    v = ctx.multiply(ip["bal"], ip["rf_till"])
                    v = ctx.divide(v, Decimal(Ltill))
                    v = ctx.multiply(v, Decimal(L))
                tot = EXACT.add(tot, v)
            p["calc_int"] = money(tot, digits)
            # getDueInterest -> min(calculatedDueInterest, emi)   [no payments]
            p["int"] = min(p["calc_int"], p["emi"])
            p["prin"] = max(money(p["emi"] - p["int"], digits), Decimal("0.00"))
            last = p["ips"][-1]
            out = money(last["bal"] + last["disb"] - p["prin"], digits)
            p["out"] = max(out, Decimal("0.00"))
            prev_out = p["out"]

    roll()

    # --- final-period true-up (ProgressiveEMICalculator.java:1181-1206) ---
    total_int = sum((p["int"] for p in periods), Decimal("0.00"))
    total_emi = sum((p["emi"] for p in periods), Decimal("0.00"))
    diff = money(Decimal(principal) + total_int - total_emi, digits)
    periods[-1]["emi"] = money(periods[-1]["emi"] + diff, digits)
    roll()

    # --- checkAndAdjustEmiIfNeeded (EmiAdjustment.shouldBeAdjusted) -------
    lower_half = (len(periods)) // 2
    emi_diff = periods[-1]["emi"] - periods[-2]["emi"]
    should_adjust = lower_half > 0 and emi_diff != 0 and abs(emi_diff) * 100 > periods[-2]["emi"] * lower_half
    return {
        "emi": emi,
        "rf": periods[0]["ips"][1]["rf"],
        "periods": periods,
        "term_days": days(dates[0], dates[-1]),
        "total_interest": sum((p["int"] for p in periods), Decimal("0.00")),
        "total_repayment": money(Decimal(principal) + sum((p["int"] for p in periods), Decimal("0.00")), digits),
        "emi_adjust_triggered": should_adjust,
    }


CASES = {
    # id: (principal, n, annualRate, precision, startDate)
    "P-CAL":       (100, 6, "7.0", 12, datetime.date(2024, 1, 1)),
    "P-00":        (100, 6, "7.0", 19, datetime.date(2024, 1, 1)),
    "P-01":        (87654321, 18, "18.5", 19, datetime.date(2024, 1, 1)),
    "P-04f":       (100, 6, "7.0", 19, datetime.date(2024, 1, 1)),
    "P-04t":       (100, 6, "7.0", 19, datetime.date(2024, 1, 1)),
    "P-MNT-5M":    (5000000, 18, "18.5", 19, datetime.date(2024, 1, 1)),
    "P-MNT-4M999": (4999999, 18, "18.5", 19, datetime.date(2024, 1, 1)),
    "P-MNT-1M2":   (1200000, 12, "21.6", 19, datetime.date(2024, 1, 1)),
    "P-MNT-50M":   (50000000, 36, "16.8", 19, datetime.date(2024, 1, 1)),
}


def main():
    obs = {c["id"]: c for c in json.load(open(sys.argv[1]))["captures"]}
    rc = 0
    for cid, (P, n, rate, prec, start) in CASES.items():
        if cid not in obs:
            print(f"{cid}: NOT IN CAPTURE FILE"); continue
        d = derive(P, n, rate, prec, start)
        o = obs[cid]["observed"]
        print(f"\n===== {cid}  principal={P} n={n} rate={rate}% precision={prec} =====")
        print(f"  derived rateFactor(period)= {d['rf']}")
        print(f"  derived EMI              = {d['emi']}")
        print(f"  derived emiAdjustTrigger = {d['emi_adjust_triggered']}")
        hdr = f"  {'#':>3} {'dueDate':<11} {'principal':>16} {'interest':>14} {'total':>16} {'balance':>16}   match"
        print(hdr)
        ok = True
        obs_rep = [p for p in o["periods"] if p["type"] == "REPAYMENT"]
        for i, p in enumerate(d["periods"]):
            op = obs_rep[i]
            tot = money(p["prin"] + p["int"])
            m = (str(p["prin"]) == op["principal"] and str(p["int"]) == op["interest"]
                 and str(tot) == op["total"] and str(p["out"]) == op["balance"]
                 and str(p["due"]) == op["dueDate"])
            ok = ok and m
            print(f"  {i+1:>3} {p['due']!s:<11} {p['prin']:>16} {p['int']:>14} {tot:>16} {p['out']:>16}   {'OK' if m else 'MISMATCH'}")
            if not m:
                print(f"      observed: {op}")
        tm = (str(d["term_days"]) == str(o["loanTermInDays"])
              and str(d["total_interest"]) == o["totalInterestAmount"]
              and str(d["total_repayment"]) == o["totalRepaymentAmount"])
        print(f"  totals derived: term={d['term_days']} interest={d['total_interest']} repayment={d['total_repayment']}")
        print(f"  totals observed: term={o['loanTermInDays']} interest={o['totalInterestAmount']} repayment={o['totalRepaymentAmount']}")
        print(f"  ==> {cid}: {'FULL MATCH' if (ok and tm) else 'MISMATCH'}")
        if not (ok and tm):
            rc = 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
