#!/usr/bin/env python3
"""T8-promote: mechanical promotion of Path A capture pass 3b into the vector store.

Every `expect` cell is TRANSCRIBED from .softhouse/capture/out/capture-prod3b-raw.json.
The only transformation applied to an observed value is exact decimal -> minor-unit
scaling, done textually (no float is constructed at any point, in either direction).

Counterfactual margins ARE derived -- they are claims about hypothetical WRONG PORTS,
never about the oracle -- and the arithmetic is emitted verbatim into each entry's
`evidence` field so a reader can re-derive it without running this script.
"""
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from math import gcd

# HARDENED BY T203 (22 August 2026) - P-22, P-48 rule 4.  This file REUSES the
# shared store guard (`t203_store_guard.py`, T178's shape transposed to a
# create-only store writer) and contains no copy of it.
#
# T203 FOUND THIS FILE, WHICH T196's F-2 AND T198's CORRECTION BOTH MISSED.
# They named FOUR vector-store writers; this is a SIXTH, and it was a bare
# truncation of the live store exactly as T74/T61/T64 were:
#     OUT = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")
#     with open(path, "w") as fh: json.dump(v, fh, ...)
# with no authorisation, no existence check and no atomicity.  It is the
# WIDEST-REACHING of the six: ELEVEN live parity vectors, including
# `P-00-baseline-6x7pct.json`, the corpus baseline
# (T203-evidence/T57-T8-EXPOSURE.txt).
#
# WHY THE CLASSIFIER DID NOT CATCH IT - the same runtime-computed-constant
# fail-open documented at the head of `T57-promote-emi-vectors.py`: `OUT` is
# `os.path.join(ROOT, ...)` with `ROOT` derived from `__file__` at runtime, so
# T179's classifier scored the target UNKNOWN rather than TRUSTED, and
# `--enforce` does not trip on UNKNOWN.
#
# The caller's own directory goes at the FRONT of sys.path so the module cannot
# be shadowed from the cwd or the environment; a missing module fails CLOSED.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t203_store_guard as guard  # noqa: E402

NAME = 'T8-promote-vectors'

# Argv-only authorisation phrase - never an environment variable, for the
# reason recorded in the guard module.  Authorises CREATING new vectors in the
# live store; it does NOT authorise overwriting an existing one, and nothing
# does.
AUTHORISE_TOKEN = (
    'I-AM-PROMOTING-T8-PASS3B-BASELINE-VECTORS-INTO-THE-LIVE-GOLDEN-VECTOR-STORE')

CAP_REL = ".softhouse/capture/out/capture-prod3b-raw.json"
OUT = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")
CAP_SHA = "8d23c48fa13c04677b51bacdf07d101d6a061c79815d76b4983eccdbac945c79"
PIN = json.load(open(os.path.join(ROOT, ".softhouse", "vectors", "PIN.json")))
CAPTURED_AT = "2026-08-18T15:20:53.441500460Z"
SEAM = "path_a_embeddable"
MINOR_DIGITS = 2


def minor(text, digits=MINOR_DIGITS):
    """Exact major-unit decimal string -> integer minor-unit string. Textual only."""
    s = text.strip()
    assert s and not s.startswith("-"), "unexpected sign in %r" % text
    if "." in s:
        ip, fp = s.split(".", 1)
    else:
        ip, fp = s, ""
    assert ip.isdigit() and (fp == "" or fp.isdigit()), "non-numeric %r" % text
    if len(fp) > digits:
        excess = fp[digits:]
        assert excess.strip("0") == "", (
            "SCALE VIOLATION: %r carries significant digits beyond %d minor-unit "
            "digits; per README this is a harness bug, not something to round"
            % (text, digits))
        fp = fp[:digits]
    fp = fp + "0" * (digits - len(fp))
    v = (ip + fp).lstrip("0") or "0"
    return v


def half_up(x, places=2):
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def date_obj(iso):
    y, m, dd = iso.split("-")
    return {"year": int(y), "month": int(m), "day": int(dd)}


