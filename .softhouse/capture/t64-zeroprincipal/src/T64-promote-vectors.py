#!/usr/bin/env python3
"""T64 — promote the pass-3g observations into the golden-vector store.

TRANSCRIBE, NEVER COMPUTE. Every `expect` cell this script writes is a value
literally present in `.softhouse/capture/out/capture-prod3g-raw.json`; the only
transformation applied to a money column is exact textual major -> minor scaling
("0.28" -> "28"), by integer string manipulation, with no float anywhere. A cell
the capture did not record is named in that row's `unrecorded_fields` and is never
filled from a rule.

The `graded_against` margin is the one DERIVED part of a vector, and it is derived
by MEASUREMENT: `.softhouse/capture/t64-zeroprincipal/out/` reports, per cell,
what each named counterfactual produces against what the oracle OBSERVED, with a
control proving the UNMUTATED port reproduces every one of those cells. This
script refuses to write a margin it cannot find in that report, and refuses to
write a vector for which no counterfactual moves a cell.

Run from the repository root:

    python3 .softhouse/capture/t64-zeroprincipal/src/T64-promote-vectors.py

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program and appears nowhere in this stack.
"""
import hashlib, json, os, sys
from math import gcd

VECTORS = ".softhouse/vectors/loanschedule"
P3G_REF = ".softhouse/capture/out/capture-prod3g-raw.json"
CF_REF = ".softhouse/capture/t64-zeroprincipal/out/t64-counterfactuals-pass3g.json"

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


# ------------------------------------------------------------------------------------------
# The named wrong implementations each vector is claimed to kill, and the capability they sit
# under. A vector may claim ONLY a counterfactual the measurement report shows moving a cell
# on that vector's own shape.
# ------------------------------------------------------------------------------------------
CF_DESCRIPTION = {
    "ZP-GUARD-NONSTRICT": (
        "Fires the EMI smoothing loop on EQUALITY where the reference oracle requires a STRICT "
        "inequality. EmiAdjustment.shouldBeAdjusted returns "
        "emiDifference.abs().multipliedBy(100).isGreaterThan(originalEmi.copy(lowerHalfOfRelatedPeriods)) "
        "[EmiAdjustment.java:31-36], and isGreaterThan is strict. On a ROUNDING-FLOOR shape the two "
        "sides are EXACTLY EQUAL to the minor unit, so > and >= decide whether the smoothing loop "
        "runs at all -- and the two schedules that result are not near neighbours: one amortizes "
        "zero principal for the whole term and settles in the final row, the other pays the loan "
        "off less than a third of the way in. Not one of the 32 promoted parity vectors lands on "
        "that equality, so all 32 score identically under both readings. MEASURED ON THE REAL "
        "HARNESS: at 32 promoted parity vectors this counterfactual is GREEN, exit 0, PASS 32 FAIL "
        "0; at 36 it is RED, exit 1, PASS 33 FAIL 3, the three failures being T64-ZP-A, T64-ZP-C "
        "and T64-ZP-D. IT CLOSES A BLIND SPOT "
        "[.softhouse/capture/t64-zeroprincipal/out/harness-mutation-runs.txt]."),
    "ZP-GUARD-SCALES-THE-INSTALLMENT": (
        "Multiplies the installment by floor(n/2) where the reference oracle compares against "
        "floor(n/2) whole currency units FLAT. Money.copy(double) REPLACES the amount rather than "
        "scaling it [Money.java:216-222], so originalEmi.copy(lowerHalfOfRelatedPeriods) in "
        "EmiAdjustment.java:33-35 has no dependence on the installment at all. Reading it as "
        "'originalEmi times k' is the obvious misreading -- the method is called on the EMI and "
        "takes a count -- and it is the reading THE AUTHOR OF THIS CAPTURE MADE from those same "
        "lines before re-opening Money.java, and recorded as wrong in "
        ".softhouse/capture/t64-zeroprincipal/MECHANISM-CORRECTION.md. MEASURED HONESTLY: this "
        "counterfactual was ALREADY GRADED before this capture -- the real harness at 32 promoted "
        "parity vectors reports exit 1, PASS 21 FAIL 11. This vector therefore ADDS CELLS AND "
        "MARGIN to an existing kill (32 -> 36 vectors moves it to PASS 22 FAIL 14) and does NOT "
        "close a blind spot, and it is recorded that way rather than claimed as new coverage "
        "[.softhouse/capture/t64-zeroprincipal/out/harness-mutation-runs.txt]."),
    "ZP-RESIDUAL-NO-RECURSION": (
        "Clamps a negative final-period installment to zero WITHOUT re-applying the residual, so "
        "the part of the residual that could not be placed is silently dropped. "
        "calculateLastUnpaidRepaymentPeriodEMI re-enters itself at "
        "ProgressiveEMICalculator.java:1211-1214. This is the EXACT recursion T59 profiled at "
        "34.9% cumulative on near-interest-only shapes and correctly declined to touch, on the "
        "stated ground that NO VECTOR GRADED IT -- 'it is a faithful port, it is innermost money "
        "code, and no vector grades that shape'. A port that drops the recursion as dead on an "
        "unpaid schedule is making exactly the judgement T59 refused to make, and this vector is "
        "the oracle that judgement lacked. MEASURED ON THE REAL HARNESS: at 32 promoted parity "
        "vectors this counterfactual is GREEN, exit 0, PASS 32 FAIL 0; at 36 it is RED, exit 1, "
        "PASS 35 FAIL 1, and the single failure is T64-ZP-B -- the ONLY shape in the corpus that "
        "drives the residual negative and makes the re-entry observable. IT CLOSES A BLIND SPOT, "
        "and it is the blind spot T59 named "
        "[.softhouse/capture/t64-zeroprincipal/out/harness-mutation-runs.txt]."),
}

