#!/usr/bin/env python3
"""
T48 -- FULL-CELL comparison over the observed payloads.  Contacts no oracle.

The program's standing lesson is that a three-scalar comparison (level installment, final
installment, total interest) has hidden two money defects and one whole field family.  This
script therefore flattens EVERY published cell -- every period row, every column, every
interest-period sub-row including the rate factor, plus the plan totals -- and reports the
count of DISAGREEING cells for each pair, never a headline scalar.

Exit 1 if a comparison that MUST be identical is not, or a comparison that MUST separate does
not.  Those expectations are stated as source-derived predictions and are the thing the
observation grades.
"""
import json
import os
import sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
PREFIX = os.environ.get("T48_OUT_PREFIX_ANALYSIS", "t48")

failures = []
notes = []


def load(name):
    with open(os.path.join(BASE, name), "r") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------- flatteners

def seam_cells(c):
    out = {}
    o = c.get("observed")
    if o is None:
        return {"__error__": c.get("error")}
    out["loanTermInDays"] = o["loanTermInDays"]
    out["totalDisbursedAmount"] = o["totalDisbursedAmount"]
    out["totalInterestAmount"] = o["totalInterestAmount"]
    out["totalRepaymentAmount"] = o["totalRepaymentAmount"]
    for i, p in enumerate(o["periods"]):
        for k, v in p.items():
            out["row%d.%s" % (i, k)] = v
    return out


def calc_cells(c):
    out = {}
    o = c.get("observed")
    if o is None:
        return {"__error__": c.get("error")}
    out["loanTermInDays"] = o["loanTermInDays"]
    for rp in o["repaymentPeriods"]:
        i = rp["index"]
        for k, v in rp.items():
            if k == "interestPeriods":
                for j, ip in enumerate(v):
                    for k2, v2 in ip.items():
                        out["p%d.ip%d.%s" % (i, j, k2)] = v2
            else:
                out["p%d.%s" % (i, k)] = v
    return out


def compare(label, a, b, cells_a, cells_b, expect):
    """expect: 'identical' or 'separate'."""
    keys = sorted(set(cells_a) | set(cells_b))
    diffs = [(k, cells_a.get(k), cells_b.get(k)) for k in keys if cells_a.get(k) != cells_b.get(k)]
    print("== %-46s %4d of %4d cells differ   (expected %s)" % (label, len(diffs), len(keys), expect))
    for k, x, y in diffs[:12]:
        print("     %-38s %-26s | %s" % (k, x, y))
    if len(diffs) > 12:
        print("     ... %d more" % (len(diffs) - 12))
    if expect == "identical" and diffs:
        failures.append("%s: expected IDENTICAL, %d cells differ" % (label, len(diffs)))
    if expect == "separate" and not diffs:
        failures.append("%s: expected SEPARATION, every cell agrees -- this capture "
                        "DISCRIMINATES NOTHING" % label)
    return diffs


# ============================================================================ PATH A (seam)
print("\n######## PATH A -- embeddable seam ########\n")
seam = load("%s-seam.json" % PREFIX)
S = {c["id"]: c for c in seam["captures"]}
SC = dict((k, seam_cells(v)) for k, v in S.items())

# --- CALIBRATION against the shipped literal ------------------------------------------
cal = S["T48-CAL"]["observed"]
shipped = {"loanTermInDays": 182, "totalDisbursedAmount": "100.00",
           "totalInterestAmount": "2.05", "totalRepaymentAmount": "102.05"}
bad = [k for k, v in shipped.items() if str(cal[k]) != str(v)]
print("CALIBRATION T48-CAL vs the shipped literal "
      "[EmbeddableProgressiveLoanScheduleGeneratorTest.java:74-77]: %s"
      % ("MATCHES on all 4 asserted values" if not bad else "MISMATCH on " + repr(bad)))
if bad:
    failures.append("T48-CAL does not reproduce the shipped literal: " + repr(bad))

