#!/usr/bin/env python3
"""
T23 RE-REVIEW — independent re-derivation of the PROGRESSIVE schedule from the pinned source.

Written from scratch for this review. It does NOT reuse .softhouse/capture/out/t21-probe-rederive.py
(whose EmiAdjustment guard I found to be wrong; see the review).

Source of every step, all in the pinned checkout at 426a23544e8426a38ae43ae404670a0a7e85b9eb:

  dates          DefaultScheduledDateGenerator.java:128-131 (step) + :168-176 (re-anchor to the seed)
                 seed = disbursement date, LoanApplicationTerms.java:583-589
  nominal rate   ProgressiveEMICalculator.java:1318-1320   rate/100 under mc
  rate factor    :1956-1958 interestFraction = daysInMonth*repayEvery / daysInYear   (mc)
                 :1959-1962 rate*fraction*actualDays / calcDays   (mc), then .setScale(prec, mode)
  1+rf           RepaymentPeriod.java:216-218  EXACT (reduce with BigDecimal::add, no MathContext)
  prod           :1816-1820  reduce(ONE, multiply(mc))
  fn             :1822-1828 + :1991-1993  fn_k = 1 + fn_{k-1}*(1+rf_k) with mc on both ops
  EMI            :1838-1841  prod * balance / fn   (mc)  then Money -> currency scale (Money.java:52)
  per period     interest = balance * rateFactor  -> currency scale;  capped at EMI
                 principal = EMI - interest, clamped at 0   (RepaymentPeriod.java:272-286, :345-350)
                 balance roll-forward clamped at 0          (RepaymentPeriod.java:389-403)
  residual       :1202-1203 diff = disbursed + interest - sum(EMI), accumulated at currency scale
                 :1205/:1210 lastEmi += diff
  re-adjust      :1258-1308 gated on EmiAdjustment.shouldBeAdjusted (EmiAdjustment.java:31-36):
                 |emiDifference| * 100 > Money(floor(n/2))    <-- copy() REPLACES the amount
                 This model DOES NOT apply the loop; it only reports whether the guard is true.
"""
from decimal import Decimal, getcontext, ROUND_HALF_UP, Context
import datetime
import calendar

PREC = 19
CTX = Context(prec=PREC, rounding=ROUND_HALF_UP)


def q(x, digits=2):
    """Money: setScale(digits, HALF_UP) — Money.java:52."""
    return Decimal(x).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)


def mul(a, b):
    return CTX.multiply(Decimal(a), Decimal(b))


def div(a, b):
    return CTX.divide(Decimal(a), Decimal(b))


def add_mc(a, b):
    return CTX.add(Decimal(a), Decimal(b))


def setscale(x, scale):
    return Decimal(x).quantize(Decimal(1).scaleb(-scale), rounding=ROUND_HALF_UP)


