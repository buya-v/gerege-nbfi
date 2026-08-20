#!/usr/bin/env python3
"""T61 — promote the pass-3f observations into the golden-vector store.

TRANSCRIBE, NEVER COMPUTE. Every `expect` cell this script writes is a value
literally present in `.softhouse/capture/out/capture-prod3f-raw.json`; the only
transformation applied to a money column is exact textual major -> minor scaling
("18000.95" -> "1800095"), by integer string manipulation, with no float
anywhere. A cell the capture did not record is named in that row's
`unrecorded_fields` and is never filled from a rule.

The `graded_against` margin is the one DERIVED part of a vector, and it is
derived by MEASUREMENT: `.softhouse/capture/t61-halfeven/out/` reports, per cell,
what the M7 counterfactual produces against what the oracle OBSERVED, with a
control proving the UNMUTATED port reproduces every one of those cells. This
script refuses to write a margin it cannot find in that report.

Run from the repository root:

    python3 .softhouse/handoff/T61-promote-vectors.py

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program and appears nowhere in this stack.
"""
import hashlib, json, os, sys
from math import gcd

VECTORS = ".softhouse/vectors/loanschedule"
P3F_REF = ".softhouse/capture/out/capture-prod3f-raw.json"
CF_REF = ".softhouse/capture/t61-halfeven/out/t61-counterfactuals-pass3f.json"

PIN = json.load(open(".softhouse/vectors/PIN.json"))
DEC1 = PIN["dec1_revision"]
COMMIT = PIN["fineract_commit"]


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def minor(text, digits):
    t = text.strip()
    neg = t.startswith("-")
    if neg:
        t = t[1:]
    ip, _, fp = t.partition(".")
    ip = ip or "0"
    over = False
    if len(fp) > digits:
        if fp[digits:].strip("0"):
            raise SystemExit(
                "INADMISSIBLE: %r carries a SIGNIFICANT digit beyond the currency scale "
                "%d. The exact conversion is impossible and this script will not round a "
                "transcription." % (text, digits))
        over = True
        fp = fp[:digits]
    fp = fp + "0" * (digits - len(fp))
    v = (ip + fp).lstrip("0") or "0"
    if not v.isdigit():
        raise SystemExit("not a decimal: %r" % text)
    return ("-" + v if neg and v != "0" else v), over


def date(s):
    y, m, d = s.split("-")
    return {"year": int(y), "month": int(m), "day": int(d)}


