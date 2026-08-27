#!/usr/bin/env python3
"""
================================ RETRACTED ================================
RETRACTED by the T21 independent audit (T21-v2), 2026-08-18. DO NOT REUSE.
See `.softhouse/reviews/T21-capture-pass3-audit.md` §9.

Companion to the retracted `t21-probe-rederive.py`; it shares the same
defective amortization model (no EMI smoothing pass; `Money.copy(double)`
misread as a multiply). Its date-sequence and P-03 structural readings were
independently CONFIRMED against source by the audit (§4), but its schedule
arithmetic must not be relied on. Superseded by
`.softhouse/reviews/t21v2/t21v2-rederive.py`. Kept only as a record.
==========================================================================

T21 AUDIT PROBE (part 2) — re-derivation of P-02, P-02b, P-03, which my first probe
did not cover because their repayment-date sequences are not plain 1st-of-month.

Date sequences are themselves re-derived from source, not copied from the capture:
  DefaultScheduledDateGenerator.java:58-73   loop: next = generateNextRepaymentDate(last,...)
  DefaultScheduledDateGenerator.java:128-131 next = plusMonths(every) then adjustDate(next, seedDate, MONTHS)
  DefaultScheduledDateGenerator.java:168-176 adjustDate: if MONTHLY and seedDay>28 and dateDay>=28:
                                             day := min(lengthOfMonth(date), seedDay)
P-03 structure: the emitted REPAYMENT #1 is the iteration-1 snapshot of a model period
that has not yet received the disbursement (ProgressiveLoanScheduleGenerator.java:118-136:
processDisbursements runs at the TOP of each period iteration, so a disbursement dated on
period 1's dueDate is applied during iteration 2). Its money row is therefore all zeros and
its balance is 0.00. Periods 2..6 are then a 5-installment EMI on the full principal.
"""
import sys, os, datetime, json
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rd", os.path.join(HERE, "t21-probe-rederive.py"))
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)


def adjust_date(d, seed):
    """DefaultScheduledDateGenerator.java:168-176 (MONTHLY only)."""
    import calendar
    if seed.day > 28 and d.day >= 28:
        return datetime.date(d.year, d.month, min(calendar.monthrange(d.year, d.month)[1], seed.day))
    return d


def gen_dates(seed, n):
    out = [seed]
    last = seed
    for _ in range(n):
        nxt = adjust_date(rd.add_months(last, 1), seed)
        out.append(nxt)
        last = nxt
    return out


def derive_with_dates(principal, dates, annual_rate, prec, digits=2):
    """Same algorithm as probe 1 but with an explicit date sequence."""
    orig = rd.add_months
    seq = list(dates)
    rd.add_months = lambda s, i: seq[i]
    try:
        return rd.derive(principal, len(seq) - 1, annual_rate, prec, seq[0], digits)
    finally:
        rd.add_months = orig


def show(cid, obs, d, skip_first_observed=0, check_totals=True):
    o = obs[cid]["observed"]
    rep = [p for p in o["periods"] if p["type"] == "REPAYMENT"][skip_first_observed:]
    print(f"\n===== {cid} =====")
    ok = True
    for i, p in enumerate(d["periods"]):
        op = rep[i]
        tot = rd.money(p["prin"] + p["int"])
        m = (str(p["prin"]) == op["principal"] and str(p["int"]) == op["interest"]
             and str(tot) == op["total"] and str(p["out"]) == op["balance"] and str(p["due"]) == op["dueDate"])
        ok = ok and m
        tail = "OK" if m else "MISMATCH observed=" + str(op)
        print(f"  {i+1+skip_first_observed:>3} {p['due']!s:<11} prin={p['prin']:>10} int={p['int']:>8} tot={tot:>10} bal={p['out']:>10}  {tail}")
    print(f"  derived  interest={d['total_interest']} repayment={d['total_repayment']} term={d['term_days']}")
    print(f"  observed interest={o['totalInterestAmount']} repayment={o['totalRepaymentAmount']} term={o['loanTermInDays']}")
    if check_totals:
        ok = ok and str(d["total_interest"]) == o["totalInterestAmount"] \
                and str(d["total_repayment"]) == o["totalRepaymentAmount"] \
                and str(d["term_days"]) == str(o["loanTermInDays"])
    else:
        ok = ok and str(d["total_interest"]) == o["totalInterestAmount"] \
                and str(d["total_repayment"]) == o["totalRepaymentAmount"]
    print(f"  ==> {cid}: {'FULL MATCH' if ok else 'MISMATCH'}")
    return ok


def main():
    obs = {c["id"]: c for c in json.load(open(sys.argv[1]))["captures"]}
    rc = 0

    for cid, seed in (("P-02", datetime.date(2024, 1, 31)), ("P-02b", datetime.date(2024, 1, 30))):
        dates = gen_dates(seed, 6)
        print(f"\n[{cid}] re-derived date sequence from source: {[str(x) for x in dates]}")
        d = derive_with_dates(100, dates, "7.0", 19)
        if not show(cid, obs, d):
            rc = 1

    # P-03: schedule start 2024-01-01, disbursement 2024-02-01.
    dates = [datetime.date(2024, 2, 1)] + [rd.add_months(datetime.date(2024, 2, 1), i) for i in range(1, 6)]
    print(f"\n[P-03] EMI runs over the 5 periods after the disbursement date: {[str(x) for x in dates]}")
    d = derive_with_dates(100, dates, "7.0", 19)
    o = obs["P-03"]["observed"]
    rep = [p for p in o["periods"] if p["type"] == "REPAYMENT"]
    print(f"  emitted REPAYMENT #1 (pre-disbursement snapshot): {rep[0]}")
    print(f"  NOTE: plan loanTermInDays is measured from the SCHEDULE start (2024-01-01), not the")
    print(f"        disbursement date, so the 5-period derivation's own term (152) is not comparable.")
    if not show("P-03", obs, d, skip_first_observed=1, check_totals=False):
        rc = 1

    print("\nALL RE-DERIVED MATCH" if rc == 0 else "\nMISMATCHES PRESENT")
    sys.exit(rc)


if __name__ == "__main__":
    main()
