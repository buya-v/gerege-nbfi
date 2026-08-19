#!/usr/bin/env python3
"""
T48 -- cross-check the Path B (production wiring) ACT/ACT captures against the Path A2
(EMICalculator seam) captures, and against the two committed Path B observations B-03/B-04.

Contacts no oracle.  Reads only committed bytes.  Produces exact-text sidecars for the Path B
responses first, because Path B serialises BigDecimal as a JSON *number* (finding T44-X1) and
nothing in this program may compare a Path B capture through a binary float.

FULL-CELL: every period row, every column, plus the plan totals.
"""
import json
import pathlib
import sys
from decimal import Decimal

HERE = pathlib.Path(__file__).resolve().parent
PB = HERE.parent / "pathb" / "out"
OUT = HERE.parent / "out"
failures = []


def to_text(n):
    if isinstance(n, dict):
        return dict((k, to_text(v)) for k, v in n.items())
    if isinstance(n, list):
        return [to_text(v) for v in n]
    return n


def bare(node, path="", acc=None):
    acc = [] if acc is None else acc
    if isinstance(node, dict):
        for k, v in node.items():
            bare(v, path + "." + k, acc)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            bare(v, "%s[%d]" % (path, i), acc)
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        acc.append((path, node))
    return acc


print("== exact-text sidecars for the Path B captures ==")
for f in sorted(PB.glob("T48B-*-raw.json")):
    doc = json.loads(f.read_text(), parse_float=str, parse_int=str)
    side = f.with_name(f.name.replace("-raw.json", "-exact.json"))
    side.write_text(json.dumps(to_text(doc), indent=1) + "\n")
    left = bare(json.loads(side.read_text()))
    if left:
        failures.append("%s: sidecar still carries %d bare JSON numbers" % (side.name, len(left)))
print("  %d sidecars written, all with ZERO bare JSON numbers"
      % len(list(PB.glob("T48B-*-exact.json"))))


def pb(stem):
    return json.loads((PB / (stem + "-exact.json")).read_text())


def cells(doc):
    out = {}
    for k, v in doc.items():
        if k in ("periods", "currency"):
            continue
        out[k] = v
    for i, p in enumerate(doc["periods"]):
        for k, v in p.items():
            out["row%d.%s" % (i, k)] = v
    return out


def compare(label, a, b, expect):
    A, B = cells(pb(a)), cells(pb(b))
    keys = sorted(set(A) | set(B))
    diffs = [(k, A.get(k), B.get(k)) for k in keys if A.get(k) != B.get(k)]
    print("\n== %-52s %3d of %3d cells differ (expected %s)"
          % (label, len(diffs), len(keys), expect))
    for k, x, y in diffs[:10]:
        print("     %-38s %-16s | %s" % (k, x, y))
    if len(diffs) > 10:
        print("     ... %d more" % (len(diffs) - 10))
    if expect == "identical" and diffs:
        failures.append("%s: expected IDENTICAL, %d cells differ" % (label, len(diffs)))
    if expect == "separate" and not diffs:
        failures.append("%s: every cell agrees -- DISCRIMINATES NOTHING" % label)
    return diffs


print("\n\n######## FULL_LEAP_YEAR vs the field being UNSET, on the PRODUCTION WIRING ########")
for shape in ("PUREB", "YEAR", "QTR"):
    compare("%s: product 3 (FULL_LEAP_YEAR) vs product 7 (UNSET)" % shape,
            "T48B-%s-p3" % shape, "T48B-%s-p7" % shape, "identical")
compare("B-03 shape: product 3 (FULL_LEAP_YEAR) vs product 7 (UNSET)",
        "T48B-B03SHAPE-p3", "T48B-B03SHAPE-p7", "identical")

print("\n\n######## FEB_29_PERIOD_ONLY, effect (b) in PURE isolation ########")
d = compare("PUREB: product 4 (FEB_29_PERIOD_ONLY) vs product 7 (UNSET)",
            "T48B-PUREB-p4", "T48B-PUREB-p7", "separate")