def rate(text):
    ip, _, fp = text.partition(".")
    num = int(ip + fp)
    den = 10 ** len(fp) * 100
    g = gcd(abs(num), den) or 1
    return {"numerator": num // g, "denominator": den // g}


CF_SPEC = dict(
    id="MONEY-QUANTIZATION-HALF-EVEN",
    capability="schedule.core",
    description=(
        "Applies HALF_EVEN where the reference oracle applies the TENANT's rounding mode at the "
        "currency quantization [Money.java:52, Money(currency, amount, mc) -> "
        "setScale(currency.getDecimalPlaces(), mc.getRoundingMode())]. Buyan ratified HALF_UP "
        "(Fineract RoundingMode ordinal 4) for MNT on 2026-08-18 and CLAUDE.md requires it to be "
        "pinned explicitly and never inherited -- because HALF_EVEN is the reference oracle's own "
        "STOCK CONFIGURATION DEFAULT. A port that reads the default instead of the tenant pin, or "
        "that reaches for a language's banker's-rounding primitive because it is the one the "
        "standard library offers, lands exactly here. The two rules differ ONLY on an exact tie "
        "and only when the truncated value is even, which is why 29 promoted parity vectors could "
        "not tell them apart: not one of them lands the quantization on a tie."),
)

CF_PROVENANCE = (
    "COUNTERFACTUAL PROVENANCE. The counterfactual value is MEASURED, not asserted: a scratch copy "
    "of the port under /tmp with exactly one named change applied, run on this vector's own "
    "request. The patch is mutation M7 of .softhouse/handoff/T61-mutations.py; the runner is "
    ".softhouse/capture/t61-halfeven/src/run-counterfactuals.py and the raw per-cell output is "
    "out/t61-counterfactuals-pass3f.json. The model's faithfulness is not assumed -- with the "
    "change switched OFF it reproduces all 60 graded money cells of the three capture cases, with "
    "ZERO mismatches, so the only thing a reported margin can be measuring is the named change.")

PREDICTION_NOTE = (
    "PREDICTION REGISTERED BEFORE THE CAPTURE. .softhouse/capture/t61-halfeven/PREDICTION.md was "
    "committed to this branch ONE COMMIT BEFORE run-pass3f.sh was run, and it names the whole "
    "schedule of all three shapes plus one sharp claim: that the oracle emits 18000.95 on period 1 "
    "of T61-HE-B, not 18000.94. The oracle confirmed all 54 predicted cells with zero mismatches "
    "[.softhouse/capture/t61-halfeven/check-prediction.py]. The git history is what makes that a "
    "checkable claim rather than a story told afterwards.")

TITLES = {
    "T61-HE-A": (
        "TIE AT THE CURRENCY QUANTIZATION, widest separation. MNT 1,000,541.50 over 6 monthly "
        "repayments at 21.6% p.a., schedule start == disbursement == 2024-01-01. Identical to the "
        "promoted on-lattice control P-LAT-Q0a in EVERY field but the principal. It is the widest "
        "HALF_UP-vs-HALF_EVEN separation found in 2,001 consecutive principals, and it kills a "
        "port that applies banker's rounding at Money.java:52 by 6 minor units."),
    "T61-HE-B": (
        "TIE AT THE CURRENCY QUANTIZATION, the clean case. MNT 1,000,052.50 over 6 monthly "
        "repayments at 21.6% p.a., schedule start == disbursement == 2024-01-01. Chosen from source "
        "algebra rather than found by search: on this lattice the period-1 rate factor is exactly "
        "0.018, so period-1 interest in minor units is 18*B/1000, an EXACT TIE when B == 250 "
        "(mod 500). B = 100005250 gives 1800094.5 with 1800094 even, so HALF_UP and HALF_EVEN "
        "disagree at that single cell before anything compounds. The oracle was OBSERVED to emit "
        "18000.95."),
    "T61-HE-C": (
        "TIE AT THE CURRENCY QUANTIZATION, third independent principal. MNT 1,000,089.50 over 6 "
        "monthly repayments at 21.6% p.a., schedule start == disbursement == 2024-01-01. A third "
        "principal separating the two tie rules, so that the kill does not rest on one arithmetic "
        "coincidence."),
}

FILENAMES = {
    "T61-HE-A": "T61-HE-A-tie-quantization-1M000541pt50-6x21pt6pct.json",
    "T61-HE-B": "T61-HE-B-tie-quantization-1M000052pt50-6x21pt6pct.json",
    "T61-HE-C": "T61-HE-C-tie-quantization-1M000089pt50-6x21pt6pct.json",
}

NOTE = (
    "TRANSCRIPTION NOTES. (1) request.currency.code is upper-cased from the capture's own "
    "spelling; admit.go requires upper case and the contract forbids the oracle's fixture spelling "
    "leaking back out. (2) request.time_zone is DECLARED, not observed: the Path A embeddable seam "
    "takes java.time.LocalDate only and has no time-zone input at all, so Asia/Ulaanbaatar is this "
    "vector's declared interpretation zone for civil dates and grades nothing. (3) "
    "request.rounding.rate_factor_scale is 19 from PIN.json's production_rounding; the capture "
    "records one MathContext precision (19) which is both. (4) On the DISBURSEMENT row, "
    "installment_number and interest_minor are marked unrecorded_fields: the oracle's own record "
    "type LoanSchedulePlanDisbursementPeriod carries four fields, its periodNumber() returns null, "
    "and it has no interest accessor at all. Its outstanding balance IS recorded by this rig and is "
    "therefore promoted. (5) The capture's per-row totalOutstandingBalance column is deliberately "
    "NOT promoted: it is principal plus interest still to accrue, not an outstanding-principal "
    "figure, and the frozen contract has no field for it. (6) PROVENANCE OF THE SHAPE. This is "
    "capture pass 3f, which is pass 3e's rig with a new case list and NOT ONE check weakened -- the "
    "same relationship pass 3c has to pass 3b. It reproduced FOUR already-committed observations as "
    "rig calibrations before emitting anything: P-CAL at (12, HALF_UP) and P-CAL-P00 at the "
    "production (19, HALF_UP) against pass 3b, P-CAL-EMI6 against pass 3c's P-EMI-6-1M014632, and "
    "P-CAL-LATQ0a against pass 3e's P-LAT-Q0a -- the last being the SAME QUESTION as this vector in "
    "every field but the principal, so the rig is calibrated on exactly the lattice, term, rate, "
    "currency and MathContext this promotion rests on. All four matched with inputs and observed "
    "blocks identical, tenant id included. (7) " + PREDICTION_NOTE)


def main():
    if not os.path.isdir(VECTORS):
        sys.exit("run me from the repository root")
    caps = {c["id"]: c for c in json.load(open(P3F_REF))["captures"]}
    cfs = {r["case"]: r for r in json.load(open(CF_REF))}
    p3f_sha = sha256(P3F_REF)

    written = 0
    for cid in ("T61-HE-A", "T61-HE-B", "T61-HE-C"):
        cap = caps[cid]
        i = cap["inputs"]
        digits = i["currencyDecimalPlaces"]
        obs = cap["observed"]

        if i["mathContextPrecision"] != 19 or i["mathContextRoundingMode"] != "HALF_UP":
            sys.exit("%s: not at the production MathContext" % cid)
        if i["ambientMoneyHelperPrecision"] != 19 or i["ambientMoneyHelperRoundingMode"] != "HALF_UP":
            sys.exit("%s: ambient MathContext is not (19, HALF_UP)" % cid)
        if cid in PIN["never_promotable_capture_case_ids"]:
            sys.exit("%s is on PIN.json's never-promotable denylist" % cid)

        periods = []
        for p in obs["periods"]:
            row = {
                "kind": p["type"],
                "installment_number": p.get("periodNumber") or 0,
                "from_date": date(p.get("periodFromDate") or p["fromDate"]),
                "due_date": date(p["dueDate"]),
            }
            unrecorded, over = [], []
            if p.get("periodNumber") is None:
                unrecorded.append("installment_number")

            pm, o = minor(p["principal"], digits)
            row["principal_minor"] = pm
            row["principal_major_text"] = p["principal"]
            if o:
                over.append("principal_minor")

            if p.get("interest") is None:
                row["interest_minor"] = ""
                row["interest_major_text"] = ""
                unrecorded.append("interest_minor")
            else:
                im, o = minor(p["interest"], digits)
                row["interest_minor"] = im
                row["interest_major_text"] = p["interest"]
                if o:
                    over.append("interest_minor")

            if p.get("balance") is None:
                row["outstanding_principal_minor"] = ""
                row["outstanding_principal_major_text"] = ""
                unrecorded.append("outstanding_principal_minor")
            else:
                bm, o = minor(p["balance"], digits)
                row["outstanding_principal_minor"] = bm
                row["outstanding_principal_major_text"] = p["balance"]
                if o:
                    over.append("outstanding_principal_minor")

            row["unrecorded_fields"] = unrecorded
            if over:
                row["over_scaled_wire_text_fields"] = over
            row["observed_total_due_minor"] = (
                minor(p["total"], digits)[0] if p.get("total") is not None else None)
            periods.append(row)

        cf = cfs[cid]
        if cf["baselineMismatches"] != 0:
            sys.exit("%s: the counterfactual control is not clean; no margin from it is usable" % cid)
        money = cf["divergent"]["M7"]
        if not money:
            sys.exit("%s: M7 moves no money cell here; it is not a grader for this shape" % cid)
        worst = max(money, key=lambda c: c["delta"])
        evidence = (
            "Derived at the ratified production MathContext (19, HALF_UP). Every OBSERVED value "
            "below is transcribed from capture case %s of %s; only the counterfactual is derived.\n"
            "MARGIN. Over this vector's graded money cells the counterfactual diverges on %d of %d. "
            "The widest single-cell disagreement is at period[%d], column %s: the oracle OBSERVED "
            "%s minor units against the counterfactual's %s, so the margin is |%s - %s| = %s MINOR "
            "UNITS.\nWHY A TIE IS REACHABLE AT ALL. On this lattice the period-1 rate factor is "
            "exactly 0.018, so period-1 interest in minor units is 18*B/1000 for a principal of B "
            "minor units -- an exact half-minor-unit tie whenever B == 250 (mod 500), and the two "
            "rules then differ whenever the truncated value is even. .softhouse/vectors/"
            "capabilities.json already records the same arithmetic from the other direction "
            "(period-1 interest 20,925.05 under HALF_UP against 20,925.04 under HALF_EVEN on "
            "principal MNT 1,162,502.50).\n%s\n%s"
            % (cid, P3F_REF, len(money), cf["cells"], worst["row"], worst["field"],
               worst["observed"], worst["value"], worst["observed"], worst["value"],
               worst["delta"], CF_PROVENANCE, PREDICTION_NOTE))

        ti, _ = minor(obs["totalInterestAmount"], digits)
        amt, over_amt = minor(i["disbursementAmount"], digits)
        if over_amt:
            sys.exit("%s: disbursement amount over-scaled" % cid)

        vec = {
            "schema": "gerege.loanschedule.vector/v1",
            "case_id": cid,
            "context": "loanschedule",
            "class": "parity",
            "title": TITLES[cid],
            "dec1_revision": DEC1,
            "_note": NOTE,
            "capabilities_required": ["schedule.core"],
            "graded_against": [{
                "id": CF_SPEC["id"],
                "capability": CF_SPEC["capability"],
                "description": CF_SPEC["description"],
                "margin_minor": str(worst["delta"]),
                "evidence": evidence,
            }],
            "retires_when_capability_graded": "",
            "provenance": {
                "kind": "oracle-capture",
                "note": (
                    "TRANSCRIBED, never computed, from Path A capture pass 3f "
                    "(.softhouse/capture/src/run-pass3f.sh, Capture3f.java). Every expect cell is a "
                    "value literally present in the referenced capture for capture case %s; the only "
                    "transformation is exact textual major->minor scaling, and the oracle's own "
                    "emitted characters are carried alongside in the *_major_text cross-check fields "
                    "so the scaling is mechanically re-checkable. Promotion script: "
                    ".softhouse/handoff/T61-promote-vectors.py (task T61)." % cid),
                "capture_ref": P3F_REF,
                "capture_sha256": p3f_sha,
                "capture_case_id": cid,
                "citation": "",
            },
            "oracle": {
                "fineract_commit": COMMIT,
                "seam": "path_a_embeddable",
                "captured_at": json.load(open(P3F_REF))["attestation"]["capturedAtUtc"],
                "threaded_mathcontext": {"precision": i["mathContextPrecision"],
                                         "rounding_mode": i["mathContextRoundingMode"]},
                "ambient_mathcontext": {"precision": i["ambientMoneyHelperPrecision"],
                                        "rounding_mode": i["ambientMoneyHelperRoundingMode"]},
            },
            "request": {
                "time_zone": "Asia/Ulaanbaatar",
                "currency": {"code": i["currencyCode"].upper(), "minor_unit_digits": digits},
                "rounding": {
                    "significant_digits": i["mathContextPrecision"],
                    "rate_factor_scale": PIN["production_rounding"]["rate_factor_scale"],
                    "mode": i["mathContextRoundingMode"],
                },
                "schedule_start_date": date(i["scheduleGenerationStartDate"]),
                "disbursements": [{"date": date(i["disbursementDate"]), "amount_minor": amt}],
                "number_of_repayments": i["numberOfRepayments"],
                "repayment_every": i.get("repaymentEvery", i.get("repaymentFrequency")),
                "repayment_frequency_unit": i["repaymentFrequencyType"],
                "annual_nominal_interest_rate": rate(i["annualNominalInterestRate"]),
                "interest_method": i["interestMethod"],
                "day_count": "FIXED_30_360",
                "down_payment_percentage": {"numerator": 0, "denominator": 1},
                "installment_rounding_multiple_minor": "0",
            },
            "expect": {
                "kind": "schedule",
                "sentinel": "",
                "last_repayment_due_date": None,
                "observed_total_interest_minor": ti,
                "periods": periods,
            },
            "invariant_exemptions": [],
        }

        path = os.path.join(VECTORS, FILENAMES[cid])
        open(path, "w").write(json.dumps(vec, indent=2, ensure_ascii=False) + "\n")
        print("wrote %s  (margin %s minor at period[%d].%s)"
              % (path, worst["delta"], worst["row"], worst["field"]))
        written += 1

    print("\n%d vectors promoted from %s (sha256 %s)" % (written, P3F_REF, p3f_sha))


if __name__ == "__main__":
    main()
