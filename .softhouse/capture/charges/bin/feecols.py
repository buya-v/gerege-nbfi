#!/usr/bin/env python3
"""T40 — the fee/penalty columns of every capture, side by side with the control.

Answers, from OBSERVATION only:
  * which period a charge lands in (index 0 = the disbursement pseudo-period),
  * whether the charge alters the EMI (`totalInstallmentAmountForPeriod`),
  * whether it alters the principal split or the outstanding principal balance.

Exact Decimal only; no float is constructed at any point.
"""
import json, os, sys
from decimal import Decimal

W = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513"
CH = W + "/.softhouse/capture/charges"


def load(p):
    with open(p) as f:
        return json.load(f, parse_float=Decimal, parse_int=Decimal)


def d2(v):
    if v is None:
        return "-"
    m = int(v * 100)
    assert Decimal(m) == v * 100
    s = "-" if m < 0 else ""
    m = abs(m)
    return f"{s}{m//100}.{m%100:02d}"


ctrl = load(CH + "/out/control/B-01-baseline-raw.json")
FC = CH + "/out/fc"

files = sorted(f for f in os.listdir(FC) if f.endswith("-raw.json"))
print("### Fee / penalty columns per period, per capture (raw observed)")
print()
print("`idx` 0 is the disbursement pseudo-period (no `period` number, dueDate = 2026-01-01).")
print()
for f in files:
    cid = f[: -len("-raw.json")]
    doc = load(FC + "/" + f)
    print(f"**{cid}**")
    print()
    print("| idx | period | fromDate | dueDate | fee | penalty | EMI (totalInstallmentAmountForPeriod) | totalDueForPeriod | principalDue | interestDue | principalLoanBalanceOutstanding |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, (c, p) in enumerate(zip(ctrl["periods"], doc["periods"])):
        def dt(v):
            return "-" if v is None else "%04d-%02d-%02d" % tuple(int(x) for x in v)
        flag = ""
        for k in ("principalDue", "interestDue", "principalLoanBalanceOutstanding",
                  "totalInstallmentAmountForPeriod"):
            if c.get(k) != p.get(k):
                flag += f" **{k} MOVED**"
        print("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |%s" % (
            i, p.get("period", "-"), dt(p.get("fromDate")), dt(p.get("dueDate")),
            d2(p.get("feeChargesDue")), d2(p.get("penaltyChargesDue")),
            d2(p.get("totalInstallmentAmountForPeriod")), d2(p.get("totalDueForPeriod")),
            d2(p.get("principalDue")), d2(p.get("interestDue")),
            d2(p.get("principalLoanBalanceOutstanding")), flag))
    print()
    print("| plan total | control | %s |" % cid)
    print("|---|---|---|")
    for k in ("totalInterestCharged", "totalFeeChargesCharged",
              "totalPenaltyChargesCharged", "totalRepaymentExpected",
              "totalPrincipalExpected"):
        print(f"| {k} | {d2(ctrl.get(k))} | {d2(doc.get(k))} |")
    # sum check: does the fee column sum to the plan total?
    fs = sum((p.get("feeChargesDue") or Decimal(0)) for p in doc["periods"])
    ps = sum((p.get("penaltyChargesDue") or Decimal(0)) for p in doc["periods"])
    print(f"| SUM of feeChargesDue over all periods | | {d2(fs)} |")
    print(f"| SUM of penaltyChargesDue over all periods | | {d2(ps)} |")
    print()
