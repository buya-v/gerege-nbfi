#!/usr/bin/env python3
"""T40 — charge-specific property invariants over every capture.

These are NOT expected values. Each one is a relation between cells of the SAME observed
document, so a FAIL is a statement about the reference oracle, not about my arithmetic.
Exact Decimal in integer minor units throughout; no float is constructed at any point.

  C1  sum(feeChargesDue over all periods)      == totalFeeChargesCharged
  C2  sum(penaltyChargesDue over all periods)  == totalPenaltyChargesCharged
  C3  per period: totalDueForPeriod == principalDue + interestDue + fee + penalty
  C4  per period: feeChargesOutstanding == feeChargesDue  (nothing paid on a projection)
      and          penaltyChargesOutstanding == penaltyChargesDue
  C5  totalRepaymentExpected == sum(totalDueForPeriod over all periods)
      -- deliberately included BECAUSE it is expected to FAIL on some captures. The
         failures are the finding; see the handoff.
  C6  sum(principalDue) == totalPrincipalExpected   (principal amortises to zero)
  C7  sum(interestDue)  == totalInterestCharged
  C8  charges never move principal: principalDue / principalLoanBalanceOutstanding /
      interestDue are cell-for-cell identical to the zero-charge control
  C9  the EMI (totalInstallmentAmountForPeriod) is cell-for-cell identical to the control
  C10 no negative money anywhere
"""
import json, os
from decimal import Decimal

W = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-aae6901cc4f028513"
CH = W + "/.softhouse/capture/charges"
FC = CH + "/out/fc"
Z = Decimal(0)


def load(p):
    with open(p) as f:
        return json.load(f, parse_float=Decimal, parse_int=Decimal)


def m(v):
    if v is None:
        return None
    q = v * 100
    assert q == q.to_integral_value(), f"sub-minor-unit value {v}"
    return int(q)


def g(p, k):
    v = p.get(k)
    return Z if v is None else v


ctrl = load(CH + "/out/control/B-01-baseline-raw.json")
rows = []
fails = 0

for f in sorted(os.listdir(FC)):
    if not f.endswith("-raw.json"):
        continue
    cid = f[: -len("-raw.json")]
    d = load(FC + "/" + f)
    ps = d["periods"]
    res = {}

    res["C1"] = m(sum(g(p, "feeChargesDue") for p in ps)) == m(g(d, "totalFeeChargesCharged"))
    res["C2"] = m(sum(g(p, "penaltyChargesDue") for p in ps)) == m(g(d, "totalPenaltyChargesCharged"))
    res["C3"] = all(
        m(g(p, "totalDueForPeriod")) ==
        m(g(p, "principalDue") + g(p, "interestDue") + g(p, "feeChargesDue") + g(p, "penaltyChargesDue"))
        for p in ps if "period" in p)
    res["C4"] = all(m(g(p, "feeChargesOutstanding")) == m(g(p, "feeChargesDue"))
                    and m(g(p, "penaltyChargesOutstanding")) == m(g(p, "penaltyChargesDue"))
                    for p in ps if "period" in p)
    res["C5"] = m(sum(g(p, "totalDueForPeriod") for p in ps)) == m(g(d, "totalRepaymentExpected"))
    res["C6"] = m(sum(g(p, "principalDue") for p in ps)) == m(g(d, "totalPrincipalExpected"))
    res["C7"] = m(sum(g(p, "interestDue") for p in ps)) == m(g(d, "totalInterestCharged"))
    res["C8"] = all(
        m(g(a, k)) == m(g(b, k))
        for a, b in zip(ctrl["periods"], ps)
        for k in ("principalDue", "principalOriginalDue", "interestDue",
                  "principalLoanBalanceOutstanding"))
    res["C9"] = all(m(g(a, "totalInstallmentAmountForPeriod")) == m(g(b, "totalInstallmentAmountForPeriod"))
                    for a, b in zip(ctrl["periods"], ps))
    res["C10"] = all(m(g(p, k)) >= 0 for p in ps
                     for k in ("principalDue", "interestDue", "feeChargesDue",
                               "penaltyChargesDue", "totalDueForPeriod",
                               "principalLoanBalanceOutstanding"))

    rows.append((cid, res))
    fails += sum(1 for v in res.values() if not v)

keys = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"]
print("| capture | " + " | ".join(keys) + " |")
print("|---" * (len(keys) + 1) + "|")
for cid, res in rows:
    print("| " + cid + " | " + " | ".join("PASS" if res[k] else "**FAIL**" for k in keys) + " |")
print()
print("C5 is expected to fail wherever a per-period charge is excluded from")
print("totalRepaymentExpected. Those failures are the finding, not a defect in this tool.")
print()
print("total assertion failures: %d" % fails)
