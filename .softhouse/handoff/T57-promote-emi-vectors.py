#!/usr/bin/env python3
"""T57: promote the two Path A pass-3c captures that trip the EMI re-adjust smoothing-loop
guard into the parity vector store, closing T9 finding F-2 (P1).

Every `expect` cell is TRANSCRIBED from .softhouse/capture/out/capture-prod3c-raw.json.
The only transformation applied to an observed value is exact decimal -> minor-unit scaling,
done textually. NO FLOAT IS CONSTRUCTED AT ANY POINT, IN EITHER DIRECTION.

Counterfactual margins ARE derived -- they are claims about hypothetical WRONG PORTS, never
about the oracle -- and each one's arithmetic is written verbatim into its `evidence` field so a
reader can re-derive it without running this script. The EMI-SMOOTHING-LOOP-OMITTED margins come
from .softhouse/capture/emiloop/noloop_model.py, whose faithfulness is established by a control
run over the already-promoted corpus (see .softhouse/capture/emiloop/analyse-output.txt).
"""
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from math import gcd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".softhouse", "capture", "emiloop"))
from noloop_model import noloop_schedule, guard  # noqa: E402

# HARDENED BY T203 (22 August 2026) - P-22, P-48 rule 4.  This file REUSES the
# shared store guard (`t203_store_guard.py`, T178's shape transposed to a
# create-only store writer) and contains no copy of it.
#
# T203 FOUND THIS FILE, WHICH T196's F-2 AND T198's CORRECTION BOTH MISSED.
# They named FOUR vector-store writers; this is a FIFTH, and it was a bare
# truncation of the live store exactly as T74/T61/T64 were:
#     OUT = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")
#     with open(path, "w") as fh: json.dump(v, fh, ...)
# with no authorisation, no existence check and no atomicity.
#
# WHY THE CLASSIFIER DID NOT CATCH IT, WHICH IS THE REUSABLE LESSON.  T179's
# classifier resolves a mutation target from module constants, and `OUT` here is
# `os.path.join(ROOT, ...)` where `ROOT` is computed at RUNTIME from `__file__`.
# The target therefore resolved to scope UNKNOWN, not TRUSTED - and `--enforce`
# does not trip on UNKNOWN.  T196-1 closed this fail-open for targets arriving
# as function PARAMETERS; the runtime-computed-constant case is still open, and
# it hid a live-store truncator in plain sight.  MEASURED: `OUT` resolves to the
# live store and both of this script's targets exist there today
# (T203-evidence/T57-T8-EXPOSURE.txt).
#
# The caller's own directory goes at the FRONT of sys.path so the module cannot
# be shadowed from the cwd or the environment; a missing module fails CLOSED.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t203_store_guard as guard_store  # noqa: E402

NAME = 'T57-promote-emi-vectors'

# Argv-only authorisation phrase - never an environment variable, for the
# reason recorded in the guard module.  Authorises CREATING new vectors in the
# live store; it does NOT authorise overwriting an existing one, and nothing
# does.
AUTHORISE_TOKEN = (
    'I-AM-PROMOTING-T57-EMI-SMOOTHING-VECTORS-INTO-THE-LIVE-GOLDEN-VECTOR-STORE')

CAP_REL = ".softhouse/capture/out/capture-prod3c-raw.json"
OUT = os.path.join(ROOT, ".softhouse", "vectors", "loanschedule")
PIN = json.load(open(os.path.join(ROOT, ".softhouse", "vectors", "PIN.json")))
SEAM = "path_a_embeddable"
MINOR_DIGITS = 2

PROMOTE = ["P-EMI-6-1M014632", "P-EMI-36-127704"]

SLUG = {
    "P-EMI-6-1M014632": "P-EMI-6-1M014632-emi-smoothing-loop",
    "P-EMI-36-127704": "P-EMI-36-127704-emi-smoothing-loop",
}

