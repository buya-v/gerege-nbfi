#!/usr/bin/env python3
"""T44 AUDIT -- independent recomputation of every published T42 number.

Written from the definitions in the T42 handoff.  Does NOT import or copy
.softhouse/capture/mathcontext/analysis/*.py.

MONEY RULE: exact Decimal only, parse_float=Decimal, no float anywhere.
Comparison is EXACT STRING on every cell (stricter than Decimal equality;
that is what "full-cell" means).
"""
import json, sys, os
from decimal import Decimal
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
MC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "mathcontext", "out"))


def load(name):
    with open(os.path.join(MC, name)) as f:
        return json.load(f, parse_float=Decimal, parse_int=int)


PLAN_SCALARS = ["loanTermInDays", "totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount"]


def cells(case):
    obs = case.get("observed")
    if obs is None:
        return None
    d = OrderedDict()
    for k in PLAN_SCALARS:
        d["plan." + k] = str(obs[k])
    for i, p in enumerate(obs["periods"]):
        for k, v in p.items():
            d["p%d.%s" % (i, k)] = str(v)
    return d


def moved(a, b):
    ca, cb = cells(a), cells(b)
    if ca is None or cb is None:
        return None
    keys = list(dict.fromkeys(list(ca.keys()) + list(cb.keys())))
    return sum(1 for k in keys if ca.get(k) != cb.get(k))


def ncells(case):
    c = cells(case)
    return 0 if c is None else len(c)


out = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.append(s)


# ================================================================ CAPTURE 1
d1 = load("t42-mathcontext.json")
by1 = {c["id"]: c for c in d1["captures"]}
say("=== capture 1:", len(d1["captures"]), "cases; ambientCanary =", repr(d1["ambientCanary"]))
say("=== moneyHelperPrecisionConstant =", d1["moneyHelperPrecisionConstant"])

say("")
say("--- E1 : the 13-shape ambient/threaded matrix (audit recomputation) ---")
say("%-32s %-14s %-12s %-14s %-16s %-4s" % ("shape", "ambient DOWN", "ambient UP", "threaded DOWN", "ambient ABSENT", "dp"))
e1_cells = 0
for i in range(13):
    n = "%02d" % i
    A = by1["T42-MX-%s-A" % n]
    B = by1["T42-MX-%s-B" % n]
    C = by1["T42-MX-%s-C" % n]
    D = by1["T42-MX-%s-D" % n]
    E = by1["T42-MX-%s-E" % n]
    shape = A["shape"]
    dp = A["inputs"]["currencyDecimalPlaces"]
    mAB, mAE, mAC = moved(A, B), moved(A, E), moved(A, C)
    absent = "generated" if D.get("observed") is not None else "THREW"

    def f(x):
        return "identical" if x == 0 else (("%d cells" % x) if x is not None else "n/a")

    say("%-32s %-14s %-12s %-14s %-16s %-4s" % (shape, f(mAB), f(mAE), f(mAC), absent, dp))
    e1_cells += ncells(A) * 3
    if D.get("observed") is not None:
        e1_cells += ncells(A)
say("E1 cells compared (A-vs-{B,E,C} + A-vs-D where D generated):", e1_cells)
tot_mx = sum(ncells(c) for c in d1["captures"] if c["family"] == "MATRIX")
say("alt: total cells present in all 65 MATRIX observations:", tot_mx)
say("alt: sum of cells over the 4 non-baseline cases per shape (B,C,D,E):",
    sum(ncells(by1["T42-MX-%02d-%s" % (i, s)]) for i in range(13) for s in "BCDE"))

say("")
say("--- absence cases: does the ABSENT run equal the ratified-ambient run? ---")
for i in range(13):
    n = "%02d" % i
    A = by1["T42-MX-%s-A" % n]
    D = by1["T42-MX-%s-D" % n]
    if D.get("observed") is None:
        say("  %-32s THREW  err=%s" % (A["shape"], D.get("error")))
    else:
        say("  %-32s A-vs-D moved %d cells" % (A["shape"], moved(A, D)))

say("")
say("--- E1 behavioural canaries ---")
say("  plain threaded flip  A.totalInterest=%s  C(threaded DOWN).totalInterest=%s"
    % (by1["T42-MX-00-A"]["observed"]["totalInterestAmount"], by1["T42-MX-00-C"]["observed"]["totalInterestAmount"]))
say("  0dp ambient flip     A=%s  B(DOWN)=%s  E(UP)=%s"
    % (by1["T42-MX-07-A"]["observed"]["totalInterestAmount"],
       by1["T42-MX-07-B"]["observed"]["totalInterestAmount"],
       by1["T42-MX-07-E"]["observed"]["totalInterestAmount"]))

say("")
say("--- did installmentAmountInMultiplesOf=1000 change the schedule at all? ---")
plain = by1["T42-MX-00-A"]
mult = by1["T42-MX-06-A"]
say("  plain vs multiples1000 (identical base shape, only instMultiplesOf differs):", moved(plain, mult), "cells differ")
say("  multiples1000 p1 total:", mult["observed"]["periods"][1]["total"],
    "| plain p1 total:", plain["observed"]["periods"][1]["total"])
dpa = by1["T42-MX-04-A"]
dpm = by1["T42-MX-05-A"]
say("  downPaymentAwkward(p=1000001) vs downPaymentMultiples1000(p=1200000): different principals, not comparable")
say("  downPaymentMultiples1000 p1 total:", dpm["observed"]["periods"][1].get("total"))
say("  downPayment25 p1(DOWN_PAYMENT) principal:", by1["T42-MX-03-A"]["observed"]["periods"][1].get("principal"))

