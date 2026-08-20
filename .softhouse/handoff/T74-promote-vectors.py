#!/usr/bin/env python3
"""T74 — promote pass 3i's group-E observations into the golden-vector store.

WHAT IS PROMOTED, AND WHAT IS DELIBERATELY NOT.

Promoted: the six `36 x 16.8 %` small-principal shapes T21 required change P1-11
asked for, in MNT at the production `currencyDecimalPlaces = 2` and the ratified
`(19, HALF_UP)`. Every one is squarely inside DEC-1's graded domain and rests on
`schedule.core`, which `.softhouse/vectors/capabilities.json` marks `exercised`
for `path_a_embeddable`.

NOT promoted, and this is the larger half of task T74: NOTHING from capture groups
A, B, C or D — the multiples-of factorials. Each of the following is on its own
sufficient to refuse them, and they are recorded in the handoff rather than
smuggled past:

  1. The frozen contract's `Currency` struct carries `Code` and `MinorUnitDigits`
     and NOTHING ELSE. There is no field for `CurrencyData.inMultiplesOf`, so a
     vector over it cannot be expressed as a contract request at all.
  2. `Currency.MinorUnitDigits == 2` is a graded-domain predicate. Groups A, C and
     D all run at 0 and are outside it by construction.
  3. `capabilities.json` records `currency.zero.decimals` with
     `in_graded_domain: false`.
  4. `installment.rounding.multiple` is `blind` on `path_a_embeddable`, and pass
     3i is the first capture that PROVES it with the two fields separated: every
     installment-only arm is byte-identical to its baseline. A vector over a blind
     capability grades nothing — the T66 lesson.
  5. Group B is the sharpest of the five. At production `decimalPlaces = 2` the
     observed blocks of `T74-B1`, `T74-B2` and `T74-B3` are IDENTICAL to the
     already-promoted `P-MNT-5M`. A vector there would duplicate an existing
     vector while claiming to grade an input it cannot move.

TRANSCRIBE, NEVER COMPUTE. Every `expect` cell is a value literally present in
`.softhouse/capture/out/capture-prod3i-raw.json` for the named case; the only
transformation is exact textual major -> minor scaling by integer string
manipulation, with no float anywhere, and the oracle's own emitted characters
travel alongside in the `*_major_text` cross-check fields.

THE ONE DERIVED FIELD is `graded_against[].margin_minor`, and it is derived by
MEASUREMENT of the oracle rather than of a model — see
`.softhouse/capture/t74-multiplesof/build-counterfactuals.py`. This script refuses
to write a margin that report does not contain.

Run from the repository root:

    python3 .softhouse/handoff/T74-promote-vectors.py

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program and appears nowhere in this stack; this seam
opens no database connection at all.
"""
import hashlib
import json
import os
import sys
from math import gcd

VECTORS = ".softhouse/vectors/loanschedule"
P3I_REF = ".softhouse/capture/out/capture-prod3i-raw.json"
CF_REF = ".softhouse/capture/t74-multiplesof/out/t74-counterfactuals-pass3i.json"

PIN = json.load(open(".softhouse/vectors/PIN.json"))
DEC1 = PIN["dec1_revision"]
COMMIT = PIN["fineract_commit"]

CASES = ["T74-E-P4", "T74-E-P59", "T74-E-P72", "T74-E-P340", "T74-E-P426", "T74-E-P6940"]

FILENAMES = {
    "T74-E-P4": "T74-E-P4-precision-boundary-mnt4pt00-36x16pt8pct.json",
    "T74-E-P59": "T74-E-P59-precision-boundary-mnt59pt00-36x16pt8pct.json",
    "T74-E-P72": "T74-E-P72-precision-boundary-mnt72pt00-36x16pt8pct.json",
    "T74-E-P340": "T74-E-P340-precision-boundary-mnt340pt00-36x16pt8pct.json",
    "T74-E-P426": "T74-E-P426-precision-boundary-mnt426pt00-36x16pt8pct.json",
    "T74-E-P6940": "T74-E-P6940-precision-boundary-mnt6940pt00-36x16pt8pct.json",
}