TITLES = {
    "T64-ZP-A": (
        "ROUNDING FLOOR, the headline zero-principal shape. MNT 0.28 over 56 monthly repayments at "
        "21.6% p.a., schedule start == disbursement == 2024-01-01. FIFTY-FIVE of its 56 repayment "
        "rows amortize EXACTLY ZERO PRINCIPAL while carrying non-zero interest, with the "
        "outstanding balance pinned at 0.28 through all of them and the whole principal settling in "
        "row 56. Before this vector the corpus had ZERO discriminating power over a repayment row "
        "with a zero principal component: its longest term was 36 periods and its smallest "
        "principal MNT 100.00, and not one promoted row had principal 0."),
    "T64-ZP-B": (
        "ROUNDING FLOOR, ONE PERIOD SHORTER -- and a completely different schedule. MNT 0.28 over "
        "55 monthly repayments at 21.6% p.a., identical to T64-ZP-A in EVERY field but the term. "
        "At n=55 the smoothing guard's two sides stop being equal, the loop fires, the installment "
        "becomes 0.02, the loan amortizes to zero at period 15 and rows 16 through 55 are ENTIRELY "
        "DEAD: principal 0.00, interest 0.00, balance 0.00. Total interest for the whole loan is "
        "ONE MINOR UNIT. A schedule with dead rows after early payoff is a second shape the corpus "
        "had never seen, and it is the only one of the four that grades the final-period residual's "
        "re-entry."),
    "T64-ZP-C": (
        "ROUNDING FLOOR at an independent rate. MNT 0.17 over 34 monthly repayments at 36.0% p.a., "
        "schedule start == disbursement == 2024-01-01. Thirty-three zero-principal rows. The "
        "principal and term are the DERIVED bound B = ceil(0.5/r) minor units and n = 2*B, not a "
        "search result, so this vector is a second independent confirmation of the mechanism rather "
        "than a second sample of one arithmetic coincidence."),
    "T64-ZP-D": (
        "ROUNDING FLOOR at a third rate. MNT 0.36 over 72 monthly repayments at 16.8% p.a., "
        "schedule start == disbursement == 2024-01-01. Seventy-one zero-principal rows, and the "
        "longest schedule in the corpus by a factor of two -- 73 rows against the previous "
        "maximum of 37."),
}

FILENAMES = {
    "T64-ZP-A": "T64-ZP-A-zero-principal-mnt0pt28-56x21pt6pct.json",
    "T64-ZP-B": "T64-ZP-B-early-payoff-dead-rows-mnt0pt28-55x21pt6pct.json",
    "T64-ZP-C": "T64-ZP-C-zero-principal-mnt0pt17-34x36pct.json",
    "T64-ZP-D": "T64-ZP-D-zero-principal-mnt0pt36-72x16pt8pct.json",
}