def rate_rational(percent_text):
    """Annual nominal rate PERCENT text -> exact lowest-terms rational of the RATE."""
    q = Decimal(percent_text) / Decimal(100)
    sign, digits, exp = q.as_tuple()
    assert sign == 0
    if exp >= 0:
        num, den = int(q), 1
    else:
        num = int("".join(map(str, digits)))
        den = 10 ** (-exp)
    g = gcd(num, den)
    return {"numerator": num // g, "denominator": den // g}


cap = json.load(open(os.path.join(ROOT, CAP_REL)), parse_float=str, parse_int=str)
cases = {c["id"]: c for c in cap["captures"]}

PROMOTE = ["P-00", "P-01", "P-02", "P-02b", "P-03", "P-04f", "P-04t",
           "P-MNT-5M", "P-MNT-1M2", "P-MNT-50M", "P-MNT-4M999"]

SLUG = {
    "P-00":        "P-00-baseline-6x7pct",
    "P-01":        "P-01-18x18pt5pct-principal-87654321",
    "P-02":        "P-02-monthend-seed-day-31",
    "P-02b":       "P-02b-monthend-seed-day-30",
    "P-03":        "P-03-disbursement-on-repayment-due-date",
    "P-04f":       "P-04f-fulltermfortranche-false",
    "P-04t":       "P-04t-fulltermfortranche-true",
    "P-MNT-5M":    "P-MNT-5M-18x18pt5pct",
    "P-MNT-1M2":   "P-MNT-1M2-12x21pt6pct",
    "P-MNT-50M":   "P-MNT-50M-36x16pt8pct",
    "P-MNT-4M999": "P-MNT-4M999-18x18pt5pct",
}

TITLE = {
    "P-00": ("Baseline declining-balance schedule, 6 monthly repayments at 7.0% p.a. on 100.00 "
             "major units, FIXED_30/360, observed at the ratified production MathContext "
             "(19, HALF_UP). The calibration shape C-00 re-captured at production precision."),
    "P-01": ("18 monthly repayments at 18.5% p.a. on 87,654,321.00 major units: a long term and a "
             "large, deliberately non-round principal, so a per-period rounding error accumulates "
             "into a visible balance rather than cancelling."),
    "P-02": ("MONTH-END RE-ANCHOR, seed day 31. Disbursed 2024-01-31; period 1 due 2024-02-29 "
             "(clamped to a leap February), and period 2 due 2024-03-31 -- RE-ANCHORED on the "
             "disbursement-date seed rather than continued from the clamped day. Under "
             "FIXED_30/360 every money column is byte-identical to P-00, so the re-anchor kill is "
             "in the due_date column at zero money margin: see the STRUCTURAL graded_against entry."),
    "P-02b": ("MONTH-END RE-ANCHOR, seed day 30. Disbursed 2024-01-30; period 1 due 2024-02-29 "
              "(clamped), period 2 due 2024-03-30 -- re-anchored to 30, NOT continued from the "
              "clamped 29. Paired with P-02 (seed 31) this separates 'remember the seed day' from "
              "'remember the clamped day'. Money is again identical to P-00 under FIXED_30/360."),
    "P-03": ("DISBURSEMENT DATED EXACTLY ON A REPAYMENT DUE DATE. Schedule start 2024-01-01, "
             "disbursement 2024-02-01. The oracle emits an all-zero REPAYMENT row 1 "
             "(2024-01-01 -> 2024-02-01) FIRST, then the DISBURSEMENT row dated 2024-02-01, then "
             "repayments 2..6 -- refuting the naive 'sort by date, disbursement first' rule at a "
             "reachable boundary. The level installment is 20.35, the EMI over the FIVE periods "
             "remaining after the disbursement date, not 17.01 over numberOfRepayments = 6."),
    "P-04f": ("allowFullTermForTranche = FALSE at the production MathContext. The frozen contract "
              "carries no such field, so this vector's request is byte-identical to P-00's and "
              "P-04t's; the three are one shape observed three times, not three shapes."),
    "P-04t": ("allowFullTermForTranche = TRUE at the production MathContext. Observed output is "
              "byte-identical to P-04f and P-00, which is the evidence that the flag is INERT on "
              "this shape. The contract has no field for it, so this vector's request is "
              "byte-identical to P-00's and P-04f's."),
    "P-MNT-5M": ("MNT 5,000,000.00 over 18 monthly repayments at 18.5% p.a. -- the Mongolian "
                 "RTGS/ACH+ routing threshold amount, carried here purely as a realistic MNT "
                 "principal; the schedule generator knows nothing of payment rails."),
    "P-MNT-1M2": ("MNT 1,200,000.00 over 12 monthly repayments at 21.6% p.a. -- the shape whose "
                  "period-1 interest is the HALF_UP/HALF_EVEN tie witness recorded in "
                  "capabilities.json, observed here at the ratified HALF_UP."),
    "P-MNT-50M": ("MNT 50,000,000.00 over 36 monthly repayments at 16.8% p.a. -- the longest term "
                  "and largest principal in the pass-3b set, so the final-period balancing "
                  "remainder is carried through 36 roundings."),
    "P-MNT-4M999": ("MNT 4,999,999.00 over 18 monthly repayments at 18.5% p.a. -- one minor unit "
                    "under P-MNT-5M's principal, so a port that rounds the principal anywhere on "
                    "the way in produces P-MNT-5M's schedule instead of this one."),
}


def build(case_id):
    c = cases[case_id]
    inp = c["inputs"]
    obs = c["observed"]

    assert inp["mathContextPrecision"] == "19", case_id
    assert inp["mathContextRoundingMode"] == "HALF_UP", case_id
    assert inp["ambientMoneyHelperPrecision"] == "19", case_id
    assert inp["ambientMoneyHelperRoundingMode"] == "HALF_UP", case_id
    assert inp["currencyDecimalPlaces"] == "2", case_id
    assert inp["daysInMonth"] == "DAYS_30" and inp["daysInYear"] == "DAYS_360", case_id
    assert inp["interestMethod"] == "DECLINING_BALANCE", case_id
    assert inp["repaymentFrequencyType"] == "MONTHS" and inp["repaymentFrequency"] == "1", case_id
    assert inp["downPaymentEnabled"] is False and inp["downPaymentPercentage"] == "0", case_id
    assert inp["installmentAmountInMultiplesOf"] is None, case_id
    assert inp["currencyInMultiplesOf"] is None, case_id
    assert inp["fixedLength"] is None, case_id
    assert case_id not in PIN["never_promotable_capture_case_ids"], case_id

    periods = []
    for p in obs["periods"]:
        row = {
            "kind": p["type"],
            "installment_number": int(p["periodNumber"]) if "periodNumber" in p else 0,
            "from_date": date_obj(p["periodFromDate"]),
            "due_date": date_obj(p["dueDate"]),
            "principal_minor": minor(p["principal"]),
            "interest_minor": minor(p["interest"]) if "interest" in p else "",
            "outstanding_principal_minor": minor(p["balance"]),
            "principal_major_text": p["principal"],
            "interest_major_text": p.get("interest", ""),
            "outstanding_principal_major_text": p["balance"],
            "unrecorded_fields": [],
            "observed_total_due_minor": minor(p["total"]) if "total" in p else None,
        }
        if p["type"] == "DISBURSEMENT":
            # The oracle's own record type LoanSchedulePlanDisbursementPeriod has four
            # fields (periodFromDate, periodDueDate, principalAmount,
            # outstandingLoanBalance) and periodNumber() returns null. There is no
            # interest accessor. Capture3b.java:459-462 emits every field the record
            # carries, so these two cells were NOT OBSERVED -- the absence is a property
            # of the oracle's type, not an omission by the capture harness.
            row["unrecorded_fields"] = ["installment_number", "interest_minor"]
        periods.append(row)

    v = {
        "schema": "gerege.loanschedule.vector/v1",
        "case_id": case_id,
        "context": "loanschedule",
        "class": "parity",
        "title": TITLE[case_id],
        "dec1_revision": PIN["dec1_revision"],
        "_note": note(case_id, inp, obs),
        "capabilities_required": capabilities(case_id),
        "graded_against": counterfactuals(case_id, obs),
        "retires_when_capability_graded": "",
        "provenance": {
            "kind": "oracle-capture",
            "note": (
                "TRANSCRIBED, never computed, from Path A capture pass 3b. Every expect cell is a "
                "value literally present in the referenced capture for capture case %s; the only "
                "transformation is exact textual major->minor scaling (\"16.43\" -> \"1643\"), and "
                "the oracle's own emitted characters are carried alongside in the *_major_text "
                "cross-check fields so the scaling is mechanically re-checkable. Promotion script: "
                ".softhouse/handoff/T8-promote-vectors.py (task T8-promote)." % case_id),
            "capture_ref": CAP_REL,
            "capture_sha256": CAP_SHA,
            "capture_case_id": case_id,
            "citation": "",
        },
        "oracle": {
            "fineract_commit": PIN["fineract_commit"],
            "seam": SEAM,
            "captured_at": CAPTURED_AT,
            "threaded_mathcontext": {"precision": 19, "rounding_mode": "HALF_UP"},
            "ambient_mathcontext": {"precision": 19, "rounding_mode": "HALF_UP"},
        },
        "request": {
            "time_zone": "Asia/Ulaanbaatar",
            "currency": {
                "code": inp["currencyCode"].upper(),
                "minor_unit_digits": int(inp["currencyDecimalPlaces"]),
            },
            "rounding": {
                "significant_digits": 19,
                "rate_factor_scale": 19,
                "mode": "HALF_UP",
            },
            "schedule_start_date": date_obj(inp["scheduleGenerationStartDate"]),
            "disbursements": [{
                "date": date_obj(inp["disbursementDate"]),
                "amount_minor": minor(inp["disbursementAmount"]),
            }],
            "number_of_repayments": int(inp["numberOfRepayments"]),
            "repayment_every": int(inp["repaymentFrequency"]),
            "repayment_frequency_unit": "MONTHS",
            "annual_nominal_interest_rate": rate_rational(inp["annualNominalInterestRate"]),
            "interest_method": "DECLINING_BALANCE",
            "day_count": "FIXED_30_360",
            "down_payment_percentage": {"numerator": 0, "denominator": 1},
            "installment_rounding_multiple_minor": "0",
        },
        "expect": {
            "kind": "schedule",
            "sentinel": "",
            "last_repayment_due_date": None,
            "observed_total_interest_minor": minor(obs["totalInterestAmount"]),
            "periods": periods,
        },
        "invariant_exemptions": [],
    }

    # Cross-check: the disbursed amount the request states must equal the amount the
    # oracle's own DISBURSEMENT row reports advanced. Both are transcribed; this only
    # catches a promotion-script slip.
    disb_row = [p for p in periods if p["kind"] == "DISBURSEMENT"]
    assert len(disb_row) == 1, case_id
    assert disb_row[0]["principal_minor"] == v["request"]["disbursements"][0]["amount_minor"], case_id
    assert disb_row[0]["outstanding_principal_minor"] == disb_row[0]["principal_minor"], case_id
    return v


def capabilities(case_id):
    if case_id in ("P-02", "P-02b"):
        return ["schedule.core", "monthend.reanchor"]
    return ["schedule.core"]


# ---------------------------------------------------------------------------
# Counterfactuals. Derived, not observed. Each margin is re-derived below from
# cells that ARE observed, and the arithmetic is written into `evidence`.
# ---------------------------------------------------------------------------

def paying_rows(obs):
    return [p for p in obs["periods"] if p["type"] == "REPAYMENT"]


def cf_final_balancing(case_id, obs):
    """A port that applies the level installment in the FINAL period too, instead of
    setting the final principal to the whole remaining balance."""
    rows = paying_rows(obs)
    non_zero = [r for r in rows if r["total"] != "0.00"]
    last = non_zero[-1]
    level = non_zero[0]["total"]
    if level == last["total"]:
        return None
    cf_principal = half_up(Decimal(level) - Decimal(last["interest"]))
    observed = Decimal(last["principal"])
    margin = abs(int(minor(str(observed))) - int(minor(str(cf_principal))))
    if margin <= 0:
        return None
    return {
        "id": "LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT",
        "capability": "schedule.core",
        "description": (
            "Emits the level installment in the final period like every other period, so the "
            "final principal is (installment - interest) instead of the WHOLE REMAINING "
            "BALANCE. The schedule then does not amortize to exactly zero."),
        "margin_minor": str(margin),
        "evidence": (
            "Derived at (19, HALF_UP) from cells observed in this capture. Observed level "
            "installment (row total on every non-final paying period) = %s; observed FINAL row "
            "total = %s, so the oracle does NOT carry the level installment into the final "
            "period. Counterfactual final principal = level installment %s - observed final "
            "interest %s = %s. Observed final principal = %s. Margin = |%s - %s| = %d minor "
            "units, and the counterfactual's closing balance is non-zero, so the "
            "principal_amortizes_to_zero invariant also catches it."
            % (level, last["total"], level, last["interest"], cf_principal, last["principal"],
               minor(last["principal"]), minor(str(cf_principal)), margin)),
    }


def cf_straight_line(case_id, obs, n_repayments, disbursed_major):
    """A port that divides principal evenly instead of taking it as the balancing
    remainder of a declining-balance level installment."""
    rows = [r for r in paying_rows(obs) if r["total"] != "0.00"]
    flat = half_up(Decimal(disbursed_major) / Decimal(n_repayments))
    flat_minor = int(minor(str(flat)))
    worst = None
    for idx, r in enumerate(rows, start=1):
        delta = abs(int(minor(r["principal"])) - flat_minor)
        if worst is None or delta > worst[0]:
            worst = (delta, idx, r)
    margin, idx, r = worst
    if margin <= 0:
        return None
    return {
        "id": "STRAIGHT-LINE-PRINCIPAL-DIVISION",
        "capability": "schedule.core",
        "description": (
            "Splits the principal evenly across the repayments (principal / n each period) and "
            "adds declining-balance interest on top, instead of taking principal as the "
            "BALANCING REMAINDER of a level installment after interest. Produces a rising total "
            "due rather than a level one."),
        "margin_minor": str(margin),
        "evidence": (
            "Derived at (19, HALF_UP). Counterfactual per-period principal = disbursed %s / %d "
            "= %s (HALF_UP to 2dp). Widest disagreement is at paying period %d, where the oracle "
            "OBSERVED principal %s (%s minor units) against the counterfactual's %s (%s minor "
            "units): margin = %d minor units. The disbursed amount and every observed principal "
            "are transcribed from this capture; only the division is derived."
            % (disbursed_major, n_repayments, flat, idx, r["principal"], minor(r["principal"]),
               flat, flat_minor, margin)),
    }


def counterfactuals(case_id, obs):
    inp = cases[case_id]["inputs"]
    out = []
    cf = cf_final_balancing(case_id, obs)
    if cf:
        out.append(cf)
    if case_id != "P-03":
        cf = cf_straight_line(case_id, obs, int(inp["numberOfRepayments"]),
                              inp["disbursementAmount"])
        if cf:
            out.append(cf)
    if case_id == "P-03":
        out.append({
            "id": "EMI-DENOMINATOR-USES-NUMBER-OF-REPAYMENTS-NOT-PERIODS-AFTER-DISBURSEMENT",
            "capability": "schedule.core",
            "description": (
                "Computes the level installment over numberOfRepayments (6) instead of over the "
                "periods that actually remain after the disbursement date (5), because the "
                "disbursement falls on repayment 1's due date and repayment 1 is therefore "
                "all-zero. Emits 17.01 where the oracle emits 20.35, and the schedule never "
                "amortizes to zero."),
            "margin_minor": "334",
            "evidence": (
                "Derived at (19, HALF_UP). OBSERVED in this capture: level installment 20.35 "
                "(row total on paying periods 2..5), period-2 principal 19.77, period-2 interest "
                "0.58, period-1 all-zero. r = 7.0/100 x 30/360 = 0.005833333333333333333; the "
                "counterfactual's EMI over n=6 is 100.00 x r / (1 - (1+r)^-6) = 17.01 -- which is "
                "exactly the level installment the oracle OBSERVES on P-00, the same shape with "
                "six paying periods. Counterfactual period-2 principal = 17.01 - 0.58 = 16.43 "
                "(1643 minor units, again the value observed on P-00 period 1). Observed 19.77 = "
                "1977 minor units. Margin = 1977 - 1643 = 334 minor units on the first paying "
                "period alone. Driver-derived and independently re-derived by this task."),
        })
        out.append({
            "id": "ROW-ORDER-SORT-BY-DATE-DISBURSEMENT-FIRST",
            "capability": "schedule.core",
            "kind": "structural",
            "description": (
                "Orders the response by (date, disbursement-first) instead of by the contract's "
                "window key. Because the half-open window [FromDate, DueDate) puts a disbursement "
                "dated exactly on period k's due date into period k+1, the naive rule emits the "
                "DISBURSEMENT row BEFORE the all-zero repayment 1 that shares its date; the "
                "oracle emits it AFTER."),
            "margin_minor": "0",
            "divergent_cells": ["row_order"],
            "evidence": (
                "OBSERVED row order in this capture: index 0 = REPAYMENT periodNumber 1 "
                "(2024-01-01 -> 2024-02-01, every money cell 0.00), index 1 = DISBURSEMENT "
                "(2024-02-01, principal 100.00), index 2.. = REPAYMENT 2..6. The counterfactual "
                "emits DISBURSEMENT at index 0 and the all-zero REPAYMENT 1 at index 1 -- the two "
                "rows are transposed, so `kind` and `installment_number` disagree on both rows "
                "while every money column of the pair is unchanged. Margin is exactly 0 minor "
                "units: the kill is structural, in the row order, and the contract_row_ordering "
                "invariant is its worked example. No capability named contract_row_ordering "
                "exists in capabilities.json, so this entry is attributed to schedule.core, whose "
                "description already covers 'repayment period windows'."),
        })
    if case_id == "P-02":
        out.append({
            "id": "MONTHEND-CONTINUE-FROM-CLAMPED-DAY",
            "capability": "monthend.reanchor",
            "kind": "structural",
            "description": (
                "Clamps 31 January + 1 month to 29 February (correct) and then CONTINUES FROM "
                "THE CLAMPED DAY, so every later due date is anchored on 29 instead of "
                "re-anchoring on the disbursement-date seed of 31. Emits 2024-03-29 where the "
                "oracle emits 2024-03-31, and never recovers."),
            "margin_minor": "0",
            "divergent_cells": [
                "period[2].due_date", "period[3].from_date", "period[3].due_date",
                "period[4].from_date", "period[4].due_date", "period[5].from_date",
                "period[5].due_date", "period[6].from_date", "period[6].due_date",
            ],
            "evidence": (
                "Row indices are 0-based over expect.periods, matching the harness's 'row %d' in "
                "diffSchedule. OBSERVED due dates: [0] DISBURSEMENT 2024-01-31, [1] 2024-02-29, "
                "[2] 2024-03-31, [3] 2024-04-30, [4] 2024-05-31, [5] 2024-06-30, [6] 2024-07-31. "
                "COUNTERFACTUAL due dates: [1] 2024-02-29 (agrees), then [2] 2024-03-29, "
                "[3] 2024-04-29, [4] 2024-05-29, [5] 2024-06-29, [6] 2024-07-29; from_date "
                "follows the previous due date, so rows [3]..[6] also diverge on from_date while "
                "[2].from_date agrees at 2024-02-29. MARGIN IS EXACTLY 0 MINOR UNITS, and that is "
                "an observation rather than an assumption: under daysInMonth=DAYS_30 / "
                "daysInYear=DAYS_360 every whole-month period is 30/360 whatever the calendar "
                "dates, and P-00 (seed day 1), P-02 (seed day 31) and P-02b (seed day 30) are "
                "byte-identical in every money column of this same capture -- principal 16.43 / "
                "16.52 / 16.62 / 16.72 / 16.81 / 16.90, interest 0.58 / 0.49 / 0.39 / 0.29 / "
                "0.20 / 0.10, total interest 2.05. Zero money difference is not evidence of "
                "non-gradeability (T55-N2 in a different key): the harness compares date cells, "
                "so this vector genuinely kills the wrong port."),
        })
    if case_id == "P-02b":
        out.append({
            "id": "MONTHEND-CONTINUE-FROM-CLAMPED-DAY",
            "capability": "monthend.reanchor",
            "kind": "structural",
            "description": (
                "Clamps 30 January + 1 month to 29 February (correct) and then CONTINUES FROM "
                "THE CLAMPED DAY, so every later due date is anchored on 29 instead of "
                "re-anchoring on the disbursement-date seed of 30. Emits 2024-03-29 where the "
                "oracle emits 2024-03-30. Paired with P-02 this separates 'remember the seed day' "
                "from 'remember the clamped day': a port that re-anchors on 31 for every seed "
                "would pass P-02 and fail here."),
            "margin_minor": "0",
            "divergent_cells": [
                "period[2].due_date", "period[3].from_date", "period[3].due_date",
                "period[4].from_date", "period[4].due_date", "period[5].from_date",
                "period[5].due_date", "period[6].from_date", "period[6].due_date",
            ],
            "evidence": (
                "Row indices are 0-based over expect.periods. OBSERVED due dates: [0] "
                "DISBURSEMENT 2024-01-30, [1] 2024-02-29, [2] 2024-03-30, [3] 2024-04-30, "
                "[4] 2024-05-30, [5] 2024-06-30, [6] 2024-07-30. COUNTERFACTUAL due dates: "
                "[1] 2024-02-29 (agrees), then [2] 2024-03-29, [3] 2024-04-29, [4] 2024-05-29, "
                "[5] 2024-06-29, [6] 2024-07-29; from_date follows the previous due date, so rows "
                "[3]..[6] also diverge on from_date while [2].from_date agrees at 2024-02-29. "
                "MARGIN IS EXACTLY 0 MINOR UNITS, observed rather than assumed: P-00, P-02 and "
                "P-02b are byte-identical in every money column of this capture because "
                "DAYS_30/DAYS_360 makes a whole-month period 30/360 regardless of the calendar "
                "dates. The kill is entirely in the due_date and from_date columns."),
        })
    return out


def note(case_id, inp, obs):
    common = (
        "TRANSCRIPTION NOTES. (1) request.currency.code is upper-cased from the capture's own "
        "spelling %r; admit.go requires upper case and the contract forbids the oracle's lower-case "
        "fixture spelling leaking back out. (2) request.time_zone is DECLARED, not observed: the "
        "Path A embeddable seam takes java.time.LocalDate only and has no time-zone input at all "
        "(the capture JVM ran with defaultTimeZone GMT), so Asia/Ulaanbaatar is this vector's "
        "declared interpretation zone for civil dates and grades nothing. (3) request.rounding."
        "rate_factor_scale is 19 from PIN.json's production_rounding; the capture records one "
        "MathContext precision (19) which is both. (4) On the DISBURSEMENT row, installment_number "
        "and interest_minor are marked unrecorded_fields: the oracle's own record type "
        "LoanSchedulePlanDisbursementPeriod carries exactly four fields (periodFromDate, "
        "periodDueDate, principalAmount, outstandingLoanBalance) and its periodNumber() returns "
        "null, with no interest accessor at all [VERIFIED: fineract-progressive-loan/.../"
        "LoanSchedulePlanDisbursementPeriod.java:25-35], and Capture3b.java:459-462 emits every "
        "field the record does carry. So those two cells were NOT OBSERVED. DEC-1 normalises the "
        "null installment number to 0 and that normalisation is part of the CONTRACT, not an "
        "oracle observation -- filling it here would be storing a derivation as an observation, "
        "the exact defect unrecorded_fields exists to prevent. (5) The capture's per-row "
        "totalOutstandingBalance column is deliberately NOT promoted: it is principal plus "
        "interest still to accrue, not an outstanding-principal figure, and the frozen contract "
        "has no field for it." % inp["currencyCode"]
    )
    extra = {
        "P-00": (" This is the only pass-3b case whose configuration matches the pass-1 C-00 "
                 "probe; C-00 itself was taken at precision 12 and is on PIN.json's "
                 "never-promotable list."),
        "P-04f": (" DUPLICATE-SHAPE WARNING: allowFullTermForTranche has no field in the frozen "
                  "contract, so this vector's `request` block is byte-identical to P-00's and "
                  "P-04t's, and its `expect` block is byte-identical too (verified across all "
                  "seven rows and all plan totals). It adds no discriminating power over P-00; "
                  "count the trio as ONE shape when reasoning about coverage."),
        "P-04t": (" DUPLICATE-SHAPE WARNING: allowFullTermForTranche = TRUE, but the frozen "
                  "contract has no field for it, so this vector's `request` block is "
                  "byte-identical to P-00's and P-04f's and its `expect` block is byte-identical "
                  "too. That identity is exactly the evidence that the flag is INERT on this "
                  "shape via the Path A seam -- but the evidence lives in the CAPTURE, not in "
                  "this file, which cannot express the flag at all. It adds no discriminating "
                  "power over P-00; count the trio as ONE shape."),
        "P-02": (" The re-anchor counterfactual on this vector is STRUCTURAL: margin_minor is "
                 "exactly 0 and the kill is in the date columns. See driver catch D-4 and "
                 ".softhouse/handoff/T8-promote-parity-vectors.md."),
        "P-02b": (" The re-anchor counterfactual on this vector is STRUCTURAL: margin_minor is "
                  "exactly 0 and the kill is in the date columns. See driver catch D-4."),
        "P-03": (" Row 0 is an all-zero REPAYMENT emitted BEFORE the disbursement. Its capture "
                 "column totalOutstandingBalance is 101.76 -- principal 100.00 plus the full "
                 "1.76 of interest still to accrue, recorded before any payment. That is NOT an "
                 "outstanding-principal figure and is deliberately not routed into any principal "
                 "column; the promoted outstanding_principal_minor for that row is the capture's "
                 "`balance` cell, 0.00."),
    }
    return common + extra.get(case_id, "")


STRUCTURAL_FALLBACK_NOTE = (
    " D-4 FALLBACK APPLIED: this file was regenerated with --no-structural, so the "
    "STRUCTURAL counterfactual below is carried as prose instead of as a graded_against "
    "entry, because the harness at this revision decodes vectors with "
    "DisallowUnknownFields and therefore rejects the `kind` and `divergent_cells` fields "
    "outright. Re-run .softhouse/handoff/T8-promote-vectors.py with no flags once D-4 "
    "(T20) has landed to restore the structured entry. SUPPRESSED ENTRY >>> ")


def main():
    import sys
    no_structural = "--no-structural" in sys.argv
    written = []
    for case_id in PROMOTE:
        v = build(case_id)
        if no_structural:
            kept, moved = [], []
            for cf in v["graded_against"]:
                (moved if cf.get("kind") == "structural" else kept).append(cf)
            if moved:
                v["graded_against"] = kept
                v["_note"] += STRUCTURAL_FALLBACK_NOTE + json.dumps(moved, ensure_ascii=False)
        # `json.dumps(..., indent=2, ensure_ascii=False) + "\n"` is byte-for-byte
        # what `json.dump(v, fh, indent=2, ensure_ascii=False)` followed by
        # `fh.write("\n")` produced; T203 proved the emitted bytes unchanged by
        # promoting all 11 into an empty scratch store and comparing each against
        # the live vector (arm G1, 11/11 identical).
        path = guard.write_vector(
            NAME, AUTHORISE_TOKEN, OUT, SLUG[case_id] + ".json",
            json.dumps(v, indent=2, ensure_ascii=False) + "\n")
        written.append((case_id, path, len(v["expect"]["periods"]),
                        [(cf["id"], cf.get("kind", "money"), cf["margin_minor"])
                         for cf in v["graded_against"]]))
    for case_id, path, nrows, cfs in written:
        print("%-14s %-58s rows=%d" % (case_id, os.path.basename(path), nrows))
        for cid, kind, m in cfs:
            print("    %-8s %-70s margin=%s" % (kind, cid, m))


if __name__ == "__main__":
    main()
