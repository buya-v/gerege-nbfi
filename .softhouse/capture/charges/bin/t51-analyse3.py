#!/usr/bin/env python3
"""
T51 -- analysis of capture passes 4, 5 and 6: the SECOND reader of the aliased slot.
Contacts no oracle; reads only committed bytes.  Run t51-analyse.py first (it writes the
sidecars for every T51-*-raw.json).
"""
import json
import pathlib
import sys

O = pathlib.Path(__file__).resolve().parents[1] / "out" / "t51"
failures = []


def load_exact(stem):
    return json.loads((O / (stem + "-exact.json")).read_text())


def cells(doc):
    if "periods" not in doc:
        return {"__http__": doc.get("httpStatusCode"),
                "__msg__": "; ".join(e.get("developerMessage", "") for e in doc.get("errors", []))}
    out = {k: v for k, v in doc.items() if k not in ("periods", "currency")}
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
    if expect == "separate" and not diffs:
        failures.append("%s: EVERY CELL AGREES -- discriminates nothing" % label)
    if expect == "identical" and diffs:
        failures.append("%s: expected IDENTICAL, %d cells differ" % (label, len(diffs)))
    if not diffs:
        print("     -> every cell agrees; on its own this comparison discriminates NOTHING.")
    return diffs


print("#" * 86)
print("# ITEM 1, passes 4-6 -- the SECOND reader of the aliased slot")
print("#" * 86)
print("""
ProgressiveEMICalculator reads the slot in exactly two places on main sources:
  * :1579  getFractionPeriodDueDateForEndOfYear      -- covered by passes 1 and 2;
  * :194   buildLoanApplicationTerms, reached only from addFullTermTrancheDisbursement [:155],
           guarded by isAllowFullTermForTranche() && numberOfRepayments > 0 &&
           action == DISBURSEMENT [:140-143].
Pass 4 tried the request-level override on a product that does not allow it; pass 5 created a
matched product pair that does; pass 6 turned the guard off on the SAME products.
""")

print("-- pass 4: the request-level override alone --")
for stem in ("T51-FTT-ON-P1", "T51-FTT-ON-P2"):
    d = load_exact(stem)
    print("   %-18s HTTP %s : %s" % (stem, d.get("httpStatusCode"),
                                     "; ".join(e.get("developerMessage", "") for e in d.get("errors", []))))
    for e in d.get("errors", []):
        for a in e.get("args", []):
            if a.get("value"):
                print("        args: %s" % a["value"])

print("\n-- passes 5 and 6: products 20 and 21, allow_full_term_for_tranche = t, "
      "differing only in interest_recognition_on_disbursement_date --")
compare("DID THE FULL-TERM-TRANCHE ARM FIRE?  product 20 with the guard ON vs the SAME "
        "product with allowFullTermForTranche=false in the request",
        "T51-FTTP-P4", "T51-FTTPOFF-P4", "separate")
compare("the same control on product 21", "T51-FTTP-P5", "T51-FTTPOFF-P5", "separate")
compare("WITH THE ARM FIRING: product 20 (flag TRUE) vs product 21 (flag FALSE)",
        "T51-FTTP-P4", "T51-FTTP-P5", "observe")
compare("with the arm OFF: product 20 (flag TRUE) vs product 21 (flag FALSE)",
        "T51-FTTPOFF-P4", "T51-FTTPOFF-P5", "observe")
compare("cross-check: the arm-off result on the tranche products vs the same request on "
        "products 17/18 (not multi-disburse)",
        "T51-FTTPOFF-P4", "T51-FTT-OFF-P1", "observe")

print("\n-- what the full-term-tranche arm actually did, cell by cell --")
for stem in ("T51-FTTPOFF-P4", "T51-FTTP-P4"):
    d = load_exact(stem)
    print("   %-18s loanTermInDays=%-6s totalInterestCharged=%-12s totalRepaymentExpected=%s"
          % (stem, d["loanTermInDays"], d["totalInterestCharged"], d["totalRepaymentExpected"]))
    for p in d["periods"]:
        if "period" not in p:
            print("        disb %-12s principalDisbursed %s"
                  % ("-".join(p["dueDate"]), p.get("principalDisbursed")))
        else:
            print("        p%-3s %-12s -> %-12s days %-4s principal %-14s interest %s"
                  % (p["period"], "-".join(p["fromDate"]), "-".join(p["dueDate"]),
                     p.get("daysInPeriod"), p.get("principalDue"), p.get("interestDue")))

print("\n")
if failures:
    print("RESULT: %d PROBLEM(S)" % len(failures))
    for p in failures:
        print("  ! " + p)
    sys.exit(1)
print("RESULT: every comparison above published its own differing-cell count.")