# --- CONTROL against committed observations -------------------------------------------
# reference-oracle.md records Path B capture B-01 at total interest 144,988.47 /
# total repayment 1,344,988.47, itself reproducing pass-3 P-MNT-1M2.
b03 = S["T48-CTL-B03"]["observed"]
ok = b03["totalInterestAmount"] == "144659.21" and b03["totalRepaymentAmount"] == "1344659.21"
print("CONTROL   T48-CTL-B03 vs committed Path B observation B-03: %s (%s / %s)"
      % ("REPRODUCED" if ok else "DIVERGED", b03["totalInterestAmount"], b03["totalRepaymentAmount"]))
if not ok:
    failures.append("T48-CTL-B03 failed to reproduce committed observation B-03")

# --- the Path A daysInYearCustomStrategy DROP, observed -------------------------------
compare("AA-1 vs AA-N3 (FEB_29 fed in, Path A)", "T48-AA-1", "T48-AA-N3",
        SC["T48-AA-1"], SC["T48-AA-N3"], "identical")
compare("AA-1 vs AA-N4 (FULL_LEAP fed in, Path A)", "T48-AA-1", "T48-AA-N4",
        SC["T48-AA-1"], SC["T48-AA-N4"], "identical")

# --- the boundary choice: 31 Dec vs 1 Jan.  ON PATH A THIS DOES NOT BIND -- see T48-N1.
# LoanApplicationTerms.toLoanConfigurationDetails() [:1746-1756] passes
# isInterestChargedFromDateSameAsDisbursalDateEnabled into the
# interestRecognitionOnDisbursementDate parameter slot of LoanConfigurationDetails
# [LoanConfigurationDetails.java:66-77, parameter 16] and never reads the field of that name.
# The expectation below is therefore IDENTICAL, and the Path A2 twin A2-AA1 vs A2-AA2 -- which
# sets the flag directly on LoanConfigurationDetails -- is where the separation shows up.
compare("AA-1 vs AA-2 (interestRecognitionOnDisb)", "T48-AA-1", "T48-AA-2",
        SC["T48-AA-1"], SC["T48-AA-2"], "identical")

# --- the arm's suppressing conjuncts ---------------------------------------------------
compare("AA-1 vs AA-N1 (DAYS_365, arm suppressed)", "T48-AA-1", "T48-AA-N1",
        SC["T48-AA-1"], SC["T48-AA-N1"], "separate")

# --- the partial arm returns BEFORE the daysInMonth switch -----------------------------
d = compare("AA-1 vs AA-11 (DAYS_30 + ACT/ACT)", "T48-AA-1", "T48-AA-11",
            SC["T48-AA-1"], SC["T48-AA-11"], "separate")
# the crossing row's interest is the cell the partial arm owns; state whether it moved
crossing_moved = [k for k, _, _ in d if k.startswith("row2.")]
notes.append("AA-1 vs AA-11: %d cells on the crossing row (row2) moved. The partial-period "
             "branch returns at :1526-1531, BEFORE the daysInMonthType switch at :1534-1541, "
             "so a rate factor computed by the arm cannot depend on daysInMonthType -- but "
             "downstream EMI levelling can still move the row." % len(crossing_moved))

# ======================================================================== PATH A2 (calc)
print("\n######## PATH A2 -- ProgressiveEMICalculator seam ########\n")
calc = load("%s-calc.json" % PREFIX)
C = {c["id"]: c for c in calc["captures"]}
CC = dict((k, calc_cells(v)) for k, v in C.items())

# --- CALIBRATION: Fineract's own shipped literals, reproduced digit for digit ----------
lits = load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shipped_literals.json")) \
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "shipped_literals.json")) else None
if lits:
    for case_id, spec in sorted(lits["cases"].items()):
        obs = C[case_id]["observed"]["repaymentPeriods"]
        rows = spec["checkPeriod_emi_dueInterest_duePrincipal_outstandingBalance"]
        mism = []
        for i, row in enumerate(rows):
            got = [obs[i]["emi"], obs[i]["dueInterest"], obs[i]["duePrincipal"],
                   obs[i]["outstandingLoanBalance"]]
            want = [str(x) for x in row]
            # the shipped literals are asserted as doubles; compare numerically
            if [float(g) for g in got] != [float(w) for w in want]:
                mism.append((i, got, want))
        print("CALIBRATION %-12s vs %s: %s" % (case_id, spec["source"],
              "ALL %d PERIODS REPRODUCED DIGIT FOR DIGIT" % len(rows) if not mism
              else "MISMATCH %r" % mism))
        if mism:
            failures.append("%s failed to reproduce its shipped literal" % case_id)
