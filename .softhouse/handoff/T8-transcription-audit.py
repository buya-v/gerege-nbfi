#!/usr/bin/env python3
"""T8-promote transcription audit.

Independent of T8-promote-vectors.py: re-reads the capture and the promoted vector
files and compares EVERY cell, using a separately-written minor-unit converter. Its
job is to catch a slip in the promotion script, so it must not import from it.
"""
import json
import os
import sys
from fractions import Fraction

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAP = json.load(open(os.path.join(ROOT, ".softhouse", "capture", "out",
                                  "capture-prod3b-raw.json")),
                parse_float=str, parse_int=str)
CASES = {c["id"]: c for c in CAP["captures"]}


def to_minor(text):
    """Independent converter: exact rational scaling by 100, must land on an integer."""
    f = Fraction(text) * 100
    assert f.denominator == 1, "scale > 2 in %r" % text
    return str(f.numerator)


def iso_to_obj(iso):
    y, m, d = iso.split("-")
    return {"year": int(y), "month": int(m), "day": int(d)}


def audit(path):
    v = json.load(open(path))
    cid = v["provenance"]["capture_case_id"]
    c = CASES[cid]
    inp, obs = c["inputs"], c["observed"]
    checked = failures = 0

    def eq(label, got, want):
        nonlocal checked, failures
        checked += 1
        if got != want:
            failures += 1
            print("    MISMATCH %-46s vector=%r capture=%r" % (label, got, want))

    eq("request.schedule_start_date", v["request"]["schedule_start_date"],
       iso_to_obj(inp["scheduleGenerationStartDate"]))
    eq("request.disbursements[0].date", v["request"]["disbursements"][0]["date"],
       iso_to_obj(inp["disbursementDate"]))
    eq("request.disbursements[0].amount_minor",
       v["request"]["disbursements"][0]["amount_minor"], to_minor(inp["disbursementAmount"]))
    eq("request.number_of_repayments", v["request"]["number_of_repayments"],
       int(inp["numberOfRepayments"]))
    eq("request.repayment_every", v["request"]["repayment_every"], int(inp["repaymentFrequency"]))
    eq("request.currency.code", v["request"]["currency"]["code"], inp["currencyCode"].upper())
    eq("request.currency.minor_unit_digits", v["request"]["currency"]["minor_unit_digits"],
       int(inp["currencyDecimalPlaces"]))
    r = Fraction(inp["annualNominalInterestRate"]) / 100
    eq("request.annual_nominal_interest_rate", v["request"]["annual_nominal_interest_rate"],
       {"numerator": r.numerator, "denominator": r.denominator})
    eq("oracle.threaded_mathcontext.precision", v["oracle"]["threaded_mathcontext"]["precision"],
       int(inp["mathContextPrecision"]))
    eq("oracle.threaded_mathcontext.rounding_mode",
       v["oracle"]["threaded_mathcontext"]["rounding_mode"], inp["mathContextRoundingMode"])
    eq("oracle.ambient_mathcontext.precision", v["oracle"]["ambient_mathcontext"]["precision"],
       int(inp["ambientMoneyHelperPrecision"]))
    eq("oracle.ambient_mathcontext.rounding_mode",
       v["oracle"]["ambient_mathcontext"]["rounding_mode"], inp["ambientMoneyHelperRoundingMode"])
    eq("expect.observed_total_interest_minor", v["expect"]["observed_total_interest_minor"],
       to_minor(obs["totalInterestAmount"]))

    eq("row count", len(v["expect"]["periods"]), len(obs["periods"]))
    for i, (row, p) in enumerate(zip(v["expect"]["periods"], obs["periods"])):
        pre = "periods[%d]" % i
        unrec = set(row["unrecorded_fields"])
        eq(pre + ".kind", row["kind"], p["type"])
        eq(pre + ".from_date", row["from_date"], iso_to_obj(p["periodFromDate"]))
        eq(pre + ".due_date", row["due_date"], iso_to_obj(p["dueDate"]))
        eq(pre + ".principal_minor", row["principal_minor"], to_minor(p["principal"]))
        eq(pre + ".principal_major_text", row["principal_major_text"], p["principal"])
        eq(pre + ".outstanding_principal_minor", row["outstanding_principal_minor"],
           to_minor(p["balance"]))
        eq(pre + ".outstanding_principal_major_text", row["outstanding_principal_major_text"],
           p["balance"])
        if "periodNumber" in p:
            eq(pre + ".installment_number", row["installment_number"], int(p["periodNumber"]))
            assert "installment_number" not in unrec, pre
        else:
            eq(pre + ".installment_number UNRECORDED", "installment_number" in unrec, True)
        if "interest" in p:
            eq(pre + ".interest_minor", row["interest_minor"], to_minor(p["interest"]))
            eq(pre + ".interest_major_text", row["interest_major_text"], p["interest"])
            assert "interest_minor" not in unrec, pre
        else:
            eq(pre + ".interest_minor UNRECORDED", "interest_minor" in unrec, True)
            eq(pre + ".interest_minor EMPTY", row["interest_minor"], "")
        if "total" in p:
            eq(pre + ".observed_total_due_minor", row["observed_total_due_minor"],
               to_minor(p["total"]))
        else:
            eq(pre + ".observed_total_due_minor NULL", row["observed_total_due_minor"], None)
        # the oracle's own split must reproduce its own total
        if "total" in p and "interest" in p:
            eq(pre + " split sums to observed total",
               int(to_minor(p["principal"])) + int(to_minor(p["interest"])),
               int(to_minor(p["total"])))

    # whole-schedule invariants over the TRANSCRIBED expectation
    adv = sum(int(r["principal_minor"]) for r in v["expect"]["periods"] if r["kind"] == "DISBURSEMENT")
    rep = sum(int(r["principal_minor"]) for r in v["expect"]["periods"]
              if r["kind"] in ("REPAYMENT", "DOWN_PAYMENT"))
    eq("invariant principal_portions_sum_to_disbursed", rep, adv)
    eq("invariant principal_amortizes_to_zero",
       v["expect"]["periods"][-1]["outstanding_principal_minor"], "0")
    interest_sum = sum(int(r["interest_minor"]) for r in v["expect"]["periods"]
                       if r["interest_minor"] != "")
    eq("invariant interest column sums to observed total interest",
       str(interest_sum), v["expect"]["observed_total_interest_minor"])
    bal, seen = 0, False
    for i, r in enumerate(v["expect"]["periods"]):
        if r["kind"] == "DISBURSEMENT":
            seen = True
            eq("invariant balance_roll_forward disb row %d" % i,
               r["outstanding_principal_minor"], r["principal_minor"])
            bal += int(r["principal_minor"])
        elif r["kind"] == "REPAYMENT":
            if not seen:
                eq("invariant pre-disbursement row %d all zero" % i,
                   (r["principal_minor"], r["interest_minor"], r["outstanding_principal_minor"]),
                   ("0", "0", "0"))
                continue
            want = max(0, bal - int(r["principal_minor"]))
            eq("invariant balance_roll_forward row %d" % i,
               r["outstanding_principal_minor"], str(want))
            bal = int(r["outstanding_principal_minor"])
    def key(dt):
        return (dt["year"], dt["month"], dt["day"])
    prev = None
    for i, r in enumerate(v["expect"]["periods"]):
        if r["kind"] != "REPAYMENT":
            continue
        eq("invariant window non-empty row %d" % i, key(r["from_date"]) < key(r["due_date"]), True)
        if prev is not None:
            eq("invariant contiguous row %d" % i, key(r["from_date"]), prev)
            eq("invariant strictly increasing row %d" % i, key(r["due_date"]) > prev, True)
        prev = key(r["due_date"])
    return checked, failures


def main():
    targets = sys.argv[1:]
    total = bad = 0
    for t in targets:
        path = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule", t)
        print("AUDIT %s" % t)
        c, f = audit(path)
        print("   %d cells compared, %d mismatches" % (c, f))
        total += c
        bad += f
    print("TOTAL %d cells compared, %d mismatches" % (total, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
