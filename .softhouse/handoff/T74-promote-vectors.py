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

# HARDENED BY T203 (22 August 2026) - P-22, P-48 rule 4.  This file REUSES the
# shared store guard (`t203_store_guard.py`, T178's shape transposed to a
# create-only store writer).  It introduces no second guard shape and contains
# no copy of the guard.  AS SHIPPED BY TASK T74 the write below was
#     open(os.path.join(VECTORS, FILENAMES[cid]), "w").write(...)
# against `VECTORS = .softhouse/vectors/loanschedule`, THE LIVE GOLDEN-VECTOR
# STORE, with no authorisation, no existence check and no atomicity.
# `open(p, "w")` is O_TRUNC: the vector was EMPTIED before a byte of
# replacement was written.  MEASURED BY T203, not asserted: against a scratch
# store seeded with sentinels at this script's own six target names the PRE-FIX
# bytes exited 0 and DESTROYED ALL SIX.  See T203-evidence/RED-prefix.txt.
# THE PROMOTION ITSELF DID NOT CHANGE - every emitted vector is byte-for-byte
# T74's, which T203 measured on a scratch store (livebytes arm, 0 changed).
# The caller's own directory goes at the FRONT of sys.path so the module cannot
# be shadowed from the cwd or the environment; a missing module fails CLOSED.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t203_store_guard as guard  # noqa: E402

NAME = 'T74-promote-vectors'

# The exact phrase that authorises CREATING new vectors in the live store.
# Long, self-describing, argv-only - never an environment variable: an env var
# is exported once in a wrapper, inherited by every child and then forgotten,
# whereas an argv word must be retyped at every invocation and is recorded in
# the process table.  It does NOT authorise overwriting an existing vector;
# nothing does.
AUTHORISE_TOKEN = (
    'I-AM-PROMOTING-T74-GROUP-E-VECTORS-INTO-THE-LIVE-GOLDEN-VECTOR-STORE')

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


# --- CORRECTED BY T82 (T75 follow-up D-1 / D-2) ---------------------------------------------------
# Four request fields were written from a constant or from a silent fallback although the capture
# RECORDS the input. Each was correct for pass 3i's cases and would have been silently wrong the
# first time a case differed — the defect only shows up as a vector that grades the wrong question,
# which is the most expensive kind to find later. Each is now DERIVED from the capture, and the
# derivation REFUSES anything it cannot account for rather than falling back.


# `day_count` was the literal "FIXED_30_360" while the capture records daysInMonth / daysInYear.
# The contract's own mapping, verbatim from contract.go:359-360:
#     DayCountFixed30Over360 -> (DaysInMonthType.DAYS_30, DaysInYearType.DAYS_360)
#     DayCountActualActual   -> (DaysInMonthType.ACTUAL,  DaysInYearType.ACTUAL)
# Anything else is a convention this store has no name for, and a vector must not guess one.
DAY_COUNT_BY_OBSERVED_PAIR = {
    ("DAYS_30", "DAYS_360"): "FIXED_30_360",
    ("ACTUAL", "ACTUAL"): "ACTUAL_ACTUAL",
}


def day_count(i, cid):
    dim, diy = i.get("daysInMonth"), i.get("daysInYear")
    if dim is None or diy is None:
        sys.exit("%s: the capture does not record daysInMonth / daysInYear (%r / %r), so the "
                 "day-count convention cannot be derived. This script will not assume one."
                 % (cid, dim, diy))
    custom = i.get("daysInYearCustomStrategy")
    if custom is not None:
        sys.exit("%s: daysInYearCustomStrategy is %r. A custom days-in-year strategy means the "
                 "(daysInMonth, daysInYear) pair no longer describes the convention in force, and "
                 "the frozen contract carries no field for it." % (cid, custom))
    key = (dim, diy)
    if key not in DAY_COUNT_BY_OBSERVED_PAIR:
        sys.exit("%s: observed (daysInMonth, daysInYear) = %r, which is not a day-count convention "
                 "the frozen contract names (contract.go:359-360 maps only %r). Refusing to write a "
                 "day_count this capture does not support."
                 % (cid, key, sorted(DAY_COUNT_BY_OBSERVED_PAIR)))
    return DAY_COUNT_BY_OBSERVED_PAIR[key]


def down_payment_percentage(i, cid):
    """`down_payment_percentage` was the literal {0, 1} while the capture records the input.

    A non-zero down payment is a DIFFERENT SHAPE, not a detail: it changes the first period's
    principal. Promoting one under a hard-coded zero would produce a vector that grades a schedule
    the request does not describe. So a non-zero observation is refused outright rather than
    transcribed — pass 3i captured none, and the case for one belongs in its own pass.
    """
    if "downPaymentEnabled" not in i or "downPaymentPercentage" not in i:
        sys.exit("%s: the capture does not record downPaymentEnabled / downPaymentPercentage; the "
                 "request field cannot be derived and this script will not assume a zero." % cid)
    enabled = i["downPaymentEnabled"]
    pct = i["downPaymentPercentage"]
    # Zero is decided by exact string inspection, never by float(). "0", "0.00", "-0.0" and "+0"
    # are all zero; anything with a non-zero digit is not.
    digits = str(pct).lstrip("+-").replace(".", "")
    is_zero = digits != "" and digits.strip("0") == "" and digits.isdigit()
    if enabled is not False or not is_zero:
        sys.exit("%s: downPaymentEnabled=%r downPaymentPercentage=%r. This script promotes only "
                 "the no-down-payment shape; a down payment moves the first period's principal and "
                 "must be captured and promoted as a shape of its own." % (cid, enabled, pct))
    return {"numerator": 0, "denominator": 1}