TITLE = {
    "P-EMI-6-1M014632": (
        "EMI RE-ADJUST SMOOTHING LOOP, 6 periods. MNT 1,014,632.00 over 6 monthly repayments at "
        "7.0% p.a. The loop checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods "
        "(ProgressiveEMICalculator.java:1258-1309) FIRES on this shape: its guard "
        "(EmiAdjustment.java:31-36) sees |lastEMI - penultimateEMI| = 4 minor units against a "
        "threshold of floor(6/2) = 3, adjusts the level installment from the recurrence's raw "
        "172,574.63 up to the observed 172,574.64, and EVERY period shifts. DEC-1 names this shape "
        "at contract.go:1656-1657 and calls reproducing the loop 'a conformance obligation, not "
        "backlog' (contract.go:1660-1661); before this vector no promoted vector graded it."),
    "P-EMI-36-127704": (
        "EMI RE-ADJUST SMOOTHING LOOP, 36 periods. MNT 127,704.00 over 36 monthly repayments at "
        "16.8% p.a. The guard sees |lastEMI - penultimateEMI| = 25 minor units against a threshold "
        "of floor(36/2) = 18, and the loop moves the level installment from the recurrence's raw "
        "4,540.29 to the observed 4,540.30. Total interest lands at 35,746.56 where a port omitting "
        "the loop produces 35,746.69. DEC-1 names this shape at contract.go:1658. The long term is "
        "the point: the divergence compounds down the schedule to 47 minor units of outstanding "
        "balance, far outside any rounding-noise reading."),
}


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
            "SCALE VIOLATION: %r carries significant digits beyond %d minor-unit digits; per "
            "README this is a harness bug, not something to round" % (text, digits))
        fp = fp[:digits]
    fp = fp + "0" * (digits - len(fp))
    return (ip + fp).lstrip("0") or "0"


def half_up(x, places=2):
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def date_obj(iso):
    y, m, dd = iso.split("-")
    return {"year": int(y), "month": int(m), "day": int(dd)}


def rate_rational(percent_text):
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
CAPTURED_AT = cap["attestation"]["capturedAtUtc"]
import hashlib  # noqa: E402
CAP_SHA = hashlib.sha256(open(os.path.join(ROOT, CAP_REL), "rb").read()).hexdigest()


def paying_rows(obs):
    return [p for p in obs["periods"] if p["type"] == "REPAYMENT"]


# ---------------------------------------------------------------------------
# THE COUNTERFACTUAL THIS TASK EXISTS FOR.
# ---------------------------------------------------------------------------