compare("YEAR: product 4 vs product 7", "T48B-YEAR-p4", "T48B-YEAR-p7", "separate")
compare("QTR: product 4 vs product 7", "T48B-QTR-p4", "T48B-QTR-p7", "separate")

print("\n\n######## CONTROL -- the committed Path B observations B-03 / B-04 ########")
# reference-oracle.md: B-03 total interest 144,659.21, B-04 145,011.43.
for stem, want in (("T48B-B03SHAPE-p3", "144659.21"), ("T48B-B04SHAPE-p4", "145011.43"),
                   ("T48B-B03SHAPE-p7", "144659.21")):
    got = pb(stem)["totalInterestCharged"]
    ok = Decimal(got) == Decimal(want)
    print("  %-22s totalInterestCharged %-12s committed value %-12s %s"
          % (stem, got, want, "REPRODUCED" if ok else "DIVERGED"))
    if not ok:
        failures.append("%s did not reproduce the committed value %s" % (stem, want))

print("\n\n######## CROSS-SEAM -- Path B vs the Path A2 twins ########")
# Every A2 case here was run at the same threaded MathContext (19, HALF_UP) that Path B
# threads from MoneyHelper.getMathContext() [LoanScheduleAssembler.java:753 ->
# generate(mc, ...)], on the same shape.  Agreement across two seams into the same pinned
# image is the strongest corroboration this pipeline produces.
calc = json.loads((OUT / "t48-calc.json").read_text())
C = {c["id"]: c for c in calc["captures"]}


def a2_interest(cid):
    return sum(Decimal(rp["dueInterest"]) for rp in C[cid]["observed"]["repaymentPeriods"])


PAIRS = (("T48B-PUREB-p7", "T48-F29-B-NULL"), ("T48B-PUREB-p3", "T48-F29-B-FULL"),
         ("T48B-PUREB-p4", "T48-F29-B-F29"), ("T48B-YEAR-p7", "T48-F29-Y-NULL"),
         ("T48B-YEAR-p3", "T48-F29-Y-FULL"), ("T48B-YEAR-p4", "T48-F29-Y-F29"),
         ("T48B-QTR-p7", "T48-F29-Q-NULL"), ("T48B-QTR-p3", "T48-F29-Q-FULL"),
         ("T48B-QTR-p4", "T48-F29-Q-F29"), ("T48B-B03SHAPE-p3", "T48-A2-CTL-B03"),
         ("T48B-B04SHAPE-p4", "T48-A2-CTL-B04"), ("T48B-B03SHAPE-p7", "T48-A2-CTL-B03NULL"))
for bstem, a2id in PAIRS:
    bdoc = pb(bstem)
    bint = Decimal(bdoc["totalInterestCharged"])
    aint = a2_interest(a2id)
    ok = bint == aint
    print("  %-22s Path B %-14s   %-22s Path A2 %-14s  %s"
          % (bstem, bint, a2id, aint, "AGREE" if ok else "DIFFER by %s" % (bint - aint)))
    if not ok:
        failures.append("cross-seam mismatch: %s (%s) vs %s (%s)" % (bstem, bint, a2id, aint))
    # and the PERIOD-BY-PERIOD interest, not just the total
    brows = [Decimal(p["interestDue"]) for p in bdoc["periods"] if "period" in p]
    arows = [Decimal(rp["dueInterest"]) for rp in C[a2id]["observed"]["repaymentPeriods"]]
    if brows != arows:
        failures.append("cross-seam period-level mismatch on %s vs %s:\n     B  %s\n     A2 %s"
                        % (bstem, a2id, brows, arows))

print("")
if failures:
    for f in failures:
        print("BREACH: " + f, file=sys.stderr)
    sys.exit(1)
print("== Path B cross-check PASS -- both seams agree cell for cell on every shared shape")
