#!/usr/bin/env python3
"""T58 — independent transcription audit of the sixteen vectors this task promoted.

WRITTEN AGAINST THE VECTORS, NOT WITH THEM. This script does not import, call or
share a line with T58-promote-vectors.py. Its major->minor converter is a second,
deliberately different implementation -- `decimal.Decimal` with the exponent read
off `as_tuple()` and the coefficient scaled by integer arithmetic, rather than the
promoter's string padding. Two independent converters agreeing is the point; one
converter checking its own output would be worth nothing.

For every promoted vector it re-derives, from the referenced capture alone:

  * the request (dates, principal, term, rate as an exact rational, currency,
    MathContext) against what the vector states;
  * every money cell of every row, in minor units;
  * every *_major_text cell against the oracle's own emitted characters;
  * every date cell;
  * the row kinds, installment numbers, per-row observed total and the plan-level
    observed total interest;
  * that every cell the vector marks `unrecorded_fields` really is absent from the
    capture, and that no cell present in the capture was silently dropped.

It also runs a float scan over the whole vector store: no JSON NUMBER token
anywhere may contain '.', 'e' or 'E'.

    python3 .softhouse/handoff/T58-transcription-audit.py
"""

import json
import os
import re
import sys
from decimal import Decimal
from fractions import Fraction

VEC_DIR = ".softhouse/vectors/loanschedule"
STORE = ".softhouse/vectors"

# vector case_id -> (capture file, capture case id)
AUDIT = {
    "P-DRIFT-A": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-A"),
    "P-DRIFT-B": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-B"),
    "P-DRIFT-C": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-C"),
    "P-DRIFT-D": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-D"),
    "P-DRIFT-E": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-E"),
    "P-DRIFT-F": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-F"),
    "P-DRIFT-G": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-G"),
    "P-DRIFT-H": (".softhouse/capture/out/capture-prod3e-raw.json", "P-DRIFT-H"),
    "P-ME-A": (".softhouse/capture/out/capture-prod3e-raw.json", "P-ME-A"),
    "P-ME-B": (".softhouse/capture/out/capture-prod3e-raw.json", "P-ME-B"),
    "P-ME-C": (".softhouse/capture/out/capture-prod3e-raw.json", "P-ME-C"),
    "P-ME-D": (".softhouse/capture/out/capture-prod3e-raw.json", "P-ME-D"),
    "P-LAT-Q0a": (".softhouse/capture/out/capture-prod3e-raw.json", "P-LAT-Q0a"),
    "P-LAT-MID": (".softhouse/capture/out/capture-prod3e-raw.json", "P-LAT-MID"),
    "P-RND-S1-21021587pt50-6x21pt6pct":
        (".softhouse/capture/out/capture-prod3d-raw.json", "P-RND-21021587PT50-6x21PT6"),
    "P-RND-S2-3139845pt86-6x7pct":
        (".softhouse/capture/out/capture-prod3d-raw.json", "P-RND-3139845PT86-6x7PT0"),
}

MONEY = [("principal_minor", "principal_major_text", "principal"),
         ("interest_minor", "interest_major_text", "interest"),
         ("outstanding_principal_minor", "outstanding_principal_major_text", "balance")]


def to_minor(text, digits):
    """A SECOND, INDEPENDENT converter. Decimal -> exact integer minor units.

    Deliberately not the promoter's algorithm: read the coefficient and exponent
    off Decimal.as_tuple() and scale by integer multiplication, refusing anything
    that would need a division. No float is constructed at any point -- Decimal
    parses the characters directly.
    """
    d = Decimal(text)
    sign, digs, exp = d.as_tuple()
    coeff = 0
    for x in digs:
        coeff = coeff * 10 + x
    shift = exp + digits          # how many powers of ten to multiply by
    if shift >= 0:
        v = coeff * (10 ** shift)
    else:
        div = 10 ** (-shift)
        if coeff % div:
            raise ValueError("%r carries a significant digit beyond scale %d" % (text, digits))
        v = coeff // div
    return -v if sign else v