def cf_emi_smoothing_loop(case_id, inp, obs):
    n = int(inp["numberOfRepayments"])
    m = noloop_schedule(inp["disbursementAmount"], n, inp["annualNominalInterestRate"])
    g = guard(n, m["lastEmi"], m["penultEmi"])
    assert g["trips"], (
        "%s DOES NOT TRIP THE GUARD -- do not promote it as a smoothing-loop vector" % case_id)

    rows = paying_rows(obs)
    assert len(rows) == len(m["rows"]) == n

    worst = (0, None, None, None, None)
    differing = 0
    for k, (orow, cfrow) in enumerate(zip(rows, m["rows"]), start=1):
        pairs = (
            ("principal_minor", int(minor(orow["principal"])), int(cfrow["principal"] * 100)),
            ("interest_minor", int(minor(orow["interest"])), int(cfrow["interest"] * 100)),
            ("outstanding_principal_minor", int(minor(orow["balance"])), int(cfrow["closing"] * 100)),
        )
        if any(o != c for _, o, c in pairs):
            differing += 1
        for label, o, c in pairs:
            if abs(o - c) > worst[0]:
                worst = (abs(o - c), k, label, o, c)
    margin, wk, wcol, wobs, wcf = worst
    assert margin > 0, case_id

    obs_ti = int(minor(obs["totalInterestAmount"]))
    cf_ti = int(m["totalInterest"] * 100)

    return {
        "id": "EMI-SMOOTHING-LOOP-OMITTED",
        "capability": "schedule.core",
        "description": (
            "Implements the level installment from the recurrence and the final-period balancing "
            "adjustment, but OMITS the smoothing loop "
            "checkAndAdjustEmiIfNeededOnRelatedRepaymentPeriods "
            "(ProgressiveEMICalculator.java:1258-1309, called at :749 on every ordinary "
            "generation, at most three iterations). The loop re-levels the installment across the "
            "related repayment periods whenever the final-period residual exceeds its guard, so a "
            "port without it emits the RAW installment %s where the oracle emits %s, and the "
            "divergence propagates through every subsequent period's principal and outstanding "
            "balance. DEC-1 calls reproducing this loop 'a conformance obligation, not backlog' "
            "(contract.go:1660-1661)."
            % (m["emi"], rows[0]["total"])),
        "margin_minor": str(margin),
        "evidence": (
            "Derived at the ratified production MathContext (19, HALF_UP); every OBSERVED value "
            "below is transcribed from this capture and only the counterfactual is derived.\n"
            "GUARD, evaluated where the oracle evaluates it. The loop runs AFTER "
            "calculateLastUnpaidRepaymentPeriodEMI (ProgressiveEMICalculator.java:747 then :749), "
            "so the state its guard sees is exactly the no-loop schedule. r = %s / 100 x 30/360 "
            "= %s (setScale 19, HALF_UP). rateFactorPlus1N = %s and fnResult = %s, both folded "
            "under mc(19) per :1816-1828, give a raw installment of %s x %s / %s = %s at Money 2dp "
            "HALF_UP. Last-period balancing (:1176-1210) then raises the final EMI to %s, so "
            "|lastEMI - penultimateEMI| = |%s - %s| = %s = %d MINOR UNITS. "
            "EmiAdjustment.shouldBeAdjusted (EmiAdjustment.java:31-36) compares |diff| x 100 "
            "against originalEmi.copy(floor(n/2)); Money.copy(double) REPLACES the amount "
            "(Money.java:220-222) so the threshold is floor(%d/2) = %d currency units flat, i.e. "
            "%d minor units. %d > %d, SO THE GUARD TRIPS and the loop fires.\n"
            "MARGIN. The oracle OBSERVES level installment %s; the counterfactual emits %s. Over "
            "the graded money columns the two schedules differ on %d of %d paying rows. The widest "
            "single-cell disagreement is at paying period %d, column %s: oracle OBSERVED %d minor "
            "units against the counterfactual's %d, so the margin is |%d - %d| = %d MINOR UNITS. "
            "Observed total interest is %s (%d minor units) against the counterfactual's %s "
            "(%d minor units), a difference of %d minor units.\n"
            "COUNTERFACTUAL PROVENANCE. The no-loop model is "
            ".softhouse/capture/emiloop/noloop_model.py, transcribed step for step from the pinned "
            "source. Its faithfulness is not assumed: as a CONTROL it reproduces every principal, "
            "interest and outstanding-balance cell of ten of the eleven already-promoted parity "
            "vectors exactly (P-03 excluded, its disbursement falling on a repayment due date), "
            "which is also the direct proof that the loop changes NOTHING on those ten and that "
            "this corpus could not grade it before. See "
            ".softhouse/capture/emiloop/analyse-output.txt."
            % (inp["annualNominalInterestRate"], m["r"], m["rateFactorPlus1N"], m["fnResult"],
               m["rateFactorPlus1N"], inp["disbursementAmount"], m["fnResult"], m["emi"],
               m["lastEmi"], m["lastEmi"], m["penultEmi"], abs(m["lastEmi"] - m["penultEmi"]),
               g["absDiffMinorUnits"], n, g["lowerHalfOfRelatedPeriods"],
               g["lowerHalfOfRelatedPeriods"], g["absDiffMinorUnits"], g["lowerHalfOfRelatedPeriods"],
               rows[0]["total"], m["emi"], differing, n, wk, wcol, wobs, wcf, wobs, wcf, margin,
               obs["totalInterestAmount"], obs_ti, m["totalInterest"], cf_ti, abs(obs_ti - cf_ti))),
    }