def repayment_every(i, cid):
    """`repayment_every` was `i.get("repaymentEvery", i.get("repaymentFrequency"))`.

    Two silent fallbacks in one expression: if `repaymentEvery` is absent the second key is tried,
    and if BOTH are absent the result is `None` — written into the vector as a null the store would
    then have to interpret. Absence of the repayment interval is not a value; it is a broken capture.
    """
    present = {k: i[k] for k in ("repaymentEvery", "repaymentFrequency") if k in i}
    if not present:
        sys.exit("%s: the capture records neither `repaymentEvery` nor `repaymentFrequency`. The "
                 "repayment interval is not defaultable — a vector with the wrong interval grades a "
                 "different loan and passes." % cid)
    vals = set(present.values())
    if len(vals) != 1:
        sys.exit("%s: `repaymentEvery` and `repaymentFrequency` disagree (%r). The capture cannot "
                 "say which interval the oracle actually ran." % (cid, present))
    v = vals.pop()
    if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
        sys.exit("%s: repayment interval is %r; expected a positive integer." % (cid, v))
    return v


# Row kinds the frozen contract fixes at InstallmentNumber 0 because they are not payable.
NON_PAYABLE_ROW_TYPES = {"DISBURSEMENT"}


def installment_number(p, cid, idx):
    """`installment_number` was `p.get("periodNumber") or 0`.

    `or` collapses a LEGITIMATE 0 into the fallback, so an absent periodNumber and a periodNumber of
    0 became indistinguishable — the P-15 shape. They are now distinguished: absence yields the
    contract's normative 0 for a non-payable row AND is recorded in `unrecorded_fields`; a recorded
    0 is transcribed as the observation it is, and is NOT recorded as unrecorded.

    Absence is legitimate on exactly one kind of row and nowhere else, so the two are told apart by
    the ROW TYPE and not by the value. `LoanSchedulePlanDisbursementPeriod` carries four fields and
    its `periodNumber()` returns null, so the rig emits no key at all for a DISBURSEMENT row; every
    payable row in this capture carries an int. [VERIFIED: 36 DISBURSEMENT rows with the key absent,
    861 REPAYMENT rows with an int, in capture-prod3i-raw.json]

    Returns (value, was_absent).
    """
    kind = p.get("type")
    absent = "periodNumber" not in p or p["periodNumber"] is None
    if kind in NON_PAYABLE_ROW_TYPES:
        if not absent:
            sys.exit("%s: period[%d] is a %s row but carries periodNumber %r. A non-payable row's "
                     "installment number is fixed at 0 by the contract (contract.go:1509-1510); an "
                     "observed one means the rig changed and the withdrawal below would be wrong."
                     % (cid, idx, kind, p["periodNumber"]))
        # The contract fixes a non-payable row's InstallmentNumber at 0 (contract.go:1509-1510).
        # That is the contract's value, not this script's guess, and the cell is withdrawn below.
        return 0, True
    if absent:
        sys.exit("%s: period[%d] is a payable %s row with NO periodNumber. The old form wrote 0 "
                 "here via `p.get(\"periodNumber\") or 0` and moved on, which is a missing input "
                 "wearing a legitimate value's clothes." % (cid, idx, kind))
    pn = p["periodNumber"]
    if not isinstance(pn, int) or isinstance(pn, bool) or pn < 0:
        sys.exit("%s: period[%d] periodNumber is %r; expected a non-negative integer. This script "
                 "will not coerce it." % (cid, idx, pn))
    # A recorded 0 is transcribed as the observation it is and is NOT reported as unrecorded — that
    # is the whole point of the correction.
    return pn, False


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
        for idx, p in enumerate(obs["periods"]):
            inst_no, inst_absent = installment_number(p, cid, idx)
            row = {
                "kind": p["type"],
                "installment_number": inst_no,
                "from_date": date(p.get("periodFromDate") or p["fromDate"]),
                "due_date": date(p["dueDate"]),
            }
            unrecorded, over = [], []
            if inst_absent:
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
                "repayment_every": repayment_every(i, cid),
                "repayment_frequency_unit": i["repaymentFrequencyType"],
                "annual_nominal_interest_rate": rate(i["annualNominalInterestRate"]),
                "interest_method": i["interestMethod"],
                "day_count": day_count(i, cid),
                "down_payment_percentage": down_payment_percentage(i, cid),
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

        path = guard.write_vector(
            NAME, AUTHORISE_TOKEN, VECTORS, FILENAMES[cid],
            json.dumps(vec, indent=2, ensure_ascii=False) + "\n")
        print("wrote %s  (margin %s minor at period[%d].%s, %d/%d graded cells move)"
              % (path, worst["delta"], worst["row"], worst["field"],
                 cf["divergentCellCount"], cf["cells"]))
        written += 1

    print("\n%d vectors promoted from %s (sha256 %s)" % (written, P3I_REF, p3i_sha))
    print("NOTHING was promoted from capture groups A, B, C or D — see this script's docstring.")


if __name__ == "__main__":
    main()
