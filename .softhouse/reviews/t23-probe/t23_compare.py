#!/usr/bin/env python3
"""
T23 — diff the pinned oracle (t23-probe2-output.txt, OBSERVED) against my re-derivation
(t23_rederive.py) which deliberately OMITS the EMI re-adjust loop (PEC:1258-1308).

A divergence is the loop firing. Every case below is inside DEC-1 revision 2's stated graded domain.
"""
import datetime
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rd", os.path.join(HERE, "t23_rederive.py"))
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)

START = datetime.date(2024, 1, 1)

rows = []
for line in open(os.path.join(HERE, "t23-probe2-output.txt")):
    if not line.startswith("CASE "):
        continue
    m = re.match(r"CASE P=(\d+) n=(\d+) rate=([\d.]+) totalInterest=([\d.]+) totalRepayment=([\d.]+) \|(.*)", line.strip())
    P, n, rate, ti, tr, rest = m.group(1), int(m.group(2)), m.group(3), m.group(4), m.group(5), m.group(6)
    per = {}
    for tok in rest.split():
        num, vals = tok.split(":")
        p, i, t, b = vals.split("/")
        per[int(num[1:])] = (p, i, t, b)
    rows.append((int(P), n, rate, ti, tr, per))

print(f"{'principal':>10} {'n':>3} {'rate':>6} | {'oracle EMI':>12} {'my EMI':>12} | {'oracle last':>12} {'my last':>12} | verdict")
print("-" * 104)
nfired = 0
for P, n, rate, ti, tr, per in rows:
    d = rd.derive(P, n, rate, START)
    my_emi = d["emi"]
    my_last = d["rows"][-1]["emi"]
    or_emi = per[1][2]
    or_last = per[n][2]
    my_ti = sum(r["interest"] for r in d["rows"])
    same = (str(my_emi) == or_emi and str(my_last) == or_last and str(my_ti) == ti)
    if not same:
        nfired += 1
    print(f"{P:>10} {n:>3} {rate:>6} | {or_emi:>12} {str(my_emi):>12} | {or_last:>12} {str(my_last):>12} | "
          f"{'IDENTICAL' if same else '*** ORACLE DIVERGES FROM THE NO-LOOP MODEL ***'}")
    if not same:
        print(f"{'':>10} {'':>3} {'':>6} |   totalInterest oracle={ti}  no-loop model={my_ti}"
              f"   (my pre-loop gap {d['emi_diff']}, guard={d['readjust_guard']})")
print()
print(f"{nfired} of {len(rows)} graded-domain cases diverge => the EMI re-adjust loop "
      f"(ProgressiveEMICalculator.java:1258-1308) changes the answer INSIDE the graded domain.")
