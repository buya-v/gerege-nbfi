#!/usr/bin/env python3
"""
T51 -- analysis of capture passes 2 and 3.  Contacts no oracle; reads only committed bytes.
Same rules as t51-analyse.py: exact-text sidecars, full-cell comparison, differing-cell
counts published, and any comparison that moves zero cells reported as discriminating
nothing.  Run t51-analyse.py FIRST -- it writes the sidecars for every T51-*-raw.json.
"""
import json
import pathlib
import sys
from decimal import Decimal

O = pathlib.Path(__file__).resolve().parents[1] / "out" / "t51"
failures = []


def load_exact(stem):
    return json.loads((O / (stem + "-exact.json")).read_text())


def cells(doc):
    out = {}
    if "periods" not in doc:
        return {"__http__": doc.get("httpStatusCode"),
                "__msg__": "; ".join(e.get("developerMessage", "") for e in doc.get("errors", []))}
    for k, v in doc.items():
        if k in ("periods", "currency"):
            continue
        out[k] = v
    for i, p in enumerate(doc["periods"]):
        for k, v in p.items():
            out["row%d.%s" % (i, k)] = v
    return out


def compare(label, a, b, expect, show=8):
    A, B = cells(load_exact(a)), cells(load_exact(b))
    keys = sorted(set(A) | set(B))
    diffs = [(k, A.get(k), B.get(k)) for k in keys if A.get(k) != B.get(k)]
    print("\n== %s\n   %d of %d cells differ   [expected: %s]" % (label, len(diffs), len(keys), expect))
    for k, x, y in diffs[:show]:
        print("     %-36s %-18s | %s" % (k, x, y))
    if len(diffs) > show:
        print("     ... %d more" % (len(diffs) - show))
    if expect == "identical" and diffs:
        failures.append("%s: expected IDENTICAL, %d cells differ" % (label, len(diffs)))
    if expect == "separate" and not diffs:
        failures.append("%s: EVERY CELL AGREES -- this comparison DISCRIMINATES NOTHING" % label)
    if not diffs:
        print("     -> every cell agrees; on its own this comparison discriminates NOTHING.")
    return diffs


def fee_rows(stem):
    doc = load_exact(stem)
    if "periods" not in doc:
        return None, doc
    rows = [(p.get("principalDisbursed"), p.get("feeChargesDue"))
            for p in doc["periods"] if "period" not in p]
    return (doc["totalFeeChargesCharged"], rows), doc


print("#" * 86)
print("# ITEM 2, pass 2 -- the shapes that BREAK the linearity that hid chargeCalculationType 5")
print("#" * 86)
print("""
Pass 1 found ct=5 byte-identical to ct=2 on three genuine tranches.  Reason, re-derived from
source and then tested: LoanChargeAssembler.java:190-204 builds ONE LoanCharge per tranche for
chargeTimeType 12, each with loanPrincipal = that tranche's principal, so the tranche reading
totals  SUM(p x t_i) = p x SUM(t_i)  -- and when the tranches sum to the loan principal that
is exactly the ct=2 reading  p x principal.  Two shapes break it.
""")

print("-- (a) tranches that DO NOT sum to the loan principal --")
print("   request principal 1,200,000 ; disbursementData 400,000 + 300,000 + 300,000 = 1,000,000")
for stem, what in (("T51-TR-07-c5-tranches-sum-1000000", "ct=5 PERCENT_OF_DISBURSEMENT_AMOUNT (id 13)"),
                   ("T51-TR-08-c2-tranches-sum-1000000", "ct=2 PERCENT_OF_AMOUNT (id 3)")):
    (tot, rows), _ = fee_rows(stem)
    print("   %-44s totalFeeChargesCharged=%-14s disbursement rows=%s" % (what, tot, rows))
compare("ct=5 vs ct=2, tranches summing to 1,000,000 against a principal of 1,200,000",
        "T51-TR-07-c5-tranches-sum-1000000", "T51-TR-08-c2-tranches-sum-1000000", "separate")

print("\n-- (b) minCap / maxCap: a clamp is not linear "
      "(LoanCharge.minimumAndMaximumCap [LoanCharge.java:326-350], caps copied onto EVERY "
      "LoanCharge at LoanChargeService.java:527-528) --")