def cf_final_balancing(obs):
    rows = [r for r in paying_rows(obs) if r["total"] != "0.00"]
    last, level = rows[-1], rows[0]["total"]
    if level == last["total"]:
        return None
    cf_principal = half_up(Decimal(level) - Decimal(last["interest"]))
    margin = abs(int(minor(last["principal"])) - int(minor(str(cf_principal))))
    if margin <= 0:
        return None
    return {
        "id": "LEVEL-INSTALLMENT-WITHOUT-FINAL-PERIOD-BALANCING-ADJUSTMENT",
        "capability": "schedule.core",
        "description": (
            "Emits the level installment in the final period like every other period, so the final "
            "principal is (installment - interest) instead of the WHOLE REMAINING BALANCE. The "
            "schedule then does not amortize to exactly zero."),
        "margin_minor": str(margin),
        "evidence": (
            "Derived at (19, HALF_UP) from cells observed in this capture. Observed level "
            "installment (row total on every non-final paying period) = %s; observed FINAL row "
            "total = %s, so the oracle does NOT carry the level installment into the final period. "
            "Counterfactual final principal = level installment %s - observed final interest %s = "
            "%s. Observed final principal = %s. Margin = |%s - %s| = %d minor units, and the "
            "counterfactual's closing balance is non-zero, so the principal_amortizes_to_zero "
            "invariant also catches it."
            % (level, last["total"], level, last["interest"], cf_principal, last["principal"],
               minor(last["principal"]), minor(str(cf_principal)), margin)),
    }


def cf_straight_line(obs, n, disbursed_major):
    rows = [r for r in paying_rows(obs) if r["total"] != "0.00"]
    flat = half_up(Decimal(disbursed_major) / Decimal(n))
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
            "adds declining-balance interest on top, instead of taking principal as the BALANCING "
            "REMAINDER of a level installment after interest. Produces a rising total due rather "
            "than a level one."),
        "margin_minor": str(margin),
        "evidence": (
            "Derived at (19, HALF_UP). Counterfactual per-period principal = disbursed %s / %d = "
            "%s (HALF_UP to 2dp). Widest disagreement is at paying period %d, where the oracle "
            "OBSERVED principal %s (%s minor units) against the counterfactual's %s (%s minor "
            "units): margin = %d minor units. The disbursed amount and every observed principal "
            "are transcribed from this capture; only the division is derived."
            % (disbursed_major, n, flat, idx, r["principal"], minor(r["principal"]), flat,
               flat_minor, margin)),
    }


NOTE_COMMON = (
    "TRANSCRIPTION NOTES. (1) request.currency.code is upper-cased from the capture's own spelling "
    "%r; admit.go requires upper case and the contract forbids the oracle's lower-case fixture "
    "spelling leaking back out. (2) request.time_zone is DECLARED, not observed: the Path A "
    "embeddable seam takes java.time.LocalDate only and has no time-zone input at all, so "
    "Asia/Ulaanbaatar is this vector's declared interpretation zone for civil dates and grades "
    "nothing. (3) request.rounding.rate_factor_scale is 19 from PIN.json's production_rounding; the "
    "capture records one MathContext precision (19) which is both. (4) On the DISBURSEMENT row, "
    "installment_number and interest_minor are marked unrecorded_fields: the oracle's own record "
    "type LoanSchedulePlanDisbursementPeriod carries exactly four fields (periodFromDate, "
    "periodDueDate, principalAmount, outstandingLoanBalance) and its periodNumber() returns null, "
    "with no interest accessor at all [VERIFIED: fineract-progressive-loan/.../"
    "LoanSchedulePlanDisbursementPeriod.java:25-35], and Capture3c.java emits every field the "
    "record does carry. So those two cells were NOT OBSERVED. DEC-1 normalises the null installment "
    "number to 0 and that normalisation is part of the CONTRACT, not an oracle observation -- "
    "filling it here would be storing a derivation as an observation, the exact defect "
    "unrecorded_fields exists to prevent. (5) The capture's per-row totalOutstandingBalance column "
    "is deliberately NOT promoted: it is principal plus interest still to accrue, not an "
    "outstanding-principal figure, and the frozen contract has no field for it. "
    "(6) PROVENANCE OF THE SHAPE: this vector's inputs are the ones DEC-1 itself names at "
    "contract.go:1655-1658. They are NOT new to the program -- task T37 captured the same two "
    "shapes through a different Path A harness (.softhouse/capture/dec1-binding/out/"
    "t37-binding.json, cases T37-3-A and T37-3-B) and pass 3c reproduces those observations cell "
    "for cell. What pass 3c adds is the pass-3b rig's guarantees, which T37's harness did not "
    "carry: the in-container attestation, the plan-level totalPrincipalAmount / totalFeeAmount / "
    "totalPenaltyAmount / totalOutstandingAmount columns, and a runner that refuses to leave a "
    "capture behind on any of eleven precondition breaches. Promotion needs those; T37's captures "
    "were never promoted. (7) THE GUARD MUST BE EVALUATED ON THE PRE-ADJUSTMENT MODEL, not on the "
    "observed output. The loop is called at ProgressiveEMICalculator.java:749, after "
    "calculateLastUnpaidRepaymentPeriodEMI at :747; once it has run, the residual it exists to "
    "shrink is smaller. On this vector the guard trips on the no-loop model and the loop then "
    "changes the schedule -- which is what makes the vector grade the loop -- so screening a "
    "candidate by re-computing the guard on the ORACLE'S OWN OUTPUT understates which shapes "
    "grade it. See .softhouse/handoff/T57-emi-smoothing-loop-vectors.md, finding N-1."
)


