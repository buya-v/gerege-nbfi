#!/usr/bin/env python3
"""
T21-v2 AUDIT — INDEPENDENT re-derivation of Fineract's progressive-loan amortization.

Written by the T21-v2 auditor by reading the PINNED source at /Users/buv/fineract
(commit 426a23544e8426a38ae43ae404670a0a7e85b9eb) only. It is not a transcription of
Capture3.java, and it does not import, read or reuse the earlier T21 worker's
`t21-probe-rederive.py`. Every arithmetic step below carries the file:line I read it from.

SOURCE ANCHORS (all in the pinned checkout):

  Rate factor
    ProgressiveEMICalculator.java:1318-1320  calcNominalInterestRatePercentage = rate / 100  (mc)
    ProgressiveEMICalculator.java:1486-1540  calculateRateFactorPerPeriod    -> DAYS_30 branch :1536-1537
    ProgressiveEMICalculator.java:1355-1417  calculateRateFactorPerPeriodForInterest -> :1403-1413
    ProgressiveEMICalculator.java:1598-1611  dispatch on repayment frequency; MONTHS -> :1607
    ProgressiveEMICalculator.java:1922-1927  rateFactorByRepaymentEveryMonth(daysInMonth=30)
    ProgressiveEMICalculator.java:1950-1963  rateFactorByRepaymentPeriod:
                                             ifpp = mult.multiply(every, mc).divide(daysInYear, mc)
                                             r    = rate.multiply(ifpp, mc)
                                                        .multiply(actualDays, mc)
                                                        .divide(calcDays, mc)
                                                        .setScale(mc.getPrecision(), mc.getRoundingMode())
                                             ^ NOTE: precision used as SCALE. This is T5's precision-vs-scale seam.
    ProgressiveEMICalculator.java:1419-1459  calculatePeriodRatio -> 1 for a regular anchored monthly schedule
    ProgressiveEMICalculator.java:1461-1481  calculateSeedDate

  rateFactorPlus1
    RepaymentPeriod.java:216-218             ONE + sum(InterestPeriod.rateFactor), EXACT add (no MathContext)

  EMI
    ProgressiveEMICalculator.java:1816-1820  rateFactorPlus1N = fold(ONE, acc.multiply(v, mc))
    ProgressiveEMICalculator.java:1822-1828  fnResult = fold over periods[1:] of fnValue
    ProgressiveEMICalculator.java:1991-1993  fnValue = ONE.add(prev.multiply(cur, mc), mc)
    ProgressiveEMICalculator.java:1838-1841  emiValue = rfN.multiply(balance, mc).divide(fnResult, mc)
    ProgressiveEMICalculator.java:1722-1742  Money.of(currency, emiValue, mc) -> scale 2; assigned to every period
    RepaymentPeriod.java:413-427             initialBalanceForEmiRecalculation = prevOutstanding + disbursed

  Per-period amounts
    InterestPeriod.java:145-158              calculatedDueInterest =
                                               balance.multiply(rateFactorTillDue, mc)
                                                      .divide(lengthTillDue, mc)
                                                      .multiply(length, mc)
    RepaymentPeriod.java:252-265             sum over interest periods with EXACT BigDecimal::add,
                                             then Money.of(..., mc) -> scale 2
    RepaymentPeriod.java:272-286             dueInterest = min(calculatedDueInterest, emi)   [no payments]
    RepaymentPeriod.java:345-350             duePrincipal = negativeToZero(emi - dueInterest)
    RepaymentPeriod.java:389-403             outstandingLoanBalance = lastIP.balance + lastIP.disbursement
                                                                      - duePrincipal   (negativeToZero)
    InterestPeriod.java:168-188              interest-period balance roll-forward

  Final-installment RESIDUAL ABSORPTION  <-- the rule the brief asks me to state
    ProgressiveEMICalculator.java:1160-1219  calculateLastUnpaidRepaymentPeriodEMI:
      diff = totalDisbursed + totalCapitalizedIncome + totalCreditedPrincipal
             + sum(dueInterest) - sum(EMI)                       [:1190-1203]
      lastUnpaidPeriod.emi = lastUnpaidPeriod.emi + diff          [:1205, :1210]
    i.e. the WHOLE residual is absorbed into the LAST not-fully-paid period's EMI in one addition.
    It is NOT a per-period "last principal = remaining balance" rule.

  EMI smoothing pass (fires only when the last EMI is far from the others)
    ProgressiveEMICalculator.java:1258-1309  checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods
    ProgressiveEMICalculator.java:1778-1789  getEmiAdjustment: diff = last.emi - penultimate.emi
    EmiAdjustment.java:31-44                 shouldBeAdjusted: floor(n/2) > 0 and diff != 0 and
                                             |diff| * 100 > Money(floor(n/2))
                                             adjustment = diff / max(1, n - uncountablePeriods)

  Money
    Money.java:40-53                         Money(currency, amount, mc): stripTrailingZeros, then
                                             setScale(decimalPlaces, getMc().getRoundingMode());
                                             the inMultiplesOf branch is gated on decimalPlaces == 0
    Money.java:494-496                       getMc() = mc if non-null else MoneyHelper.getMathContext()
    MoneyHelper.java:35, 91-93               PRECISION = 19; getMathContext() = (19, tenantRoundingMode)

  Schedule dates
    DefaultScheduledDateGenerator.java       plusMonths + month-end re-anchor (see adjust_date below)

  Emission order / loanTermInDays
    ProgressiveLoanScheduleGenerator.java:116-145  processDisbursements runs at the TOP of each period
                                             iteration, so a disbursement dated on period 1's DUE date is
                                             applied in iteration 2 and its row lands AFTER period 1's row.
    ProgressiveLoanInterestScheduleModel.java:200-207  loanTermInDays = firstPeriod.fromDate ->
                                             lastPeriod.dueDate  (SCHEDULE start, not disbursement date)
"""
from decimal import Decimal, Context, ROUND_HALF_UP
import calendar
import datetime
import json
import sys