print("   tranches 500,000 + 300,000 + 400,000 ; 1.2345 % of each is 6172.5 / 3703.5 / 4938")
for stem, what in (("T51-TR-09-c5-maxcap", "ct=5, maxCap 5000 (charge 15)"),
                   ("T51-TR-10-c2-maxcap", "ct=2, maxCap 5000 (charge 16)"),
                   ("T51-TR-13-c5-maxcap-onetranche", "ct=5, maxCap 5000, ONE tranche of 1,200,000"),
                   ("T51-TR-11-c5-mincap", "ct=5, minCap 8000, 0.1 % (charge 17)"),
                   ("T51-TR-12-c2-mincap", "ct=2, minCap 8000, 0.1 % (charge 18)")):
    (tot, rows), _ = fee_rows(stem)
    print("   %-50s totalFeeChargesCharged=%-12s rows=%s" % (what, tot, rows))
compare("maxCap 5000: ct=5 (per tranche) vs ct=2 (once)",
        "T51-TR-09-c5-maxcap", "T51-TR-10-c2-maxcap", "separate")
compare("minCap 8000: ct=5 (per tranche) vs ct=2 (once)",
        "T51-TR-11-c5-mincap", "T51-TR-12-c2-mincap", "separate")
compare("maxCap 5000 on ct=5 with THREE tranches vs the same charge on ONE tranche",
        "T51-TR-09-c5-maxcap", "T51-TR-13-c5-maxcap-onetranche", "separate")
compare("maxCap 5000 vs no cap, both ct=5, three tranches (does the cap bind at all?)",
        "T51-TR-09-c5-maxcap", "T51-TR-01-c5-tranche-P3", "separate")

print("""
   RE-DERIVATION vs OBSERVATION (the totals above are the ORACLE's; the arithmetic is mine):
     per-tranche maxCap : min(6172.5,5000) + min(3703.5,5000) + min(4938,5000) = 13641.50
     whole-loan  maxCap : min(14814,5000)                                      =  5000.00
     per-tranche minCap : max(500,8000) + max(300,8000) + max(400,8000)        = 24000.00
     whole-loan  minCap : max(1200,8000)                                       =  8000.00
""")

print("\n" + "#" * 86)
print("# ITEM 1, pass 2 -- the other crossing direction (non-leap -> leap)")
print("#" * 86)
compare("NL2L, disbursed 15 Dec 2023 (365-day year crossing INTO a 366-day year): "
        "product 17 (flag TRUE) vs product 18 (flag FALSE)",
        "T51-IROD-NL2L-P1", "T51-IROD-NL2L-P2", "observe")
doc = load_exact("T51-IROD-NL2L-P1")
print("   observed period 1: %s -> %s   interestDue %s   totalInterestCharged %s"
      % ("-".join(doc["periods"][1]["fromDate"]), "-".join(doc["periods"][1]["dueDate"]),
         doc["periods"][1]["interestDue"], doc["totalInterestCharged"]))

print("\n" + "#" * 86)
print("# ITEM 3 -- fixedLength")
print("#" * 86)
print("""
`fixedLength` is a supported calculateLoanSchedule parameter [LoanScheduleValidator.java:77]
and has two guards, both reached from LoanApplicationValidator.fixedLengthValidations
[:819-834] into LoanProductDataValidator.fixedLengthValidations [:2764-2797]:
  * `thereIsInterest` -- derived from the REQUEST's interestRatePerPeriod [:829-830] -- must
    be false, else HTTP 403 "Fixed Length configuration is only allowed for zero interest
    products" [:2784-2787];
  * fixedLength >= ((numberOfRepayments - 1) * repayEvery) + 1, else HTTP 403 [:2790-2796].
""")
for stem in ("T51-FL-INTEREST-REJECT", "T51-FL0-11"):
    d = load_exact(stem)
    print("   %-26s HTTP %s : %s" % (stem, d.get("httpStatusCode"),
                                     "; ".join(e.get("developerMessage", "") for e in d.get("errors", []))))
print()
for stem in ("T51-FL0-CTRL", "T51-FL0-12", "T51-FL0-18", "T51-FL0-365"):
    d = load_exact(stem)
    last = [p for p in d["periods"] if "period" in p][-1]
    print("   %-16s loanTermInDays=%-8s last period %s -> %s   totalInterestCharged=%s"
          % (stem, d["loanTermInDays"], "-".join(last["fromDate"]), "-".join(last["dueDate"]),
             d["totalInterestCharged"]))
compare("fixedLength 12 (== the natural term) vs no fixedLength",
        "T51-FL0-12", "T51-FL0-CTRL", "observe")
compare("fixedLength 18 vs no fixedLength", "T51-FL0-18", "T51-FL0-CTRL", "separate")
compare("fixedLength 365 vs fixedLength 18", "T51-FL0-365", "T51-FL0-18", "separate")

print("\n")
if failures:
    print("RESULT: %d PROBLEM(S)" % len(failures))
    for p in failures:
        print("  ! " + p)
    sys.exit(1)
print("RESULT: every comparison above published its own differing-cell count.")
