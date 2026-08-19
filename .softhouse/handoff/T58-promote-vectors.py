#!/usr/bin/env python3
"""T58 — promote observed captures into the golden-vector store.

TRANSCRIBE, NEVER COMPUTE. Every `expect` cell this script writes is a value
literally present in the referenced capture; the only transformation applied to a
money column is exact textual major -> minor scaling ("172574.64" -> "17257464"),
done by integer string manipulation with no float anywhere. A cell the capture did
not record is named in that row's `unrecorded_fields` and is never filled from a
rule -- filling it would store a derivation as an observation.

The `graded_against` margins are the one DERIVED part of a vector, and they are
derived by MEASUREMENT rather than by assertion: the counterfactual runs in
.softhouse/capture/t58-counterfactuals/ report, per cell, what a named wrong
implementation produces against what the oracle OBSERVED. This script reads those
reports and refuses to write a margin it cannot find there.

Run from the repository root:

    python3 .softhouse/handoff/T58-promote-vectors.py

"The oracle" is the Fineract reference implementation. Oracle Database is a
prohibited product in this program and appears nowhere in this stack.
"""

import hashlib
import json
import os
import sys

ROOT = os.getcwd()
VECTORS = ".softhouse/vectors/loanschedule"

P3E_REF = ".softhouse/capture/out/capture-prod3e-raw.json"
T39_REF = ".softhouse/capture/periodratio/out/t39-periodratio.json"   # corroboration only
P3D_REF = ".softhouse/capture/out/capture-prod3d-raw.json"
CF_P3E = ".softhouse/capture/t58-counterfactuals/out/t58-counterfactuals-pass3e.json"
CF_P3D = ".softhouse/capture/t58-counterfactuals/out/t58-counterfactuals-pass3d.json"

PIN = json.load(open(".softhouse/vectors/PIN.json"))
DEC1 = PIN["dec1_revision"]
COMMIT = PIN["fineract_commit"]


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------------------
# exact decimal text -> minor units. No float, ever.
# ---------------------------------------------------------------------------

