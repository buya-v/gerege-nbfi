#!/usr/bin/env python3
# T44 audit leg — analyse the four live discrimination probes. Exact Decimal, integer minor
# units, no float anywhere.
import json, os, hashlib
from decimal import Decimal

AUD = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse/capture/audit-t44/charges"
SH = "/Users/buv/gerege-nbfi/.claude/worktrees/agent-a0de129ee93ba6bd9/.softhouse"

def load(p):
    with open(p) as f:
        return json.load(f, parse_float=Decimal)

def minor(v):
    if v is None:
        return None
    d = v if isinstance(v, Decimal) else Decimal(str(v))
    q = d * 100
    assert q == q.to_integral_value(), "sub-minor-unit %s" % d
    return int(q)

def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def rnd_half_up(num, den):
    q = num // den
    if (num - q * den) * 2 >= den:
        q += 1
    return q

R = []
def say(s):
    R.append(s); print(s)

ctrl1 = load(SH + "/capture/charges/out/control/B-01-baseline-raw.json")
ctrl2 = load(SH + "/capture/charges/out/control/B-02-multiplesof100-raw.json")

say("# T44 audit leg (charges) - live discrimination probes AP-1..AP-4")
say("")
say("All four issued against the live pinned oracle, tenant `gerege`, "
    "POST /loans?command=calculateLoanSchedule (persists nothing).")
say("")

def rows(doc):
    out = []
    for p in doc["periods"]:
        if p.get("period") is None:
            out.append(("disb", minor(p.get("feeChargesDue")) or 0, minor(p.get("penaltyChargesDue")) or 0))
        else:
            out.append((p["period"], minor(p["feeChargesDue"]), minor(p["penaltyChargesDue"])))
    return out

for pid, desc, ctrl in [
    ("AP-1-sdd-pctinterest-inside-p1", "charge 11 (PCT_OF_INTEREST, SPECIFIED_DUE_DATE) due 20 Jan 2026 - STRICTLY INSIDE period 1, separated path", ctrl1),
    ("AP-2-sdd-pctinterest-on-p1-duedate", "charge 11 due 01 Feb 2026 = period 1 dueDate = period 2 fromDate, separated path", ctrl1),
    ("AP-3-sdd-pctinterest-on-p3-duedate", "charge 11 due 01 Apr 2026 = period 3 dueDate = period 4 fromDate, separated path", ctrl1),
    ("AP-4-b02-pctamtint-instalment", "charge 5 (PCT_OF_AMOUNT_AND_INTEREST, INSTALMENT_FEE) on product 2 (installmentAmountInMultiplesOf=100), so EMI != principal+interest", ctrl2),
]:
    p = os.path.join(AUD, "out/probes", pid + "-raw.json")
    d = load(p)
    say("## %s" % pid)
    say("")
    say("%s" % desc)
    say("")
    say("sha256 `%s`" % sha(p))
    say("")
    landed = [(a, b, c) for (a, b, c) in rows(d) if b or c]
    say("| totalFee | totalPenalty | totalRepaymentExpected | landed in (period:fee minor) |")
    say("|---|---|---|---|")
    say("| %d | %d | %d | %s |" % (minor(d["totalFeeChargesCharged"]), minor(d["totalPenaltyChargesCharged"]),
        minor(d["totalRepaymentExpected"]), ", ".join("%s:%d" % (a, b) for a, b, c in landed) or "NOWHERE"))
    say("")
    say("control totalRepaymentExpected = %d ; control totalInterestCharged = %d"
        % (minor(ctrl["totalRepaymentExpected"]), minor(ctrl["totalInterestCharged"])))
    say("")

# --- AP-4: does the base = principal+interest, or the (rounded-to-100) EMI? ---
say("## AP-4 - which base does PERCENT_OF_AMOUNT_AND_INTEREST INSTALMENT_FEE use?")
say("")
d4 = load(os.path.join(AUD, "out/probes", "AP-4-b02-pctamtint-instalment-raw.json"))
say("| period | principalDue+interestDue | EMI (totalInstallmentAmountForPeriod) | 1.2345% of P+I | 1.2345% of EMI | observed fee | matches |")
say("|---|---|---|---|---|---|---|")
sep = 0
for a, b in zip(d4["periods"], ctrl2["periods"]):
    if a.get("period") is None:
        continue
    pi = minor(b["principalDue"]) + minor(b["interestDue"])
    emi = minor(b["totalInstallmentAmountForPeriod"])
    e_pi = rnd_half_up(pi * 12345, 1000000)
    e_emi = rnd_half_up(emi * 12345, 1000000)
    obs = minor(a["feeChargesDue"])
    if e_pi != e_emi:
        sep += 1
    which = ("P+I" if obs == e_pi else "") + ("/EMI" if obs == e_emi else "")
    say("| %s | %d | %d | %d | %d | %d | %s |" % (a["period"], pi, emi, e_pi, e_emi, obs, which or "**NEITHER**"))
say("")
say("periods on which the two candidate bases give DIFFERENT answers: **%d of 12**" % sep)
say("")

with open(os.path.join(AUD, "out", "PROBES.md"), "w") as f:
    f.write("\n".join(R) + "\n")