def plus_months(d, n):
    """java.time.LocalDate.plusMonths — clamps the day to the target month's length."""
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def reanchor(d, seed):
    """DefaultScheduledDateGenerator.adjustDate, :168-176 — monthly only."""
    if seed.day > 28 and d.day >= 28:
        return datetime.date(d.year, d.month, min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def due_dates(start, seed, n, every=1):
    out = []
    cur = start
    for _ in range(n):
        cur = reanchor(plus_months(cur, every), seed)
        out.append(cur)
    return out


def derive(principal, n, annual_rate_pct, start, seed=None, digits=2,
           days_in_month=30, days_in_year=360, every=1):
    seed = seed or start
    dates = [start] + due_dates(start, seed, n, every)

    rate = div(Decimal(str(annual_rate_pct)), Decimal(100))          # :1318-1320

    rfs = []
    for i in range(n):
        actual = Decimal((dates[i + 1] - dates[i]).days)
        calc = actual
        frac = div(mul(Decimal(days_in_month), Decimal(every)), Decimal(days_in_year))   # :1956-1958
        rf = div(mul(mul(rate, frac), actual), calc)                                      # :1959-1962
        rfs.append(setscale(rf, PREC))                                                    # setScale(prec, mode)

    plus1 = [Decimal(1) + r for r in rfs]                             # EXACT, RepaymentPeriod.java:216-218

    prod = Decimal(1)                                                 # :1816-1820
    for p in plus1:
        prod = mul(prod, p)

    fn = Decimal(1)                                                   # :1822-1828 / :1991-1993
    for p in plus1[1:]:
        fn = add_mc(Decimal(1), mul(fn, p))

    emi_raw = div(mul(prod, Decimal(principal)), fn)                  # :1838-1841
    emi = q(emi_raw, digits)                                          # Money.java:52

    balance = q(Decimal(principal), digits)
    rows = []
    for i in range(n):
        interest = q(mul(balance, rfs[i]), digits)
        if interest > emi:
            interest = emi
        prin = emi - interest
        if prin < 0:
            prin = Decimal("0.00")
        new_balance = balance - prin
        if new_balance < 0:
            new_balance = Decimal("0.00")
        rows.append({"from": dates[i], "due": dates[i + 1], "emi": emi,
                     "interest": interest, "principal": prin, "balance": new_balance})
        balance = new_balance

    # residual true-up, :1202-1203 / :1205 / :1210 — every sum at currency scale
    total_int = sum((r["interest"] for r in rows), Decimal("0.00"))
    total_emi = sum((r["emi"] for r in rows), Decimal("0.00"))
    diff = q(Decimal(principal) + total_int - total_emi, digits)
    rows[-1]["emi"] = q(rows[-1]["emi"] + diff, digits)
    # principal falls out as EMI - interest (RepaymentPeriod.java:345-350)
    rows[-1]["principal"] = rows[-1]["emi"] - rows[-1]["interest"]
    if rows[-1]["principal"] < 0:
        rows[-1]["principal"] = Decimal("0.00")
    rows[-1]["balance"] = max(Decimal("0.00"),
                              (rows[-2]["balance"] if n > 1 else q(Decimal(principal), digits)) - rows[-1]["principal"])

    # EmiAdjustment guard — CORRECT reading of EmiAdjustment.java:31-36
    unpaid = [r for r in rows if r["emi"] != 0]
    guard = False
    emi_diff = Decimal("0.00")
    if len(unpaid) >= 2:
        emi_diff = unpaid[-1]["emi"] - unpaid[-2]["emi"]
        lower_half = Decimal(len(rows) // 2)
        guard = lower_half > 0 and emi_diff != 0 and abs(emi_diff) * 100 > lower_half

    return {
        "emi": emi, "rows": rows, "diff": diff,
        "total_interest": total_int if diff == 0 else sum((r["interest"] for r in rows), Decimal("0.00")),
        "total_repayment": q(Decimal(principal) + sum((r["interest"] for r in rows), Decimal("0.00")), digits),
        "term_days": (dates[-1] - dates[0]).days,
        "emi_diff": emi_diff, "readjust_guard": guard,
    }


if __name__ == "__main__":
    import json
    import sys

    cases = [
        # id, principal, n, rate, start, seed
        ("P-00",        100,       6,  "7.0",  datetime.date(2024, 1, 1),  None),
        ("P-01",        87654321, 18,  "18.5", datetime.date(2024, 1, 1),  None),
        ("P-02",        100,       6,  "7.0",  datetime.date(2024, 1, 31), datetime.date(2024, 1, 31)),
        ("P-02b",       100,       6,  "7.0",  datetime.date(2024, 1, 30), datetime.date(2024, 1, 30)),
        ("P-MNT-5M",    5000000,  18,  "18.5", datetime.date(2024, 1, 1),  None),
        ("P-MNT-1M2",   1200000,  12,  "21.6", datetime.date(2024, 1, 1),  None),
        ("P-MNT-50M",   50000000, 36,  "16.8", datetime.date(2024, 1, 1),  None),
        ("P-MNT-4M999", 4999999,  18,  "18.5", datetime.date(2024, 1, 1),  None),
    ]

    obs = json.load(open(".softhouse/capture/out/capture-prod-raw.json"))
    byid = {c["id"]: c for c in obs["captures"]}

    allok = True
    for cid, P, n, r, start, seed in cases:
        d = derive(P, n, r, start, seed)
        o = byid[cid]["observed"]
        ok = True
        msgs = []
        if str(d["term_days"]) != str(o["loanTermInDays"]):
            ok = False
            msgs.append(f"term {d['term_days']} vs {o['loanTermInDays']}")
        orows = [p for p in o["periods"] if p["type"] == "REPAYMENT"]
        for i, (mine, theirs) in enumerate(zip(d["rows"], orows), 1):
            if (str(mine["principal"]) != theirs["principal"] or str(mine["interest"]) != theirs["interest"]
                    or str(mine["balance"]) != theirs["balance"] or str(mine["due"]) != theirs["dueDate"]):
                ok = False
                msgs.append(f"p{i} mine {mine['due']} {mine['principal']}/{mine['interest']}/{mine['balance']}"
                            f" vs oracle {theirs['dueDate']} {theirs['principal']}/{theirs['interest']}/{theirs['balance']}")
        ti = sum((x["interest"] for x in d["rows"]), Decimal("0.00"))
        if str(ti) != o["totalInterestAmount"]:
            ok = False
            msgs.append(f"totalInterest {ti} vs {o['totalInterestAmount']}")
        allok &= ok
        print(f"{cid:<14} {'MATCH' if ok else 'MISMATCH'}   EMI={d['emi']} diff={d['diff']} "
              f"emiGap={d['emi_diff']} readjustGuard={d['readjust_guard']}")
        for m in msgs[:6]:
            print("      ", m)
    print()
    print("ALL 8 RE-DERIVED CAPTURES MATCH THE ORACLE TO THE MINOR UNIT" if allok else "*** MISMATCH ***")