DERIVATION_NOTE = (
    "WHY A ZERO-PRINCIPAL ROW IS REACHABLE AT ALL, AND ONLY HERE. A repayment row's principal is "
    "max(0, installment - due interest) [RepaymentPeriod.java:345-350], and both quantities are "
    "quantized to the currency scale before they meet [Money.java:52]. The exact installment/"
    "interest gap is B*r/((1+r)^n - 1), strictly positive for every finite n, so the two can only "
    "land on the same minor unit when that gap closes below half a minor unit. With B the principal "
    "in MINOR UNITS that needs B >= ceil(0.5/r) -- so the interest itself quantizes to at least one "
    "minor unit -- and a term long enough that the EMI smoothing guard does not fire and undo it. "
    "The guard is |emiDifference| * 100 > floor(n/2) whole currency units [EmiAdjustment.java:31-36 "
    "with Money.copy(double) at Money.java:216-222], which on this shape is B > floor(n/2) in minor "
    "units, i.e. it stops firing at n >= 2*B. THE CONSEQUENCE IS THE FINDING: at any commercially "
    "realistic Mongolian principal the term required is astronomical, so the path T59 profiled is "
    "reachable only at the rounding floor, and a vector that grades it must live there.")

PREDICTION_NOTE = (
    "PREDICTION REGISTERED BEFORE THE CAPTURE. .softhouse/capture/t64-zeroprincipal/PREDICTION.md "
    "and predicted-schedules.json were committed to this branch ONE COMMIT BEFORE run-pass3g.sh was "
    "run, and between them they name every cell of all four shapes -- 221 rows -- plus four sharp "
    "claims, including that T64-ZP-B, one period shorter than T64-ZP-A, comes back as a completely "
    "different schedule that pays off at period 15. The oracle confirmed all 1,539 predicted cells "
    "with zero mismatches [.softhouse/capture/t64-zeroprincipal/check-prediction.py]. The git "
    "history is what makes that a checkable claim rather than a story told afterwards. ONE PART OF "
    "THE PREDICTION'S REASONING WAS WRONG AND IS RECORDED AS WRONG: PREDICTION.md section 2.4 "
    "attributed the n >= 2*B threshold to the smoothing ADJUSTMENT quantizing to zero, when the "
    "real gate is shouldBeAdjusted() returning false. Same threshold, wrong mechanism; the "
    "correction is in MECHANISM-CORRECTION.md next to it. Right answer, wrong reason is pattern "
    "P-11, and the reason is the part a later contributor reuses.")

CF_PROVENANCE = (
    "COUNTERFACTUAL PROVENANCE. The counterfactual value is MEASURED, not asserted: a scratch copy "
    "of the port under /tmp with exactly one named change applied, run on this vector's own "
    "request. The patch set is .softhouse/capture/t64-zeroprincipal/src/T64-mutations.py, the "
    "runner is src/run-counterfactuals.py and the raw per-cell output is "
    "out/t64-counterfactuals-pass3g.json. The model's faithfulness is not assumed -- with every "
    "change switched OFF it reproduces all 659 graded money cells of the four capture cases, with "
    "ZERO mismatches, so the only thing a reported margin can be measuring is the named change.")

NOTE_TAIL = (
    "TRANSCRIPTION NOTES. (1) request.currency.code is upper-cased from the capture's own spelling; "
    "admit.go requires upper case and the contract forbids the oracle's fixture spelling leaking "
    "back out. (2) request.time_zone is DECLARED, not observed: the Path A embeddable seam takes "
    "java.time.LocalDate only and has no time-zone input at all, so Asia/Ulaanbaatar is this "
    "vector's declared interpretation zone for civil dates and grades nothing. (3) "
    "request.rounding.rate_factor_scale is 19 from PIN.json's production_rounding; the capture "
    "records one MathContext precision (19) which is both. (4) On the DISBURSEMENT row, "
    "installment_number and interest_minor are marked unrecorded_fields: the oracle's own record "
    "type LoanSchedulePlanDisbursementPeriod carries four fields, its periodNumber() returns null, "
    "and it has no interest accessor at all. Its outstanding balance IS recorded by this rig and is "
    "therefore promoted. (5) The capture's per-row totalOutstandingBalance column is deliberately "
    "NOT promoted: it is principal plus interest still to accrue, not an outstanding-principal "
    "figure, and the frozen contract has no field for it. (6) PROVENANCE OF THE SHAPE. This is "
    "capture pass 3g, which is pass 3f's rig with a new case list and NOT ONE check weakened. It "
    "reproduced SIX already-committed observations as rig calibrations before emitting anything: "
    "pass 3f's four unchanged, plus P-CAL-MNT50M against pass 3b's P-MNT-50M (n=36, the LONGEST "
    "TERM in the promoted corpus) and P-CAL-DRIFTF against pass 3e's P-DRIFT-F (MNT 1.00, the "
    "SMALLEST PRINCIPAL in it) -- the two axes this pass extends, so the rig is calibrated at the "
    "far end of both rather than merely somewhere nearby. All six matched with inputs and observed "
    "blocks identical, tenant id included. (7) " + DERIVATION_NOTE + " (8) " + PREDICTION_NOTE)