def minor(text, digits):
    """Return (minor_units_string, over_scaled_bool)."""
    t = text.strip()
    neg = t.startswith("-")
    if neg:
        t = t[1:]
    ip, _, fp = t.partition(".")
    if ip == "":
        ip = "0"
    over = False
    if len(fp) > digits:
        tail = fp[digits:]
        if tail.strip("0"):
            raise SystemExit(
                "INADMISSIBLE: %r carries a SIGNIFICANT digit beyond the currency "
                "scale %d. The exact conversion is impossible and this script will "
                "not round a transcription." % (text, digits))
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
    """'21.6' -> exact lowest-terms {27, 125}. Percent, so denominator x 100."""
    ip, _, fp = text.partition(".")
    num = int(ip + fp)
    den = 10 ** len(fp) * 100
    from math import gcd
    g = gcd(abs(num), den) or 1
    return {"numerator": num // g, "denominator": den // g}


# ---------------------------------------------------------------------------
# the named counterfactuals, and where the source refutes each one
# ---------------------------------------------------------------------------

CF = {
    "TEXTBOOK": dict(
        id="INTEREST-SEGMENT-TEXTBOOK-BALANCE-TIMES-RATEFACTOR",
        capability="schedule.core",
        description=(
            "Computes a segment's interest as the textbook balance x rateFactor -- one exact "
            "expression rounded ONCE -- instead of the reference oracle's THREE separately "
            "MathContext-rounded operations in a fixed order [InterestPeriod.java:154-157: "
            "multiply(mc), then divide by the segment's lengthTillDue (mc), then multiply by the "
            "segment's own day count (mc)]. Operations two and three cancel ALGEBRAICALLY inside "
            "the graded domain -- lengthTillDue equals the segment length on every segment "
            "carrying a balance -- and DO NOT cancel numerically at 19 significant digits. This "
            "reading is the single most natural thing a port author writes, and until this vector "
            "no promoted capture could tell it from the oracle."),
    ),
    "NOSETSCALE": dict(
        id="RATE-FACTOR-WITHOUT-TRAILING-SETSCALE",
        capability="schedule.core",
        description=(
            "Omits the trailing setScale(RateFactorScale, HALF_UP) the reference oracle applies to "
            "the rate factor at ProgressiveEMICalculator.java:1962, keeping instead the 19 "
            "SIGNIFICANT DIGITS the preceding operations left. A scale is not a precision: on a "
            "quantity of order 0.005 to 0.02 a 19-decimal-place scale is strictly lossier than 19 "
            "significant digits, so dropping the step is not a no-op. DEC-1 says of this step that "
            "'the loss reaches a payable amount'; this vector is the first OBSERVATION of that "
            "claim on a concrete request, and it lands on an interest cell."),
    ),
    "PERIODRATIO": dict(
        id="INTEREST-RATE-FACTOR-MULTIPLIER-REPAYMENTEVERY-NOT-PERIODRATIO",
        capability="schedule.core",
        description=(
            "Passes RepaymentEvery into the rate-factor multiplier slot that the INTEREST call "
            "site fills with periodRatio. The reference oracle has TWO call sites with TWO "
            "specifications: calculateRateFactorPerPeriodForInterest passes periodRatio "
            "[ProgressiveEMICalculator.java:1412-1413] and calculateRateFactorPerPeriod passes "
            "repaymentEvery [:1536-1537]. They coincide exactly when every repayment window sits "
            "on the schedule-start lattice, which is why an on-lattice corpus cannot tell them "
            "apart at all; move the month-end re-anchor's seed off that lattice and they diverge."),
    ),
    "SEEDSTART": dict(
        id="PERIODRATIO-SEED-ALWAYS-SCHEDULE-START",
        capability="schedule.core",
        description=(
            "Makes calculateSeedDate return the schedule start unconditionally, instead of "
            "returning it only when BOTH conjuncts hold and the period's own from-date otherwise "
            "[ProgressiveEMICalculator.java:1477-1480]. The two seeds of this generator are "
            "different dates -- the month-end re-anchor is seeded on the DISBURSEMENT and "
            "calculateSeedDate on the SCHEDULE START -- and that asymmetry is the entire mechanism "
            "by which periodRatio leaves the lattice."),
    ),
    "REANCHORGT": dict(
        id="MONTHEND-REANCHOR-GUARD-STRICTLY-GREATER-THAN-28",
        capability="monthend.reanchor",
        description=(
            "Weakens the month-end re-anchor guard from dateDay >= 28 to dateDay > 28. The "
            "reference oracle's adjustDate fires on seedDay > 28 AND dateDay >= 28 "
            "[DefaultScheduledDateGenerator.java:168-176] -- an asymmetric pair of comparisons that "
            "reads like a typo and is not one. Weakening it silently drops the re-anchor on every "
            "period whose stepped date lands on the 28th, which is exactly what a leap February "
            "produces."),
    ),
    "MONTHENDCLAMP": dict(
        id="MONTHEND-CONTINUE-FROM-CLAMPED-DAY",
        capability="monthend.reanchor",
        description=(
            "Clamps the stepped date into the short month's length and then CONTINUES FROM THE "
            "CLAMPED DAY, instead of re-anchoring on the disbursement-date seed "
            "[DefaultScheduledDateGenerator.java:168-176]. A schedule seeded on 31 January must "
            "return to the 31st the moment a month is long enough: 2024-02-29, then 2024-03-31 -- "
            "not 2024-03-29. Clamp-and-forget is the obvious implementation and it is wrong."),
    ),
    "SMOOTHINGOFF": dict(
        id="EMI-SMOOTHING-LOOP-OMITTED",
        capability="schedule.core",
        description=(
            "Omits checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods "
            "[ProgressiveEMICalculator.java:1258-1309], which the oracle calls on every ordinary "
            "generation at :749 and which re-levels the installment across the related repayment "
            "periods whenever the final-period residual exceeds its guard. DEC-1 calls reproducing "
            "this loop 'a conformance obligation, not backlog' (contract.go:1660-1661)."),
    ),
    "NOFINALADJ": dict(
        id="LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT",
        capability="schedule.core",
        description=(
            "Emits the level installment in the final period like every other period, so the final "
            "principal is (installment - interest) rather than the WHOLE REMAINING BALANCE "
            "[ProgressiveEMICalculator.java:1160-1219]. The schedule then does not amortize to "
            "exactly zero."),
    ),
}

CF_PROVENANCE = (
    "COUNTERFACTUAL PROVENANCE. The counterfactual value is MEASURED, not asserted: a scratch copy "
    "of the port at /tmp/t58mut with exactly one named change applied, run on this vector's own "
    "request. The patches are .softhouse/capture/t58-counterfactuals/src/apply-mutations-*.py and "
    "the runner is src/t58cf.go.txt; the raw per-cell output is out/t58-counterfactuals-*.json. "
    "The model's faithfulness is not assumed -- with the change switched OFF it reproduces all 508 "
    "graded money cells of the 20 in-domain capture cases it was run against, with ZERO "
    "mismatches, so the only thing a reported margin can be measuring is the named change.")


# ---------------------------------------------------------------------------
# capture readers
# ---------------------------------------------------------------------------

def read_p3e():
    doc = json.load(open(P3E_REF))
    return {c["id"]: c for c in doc["captures"]}


def read_p3d():
    doc = json.load(open(P3D_REF))
    return {c["id"]: c for c in doc["captures"]}


def read_cf(path):
    return {r["case"]: r for r in json.load(open(path))}


def period_from(p):
    return p.get("fromDate") or p.get("periodFromDate")


def fee_key(p):
    return "fee" if "fee" in p else "feeAmount"


# ---------------------------------------------------------------------------
# expect block -- pure transcription
# ---------------------------------------------------------------------------

def build_expect(cap, digits):
    obs = cap["observed"]
    periods = []
    over_total = 0
    for p in obs["periods"]:
        kind = p["type"]
        row = {
            "kind": kind,
            "installment_number": p.get("periodNumber") or 0,
            "from_date": date(period_from(p)),
            "due_date": date(p["dueDate"]),
        }
        unrecorded = []
        over = []

        if p.get("periodNumber") is None:
            unrecorded.append("installment_number")

        # principal -- recorded on every row of both capture shapes
        pm, o = minor(p["principal"], digits)
        row["principal_minor"] = pm
        row["principal_major_text"] = p["principal"]
        if o:
            over.append("principal_minor")

        # interest -- absent on a DISBURSEMENT row in both shapes
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

        # outstanding principal -- the capture's own `balance` column. The T39
        # harness does NOT record it on a DISBURSEMENT row; pass 3d does.
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
            over_total += len(over)
        row["observed_total_due_minor"] = (
            minor(p["total"], digits)[0] if p.get("total") is not None else None)
        periods.append(row)

    ti, _ = minor(obs["totalInterestAmount"], digits)
    return {
        "kind": "schedule",
        "sentinel": "",
        "last_repayment_due_date": None,
        "observed_total_interest_minor": ti,
        "periods": periods,
    }, over_total


def ambient(cap):
    """The ambient MoneyHelper MathContext, READ OFF THE CAPTURE, never assumed.

    T39's harness records it as one text field; pass 3b/3c/3d record it as two
    typed fields as well. Both are parsed rather than defaulted -- a vector whose
    ambient context is asserted rather than observed is exactly the escape hatch
    the store's probe guard exists to close.
    """
    i = cap["inputs"]
    if "ambientMoneyHelperPrecision" in i:
        return {"precision": i["ambientMoneyHelperPrecision"],
                "rounding_mode": i["ambientMoneyHelperRoundingMode"]}
    text = i["ambientMoneyHelperMathContext"]          # "precision=19 roundingMode=HALF_UP"
    parts = dict(kv.split("=", 1) for kv in text.split())
    return {"precision": int(parts["precision"]), "rounding_mode": parts["roundingMode"]}


def build_request(cap):
    i = cap["inputs"]
    digits = i["currencyDecimalPlaces"]
    every = i.get("repaymentEvery", i.get("repaymentFrequency"))
    amt, over = minor(i["disbursementAmount"], digits)
    if over:
        raise SystemExit("disbursement amount over-scaled: %r" % i["disbursementAmount"])
    return {
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
        "repayment_every": every,
        "repayment_frequency_unit": i["repaymentFrequencyType"],
        "annual_nominal_interest_rate": rate(i["annualNominalInterestRate"]),
        "interest_method": i["interestMethod"],
        "day_count": "FIXED_30_360",
        "down_payment_percentage": {"numerator": 0, "denominator": 1},
        "installment_rounding_multiple_minor": "0",
    }


# ---------------------------------------------------------------------------
# graded_against -- derived from the measured counterfactual reports
# ---------------------------------------------------------------------------

FIELD_MAJOR = {
    "principal_minor": "principal",
    "interest_minor": "interest",
    "outstanding_principal_minor": "outstanding principal",
}


def graded_against(cf_rec, mutations, capabilities, capture_ref, capture_case):
    out = []
    for mut in mutations:
        spec = CF[mut]
        if spec["capability"] not in capabilities:
            raise SystemExit("%s: counterfactual %s needs capability %s, which this vector does not "
                             "require" % (capture_case, mut, spec["capability"]))
        money = cf_rec["divergent"].get(mut, [])
        dates = cf_rec["dateDivergent"].get(mut, [])
        if money:
            worst = max(money, key=lambda c: c["delta"])
            ev = (
                "Derived at the ratified production MathContext (19, HALF_UP). Every OBSERVED value "
                "below is transcribed from capture case %s of %s; only the counterfactual is derived.\n"
                "MARGIN. Over this vector's graded money cells the counterfactual diverges on %d of "
                "%d. The widest single-cell disagreement is at period[%d], column %s: the oracle "
                "OBSERVED %s minor units against the counterfactual's %s, so the margin is |%s - %s| "
                "= %s MINOR UNITS.\n%s"
                % (capture_case, capture_ref, len(money), cf_rec["cells"], worst["row"],
                   worst["field"], worst["observed"], worst["value"], worst["observed"],
                   worst["value"], worst["delta"], CF_PROVENANCE))
            out.append({
                "id": spec["id"],
                "capability": spec["capability"],
                "description": spec["description"],
                "margin_minor": str(worst["delta"]),
                "evidence": ev,
            })
        elif dates:
            cells = []
            shown = []
            for line in dates:
                # "period[N].field observed A, counterfactual B"
                head, rest = line.split(" observed ", 1)
                seen, cf_val = rest.split(", counterfactual ", 1)
                cells.append(head.strip())
                shown.append("%s the oracle was OBSERVED to emit %s, and the counterfactual emits %s "
                             "instead" % (head.strip(), seen.strip(), cf_val.strip()))
            ev = (
                "Derived at the ratified production MathContext (19, HALF_UP). This counterfactual "
                "moves NO money cell on this shape -- all %d graded money cells are identical, which "
                "is why it is recorded as a structural kill with margin 0 rather than as a money kill "
                "with a margin it does not have. It moves %d DATE cells, each of which this vector "
                "records and grades. Cell by cell, the observed value and the wrong one: %s. The "
                "observed dates are transcribed from capture case %s of %s; only the counterfactual "
                "dates are derived.\n%s"
                % (cf_rec["cells"], len(cells), "; ".join(shown), capture_case, capture_ref,
                   CF_PROVENANCE))
            out.append({
                "id": spec["id"],
                "kind": "structural",
                "capability": spec["capability"],
                "description": spec["description"],
                "margin_minor": "0",
                "divergent_cells": cells,
                "evidence": ev,
            })
        else:
            raise SystemExit("%s: counterfactual %s separates NOTHING on this shape. A vector that "
                             "does not kill it may not claim it." % (capture_case, mut))
    return out


# ---------------------------------------------------------------------------
# the promotion table
# ---------------------------------------------------------------------------

P3E_NOTE = (
    "TRANSCRIPTION NOTES. (1) request.currency.code is upper-cased from the capture's own spelling; "
    "admit.go requires upper case and the contract forbids the oracle's lower-case fixture spelling "
    "leaking back out. (2) request.time_zone is DECLARED, not observed: the Path A embeddable seam "
    "takes java.time.LocalDate only and has no time-zone input at all, so Asia/Ulaanbaatar is this "
    "vector's declared interpretation zone for civil dates and grades nothing. (3) "
    "request.rounding.rate_factor_scale is 19 from PIN.json's production_rounding; the capture "
    "records one MathContext precision (19) which is both. (4) On the DISBURSEMENT row, "
    "installment_number and interest_minor are marked unrecorded_fields: the oracle's own record "
    "type LoanSchedulePlanDisbursementPeriod carries four fields and its periodNumber() returns "
    "null, with no interest accessor at all. Its outstanding balance IS recorded by this rig and is "
    "therefore promoted. (5) The capture's per-row totalOutstandingBalance column is deliberately "
    "NOT promoted: it is principal plus interest still to accrue, not an outstanding-principal "
    "figure, and the frozen contract has no field for it. (6) PROVENANCE OF THE SHAPE, AND WHY IT "
    "WAS RE-OBSERVED. Task T39 asked this exact request of the same pinned oracle two fires ago "
    "through a DIFFERENT Path A harness (CapturePeriodRatio.java, "
    ".softhouse/capture/periodratio/out/t39-periodratio.json) and the observation was never "
    "promoted. That harness records only {type, fromDate, dueDate, principal} on a DISBURSEMENT row "
    "and NOT that row's outstanding balance, so a vector transcribed from it must withdraw the cell "
    "as unrecorded -- whereupon the harness's own --self-test replay answers 0 for it and the "
    "balance_roll_forward invariant reads the placeholder as a violation (finding T58-N2, a "
    "D-5-class harness defect one layer down: D-5 taught the CELL comparison to skip an unrecorded "
    "cell; the INVARIANT layer still grades the placeholder). Rather than exempt an invariant to "
    "get a promotion out, pass 3e RE-OBSERVED all fourteen shapes on the pass-3b/3c/3d rig, which "
    "records that column. (7) CROSS-HARNESS REPRODUCTION. Because the requests are field for field "
    "T39's, the two observations are comparable, and they were compared: 14 case pairs, 134 "
    "schedule rows, 1,698 cells, ZERO differences "
    "[.softhouse/capture/t58-counterfactuals/src/cross-harness-t39-vs-pass3e.py]. Two independent "
    "Path A harnesses, two fires apart, agree on every cell either of them recorded.")

P3D_NOTE = (
    "TRANSCRIPTION NOTES. (1) request.currency.code is upper-cased from the capture's own spelling. "
    "(2) request.time_zone is DECLARED, not observed: the Path A embeddable seam has no time-zone "
    "input at all. (3) request.rounding.rate_factor_scale is 19 from PIN.json's production_rounding. "
    "(4) On the DISBURSEMENT row, installment_number and interest_minor are marked unrecorded_fields: "
    "the oracle's own record type LoanSchedulePlanDisbursementPeriod carries four fields and its "
    "periodNumber() returns null, with no interest accessor at all. Its outstanding balance IS "
    "recorded by this rig and is therefore promoted. (5) The capture's per-row "
    "totalOutstandingBalance column is deliberately NOT promoted: the frozen contract has no field "
    "for it. (6) PROVENANCE OF THE SHAPE: task T11's independent adversarial review swept 6,000 "
    "in-graded-domain shapes against five rounding-placement counterfactuals and located this one. "
    "T11 also PREDICTED the divergent cells. The prediction was treated as a hypothesis and never "
    "transcribed: this vector's every cell is what the pinned oracle actually returned on 2026-08-19 "
    "through pass 3d, and the prediction is recorded in the handoff as confirmed or contradicted "
    "against the observation.")

PROMOTE = [
    # (case_id, filename, source, capture_case, title, capabilities, mutations)
    ("P-LAT-Q0a", "P-LAT-Q0a-6x21pt6pct-1M2.json", "p3e", "P-LAT-Q0a",
     "ON-LATTICE CONTROL. MNT 1,200,000.00 over 6 monthly repayments at 21.6% p.a., schedule start "
     "== disbursement == 2024-01-01. Captured by task T39 as the reproduction control for its eight "
     "drift shapes and never promoted. It sits ON the schedule-start lattice, so every one of the "
     "lattice counterfactuals its sibling drift vectors kill moves ZERO cells here -- which is "
     "exactly what makes it a control worth having in the store rather than a redundant shape: it "
     "pins the answer on the lattice while P-DRIFT-A..H pin it off the lattice, and a port that "
     "'fixed' the drift by breaking the on-lattice case would be caught here.",
     ["schedule.core"], ["NOFINALADJ"]),

    ("P-LAT-MID", "P-LAT-MID-6x21pt6pct-mid-month-start.json", "p3e", "P-LAT-MID",
     "MID-MONTH START, ON LATTICE. MNT 1,200,000.00 over 6 monthly repayments at 21.6% p.a., "
     "schedule start == disbursement == 2024-01-15. The whole promoted corpus before this vector "
     "started a schedule on the 1st, the 30th or the 31st of a month; nothing observed a start day "
     "in the ordinary middle of a month, where the month-end rules are all inert and the lattice is "
     "clean. A port that special-cased its way to the right answer on the days the corpus happened "
     "to contain would be caught here.",
     ["schedule.core"], ["NOFINALADJ"]),

    ("P-DRIFT-A", "P-DRIFT-A-drift-start28-disb31-6x21pt6pct.json", "p3e", "P-DRIFT-A",
     "PERIODRATIO DRIFT, the named shape. MNT 1,200,000.00 over 6 monthly repayments at 21.6% p.a., "
     "schedule start 2024-01-28 and disbursement 2024-01-31. THE TWO SEEDS ARE DIFFERENT DATES: the "
     "month-end re-anchor is seeded on the DISBURSEMENT [LoanApplicationTerms.java:583-589] and "
     "calculateSeedDate on the SCHEDULE START [ProgressiveEMICalculator.java:1462]. Every previously "
     "promoted vector had them equal, so every repayment window sat on the schedule-start lattice and "
     "periodRatio was indistinguishable from RepaymentEvery on all 1,350 graded cells. Move them two "
     "days apart across a month end and the lattice breaks from period 2 onward.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "REANCHORGT", "MONTHENDCLAMP", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-DRIFT-B", "P-DRIFT-B-drift-start28-disb29-6x21pt6pct.json", "p3e", "P-DRIFT-B",
     "PERIODRATIO DRIFT at a ONE-DAY seed gap. MNT 1,200,000.00 over 6 monthly repayments at 21.6% "
     "p.a., schedule start 2024-01-28 and disbursement 2024-01-29 -- the smallest gap that still "
     "leaves the lattice, and the shape task T34 hand-worked. It grades the same seam as P-DRIFT-A "
     "at a different offset, so a port that hard-coded a three-day correction would pass A and fail "
     "here.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "REANCHORGT", "MONTHENDCLAMP", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-DRIFT-C", "P-DRIFT-C-drift-12x16pt8pct-5M.json", "p3e", "P-DRIFT-C",
     "PERIODRATIO DRIFT over TWELVE periods. MNT 5,000,000.00 over 12 monthly repayments at 16.8% "
     "p.a., schedule start 2024-01-29 and disbursement 2024-01-31. The drift is not a first-period "
     "artefact: it re-enters every time the re-anchor moves a boundary, so it accumulates over a "
     "full year of periods rather than washing out.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "MONTHENDCLAMP", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-DRIFT-D", "P-DRIFT-D-drift-36x21pt6pct-50M.json", "p3e", "P-DRIFT-D",
     "PERIODRATIO DRIFT at the corpus's WORST MARGIN. MNT 50,000,000.00 over 36 monthly repayments "
     "at 21.6% p.a., schedule start 2024-01-28 and disbursement 2024-01-31. This is the largest "
     "money margin any vector in this store carries by two orders of magnitude, and it is an "
     "ordinary NBFI three-year loan, not a constructed edge case.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "REANCHORGT", "MONTHENDCLAMP", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-DRIFT-E", "P-DRIFT-E-drift-common-year-2025.json", "p3e", "P-DRIFT-E",
     "PERIODRATIO DRIFT in a COMMON year. MNT 1,200,000.00 over 6 monthly repayments at 21.6% p.a., "
     "schedule start 2025-01-28 and disbursement 2025-01-31. Identical to P-DRIFT-A but for the "
     "year: February is 28 days rather than 29, so the re-anchor's clamp lands on a different day "
     "and the drift pattern differs. A port that got the leap case right by accident is caught here.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "REANCHORGT", "MONTHENDCLAMP", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-DRIFT-F", "P-DRIFT-F-drift-smallest-principal-mnt100.json", "p3e", "P-DRIFT-F",
     "PERIODRATIO DRIFT at the SMALLEST principal in the store. MNT 100.00 over 6 monthly repayments "
     "at 21.6% p.a., schedule start 2024-01-28 and disbursement 2024-01-31. The drift is not a "
     "large-number effect: at a hundred tugriks it still moves cells, in single minor units, which is "
     "where a port that rounds early rather than at the currency layer shows itself.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "REANCHORGT", "MONTHENDCLAMP", "NOFINALADJ"]),

    ("P-DRIFT-G", "P-DRIFT-G-drift-seeded-in-march.json", "p3e", "P-DRIFT-G",
     "PERIODRATIO DRIFT seeded in MARCH, not January. MNT 2,500,000.00 over 6 monthly repayments at "
     "16.8% p.a., schedule start 2024-03-28 and disbursement 2024-03-31. Every other drift shape in "
     "this store is seeded in January and therefore meets February immediately; this one meets a "
     "30-day April first. A port whose month-end handling was tuned on February alone is caught here.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "REANCHORGT", "MONTHENDCLAMP", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-DRIFT-H", "P-DRIFT-H-drift-seeded-in-30-day-month.json", "p3e", "P-DRIFT-H",
     "PERIODRATIO DRIFT seeded in a 30-DAY month. MNT 3,000,000.00 over 6 monthly repayments at "
     "16.8% p.a., schedule start 2024-11-28 and disbursement 2024-11-30. The seed day is 30, not 31, "
     "so the re-anchor's min(lengthOfMonth, seedDay) takes the OTHER branch on every long month. "
     "Together with P-DRIFT-A this grades both branches of that min.",
     ["schedule.core", "monthend.reanchor"],
     ["PERIODRATIO", "SEEDSTART", "REANCHORGT", "MONTHENDCLAMP", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-ME-A", "P-ME-A-monthend-3M924149-6x16pt8pct.json", "p3e", "P-ME-A",
     "MONTH-END SPECIAL CASE, and -- unexpectedly -- THE ROUNDING-PLACEMENT SURVIVOR S-1 KILLED "
     "WITHOUT AN ORACLE RUN. MNT 3,924,149.00 over 6 monthly repayments at 16.8% p.a., schedule start "
     "== disbursement == 2024-01-31. The month-end special case in calculatePeriodRatio "
     "[ProgressiveEMICalculator.java:1426-1436] fires on periods 2, 4 and 6. This capture has been "
     "sitting in the tree unpromoted for two fires, and it separates the textbook balance x rateFactor "
     "reading by one minor unit on six of its graded cells -- a survivor the program had planned to "
     "spend an oracle run on. Finding T58-N1.",
     ["schedule.core", "monthend.reanchor"],
     ["TEXTBOOK", "MONTHENDCLAMP", "NOFINALADJ"]),

    ("P-ME-B", "P-ME-B-monthend-1M2-6x21pt6pct.json", "p3e", "P-ME-B",
     "MONTH-END SPECIAL CASE, 31 January seed at 21.6%. MNT 1,200,000.00 over 6 monthly repayments, "
     "schedule start == disbursement == 2024-01-31. Its money columns are identical under the "
     "clamp-and-forget port and it still grades that port, on the DATE column, by nine cells -- the "
     "structural-kill shape this store's README names, at a rate and principal P-02 does not cover.",
     ["schedule.core", "monthend.reanchor"],
     ["MONTHENDCLAMP", "NOFINALADJ"]),

    ("P-ME-C", "P-ME-C-monthend-common-year-2023.json", "p3e", "P-ME-C",
     "MONTH-END SPECIAL CASE in a COMMON year. MNT 1,200,000.00 over 6 monthly repayments at 21.6% "
     "p.a., schedule start == disbursement == 2023-01-31. February is 28 days, so the stepped date "
     "lands on the 28th -- exactly the day the re-anchor guard's dateDay >= 28 admits and a > 28 "
     "reading drops. THIS IS THE ONLY VECTOR IN THE STORE THAT GRADES THAT COMPARISON, and it grades "
     "it structurally: the money is unchanged and nine dates move.",
     ["schedule.core", "monthend.reanchor"],
     ["REANCHORGT", "MONTHENDCLAMP", "NOFINALADJ"]),

    ("P-ME-D", "P-ME-D-monthend-seed-day-30.json", "p3e", "P-ME-D",
     "MONTH-END SPECIAL CASE firing on ONE period only. MNT 1,200,000.00 over 6 monthly repayments at "
     "21.6% p.a., schedule start == disbursement == 2024-01-30. Seed day 30 rather than 31, so "
     "min(lengthOfMonth, seedDay) returns the seed on every month except February and the special "
     "case fires exactly once.",
     ["schedule.core", "monthend.reanchor"],
     ["MONTHENDCLAMP", "NOFINALADJ"]),

    ("P-RND-S1-21021587pt50-6x21pt6pct",
     "P-RND-S1-21021587pt50-6x21pt6pct-textbook-ratefactor.json", "p3d",
     "P-RND-21021587PT50-6x21PT6",
     "ROUNDING PLACEMENT S-1, OBSERVED AT LAST. MNT 21,021,587.50 over 6 monthly repayments at 21.6% "
     "p.a., schedule start == disbursement == 2024-01-01 -- an ordinary on-lattice MNT loan. It "
     "separates the textbook balance x rateFactor reading from the reference oracle's three "
     "separately MathContext-rounded operations [InterestPeriod.java:154-157] IN A PAYABLE AMOUNT: "
     "interest on installment 1 and principal on every installment thereafter. That reading had been "
     "argued from source three times across this program and OBSERVED ZERO TIMES; this vector is the "
     "observation. Captured by pass 3d specifically for it.",
     ["schedule.core"], ["TEXTBOOK", "SMOOTHINGOFF", "NOFINALADJ"]),

    ("P-RND-S2-3139845pt86-6x7pct",
     "P-RND-S2-3139845pt86-6x7pct-ratefactor-setscale.json", "p3d",
     "P-RND-3139845PT86-6x7PT0",
     "ROUNDING PLACEMENT S-2, OBSERVED AT LAST. MNT 3,139,845.86 over 6 monthly repayments at 7.0% "
     "p.a., schedule start == disbursement == 2024-01-01 -- an ordinary on-lattice MNT loan. It "
     "separates the rate factor computed WITHOUT the trailing setScale at "
     "ProgressiveEMICalculator.java:1962 from the oracle's own, on installment 2's INTEREST: MNT "
     "15,307.35 observed against MNT 15,307.36. DEC-1 claims of that setScale that 'the loss reaches "
     "a payable amount'; this vector is the first observation of the claim on a concrete request. "
     "A rounding step twice dismissed as redundant in this program's history and twice found to be a "
     "money defect.",
     ["schedule.core"], ["NOSETSCALE", "NOFINALADJ"]),
]


def main():
    p3e = read_p3e()
    p3d = read_p3d()
    cf3e = read_cf(CF_P3E)
    cf3d = read_cf(CF_P3D)
    sha3e = sha256(P3E_REF)
    sha3d = sha256(P3D_REF)
    at3e = json.load(open(P3E_REF))["attestation"]["capturedAtUtc"]

    written = 0
    over_declared = 0
    for case_id, fname, src, cap_id, title, caps, muts in PROMOTE:
        if src == "p3e":
            cap, cf_rec, ref, sha = p3e[cap_id], cf3e[cap_id], P3E_REF, sha3e
            note, captured_at = P3E_NOTE, at3e
            prov_note = (
                "TRANSCRIBED, never computed, from Path A capture pass 3e "
                "(.softhouse/capture/src/run-pass3e.sh, Capture3e.java). Every expect cell is a value "
                "literally present in the referenced capture for capture case %s; the only "
                "transformation is exact textual major->minor scaling, and the oracle's own emitted "
                "characters are carried alongside in the *_major_text cross-check fields so the "
                "scaling is mechanically re-checkable. Pass 3e is pass 3d's rig with a new case list "
                "and NOT ONE check weakened; it reproduced three already-committed observations as rig "
                "calibrations before emitting anything -- P-CAL at (12, HALF_UP) and P-CAL-P00 at the "
                "production (19, HALF_UP) against pass 3b, and P-CAL-EMI6 against pass 3c's "
                "P-EMI-6-1M014632, an MNT case at production precision whose observation is already a "
                "promoted parity vector -- with inputs and observed blocks identical in all three. "
                "Promotion script: .softhouse/handoff/T58-promote-vectors.py (task T58)." % cap_id)
        else:
            cap, cf_rec, ref, sha = p3d[cap_id], cf3d[cap_id], P3D_REF, sha3d
            note = P3D_NOTE
            captured_at = json.load(open(P3D_REF))["attestation"]["capturedAtUtc"]
            prov_note = (
                "TRANSCRIBED, never computed, from Path A capture pass 3d "
                "(.softhouse/capture/src/run-pass3d.sh, Capture3d.java). Every expect cell is a value "
                "literally present in the referenced capture for capture case %s; the only "
                "transformation is exact textual major->minor scaling. Pass 3d is pass 3c's rig with a "
                "new case list and ONE MORE precondition check, not one weakened: it reproduced THREE "
                "already-committed observations as rig calibrations before emitting anything -- P-CAL "
                "at (12, HALF_UP) and P-CAL-P00 at the production (19, HALF_UP) against pass 3b, and "
                "P-CAL-EMI6 against pass 3c's P-EMI-6-1M014632, an MNT case at production precision "
                "whose observation is already a promoted parity vector. Inputs and observed blocks "
                "were identical in all three. Promotion script: "
                ".softhouse/handoff/T58-promote-vectors.py (task T58)." % cap_id)

        if cf_rec.get("baselineMismatches", 0) or cf_rec.get("baselineDateMismatches", 0):
            raise SystemExit("%s: the counterfactual model's UNMUTATED reading does not reproduce the "
                             "capture; no margin from it may be believed" % cap_id)

        digits = cap["inputs"]["currencyDecimalPlaces"]
        expect, over = build_expect(cap, digits)
        over_declared += over

        vec = {
            "schema": "gerege.loanschedule.vector/v1",
            "case_id": case_id,
            "context": "loanschedule",
            "class": "parity",
            "title": title,
            "dec1_revision": DEC1,
            "_note": note,
            "capabilities_required": caps,
            "graded_against": graded_against(cf_rec, muts, caps, ref, cap_id),
            "retires_when_capability_graded": "",
            "provenance": {
                "kind": "oracle-capture",
                "note": prov_note,
                "capture_ref": ref,
                "capture_sha256": sha,
                "capture_case_id": cap_id,
                "citation": "",
            },
            "oracle": {
                "fineract_commit": COMMIT,
                "seam": "path_a_embeddable",
                "captured_at": captured_at,
                "threaded_mathcontext": {
                    "precision": cap["inputs"]["mathContextPrecision"],
                    "rounding_mode": cap["inputs"]["mathContextRoundingMode"],
                },
                "ambient_mathcontext": ambient(cap),
            },
            "request": build_request(cap),
            "expect": expect,
            "invariant_exemptions": [],
        }

        path = os.path.join(VECTORS, fname)
        if os.path.exists(path):
            raise SystemExit("refusing to overwrite an existing vector: %s" % path)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(vec, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        written += 1
        print("wrote %-58s  %d rows, %d counterfactuals" % (fname, len(expect["periods"]), len(muts)))

    print("\n%d vectors written, %d over-scaled money columns declared" % (written, over_declared))


if __name__ == "__main__":
    main()