say("")
say("--- capture 1 precision sweep ---")
prec_ids = sorted({c["id"].rsplit("-", 1)[0] for c in d1["captures"] if c["family"] == "PRECISION"})
say("  shapes:", len(prec_ids))
sep1912 = sep198 = 0
c1_prec_cells = 0
for pid in prec_ids:
    a = by1[pid + "-p19"]
    b = by1[pid + "-p12"]
    c = by1[pid + "-p8"]
    m1, m2 = moved(a, b), moved(a, c)
    c1_prec_cells += ncells(a) * 2
    if m1:
        sep1912 += 1
    if m2:
        sep198 += 1
say("  separate 19-vs-12:", sep1912, "of", len(prec_ids))
say("  separate 19-vs-8 :", sep198, "of", len(prec_ids))
say("  cells compared (48 shapes x 2 comparisons x cells-per-shape):", c1_prec_cells)

# ================================================================ CAPTURE 2
d2 = load("t42-mathcontext2.json")
by2 = {c["id"]: c for c in d2["captures"]}
say("")
say("=== capture 2:", len(d2["captures"]), "cases")

say("")
say("--- E2 : the two wirings, side by side ---")
for tag in ("", "tie-"):
    base = by2["T42B-PA-%sord4" % tag]
    baseB = by2["T42B-PB-%sord4" % tag]
    for ordn in (1, 0, 6):
        pa = by2["T42B-PA-%sord%d" % (tag, ordn)]
        pb = by2["T42B-PB-%sord%d" % (tag, ordn)]
        say("  %-6s 4->%d  PathA moved %2d cells | PathB moved %2d cells | PB int %s -> %s | PB effective mc '%s'"
            % (tag or "plain", ordn, moved(base, pa), moved(baseB, pb),
               baseB["observed"]["totalInterestAmount"], pb["observed"]["totalInterestAmount"],
               pb["inputs"]["effectiveThreadedMathContext"]))
    say("  %-6s PathA effective mc at ord4: '%s' ; ambient '%s' ; PA-vs-PB at ord4 moved %d"
        % (tag or "plain", base["inputs"]["effectiveThreadedMathContext"],
           base["inputs"]["ambientMoneyHelperMathContext"], moved(base, baseB)))
wiring_cells = sum(ncells(c) for c in d2["captures"] if c["family"] == "WIRING")
say("  total cells present in the 16 WIRING observations:", wiring_cells)

say("")
say("--- (b) capture 2 precision bisection ---")
prec2 = sorted({c["id"].rsplit("-", 1)[0] for c in d2["captures"] if c["family"] == "PRECISION"})
say("  shapes:", len(prec2))
c2_prec_cells = 0
seps = []
for pid in prec2:
    a = by2[pid + "-p19"]
    b = by2[pid + "-p12"]
    m = moved(a, b)
    c2_prec_cells += ncells(a)
    seps.append((pid, a["inputs"]["disbursementAmount"], a["inputs"]["numberOfRepayments"],
                 str(a["inputs"]["annualNominalInterestRate"]), m,
                 str(a["observed"]["totalInterestAmount"]), str(b["observed"]["totalInterestAmount"])))
say("  cells compared (62 shapes x 1 comparison):", c2_prec_cells)
say("")
say("  %-16s %-18s %-4s %-6s %-6s %-18s %-18s" % ("id", "principal", "n", "rate", "cells", "p19 interest", "p12 interest"))
for s in seps:
    say("  %-16s %-18s %-4s %-6s %-6s %-18s %-18s" % s)

say("")
say("--- smallest separating principal per (n, rate) family ---")
fam = {}
for pid, princ, n, rate, m, i19, i12 in seps:
    key = (n, rate)
    if m:
        cur = fam.get(key)
        if cur is None or Decimal(princ) < Decimal(cur[0]):
            fam[key] = (princ, m, i19, i12)
for k in sorted(fam, key=lambda x: (int(x[0]), Decimal(x[1]))):
    say("  n=%s rate=%s -> smallest separating principal %s (%d cells) p19=%s p12=%s"
        % (k[0], k[1], fam[k][0], fam[k][1], fam[k][2], fam[k][3]))

say("")
say("--- non-monotonicity check (ladder per family, SEP = separates 19 vs 12) ---")
for key in sorted({(n, rate) for _, _, n, rate, _, _, _ in seps}, key=lambda x: (int(x[0]), Decimal(x[1]))):
    row = [(Decimal(p), m) for _, p, n, rate, m, _, _ in seps if (n, rate) == key]
    row.sort()
    say("  n=%s rate=%s : %s" % (key[0], key[1], " ".join(("%s:%s" % (p, "SEP" if m else "-")) for p, m in row)))

say("")
say("=== CELL TOTALS ===")
say("  E1 matrix (my accounting)      :", e1_cells)
say("  capture 1 precision sweep      :", c1_prec_cells)
say("  capture 2 precision bisection  :", c2_prec_cells)
say("  capture 2 wiring               :", wiring_cells)
say("  sum                            :", e1_cells + c1_prec_cells + c2_prec_cells + wiring_cells)
say("  T42 claims 3,820 + 90,528 + 147,676 + 1,284 = 243,308 ; and 238,204 for the precision search")
say("  my precision-only total (c1+c2):", c1_prec_cells + c2_prec_cells)

with open(os.path.join(HERE, "audit_recompute-output.txt"), "w") as f:
    f.write("\n".join(out) + "\n")