TITLES = {
    "T74-E-P4":
        "PRECISION BOUNDARY at the smallest divergent principal. MNT 4.00 over 36 monthly "
        "repayments at 16.8% p.a., schedule start == disbursement == 2024-01-01. FOUR TUGRIKS. "
        "This shape is the counter-example to the idea that arithmetic precision only matters on "
        "large loans: at 36 periods the oracle's own answer moves between MathContext precision 12 "
        "and the ratified 19, at a principal of 400 minor units.",
    "T74-E-P59":
        "PRECISION BOUNDARY, MNT 59.00 over 36 monthly repayments at 16.8% p.a. The divergence "
        "runs the OTHER WAY from MNT 4.00's -- 16.51 observed against the low-precision 16.52 -- "
        "so the pair together shows the effect is a rounding boundary, not a systematic bias a "
        "port could correct for with a sign.",
    "T74-E-P72":
        "PRECISION BOUNDARY, MNT 72.00 over 36 monthly repayments at 16.8% p.a. The THINNEST of "
        "the six: exactly one graded money cell moves, the final period's interest, 0.04 against "
        "0.03. A corpus that only samples wide divergences would call this shape safe.",
    "T74-E-P340":
        "PRECISION BOUNDARY, MNT 340.00 over 36 monthly repayments at 16.8% p.a.",
    "T74-E-P426":
        "PRECISION BOUNDARY, widest separation of the six. MNT 426.00 over 36 monthly repayments "
        "at 16.8% p.a. Thirty-nine graded cells move and the widest is 2 minor units, against 1 "
        "for every other principal in this family.",
    "T74-E-P6940":
        "PRECISION BOUNDARY, MNT 6,940.00 over 36 monthly repayments at 16.8% p.a. The largest of "
        "the six, included because the SAME shape at MNT 50,000,000 -- the promoted P-MNT-50M -- "
        "is precision-INSENSITIVE. Divergence is a property of the (principal, n, rate) triple, "
        "not of magnitude, and this pair of vectors is what stops that being re-learned.",
}

CF_ID = "MATHCONTEXT-PRECISION-12-INSTEAD-OF-RATIFIED-19"
CF_DESCRIPTION = (
    "Runs the intermediate arithmetic at 12 significant digits instead of the ratified 19. "
    "`Rounding.SignificantDigits == 19` is a graded-domain predicate of the frozen contract and a "
    "ratified tenant parameter: MoneyHelper.PRECISION = 19 is a COMPILE-TIME CONSTANT and "
    "getMathContext() returns new MathContext(19, tenantRoundingMode) [MoneyHelper.java:35,91-93], "
    "so only the MODE is configurable. A port that hard-codes some other working precision, that "
    "reaches for whatever its decimal library offers by default, or that reads precision 12 out of "
    "one of Fineract's own MOCKED TESTS -- where 12 is the value that appears -- lands exactly "
    "here. Before this vector family the corpus could not see it: the store's README records that "
    "T55 witnessed no shape separating precision 19 from 12, and every promoted vector was "
    "precision-insensitive, so the MathContext was recorded as provenance and graded nothing.")
CF_PROVENANCE = (
    "COUNTERFACTUAL PROVENANCE, AND WHY IT IS STRONGER THAN THIS STORE'S OTHERS. The other "
    "counterfactuals in this corpus (T58, T61, T64) are measured by mutating the GO PORT and "
    "re-running it, and each needs a control proving the unmutated model reproduces the oracle "
    "before its margin means anything. THIS ONE CONTAINS NO MODEL. Both arms are observations of "
    "the reference oracle, taken in the SAME RUN of .softhouse/capture/src/run-pass3i.sh, through "
    "the same seam, behind the same nine rig calibrations, differing in exactly one input -- the "
    "threaded MathContext precision -- which build-counterfactuals.py ASSERTS by comparing the two "
    "inputs blocks field by field and refusing any pair that differs in anything else. The "
    "counterfactual case id is recorded below and its capture case is in the same artefact. "
    "WHAT THIS DOES NOT ESTABLISH: it says nothing about where a port with some OTHER precision "
    "defect lands, and nothing about the rounding MODE, which is HALF_UP on both arms.")