else:
    failures.append("analysis/shipped_literals.json missing -- no calibration possible")

# --- CONTROL: reproduce the committed Path B observations B-03 and B-04 ----------------
# reference-oracle.md records B-03 (FULL_LEAP_YEAR) 144,659.21 and B-04 (FEB_29_PERIOD_ONLY)
# 145,011.43 total interest, 12/12 periods differing, taken through the RUNNING SERVER.
from decimal import Decimal  # noqa: E402

for case_id, want in (("T48-A2-CTL-B03", "144659.21"), ("T48-A2-CTL-B04", "145011.43"),
                      ("T48-A2-CTL-B03NULL", "144659.21")):
    got = sum(Decimal(rp["dueInterest"]) for rp in C[case_id]["observed"]["repaymentPeriods"])
    good = str(got) == want
    print("CONTROL   %-20s sum of dueInterest = %s  (committed Path B value %s): %s"
          % (case_id, got, want, "REPRODUCED" if good else "DIVERGED"))
    if not good:
        failures.append("%s did not reproduce the committed Path B total interest %s" % (case_id, want))

# --- FULL_LEAP_YEAR vs the field being UNSET ------------------------------------------
for fam in ("Q", "M", "Y", "B", "A"):
    compare("F29-%s-NULL vs F29-%s-FULL" % (fam, fam), "a", "b",
            CC["T48-F29-%s-NULL" % fam], CC["T48-F29-%s-FULL" % fam], "identical")

# --- FEB_29_PERIOD_ONLY, effect (a) and effect (b) -------------------------------------
compare("F29-Q-NULL vs F29-Q-F29 (has Feb 29 period)", "a", "b",
        CC["T48-F29-Q-NULL"], CC["T48-F29-Q-F29"], "separate")
compare("F29-M-NULL vs F29-M-F29 (both effects present)", "a", "b",
        CC["T48-F29-M-NULL"], CC["T48-F29-M-F29"], "separate")
compare("F29-Y-NULL vs F29-Y-F29 (one-year schedule)", "a", "b",
        CC["T48-F29-Y-NULL"], CC["T48-F29-Y-F29"], "separate")
compare("F29-B-NULL vs F29-B-F29 (EFFECT B PURE)", "a", "b",
        CC["T48-F29-B-NULL"], CC["T48-F29-B-F29"], "separate")
compare("F29-A-NULL vs F29-A-F29 (EFFECT A PURE)", "a", "b",
        CC["T48-F29-A-NULL"], CC["T48-F29-A-F29"], "separate")
compare("F29-C-NULL vs F29-C-F29 (Feb 29 IN a period)", "a", "b",
        CC["T48-F29-C-NULL"], CC["T48-F29-C-F29"], "separate")

# --- the boundary choice again, at rate-factor resolution ------------------------------
compare("A2-AA1 vs A2-AA2 (31 Dec vs 1 Jan boundary)", "a", "b",
        CC["T48-A2-AA1"], CC["T48-A2-AA2"], "separate")

# --- RATE FACTORS ONLY.  ------------------------------------------------------------
# A money cell can move for a reason the arm did not cause: the EMI is levelled across the
# whole schedule, so a change in ANY period's rate factor moves the principal split of EVERY
# period.  The rate factor is the ONLY cell the arm under observation actually owns, so it is
# compared on its own here.  A comparison that moves money but not rate factors did not
# discriminate the arm; it discriminated the levelling.
print("")


def rate_factors(cells):
    return dict((k, v) for k, v in cells.items() if "rateFactor" in k)


def rf_compare(label, a, b):
    A, B = rate_factors(CC[a]), rate_factors(CC[b])
    keys = sorted(set(A) | set(B))
    diffs = [(k, A.get(k), B.get(k)) for k in keys if A.get(k) != B.get(k)]
    print("RF  %-44s %3d of %3d rate-factor cells differ" % (label, len(diffs), len(keys)))
    for k, x, y in diffs:
        print("      %-34s %-24s | %s" % (k, x, y))
    return diffs


