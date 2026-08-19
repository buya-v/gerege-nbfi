#!/usr/bin/env python3
"""T57 transcription audit.

INDEPENDENT of T57-promote-emi-vectors.py: it re-reads the pass-3c capture and the promoted
vector files and compares EVERY cell. It must not import from the promotion script, and its
minor-unit converter is written a THIRD way on purpose -- pure integer string splicing, where
the promotion script uses a textual split-and-pad and T8's auditor uses Fraction arithmetic.
Three independent converters agreeing is the point.

    python3 .softhouse/handoff/T57-transcription-audit.py <vector-file> [<vector-file> ...]

Exits non-zero on any mismatch.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAPPATH = os.path.join(ROOT, ".softhouse", "capture", "out", "capture-prod3c-raw.json")
CAP = json.load(open(CAPPATH), parse_float=str, parse_int=str)
CASES = {c["id"]: c for c in CAP["captures"]}


def to_minor(text):
    """Third independent converter: integer string splicing, no Decimal and no Fraction.
    Rejects anything that is not exactly two decimal places or fewer."""
    assert isinstance(text, str) and text, repr(text)
    neg = text.startswith("-")
    assert not neg, "negative money in %r" % text
    head, dot, tail = text.partition(".")
    assert head.isdigit(), repr(text)
    if dot:
        assert tail.isdigit(), repr(text)
        assert len(tail) <= 2 or tail[2:].count("0") == len(tail[2:]), "scale > 2 in %r" % text
        tail = (tail + "00")[:2]
    else:
        tail = "00"
    return str(int(head + tail))


def iso_to_obj(iso):
    y, m, d = iso.split("-")
    return {"year": int(y), "month": int(m), "day": int(d)}


def audit(path):
    v = json.load(open(path))
    cid = v["provenance"]["capture_case_id"]
    assert v["provenance"]["capture_ref"].endswith("capture-prod3c-raw.json"), path
    c = CASES[cid]
    inp, obs = c["inputs"], c["observed"]
    checked = failures = 0

    def eq(label, got, want):
        nonlocal checked, failures
        checked += 1
        if got != want:
            failures += 1
            print("    MISMATCH %-52s vector=%r capture=%r" % (label, got, want))

    # ---- provenance and pins -------------------------------------------------------------
    import hashlib
    eq("provenance.capture_sha256",
       v["provenance"]["capture_sha256"], hashlib.sha256(open(CAPPATH, "rb").read()).hexdigest())
    eq("oracle.captured_at", v["oracle"]["captured_at"], CAP["attestation"]["capturedAtUtc"])
    eq("oracle.fineract_commit", v["oracle"]["fineract_commit"],
       CAP["attestation"]["fineract"]["gitCommitId"])
    eq("class is parity", v["class"], "parity")

    # ---- request -------------------------------------------------------------------------
    eq("request.schedule_start_date", v["request"]["schedule_start_date"],
       iso_to_obj(inp["scheduleGenerationStartDate"]))
    eq("request.disbursements[0].date", v["request"]["disbursements"][0]["date"],
       iso_to_obj(inp["disbursementDate"]))
    eq("request.disbursements[0].amount_minor",
       v["request"]["disbursements"][0]["amount_minor"], to_minor(inp["disbursementAmount"]))
    eq("request.number_of_repayments", v["request"]["number_of_repayments"],
       int(inp["numberOfRepayments"]))
    eq("request.repayment_every", v["request"]["repayment_every"], int(inp["repaymentFrequency"]))
    eq("request.repayment_frequency_unit", v["request"]["repayment_frequency_unit"],
       inp["repaymentFrequencyType"])
    eq("request.currency.code", v["request"]["currency"]["code"], inp["currencyCode"].upper())
    eq("request.currency.minor_unit_digits", v["request"]["currency"]["minor_unit_digits"],
       int(inp["currencyDecimalPlaces"]))
    eq("request.interest_method", v["request"]["interest_method"], inp["interestMethod"])
    # rate: percent text -> exact rational, by integer arithmetic only
    ph, _, pt = inp["annualNominalInterestRate"].partition(".")
    num, den = int(ph + pt), 100 * (10 ** len(pt))
    g = __import__("math").gcd(num, den)
    eq("request.annual_nominal_interest_rate", v["request"]["annual_nominal_interest_rate"],
       {"numerator": num // g, "denominator": den // g})
    eq("oracle.threaded_mathcontext.precision", v["oracle"]["threaded_mathcontext"]["precision"],
       int(inp["mathContextPrecision"]))
    eq("oracle.threaded_mathcontext.rounding_mode",
       v["oracle"]["threaded_mathcontext"]["rounding_mode"], inp["mathContextRoundingMode"])
    eq("oracle.ambient_mathcontext.precision", v["oracle"]["ambient_mathcontext"]["precision"],
       int(inp["ambientMoneyHelperPrecision"]))
    eq("oracle.ambient_mathcontext.rounding_mode",
       v["oracle"]["ambient_mathcontext"]["rounding_mode"], inp["ambientMoneyHelperRoundingMode"])

    # ---- expect --------------------------------------------------------------------------
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
            eq(pre + ".installment_number NOT unrecorded", "installment_number" in unrec, False)
        else:
            eq(pre + ".installment_number UNRECORDED", "installment_number" in unrec, True)
        if "interest" in p:
            eq(pre + ".interest_minor", row["interest_minor"], to_minor(p["interest"]))
            eq(pre + ".interest_major_text", row["interest_major_text"], p["interest"])
            eq(pre + ".interest_minor NOT unrecorded", "interest_minor" in unrec, False)
        else:
            eq(pre + ".interest_minor UNRECORDED", "interest_minor" in unrec, True)
            eq(pre + ".interest_minor EMPTY", row["interest_minor"], "")
        if "total" in p:
            eq(pre + ".observed_total_due_minor", row["observed_total_due_minor"],
               to_minor(p["total"]))
            if "interest" in p:
                eq(pre + " oracle split sums to oracle total",
                   int(to_minor(p["principal"])) + int(to_minor(p["interest"])),
                   int(to_minor(p["total"])))
        else:
            eq(pre + ".observed_total_due_minor NULL", row["observed_total_due_minor"], None)

    # ---- invariants over the TRANSCRIBED expectation --------------------------------------
    adv = sum(int(r["principal_minor"]) for r in v["expect"]["periods"] if r["kind"] == "DISBURSEMENT")
    rep = sum(int(r["principal_minor"]) for r in v["expect"]["periods"]
              if r["kind"] in ("REPAYMENT", "DOWN_PAYMENT"))
    eq("invariant principal_portions_sum_to_disbursed", rep, adv)
    eq("invariant principal_amortizes_to_zero",
       v["expect"]["periods"][-1]["outstanding_principal_minor"], "0")
    isum = sum(int(r["interest_minor"]) for r in v["expect"]["periods"] if r["interest_minor"] != "")
    eq("invariant interest column sums to observed total interest",
       str(isum), v["expect"]["observed_total_interest_minor"])
    bal, seen = 0, False
    for i, r in enumerate(v["expect"]["periods"]):
        if r["kind"] == "DISBURSEMENT":
            seen = True
            eq("invariant balance_roll_forward disb row %d" % i,
               r["outstanding_principal_minor"], r["principal_minor"])
            bal += int(r["principal_minor"])
        elif r["kind"] == "REPAYMENT" and seen:
            eq("invariant balance_roll_forward row %d" % i,
               r["outstanding_principal_minor"], str(max(0, bal - int(r["principal_minor"]))))
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

    # ---- graded_against shape --------------------------------------------------------------
    eq("graded_against non-empty", len(v["graded_against"]) > 0, True)
    ids = [cf["id"] for cf in v["graded_against"]]
    eq("EMI-SMOOTHING-LOOP-OMITTED present", "EMI-SMOOTHING-LOOP-OMITTED" in ids, True)
    for cf in v["graded_against"]:
        eq("graded_against[%s] kind is money" % cf["id"], cf.get("kind", "money"), "money")
        eq("graded_against[%s] margin > 0" % cf["id"], int(cf["margin_minor"]) > 0, True)
        eq("graded_against[%s] divergent_cells empty" % cf["id"], cf.get("divergent_cells", []), [])
        eq("graded_against[%s] evidence non-empty" % cf["id"], bool(cf["evidence"].strip()), True)

    return checked, failures


def main():
    total = bad = 0
    for t in sys.argv[1:]:
        path = t if os.path.isabs(t) else os.path.join(ROOT, ".softhouse", "vectors", "loanschedule", t)
        print("AUDIT %s" % os.path.basename(path))
        c, f = audit(path)
        print("   %d cells compared, %d mismatches" % (c, f))
        total += c
        bad += f
    print("TOTAL %d cells compared, %d mismatches" % (total, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