PREDICTION_NOTE = (
    "PREDICTION REGISTERED BEFORE THE CAPTURE. .softhouse/capture/t74-multiplesof/PREDICTION.md "
    "and predicted.json were committed to this branch TWO COMMITS BEFORE run-pass3i.sh was run, "
    "and among 1,083 registered predictions they name the total interest of all six of these "
    "shapes at BOTH precisions, transcribed from T21's own probe transcript. All twelve totals "
    "were confirmed by the oracle [.softhouse/capture/t74-multiplesof/check-prediction.py]. That "
    "is also a P-16 check on the document under this task's review: twelve numbers taken out of "
    "the T21 audit and put back to the oracle, and the audit was right about all of them.")

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
    "and it has no interest accessor at all. Its outstanding balance IS recorded by this rig and "
    "is therefore promoted. (5) The capture's per-row totalOutstandingBalance column is "
    "deliberately NOT promoted: it is principal plus interest still to accrue, not an "
    "outstanding-principal figure, and the frozen contract has no field for it. (6) PROVENANCE OF "
    "THE SHAPE. Capture pass 3i is pass 3h's rig with ONE STRUCTURAL FIX -- "
    "CurrencyData.inMultiplesOf and installmentAmountInMultiplesOf finally have separate slots, "
    "T21 required change P1-8 -- and a new case list, with NOT ONE precondition weakened, three "
    "added and one replaced by a stronger form. It reproduced NINE already-committed observations "
    "as rig calibrations before emitting anything: P-CAL at (12, HALF_UP) and P-CAL-P00, "
    "P-CAL-MNT50M and P-CAL-MNT5M at the production (19, HALF_UP) against pass 3b; P-CAL-EMI6 "
    "against pass 3c; P-CAL-LATQ0a and P-CAL-DRIFTF against pass 3e; P-CAL-ZPA and P-CAL-ZPB "
    "against pass 3g. All nine matched with inputs and observed blocks identical, tenant id "
    "included. P-CAL-MNT50M is the SAME 36 x 16.8% SHAPE as this vector at a principal of "
    "50,000,000, so the rig is calibrated on this vector's own term and rate, at a size where the "
    "oracle is precision-INSENSITIVE. (7) WHY THIS SHAPE IS IN THE STORE AT ALL. T21 required "
    "change P1-11: the pass-3 report claimed precision is load-bearing only above a size "
    "threshold; T21's auditor refuted it against the oracle at principals as small as MNT 4.00 on "
    "exactly this shape and asked for it to be captured. This is that capture, promoted. (8) " +
    PREDICTION_NOTE)


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def minor(text, digits):
    t = str(text).strip()
    neg = t.startswith("-")
    if neg:
        t = t[1:]
    if "e" in t or "E" in t:
        sys.exit("INADMISSIBLE: exponent in money string %r" % text)
    ip, _, fp = t.partition(".")
    ip = ip or "0"
    over = False
    if len(fp) > digits:
        if fp[digits:].strip("0"):
            sys.exit("INADMISSIBLE: %r carries a SIGNIFICANT digit beyond the currency scale %d; "
                     "the exact conversion is impossible and this script will not round a "
                     "transcription." % (text, digits))
        over = True
        fp = fp[:digits]
    fp = fp + "0" * (digits - len(fp))
    v = (ip + fp).lstrip("0") or "0"
    if not v.isdigit():
        sys.exit("not a decimal: %r" % text)
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


