#!/usr/bin/env python3
"""Failability proof for audit_invariants.py.

Corrupt ONE observation in memory and re-run the same invariant bodies.
"An assertion suite that has never failed has not been tested" (.softhouse/patterns.md).
Exits 0 only if at least 6 distinct invariants fire.
"""
import json, os, re, sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, "..", "..", "..", "mathcontext", "out", "t42-mathcontext.json"))
doc = json.load(open(P))
c = [x for x in doc["captures"] if x["id"] == "T42-CTL-Q0a"][0]
obs = c["observed"]
print("before: p1.principal =", obs["periods"][1]["principal"],
      " totalInterestAmount =", obs["totalInterestAmount"])

obs["periods"][1]["principal"] = "999999.99"   # breaks I1, I3
obs["totalInterestAmount"] = "1.234"           # breaks I2, I5-scale
obs["periods"][2]["interest"] = "-1.00"        # breaks I4
obs["periods"][3]["total"] = "1.0E+5"          # breaks I5-float

MONEY = ("principal", "interest", "fee", "penalty", "total", "balance", "totalOutstandingBalance")
fired = []

disb = sum(Decimal(p["principal"]) for p in obs["periods"] if p["type"] == "DISBURSEMENT")
paid = sum(Decimal(p["principal"]) for p in obs["periods"] if p["type"] in ("REPAYMENT", "DOWN_PAYMENT"))
if disb != paid:
    fired.append("I1-principal-amortizes fired: disbursed %s != due %s" % (disb, paid))

si = sum(Decimal(p["interest"]) for p in obs["periods"] if p["type"] == "REPAYMENT")
if si != Decimal(obs["totalInterestAmount"]):
    fired.append("I2-interest-sums fired: %s != %s" % (si, obs["totalInterestAmount"]))

for i, p in enumerate(obs["periods"]):
    if p["type"] != "REPAYMENT":
        continue
    if Decimal(p["total"]) != sum(Decimal(p[k]) for k in ("principal", "interest", "fee", "penalty")):
        fired.append("I3-row-splits fired at period %d" % i)
        break

if any(Decimal(str(v)) < 0 for p in obs["periods"] for k, v in p.items() if k in MONEY):
    fired.append("I4-negative fired")

if any(re.search(r"[eE]", str(v)) for p in obs["periods"] for k, v in p.items() if k in MONEY):
    fired.append("I5-float fired")

if len(str(obs["totalInterestAmount"]).split(".")[1]) > 2:
    fired.append("I5-scale fired")

for f in fired:
    print("  " + f)
ok = len(fired) >= 6
print("FAILABILITY:", "PASS -- %d invariants fired on the corrupted payload" % len(fired) if ok
      else "INSUFFICIENT -- only %d fired" % len(fired))
sys.exit(0 if ok else 1)