rf_compare("F29-Q-NULL vs F29-Q-F29", "T48-F29-Q-NULL", "T48-F29-Q-F29")
rf_compare("F29-B-NULL vs F29-B-F29 (EFFECT B PURE)", "T48-F29-B-NULL", "T48-F29-B-F29")
rf_compare("F29-A-NULL vs F29-A-F29 (EFFECT A PURE)", "T48-F29-A-NULL", "T48-F29-A-F29")
rf_compare("F29-C-NULL vs F29-C-F29 (Feb 29 in a period)", "T48-F29-C-NULL", "T48-F29-C-F29")
rf_compare("F29-Y-NULL vs F29-Y-F29", "T48-F29-Y-NULL", "T48-F29-Y-F29")
rf_compare("A2-AA1 vs A2-AA2 (boundary choice)", "T48-A2-AA1", "T48-A2-AA2")
rf_compare("A2-CTL-B03 vs A2-CTL-B04", "T48-A2-CTL-B03", "T48-A2-CTL-B04")
d = rf_compare("A2-CTL-B03 vs A2-CTL-B03NULL (FULL == unset)",
               "T48-A2-CTL-B03", "T48-A2-CTL-B03NULL")
if d:
    failures.append("FULL_LEAP_YEAR moved a rate factor vs unset on the B-03 shape")
for fam in ("Q", "M", "Y", "B", "A"):
    d = rf_compare("F29-%s-NULL vs F29-%s-FULL" % (fam, fam),
                   "T48-F29-%s-NULL" % fam, "T48-F29-%s-FULL" % fam)
    if d:
        failures.append("FULL_LEAP_YEAR moved a rate factor vs the field being unset (family %s)" % fam)

# ======================================================================= EXACTNESS PROBE
print("\n######## EXACTNESS PROBE -- ProgressiveEMICalculator.java:1975 ########\n")
ex = load("%s-exact.json" % PREFIX)
sites = 0
not_bit_identical = 0
rf_match = 0
rf_mismatch = []
for c in ex["captures"]:
    o = c.get("observed")
    if not o or c.get("family") == "EXACTNESS-CANARY":
        continue
    for p in o["probes"]:
        if "note" in p or "error" in p:
            continue
        sites += 1
        if not p["productsBitIdentical"]:
            not_bit_identical += 1
        if p["oracleRateFactorMatchesExactRederivation"]:
            rf_match += 1
        else:
            rf_mismatch.append((c["id"], p["fromDate"], p["dueDate"], p["oracleRateFactor"],
                                p["rederivedRateFactorFromExactProduct"]))
print("probe sites (interest periods crossing a year boundary): %d" % sites)
print("sites where ONE.multiply(f) differs from ONE.multiply(f, mc): %d" % not_bit_identical)
print("sites where the oracle's own rate factor equals setScale(prec, mode)(rate x f): %d" % rf_match)
print("sites where it does NOT (i.e. the arm did not fire there): %d" % len(rf_mismatch))
for m in rf_mismatch:
    print("     %-16s %s..%s  oracle %s   arm-would-give %s" % m)
if sites == 0:
    failures.append("the exactness probe found NO probe site -- it observed nothing")

canary = None
for c in ex["captures"]:
    if c.get("family") == "EXACTNESS-CANARY":
        canary = c
if canary is None:
    failures.append("no vacuity canary in the exactness payload -- a probe that always says "
                    "IDENTICAL is worthless without one")
else:
    legs = canary["observed"]["probes"]
    separated = [l for l in legs if not l["productsBitIdentical"]]
    print("\nVACUITY CANARY (local construction, NOT an oracle output): %d of %d legs SEPARATE"
          % (len(separated), len(legs)))
    for l in legs:
        print("     %-38s bitIdentical=%s   exact=%s  rounded=%s"
              % (l["leg"], l["productsBitIdentical"], l["exactProduct"], l["roundedProduct"]))
    if not separated:
        failures.append("the vacuity canary did NOT separate on any leg -- the exactness "
                        "comparison is incapable of detecting a difference and its "
                        "'IDENTICAL' verdict is worthless")

print("")
for n in notes:
    print("NOTE: " + n)

if failures:
    print("")
    for f in failures:
        print("BREACH: " + f, file=sys.stderr)
    sys.exit(1)
print("\n== analysis PASS -- every stated expectation held")