def main():
    if not os.path.isdir(VECTORS):
        sys.exit("run me from the repository root")
    doc = json.load(open(P3I_REF))
    caps = {c["id"]: c for c in doc["captures"]}
    cfs = {r["case"]: r for r in json.load(open(CF_REF))}
    p3i_sha = sha256(P3I_REF)
    captured_at = doc["attestation"]["capturedAtUtc"]

    written = 0
    for cid in CASES:
        cap = caps[cid]
        i = cap["inputs"]
        obs = cap["observed"]
        digits = i["currencyDecimalPlaces"]

        # --- admissibility, asserted rather than assumed -------------------------------
        if i["mathContextPrecision"] != 19 or i["mathContextRoundingMode"] != "HALF_UP":
            sys.exit("%s: not at the production threaded MathContext" % cid)
        if i["ambientMoneyHelperPrecision"] != 19 or i["ambientMoneyHelperRoundingMode"] != "HALF_UP":
            sys.exit("%s: ambient MathContext is not (19, HALF_UP)" % cid)
        if cid in PIN["never_promotable_capture_case_ids"]:
            sys.exit("%s is on PIN.json's never-promotable denylist" % cid)
        if digits != 2:
            sys.exit("%s: currencyDecimalPlaces is %d; DEC-1's graded domain is 2 only, and at 0 a "
                     "second rounding channel switches on inside the oracle (Money.java:48-51)"
                     % (cid, digits))
        # The two inputs pass 3i exists to separate must BOTH be absent from anything promoted.
        # Neither is a field the frozen contract carries, and one of them is blind on this seam.
        if i["currencyInMultiplesOf"] is not None:
            sys.exit("%s: currencyInMultiplesOf is set. The frozen contract has no field for it "
                     "(Currency carries Code and MinorUnitDigits only) and nothing that varies it "
                     "may be promoted." % cid)
        if i["installmentAmountInMultiplesOf"] is not None:
            sys.exit("%s: installmentAmountInMultiplesOf is set, and capabilities.json marks "
                     "installment.rounding.multiple BLIND on path_a_embeddable." % cid)
        if cap.get("pathIdentity", {}).get("identical") is not True:
            sys.exit("%s: pathIdentity is not identical" % cid)

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

        cf = cfs.get(cid)
        if cf is None:
            sys.exit("%s: no counterfactual measurement; this script will not invent a margin" % cid)
        if not cf["divergent"]:
            sys.exit("%s: the precision counterfactual moves no graded money cell here, so this "
                     "shape does not kill it and must not claim to." % cid)
        worst = cf["widest"]
        evidence = (
            "OBSERVED at the ratified production MathContext (19, HALF_UP). Every expect cell is "
            "transcribed from capture case %s of %s.\n"
            "MARGIN. Over this vector's graded money cells the counterfactual diverges on %d of "
            "%d. The widest single-cell disagreement is at period[%d], column %s: the oracle "
            "OBSERVED %d minor units against the counterfactual's %d, so the margin is "
            "|%d - %d| = %d MINOR UNITS. Total interest moves from %s at the ratified precision to "
            "%s at 12.\n"
            "THE COUNTERFACTUAL IS ALSO AN OBSERVATION. It is capture case %s of the SAME artefact "
            "-- the same request put to the same oracle through the same seam in the same run, at "
            "MathContext precision 12 instead of 19 and identical in every other input.\n%s\n%s"
            % (cid, P3I_REF, cf["divergentCellCount"], cf["cells"],
               worst["row"], worst["field"], worst["observed"], worst["counterfactual"],
               worst["observed"], worst["counterfactual"], worst["delta"],
               cf["observedTotalInterest"], cf["counterfactualTotalInterest"],
               cf["counterfactualCase"], CF_PROVENANCE, PREDICTION_NOTE))

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
                "id": CF_ID,
                "capability": "schedule.core",
                "description": CF_DESCRIPTION,
                "margin_minor": str(worst["delta"]),
                "evidence": evidence,
            }],
            "retires_when_capability_graded": "",
            "provenance": {
                "kind": "oracle-capture",
                "note": (
                    "TRANSCRIBED, never computed, from Path A capture pass 3i "
                    "(.softhouse/capture/src/run-pass3i.sh, Capture3i.java). Every expect cell is a "
                    "value literally present in the referenced capture for capture case %s; the "
                    "only transformation is exact textual major->minor scaling, and the oracle's "
                    "own emitted characters are carried alongside in the *_major_text cross-check "
                    "fields so the scaling is mechanically re-checkable. Promotion script: "
                    ".softhouse/handoff/T74-promote-vectors.py (task T74)." % cid),
                "capture_ref": P3I_REF,
                "capture_sha256": p3i_sha,
                "capture_case_id": cid,
                "citation": "",
            },
            "oracle": {
                "fineract_commit": COMMIT,
                "seam": "path_a_embeddable",
                "captured_at": captured_at,
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
        print("wrote %s  (margin %s minor at period[%d].%s, %d/%d graded cells move)"
              % (path, worst["delta"], worst["row"], worst["field"],
                 cf["divergentCellCount"], cf["cells"]))
        written += 1

    print("\n%d vectors promoted from %s (sha256 %s)" % (written, P3I_REF, p3i_sha))
    print("NOTHING was promoted from capture groups A, B, C or D — see this script's docstring.")


if __name__ == "__main__":
    main()
