#!/usr/bin/env python3
"""T44 AUDIT -- property invariants re-run over T42's COMMITTED payloads.

T42 ships no C1..C10 invariant suite.  These are the invariants that apply to a
LoanSchedulePlan payload, re-derived here and RUN, not claimed.

MONEY RULE: exact Decimal, integer minor units, no float anywhere.
T41 decision C-1 is respected: `plan total == sum of row totals` is NOT asserted as
a failure, only reported, because it is known to be wrong about the oracle.
"""
import json, os, re, sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "mathcontext", "out"))

MONEY_KEYS = {"principal", "interest", "fee", "penalty", "total", "balance", "totalOutstandingBalance"}
FLOATISH = re.compile(r"[eE]")

out = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.append(s)


def check(payload, tag, dp_of):
    doc = json.load(open(os.path.join(MC, payload)), parse_float=Decimal)
    fails = {}
    n_obs = 0

    def bad(inv, cid, msg):
        fails.setdefault(inv, []).append("%s: %s" % (cid, msg))

    for c in doc["captures"]:
        obs = c.get("observed")
        if obs is None:
            continue
        n_obs += 1
        cid = c["id"]
        dp = dp_of(c)
        periods = obs["periods"]

        # ---- I5 no float-shaped / non-minor-unit value ----------------------
        for p in periods:
            for k, v in p.items():
                if k not in MONEY_KEYS:
                    continue
                s = str(v)
                if FLOATISH.search(s):
                    bad("I5-float", cid, "%s=%s has exponent notation" % (k, s))
                frac = s.split(".")[1] if "." in s else ""
                if len(frac) > dp:
                    bad("I5-scale", cid, "%s=%s has %d dp, currency has %d" % (k, s, len(frac), dp))
        for k in ("totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"):
            s = str(obs[k])
            if FLOATISH.search(s):
                bad("I5-float", cid, "plan.%s=%s has exponent notation" % (k, s))
            frac = s.split(".")[1] if "." in s else ""
            if len(frac) > dp:
                bad("I5-scale", cid, "plan.%s=%s has %d dp" % (k, s, len(frac)))

        # ---- I4 no negative money -------------------------------------------
        for i, p in enumerate(periods):
            for k, v in p.items():
                if k in MONEY_KEYS and Decimal(str(v)) < 0:
                    bad("I4-negative", cid, "period %d %s=%s" % (i, k, v))

        # ---- I1 principal amortizes to zero ---------------------------------
        disb = sum((Decimal(str(p["principal"])) for p in periods if p["type"] == "DISBURSEMENT"), Decimal(0))
        paid = sum((Decimal(str(p["principal"])) for p in periods if p["type"] in ("REPAYMENT", "DOWN_PAYMENT")),
                   Decimal(0))
        if disb != paid:
            bad("I1-principal-amortizes", cid, "disbursed %s != sum principal due %s (delta %s)" % (disb, paid, paid - disb))
        if disb != Decimal(str(obs["totalDisbursedAmount"])):
            bad("I1b-plan-disbursed", cid, "plan.totalDisbursedAmount %s != disbursement rows %s"
                % (obs["totalDisbursedAmount"], disb))
        last = [p for p in periods if p["type"] in ("REPAYMENT", "DOWN_PAYMENT")][-1]
        if Decimal(str(last["balance"])) != 0:
            bad("I1c-final-balance", cid, "final row balance %s != 0" % last["balance"])

        # ---- I2 sum of interest == plan total interest ----------------------
        si = sum((Decimal(str(p["interest"])) for p in periods if p["type"] == "REPAYMENT"), Decimal(0))
        if si != Decimal(str(obs["totalInterestAmount"])):
            bad("I2-interest-sums", cid, "sum row interest %s != plan.totalInterestAmount %s"
                % (si, obs["totalInterestAmount"]))

        # ---- I3 per-row total == principal + interest + fee + penalty -------
        for i, p in enumerate(periods):
            if p["type"] != "REPAYMENT":
                continue
            lhs = Decimal(str(p["total"]))
            rhs = sum(Decimal(str(p[k])) for k in ("principal", "interest", "fee", "penalty"))
            if lhs != rhs:
                bad("I3-row-splits", cid, "period %d total %s != p+i+f+p %s" % (i, lhs, rhs))

        # ---- I6 (REPORTED ONLY -- T41 C-1) plan total vs sum of row totals ---
        st = sum((Decimal(str(p["total"])) for p in periods if p["type"] in ("REPAYMENT", "DOWN_PAYMENT")), Decimal(0))
        if st != Decimal(str(obs["totalRepaymentAmount"])):
            bad("I6-REPORTED-ONLY-plan-total", cid, "sum row totals %s != plan.totalRepaymentAmount %s"
                % (st, obs["totalRepaymentAmount"]))

        # ---- I7 balance ladder is non-increasing ----------------------------
        prev = None
        for i, p in enumerate(periods):
            if "balance" not in p:
                continue
            b = Decimal(str(p["balance"]))
            if prev is not None and b > prev:
                bad("I7-balance-monotone", cid, "period %d balance %s > previous %s" % (i, b, prev))
            prev = b

    say("=== %s : %d observations checked ===" % (tag, n_obs))
    for inv in sorted(fails):
        say("  %-32s FAIL on %d cases; first 4:" % (inv, len(fails[inv])))
        for m in fails[inv][:4]:
            say("      " + m)
    clean = [i for i in ("I1-principal-amortizes", "I1b-plan-disbursed", "I1c-final-balance", "I2-interest-sums",
                         "I3-row-splits", "I4-negative", "I5-float", "I5-scale", "I7-balance-monotone",
                         "I6-REPORTED-ONLY-plan-total") if i not in fails]
    say("  CLEAN:", ", ".join(clean) if clean else "(none)")
    say("")
    return fails


f1 = check("t42-mathcontext.json", "capture 1", lambda c: int(c["inputs"]["currencyDecimalPlaces"]))
f2 = check("t42-mathcontext2.json", "capture 2", lambda c: int(c["inputs"]["currencyDecimalPlaces"]))

with open(os.path.join(HERE, "audit_invariants-output.txt"), "w") as fh:
    fh.write("\n".join(out) + "\n")