EXACT = Context(prec=400, rounding=ROUND_HALF_UP)


def ctx(prec):
    return Context(prec=prec, rounding=ROUND_HALF_UP)


def money(x, dp):
    """Money.java:45,52 — stripTrailingZeros then setScale(dp, HALF_UP)."""
    return x.quantize(Decimal(1).scaleb(-dp), rounding=ROUND_HALF_UP)


def plus_months(d, n):
    """java.time.LocalDate.plusMonths: clamp day to the target month length."""
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    return datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def adjust_date(d, seed):
    """DefaultScheduledDateGenerator month-end re-anchor for MONTHLY."""
    if seed.day > 28 and d.day >= 28:
        return datetime.date(d.year, d.month, min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def schedule_dates(seed, n):
    out = [seed]
    last = seed
    for _ in range(n):
        last = adjust_date(plus_months(last, 1), seed)
        out.append(last)
    return out


def rate_factor(annual_rate, prec, actual_days, calc_days, days_in_month=30, days_in_year=360, every=1):
    """ProgressiveEMICalculator.java:1950-1963, reached via :1536-1537 -> :1607 -> :1922-1927."""
    if calc_days == 0:
        return Decimal(0)
    c = ctx(prec)
    rate = c.divide(Decimal(annual_rate), Decimal(100))                      # :1319
    ifpp = c.divide(c.multiply(Decimal(days_in_month), Decimal(every)), Decimal(days_in_year))  # :1956-1958
    v = c.divide(c.multiply(c.multiply(rate, ifpp), Decimal(actual_days)), Decimal(calc_days))  # :1959-1962
    return v.quantize(Decimal(1).scaleb(-prec), rounding=ROUND_HALF_UP)      # setScale(prec)


def derive(principal, n, annual_rate, prec, start, dp=2, dates=None):
    """Single disbursement on the schedule start date, monthly, DAYS_30 / DAYS_360,
    DECLINING_BALANCE, no down payment, no charges, no payments."""
    c = ctx(prec)
    ds = dates if dates is not None else schedule_dates(start, n)

    # --- interest periods -------------------------------------------------
    # ProgressiveLoanInterestScheduleModel.java:280-296 — the disbursement splits period 1's
    # single interest period into a zero-length IP holding the money plus a full-length IP.
    periods = []
    for i in range(len(ds) - 1):
        f, d = ds[i], ds[i + 1]
        calc = (d - f).days
        if i == 0:
            ips = [{"from": f, "due": f, "disb": money(Decimal(principal), dp)},
                   {"from": f, "due": d, "disb": Decimal(0).quantize(Decimal(1).scaleb(-dp))}]
        else:
            ips = [{"from": f, "due": d, "disb": Decimal(0).quantize(Decimal(1).scaleb(-dp))}]
        for ip in ips:
            ip["rf"] = rate_factor(annual_rate, prec, (ip["due"] - ip["from"]).days, calc)
            ip["rf_till"] = rate_factor(annual_rate, prec, (d - ip["from"]).days, calc)
            ip["bal"] = money(Decimal(0), dp)
        periods.append({"from": f, "due": d, "calc": calc, "ips": ips})

    # --- rateFactorPlus1 (RepaymentPeriod.java:216-218, EXACT addition) ----
    for p in periods:
        s = Decimal(1)
        for ip in p["ips"]:
            s = EXACT.add(s, ip["rf"])
        p["rfp1"] = s

    # --- EMI (ProgressiveEMICalculator.java:1722-1742) ---------------------
    rf_n = Decimal(1)
    for p in periods:
        rf_n = c.multiply(rf_n, p["rfp1"])                                    # :1818-1819
    fn = Decimal(1)
    for p in periods[1:]:
        fn = c.add(Decimal(1), c.multiply(fn, p["rfp1"]))                     # :1991-1993
    # RepaymentPeriod.java:413-427 — first period has no previous, so balance = its disbursements
    init_balance = money(Decimal(principal), dp)
    emi = money(c.divide(c.multiply(rf_n, init_balance), fn), dp)             # :1838-1841 + Money scale
    for p in periods:
        p["emi"] = emi

    def roll():
        """Interest-period balance roll-forward + per-period due amounts."""
        prev_out = None
        for p in periods:
            for j, ip in enumerate(p["ips"]):
                if j == 0:
                    ip["bal"] = prev_out if prev_out is not None else money(Decimal(0), dp)   # IP:168-179
                else:
                    prev = p["ips"][j - 1]
                    ip["bal"] = money(prev["bal"] + prev["disb"], dp)                          # IP:180-187
            acc = Decimal(0)
            for ip in p["ips"]:
                L = (ip["due"] - ip["from"]).days                                              # IP:160-162
                Ltill = (p["due"] - ip["from"]).days                                           # IP:164-166
                if Ltill == 0 or L == 0:
                    v = Decimal(0)                                                             # IP:146-148
                else:
                    v = c.multiply(c.divide(c.multiply(ip["bal"], ip["rf_till"]), Decimal(Ltill)), Decimal(L))
                acc = EXACT.add(acc, v)                                                        # RP:255-257
            p["calc_int"] = money(acc, dp)
            p["int"] = min(p["calc_int"], p["emi"])                                            # RP:272-286
            p["prin"] = max(money(p["emi"] - p["int"], dp), Decimal(0))                        # RP:345-350
            last = p["ips"][-1]
            out = money(last["bal"] + last["disb"] - p["prin"], dp)                            # RP:389-403
            p["out"] = max(out, money(Decimal(0), dp))
            prev_out = p["out"]

    roll()

    # --- residual absorption (ProgressiveEMICalculator.java:1160-1219) -----
    def absorb():
        total_int = sum((p["int"] for p in periods), Decimal(0))
        total_emi = sum((p["emi"] for p in periods), Decimal(0))
        total_disb = sum((ip["disb"] for p in periods for ip in p["ips"]), Decimal(0))
        diff = money(total_disb + total_int - total_emi, dp)                                   # :1202-1203
        periods[-1]["emi"] = money(periods[-1]["emi"] + diff, dp)                              # :1205,:1210
        roll()

    absorb()

    # --- EMI smoothing pass (ProgressiveEMICalculator.java:1258-1309) ------
    smoothing_iterations = 0
    for _ in range(3):
        last, penult = periods[-1], periods[-2]
        diff = last["emi"] - penult["emi"]
        lower_half = len(periods) // 2
        if lower_half <= 0 or diff == 0:
            break
        if not (abs(diff) * 100 > money(Decimal(lower_half), dp)):                             # EmiAdjustment:31-36
            break
        # uncountablePeriods: getUncountablePeriods counts fully-paid-ish periods; zero here.
        adjusted = money(penult["emi"] + money(diff / max(1, len(periods)), dp), dp)           # EmiAdjustment:38-43
        if adjusted == penult["emi"]:
            break
        prev_diff = abs(diff)
        saved = [p["emi"] for p in periods]
        for p in periods:
            p["emi"] = adjusted
        roll()
        absorb()
        if not (abs(periods[-1]["emi"] - periods[-2]["emi"]) < prev_diff):
            for p, e in zip(periods, saved):
                p["emi"] = e
            roll()
            absorb()
            break
        smoothing_iterations += 1

    total_int = sum((p["int"] for p in periods), Decimal(0))
    total_prin = sum((p["prin"] for p in periods), Decimal(0))
    return {
        "periods": periods,
        "emi": emi,
        "total_interest": money(total_int, dp),
        "total_principal": money(total_prin, dp),
        "total_repayment": money(total_prin + total_int, dp),
        "term_days": (ds[-1] - ds[0]).days,
        "smoothing_iterations": smoothing_iterations,
    }


# ---------------------------------------------------------------------------


def check(capture, dates=None, skip_observed=0, principal=None, start=None, compare_term=True):
    inp = capture["inputs"]
    obs = capture["observed"]
    dp = int(inp["currencyDecimalPlaces"])
    P = principal if principal is not None else inp["disbursementAmount"]
    n = int(inp["numberOfRepayments"])
    s = start or datetime.date.fromisoformat(inp["scheduleGenerationStartDate"])
    d = derive(P, n, inp["annualNominalInterestRate"], int(inp["mathContextPrecision"]), s, dp, dates)
    rep = [p for p in obs["periods"] if p["type"] == "REPAYMENT"][skip_observed:]
    ok = True
    bad = []
    for i, p in enumerate(d["periods"]):
        o = rep[i]
        tot = money(p["prin"] + p["int"], dp)
        cells = {
            "dueDate": (str(p["due"]), o["dueDate"]),
            "principal": (str(p["prin"]), o["principal"]),
            "interest": (str(p["int"]), o["interest"]),
            "total": (str(tot), o["total"]),
            "balance": (str(p["out"]), o["balance"]),
        }
        for k, (mine, theirs) in cells.items():
            if mine != theirs:
                ok = False
                bad.append(f"    period {i + 1 + skip_observed} {k}: derived={mine} observed={theirs}")
    tot_checks = [
        ("totalInterestAmount", str(d["total_interest"]), obs["totalInterestAmount"]),
        ("totalRepaymentAmount", str(d["total_repayment"]), obs["totalRepaymentAmount"]),
    ]
    if compare_term:
        tot_checks.append(("loanTermInDays", str(d["term_days"]), str(obs["loanTermInDays"])))
    for k, mine, theirs in tot_checks:
        if mine != theirs:
            ok = False
            bad.append(f"    {k}: derived={mine} observed={theirs}")
    print(f"  {capture['id']:<13} {'FULL MATCH' if ok else 'MISMATCH'}"
          f"   (EMI={d['emi']}, smoothing passes={d['smoothing_iterations']})")
    for b in bad:
        print(b)
    return ok


def main(path):
    caps = {c["id"]: c for c in json.load(open(path))["captures"]}
    rc = 0
    print("=== plain 1st-of-month schedules, disbursement on the schedule start date ===")
    for cid in ("P-CAL", "P-00", "P-01", "P-04f", "P-04t", "P-MNT-5M", "P-MNT-1M2", "P-MNT-50M", "P-MNT-4M999"):
        if not check(caps[cid]):
            rc = 1

    print("\n=== month-end re-anchored schedules ===")
    for cid, seed in (("P-02", datetime.date(2024, 1, 31)), ("P-02b", datetime.date(2024, 1, 30))):
        if not check(caps[cid], dates=schedule_dates(seed, 6), start=seed):
            rc = 1

    print("\n=== P-03: disbursement on period 1's due date ===")
    print("    period 1 is the pre-disbursement snapshot (all zeros); the EMI runs over periods 2..6,")
    print("    a 5-installment schedule seeded at the disbursement date 2024-02-01.")
    ds = schedule_dates(datetime.date(2024, 2, 1), 5)
    c3 = dict(caps["P-03"])
    c3["inputs"] = dict(c3["inputs"], numberOfRepayments=5)
    if not check(c3, dates=ds, skip_observed=1, start=datetime.date(2024, 2, 1), compare_term=False):
        rc = 1
    obs = caps["P-03"]["observed"]
    print(f"    plan loanTermInDays observed = {obs['loanTermInDays']}; "
          f"schedule start 2024-01-01 -> last due 2024-07-01 = "
          f"{(datetime.date(2024, 7, 1) - datetime.date(2024, 1, 1)).days} days "
          f"[ProgressiveLoanInterestScheduleModel.java:200-207]")

    print("\nALL RE-DERIVATIONS MATCH" if rc == 0 else "\nMISMATCHES PRESENT")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
