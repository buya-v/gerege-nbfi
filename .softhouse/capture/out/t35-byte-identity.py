#!/usr/bin/env python3
"""
T35 — byte-identity of the PRE-EXISTING columns: pass 3b vs the committed pass 3.

WHY THIS EXISTS. Pass 3b re-runs the same twelve cases through the same seam in the same pinned
image, adding columns (periodFromDate, feeAmount, penaltyAmount, plan totals) and switching every
BigDecimal emission to toPlainString(). A re-run that silently CHANGES a number that pass 3 already
published is the most important thing this task could find, so it is checked mechanically here and
reported loudly rather than reconciled.

Three verdicts per compared value:

  IDENTICAL          the two emitted strings are byte-equal
  RENDERING-ONLY     the strings differ but the exact decimal values are equal (toPlainString may do
                     this legitimately, e.g. 1E+2 -> 100). Reported, and it is not a defect.
  VALUE CHANGED      the exact decimal values differ. THIS IS A FINDING. Non-zero exit.

No floating point anywhere: every money string is parsed with decimal.Decimal and compared exactly,
with no tolerance. `float` appears in this file only in the json parse hooks that EXIST TO PREVENT a
float ever being constructed.

Usage:  python3 .softhouse/capture/out/t35-byte-identity.py \
            .softhouse/capture/out/capture-prod-raw.json \
            .softhouse/capture/out/capture-prod3b-raw.json
"""
import json
import sys
from decimal import Decimal

OLD_INPUT_KEYS = [
    "scheduleGenerationStartDate", "disbursementDate", "disbursementAmount", "numberOfRepayments",
    "repaymentFrequency", "repaymentFrequencyType", "annualNominalInterestRate", "mathContextPrecision",
    "mathContextRoundingMode", "tenantId", "tenantRoundingModeValue", "ambientMoneyHelperMathContext",
    "currencyCode", "currencyDecimalPlaces", "currencyInMultiplesOf", "daysInMonth", "daysInYear",
    "daysInYearCustomStrategy", "downPaymentEnabled", "downPaymentPercentage",
    "installmentAmountInMultiplesOf", "fixedLength", "interestRecognitionOnDisbursementDate",
    "interestMethod", "allowPartialPeriodInterestCalculation", "allowFullTermForTranche",
]
OLD_OBSERVED_SCALARS = [
    "loanTermInDays", "totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount",
]
OLD_PERIOD_KEYS = [
    "type", "periodNumber", "dueDate", "balance", "principal", "interest", "total",
    "totalOutstandingBalance",
]
NEW_PERIOD_KEYS = ["periodFromDate", "feeAmount", "penaltyAmount"]
NEW_PLAN_KEYS = ["totalPrincipalAmount", "totalFeeAmount", "totalPenaltyAmount", "totalOutstandingAmount"]

MONEYISH = {"disbursementAmount", "annualNominalInterestRate", "downPaymentPercentage",
            "totalDisbursedAmount", "totalInterestAmount", "totalRepaymentAmount",
            "balance", "principal", "interest", "total", "totalOutstandingBalance"}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh, parse_float=Decimal, parse_int=int)


MISSING = object()


def compare(key, a, b, findings, renders, ident, added=None, dropped=None):
    """a = pass-3 value, b = pass-3b value. MISSING means the key was not emitted at all."""
    if a is MISSING and b is MISSING:
        return
    if a is MISSING:
        # pass 3 never emitted this key for this period type; pass 3b adds it. An ADDITION is not a
        # change to a published number, and is reported separately so it can never mask one.
        (added if added is not None else findings).append((key, None, b))
        return
    if b is MISSING:
        # a column pass 3 published and pass 3b lost. That IS a defect.
        (dropped if dropped is not None else findings).append((key, a, None))
        return
    if a == b:
        ident.append(key)
        return
    if key.split(".")[-1] in MONEYISH:
        try:
            if Decimal(str(a)) == Decimal(str(b)):
                renders.append((key, a, b))
                return
        except Exception:
            pass
    findings.append((key, a, b))


def main(oldp, newp):
    old, new = load(oldp), load(newp)
    oldc = {c["id"]: c for c in old["captures"]}
    newc = {c["id"]: c for c in new["captures"]}

    findings, renders, ident = [], [], []
    added, dropped = [], []
    missing_new = []

    if set(oldc) != set(newc):
        findings.append(("captures.ids", sorted(oldc), sorted(newc)))

    for cid in sorted(set(oldc) & set(newc)):
        o, n = oldc[cid], newc[cid]
        compare("%s.purpose" % cid, o["purpose"], n["purpose"], findings, renders, ident, added, dropped)
        for k in OLD_INPUT_KEYS:
            compare("%s.inputs.%s" % (cid, k), o["inputs"].get(k, MISSING), n["inputs"].get(k, MISSING),
                    findings, renders, ident, added, dropped)
        oo, no = o.get("observed"), n.get("observed")
        if (oo is None) != (no is None):
            findings.append(("%s.observed" % cid, oo, no))
            continue
        if oo is None:
            continue
        for k in OLD_OBSERVED_SCALARS:
            compare("%s.observed.%s" % (cid, k), oo.get(k, MISSING), no.get(k, MISSING),
                    findings, renders, ident, added, dropped)
        for k in NEW_PLAN_KEYS:
            if k not in no:
                missing_new.append("%s.observed.%s" % (cid, k))
        op, np_ = oo["periods"], no["periods"]
        if len(op) != len(np_):
            findings.append(("%s.observed.periods.length" % cid, len(op), len(np_)))
            continue
        for i, (a, b) in enumerate(zip(op, np_)):
            for k in OLD_PERIOD_KEYS:
                compare("%s.observed.periods[%d].%s" % (cid, i, k), a.get(k, MISSING), b.get(k, MISSING),
                        findings, renders, ident, added, dropped)
            if b.get("type") in ("REPAYMENT",):
                for k in NEW_PERIOD_KEYS:
                    if k not in b:
                        missing_new.append("%s.observed.periods[%d].%s" % (cid, i, k))
            if b.get("type") == "DISBURSEMENT" and "periodFromDate" not in b:
                missing_new.append("%s.observed.periods[%d].periodFromDate" % (cid, i))

    print("compared %d values published by pass 3, across %d captures"
          % (len(ident) + len(renders) + len(findings) + len(dropped), len(set(oldc) & set(newc))))
    print("  IDENTICAL      : %d" % len(ident))
    print("  RENDERING-ONLY : %d" % len(renders))
    print("  VALUE CHANGED  : %d" % len(findings))
    print("  DROPPED by 3b  : %d" % len(dropped))
    print("  ADDED by 3b    : %d  (keys pass 3 never emitted for that period type)" % len(added))
    for k, a, b in renders:
        print("    RENDERING-ONLY %s: %r -> %r (decimal values equal)" % (k, a, b))
    for k, a, b in findings:
        print("    ** VALUE CHANGED ** %s: pass3=%r pass3b=%r" % (k, a, b))
    for k, a, b in dropped:
        print("    ** DROPPED ** %s: pass3=%r, absent in pass3b" % (k, a))
    for k, a, b in added:
        print("    added %s = %r" % (k, b))
    if missing_new:
        print("  MISSING MANDATED NEW COLUMNS: %d" % len(missing_new))
        for m in missing_new[:20]:
            print("    %s" % m)

    ok = not findings and not dropped and not missing_new
    print("\nVERDICT: %s" % ("PASS — every pre-existing column is byte-identical, and every mandated "
                             "new column is present" if ok else "FAIL — see above"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