def build(case_id):
    c = cases[case_id]
    inp, obs = c["inputs"], c["observed"]

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
    assert inp["daysInYearCustomStrategy"] is None, case_id
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
            row["unrecorded_fields"] = ["installment_number", "interest_minor"]
        periods.append(row)

    graded = [cf_emi_smoothing_loop(case_id, inp, obs)]
    for cf in (cf_final_balancing(obs),
               cf_straight_line(obs, int(inp["numberOfRepayments"]), inp["disbursementAmount"])):
        if cf:
            graded.append(cf)

    v = {
        "schema": "gerege.loanschedule.vector/v1",
        "case_id": case_id,
        "context": "loanschedule",
        "class": "parity",
        "title": TITLE[case_id],
        "dec1_revision": PIN["dec1_revision"],
        "_note": NOTE_COMMON % inp["currencyCode"],
        "capabilities_required": ["schedule.core"],
        "graded_against": graded,
        "retires_when_capability_graded": "",
        "provenance": {
            "kind": "oracle-capture",
            "note": (
                "TRANSCRIBED, never computed, from Path A capture pass 3c "
                "(.softhouse/capture/src/run-pass3c.sh, Capture3c.java). Every expect cell is a "
                "value literally present in the referenced capture for capture case %s; the only "
                "transformation is exact textual major->minor scaling (\"172574.64\" -> "
                "\"17257464\"), and the oracle's own emitted characters are carried alongside in "
                "the *_major_text cross-check fields so the scaling is mechanically re-checkable. "
                "The pass-3c run reproduced two already-committed pass-3b observations as rig "
                "calibrations before emitting anything: P-CAL at (12, HALF_UP) and P-CAL-P00 at the "
                "production (19, HALF_UP), inputs and observed blocks both identical. Promotion "
                "script: .softhouse/handoff/T57-promote-emi-vectors.py (task T57)." % case_id),
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
            "rounding": {"significant_digits": 19, "rate_factor_scale": 19, "mode": "HALF_UP"},
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

    disb = [p for p in periods if p["kind"] == "DISBURSEMENT"]
    assert len(disb) == 1, case_id
    assert disb[0]["principal_minor"] == v["request"]["disbursements"][0]["amount_minor"], case_id
    assert disb[0]["outstanding_principal_minor"] == disb[0]["principal_minor"], case_id
    return v


def main():
    for case_id in PROMOTE:
        v = build(case_id)
        # `json.dumps(..., indent=2, ensure_ascii=False) + "\n"` is byte-for-byte
        # what `json.dump(v, fh, indent=2, ensure_ascii=False)` followed by
        # `fh.write("\n")` produced; T203 proved the emitted bytes unchanged by
        # promoting both into an empty scratch store and comparing each against
        # the live vector (arm G1, 2/2 identical).
        path = guard_store.write_vector(
            NAME, AUTHORISE_TOKEN, OUT, SLUG[case_id] + ".json",
            json.dumps(v, indent=2, ensure_ascii=False) + "\n")
        print("%-18s %-52s rows=%d" % (case_id, os.path.basename(path), len(v["expect"]["periods"])))
        for cf in v["graded_against"]:
            print("    %-8s %-58s margin=%s"
                  % (cf.get("kind", "money"), cf["id"], cf["margin_minor"]))


if __name__ == "__main__":
    main()