CLAIMS = {
    "T64-ZP-A": ["ZP-GUARD-NONSTRICT", "ZP-GUARD-SCALES-THE-INSTALLMENT"],
    "T64-ZP-B": ["ZP-RESIDUAL-NO-RECURSION"],
    "T64-ZP-C": ["ZP-GUARD-NONSTRICT", "ZP-GUARD-SCALES-THE-INSTALLMENT"],
    "T64-ZP-D": ["ZP-GUARD-NONSTRICT", "ZP-GUARD-SCALES-THE-INSTALLMENT"],
}


def main():
    if not os.path.isdir(VECTORS):
        sys.exit("run me from the repository root")
    doc = json.load(open(P3G_REF))
    caps = {c["id"]: c for c in doc["captures"]}
    cfs = {r["case"]: r for r in json.load(open(CF_REF))}
    p3g_sha = sha256(P3G_REF)

    written = 0
    for cid in ("T64-ZP-A", "T64-ZP-B", "T64-ZP-C", "T64-ZP-D"):
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

        graded_against = []
        for mid in CLAIMS[cid]:
            cells = cf["divergent"][mid]
            if not cells:
                sys.exit("%s: %s moves no money cell here; it is not a grader for this shape"
                         % (cid, mid))
            worst = max(cells, key=lambda c: c["delta"])
            evidence = (
                "Derived at the ratified production MathContext (19, HALF_UP). Every OBSERVED value "
                "below is transcribed from capture case %s of %s; only the counterfactual is "
                "derived.\nMARGIN. Over this vector's graded money cells the counterfactual diverges "
                "on %d of %d. The widest single-cell disagreement is at period[%d], column %s: the "
                "oracle OBSERVED %s minor units against the counterfactual's %s, so the margin is "
                "|%s - %s| = %s MINOR UNITS.\n%s\n%s\n%s"
                % (cid, P3G_REF, len(cells), cf["cells"], worst["row"], worst["field"],
                   worst["observed"], worst["value"], worst["observed"], worst["value"],
                   worst["delta"], DERIVATION_NOTE, CF_PROVENANCE, PREDICTION_NOTE))
            graded_against.append({
                "id": mid,
                "capability": "schedule.core",
                "description": CF_DESCRIPTION[mid],
                "margin_minor": str(worst["delta"]),
                "evidence": evidence,
            })

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
            "_note": NOTE_TAIL,
            "capabilities_required": ["schedule.core"],
            "graded_against": graded_against,
            "retires_when_capability_graded": "",
            "provenance": {
                "kind": "oracle-capture",
                "note": (
                    "TRANSCRIBED, never computed, from Path A capture pass 3g "
                    "(.softhouse/capture/src/run-pass3g.sh, Capture3g.java). Every expect cell is a "
                    "value literally present in the referenced capture for capture case %s; the only "
                    "transformation is exact textual major->minor scaling, and the oracle's own "
                    "emitted characters are carried alongside in the *_major_text cross-check fields "
                    "so the scaling is mechanically re-checkable. Promotion script: "
                    ".softhouse/capture/t64-zeroprincipal/src/T64-promote-vectors.py (task T64)." % cid),
                "capture_ref": P3G_REF,
                "capture_sha256": p3g_sha,
                "capture_case_id": cid,
                "citation": "",
            },
            "oracle": {
                "fineract_commit": COMMIT,
                "seam": "path_a_embeddable",
                "captured_at": doc["attestation"]["capturedAtUtc"],
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
        print("wrote %s  (%d rows, %d counterfactual(s): %s)"
              % (path, len(periods), len(graded_against),
                 ", ".join("%s margin %s" % (g["id"], g["margin_minor"]) for g in graded_against)))
        written += 1

    print("\n%d vectors promoted from %s (sha256 %s)" % (written, P3G_REF, p3g_sha))


if __name__ == "__main__":
    main()
