#!/usr/bin/env python3
# T44 audit leg — spot-check of every published number in T40 handoff sections 4-9,
# read straight off the raw JSON leaves. Exact Decimal, no float.
import json, os
from decimal import Decimal

B = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse/capture/charges/out/fc/"
OUT = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse/capture/audit-t44/charges/out/SPOTCHECK.txt"

def L(p):
    with open(B + p) as f:
        return json.load(f, parse_float=Decimal)

R = []
def say(*a):
    s = " ".join(str(x) for x in a)
    R.append(s); print(s)

d = L("FC-01-flat-disbursement-raw.json")
say("=== FC-01 (handoff §5 worked example, all 13 rows) ===")
for p in d["periods"]:
    say(p.get("period"), p.get("fromDate"), p.get("dueDate"), p.get("daysInPeriod"),
        p.get("principalDue"), p.get("interestDue"), p.get("feeChargesDue"), p.get("penaltyChargesDue"),
        p.get("principalLoanBalanceOutstanding"), p.get("totalDueForPeriod"),
        p.get("totalInstallmentAmountForPeriod"))
say("totals:", d["totalPrincipalExpected"], d["totalInterestCharged"], d["totalFeeChargesCharged"],
    d["totalPenaltyChargesCharged"], d["totalRepaymentExpected"], d.get("loanTermInDays"))
say("")
say("=== FC-02 (handoff §6 Q1) ===")
d = L("FC-02-flat-instalment-raw.json")
for p in d["periods"]:
    if p.get("period") in (1, 11, 12):
        say(p["period"], p["totalInstallmentAmountForPeriod"], p["feeChargesDue"], p["totalDueForPeriod"])
say("")
say("=== FC-15 (handoff §6 Q6) ===")
d = L("FC-15-combined-fee-and-penalty-raw.json")
for p in d["periods"]:
    say(p.get("period"), p.get("feeChargesDue"), p.get("penaltyChargesDue"),
        p.get("totalDueForPeriod"), p.get("totalInstallmentAmountForPeriod"))
say("totals:", d["totalFeeChargesCharged"], d["totalPenaltyChargesCharged"], d["totalRepaymentExpected"])
say("")
say("=== FC-09 per-period fees (handoff §6 Q5) ===")
say([str(p["feeChargesDue"]) for p in L("FC-09-pctamount-instalment-raw.json")["periods"] if p.get("period")])
say("=== FC-04 per-period fees (handoff §6 Q5) ===")
say([str(p["feeChargesDue"]) for p in L("FC-04-pctinterest-instalment-raw.json")["periods"] if p.get("period")])
say("=== FC-05 distinct per-period fees (handoff §6 Q5: '1,383.66 on every period') ===")
say(sorted({str(p["feeChargesDue"]) for p in L("FC-05-pctamountinterest-instalment-raw.json")["periods"] if p.get("period")}))
say("=== FC-03/FC-10/FC-19/FC-21 totals (handoff §6 Q5, §7 D-1) ===")
for n in ("FC-03-pctamount-disbursement", "FC-10-pctamount-inside-p6",
          "FC-19-pctinterest-sdd-inside-p6", "FC-21-pctamtint-sdd-inside-p6",
          "FC-04-pctinterest-instalment", "FC-05-pctamountinterest-instalment",
          "FC-08-penalty-instalment", "FC-07-fee-on-p3-duedate", "FC-02-flat-instalment"):
    x = L(n + "-raw.json")
    say(n, "fee=", x["totalFeeChargesCharged"], "pen=", x["totalPenaltyChargesCharged"],
        "TRE=", x["totalRepaymentExpected"])
say("=== FC-11 disbursement-row fee (handoff §6 Q3: 'periods[0] fee stays 0.00') ===")
x = L("FC-11-fee-on-disbursement-date-raw.json")
say("periods[0] feeChargesDue =", x["periods"][0]["feeChargesDue"], "; period 1 fee =",
    [p["feeChargesDue"] for p in x["periods"] if p.get("period") == 1][0])
say("=== FC-03 disbursement-row fee (handoff §6 Q3: 14,814.00 in periods[0]) ===")
say(L("FC-03-pctamount-disbursement-raw.json")["periods"][0]["feeChargesDue"])
say("=== FC-01 principalLoanBalanceOutstanding on the disbursement row (handoff Q2) ===")
say(L("FC-01-flat-disbursement-raw.json")["periods"][0].get("principalLoanBalanceOutstanding"))

with open(OUT, "w") as f:
    f.write("\n".join(R) + "\n")