def to_rate(text):
    """'21.6' percent -> the exact lowest-terms Fraction 27/125, via Fraction(Decimal)."""
    return Fraction(Decimal(text)) / 100


def cap_from(row):
    return row.get("periodFromDate") or row.get("fromDate")


def float_scan():
    """No JSON NUMBER token in the store may carry '.', 'e' or 'E'.

    Strings are stripped first, so a decimal inside a quoted *_major_text or a
    prose evidence field is not a false positive -- the rule is about NUMBERS.
    """
    bad = []
    files = 0
    for dirpath, _, names in os.walk(STORE):
        for n in sorted(names):
            if not n.endswith(".json"):
                continue
            p = os.path.join(dirpath, n)
            files += 1
            raw = open(p, encoding="utf-8").read()
            # remove every JSON string literal, escapes included
            stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', raw)
            for m in re.finditer(r'-?\d[\d.eE+-]*', stripped):
                tok = m.group(0)
                if any(c in tok for c in ".eE"):
                    bad.append("%s: bare number token %r" % (p, tok))
    return files, bad


def main():
    problems = []
    checked = matched = 0
    rows = 0

    caps = {}
    for path, _ in AUDIT.values():
        if path not in caps:
            caps[path] = {c["id"]: c for c in json.load(open(path))["captures"]}

    by_case = {}
    for n in sorted(os.listdir(VEC_DIR)):
        if not n.endswith(".json"):
            continue
        v = json.load(open(os.path.join(VEC_DIR, n)))
        by_case[v["case_id"]] = (n, v)

    for case_id, (cap_path, cap_id) in sorted(AUDIT.items()):
        if case_id not in by_case:
            problems.append("%s: no vector file carries this case_id" % case_id)
            continue
        fname, v = by_case[case_id]
        cap = caps[cap_path][cap_id]
        ci, co = cap["inputs"], cap["observed"]
        digits = ci["currencyDecimalPlaces"]

        def chk(what, got, want):
            nonlocal checked, matched
            checked += 1
            if got == want:
                matched += 1
            else:
                problems.append("%s (%s) %s: vector %r, capture %r" % (case_id, fname, what, got, want))

        # --- provenance points at the file and case this audit read -------------
        chk("provenance.capture_ref", v["provenance"]["capture_ref"], cap_path)
        chk("provenance.capture_case_id", v["provenance"]["capture_case_id"], cap_id)

        # --- request -----------------------------------------------------------
        r = v["request"]
        sd = ci["scheduleGenerationStartDate"].split("-")
        chk("schedule_start_date", r["schedule_start_date"],
            {"year": int(sd[0]), "month": int(sd[1]), "day": int(sd[2])})
        dd = ci["disbursementDate"].split("-")
        chk("disbursement.date", r["disbursements"][0]["date"],
            {"year": int(dd[0]), "month": int(dd[1]), "day": int(dd[2])})
        chk("disbursement.amount_minor", r["disbursements"][0]["amount_minor"],
            str(to_minor(ci["disbursementAmount"], digits)))
        chk("number_of_repayments", r["number_of_repayments"], ci["numberOfRepayments"])
        chk("repayment_every", r["repayment_every"],
            ci.get("repaymentEvery", ci.get("repaymentFrequency")))
        chk("repayment_frequency_unit", r["repayment_frequency_unit"], ci["repaymentFrequencyType"])
        chk("interest_method", r["interest_method"], ci["interestMethod"])
        chk("currency.code", r["currency"]["code"], ci["currencyCode"].upper())
        chk("currency.minor_unit_digits", r["currency"]["minor_unit_digits"], digits)
        chk("rounding.significant_digits", r["rounding"]["significant_digits"], ci["mathContextPrecision"])
        chk("rounding.mode", r["rounding"]["mode"], ci["mathContextRoundingMode"])
        f = to_rate(ci["annualNominalInterestRate"])
        chk("annual_nominal_interest_rate", r["annual_nominal_interest_rate"],
            {"numerator": f.numerator, "denominator": f.denominator})
        chk("day_count (DAYS_30 + DAYS_360)", r["day_count"],
            "FIXED_30_360" if (ci["daysInMonth"], ci["daysInYear"]) == ("DAYS_30", "DAYS_360") else "?")
        chk("oracle.fineract_commit", v["oracle"]["fineract_commit"],
            json.load(open(cap_path)).get("fineractCommit")
            or json.load(open(cap_path))["attestation"]["fineract"]["gitCommitId"])
        chk("oracle.threaded_mathcontext.precision",
            v["oracle"]["threaded_mathcontext"]["precision"], ci["mathContextPrecision"])

        # --- expect ------------------------------------------------------------
        e = v["expect"]
        chk("observed_total_interest_minor", e["observed_total_interest_minor"],
            str(to_minor(co["totalInterestAmount"], digits)))
        chk("row count", len(e["periods"]), len(co["periods"]))

        for i, (row, crow) in enumerate(zip(e["periods"], co["periods"])):
            rows += 1
            tag = "period[%d]" % i
            chk(tag + ".kind", row["kind"], crow["type"])

            cf = cap_from(crow).split("-")
            chk(tag + ".from_date", row["from_date"],
                {"year": int(cf[0]), "month": int(cf[1]), "day": int(cf[2])})
            cd = crow["dueDate"].split("-")
            chk(tag + ".due_date", row["due_date"],
                {"year": int(cd[0]), "month": int(cd[1]), "day": int(cd[2])})

            unrec = row["unrecorded_fields"]
            if crow.get("periodNumber") is None:
                if "installment_number" not in unrec:
                    problems.append("%s %s: periodNumber absent from the capture but not "
                                    "withdrawn" % (case_id, tag))
                chk(tag + ".installment_number (normalised, withdrawn)", row["installment_number"], 0)
            else:
                if "installment_number" in unrec:
                    problems.append("%s %s: periodNumber IS recorded but the vector withdraws it"
                                    % (case_id, tag))
                chk(tag + ".installment_number", row["installment_number"], crow["periodNumber"])

            for minor_f, text_f, cap_f in MONEY:
                present = crow.get(cap_f) is not None
                withdrawn = minor_f in unrec
                if present and withdrawn:
                    problems.append("%s %s: %s IS recorded (%r) but the vector withdraws it"
                                    % (case_id, tag, cap_f, crow[cap_f]))
                if not present and not withdrawn:
                    problems.append("%s %s: %s is NOT in the capture and is not withdrawn"
                                    % (case_id, tag, cap_f))
                if not present:
                    chk(tag + "." + minor_f + " (withdrawn, empty)", row[minor_f], "")
                    chk(tag + "." + text_f + " (withdrawn, empty)", row[text_f], "")
                    continue
                chk(tag + "." + minor_f, row[minor_f], str(to_minor(crow[cap_f], digits)))
                chk(tag + "." + text_f + " (oracle's own characters)", row[text_f], crow[cap_f])

            if crow.get("total") is None:
                chk(tag + ".observed_total_due_minor (absent)", row["observed_total_due_minor"], None)
            else:
                chk(tag + ".observed_total_due_minor", row["observed_total_due_minor"],
                    str(to_minor(crow["total"], digits)))

    files, floats = float_scan()

    print("T58 TRANSCRIPTION AUDIT — independent converter, written against the vectors")
    print("  vectors audited          %d" % len(AUDIT))
    print("  schedule rows audited    %d" % rows)
    print("  cells checked            %d" % checked)
    print("  cells matched            %d" % matched)
    print("  discrepancies            %d" % len(problems))
    for p in problems:
        print("    " + p)
    print()
    print("FLOAT SCAN over %s" % STORE)
    print("  JSON files scanned       %d" % files)
    print("  bare number tokens containing '.', 'e' or 'E': %d" % len(floats))
    for b in floats:
        print("    " + b)
    return 1 if (problems or floats) else 0


if __name__ == "__main__":
    sys.exit(main())
