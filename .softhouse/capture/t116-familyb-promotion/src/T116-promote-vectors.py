#!/usr/bin/env python3
"""T116 — promote the three T116 cells into `.softhouse/vectors/loanschedule/`.

    python3 .softhouse/capture/t116-familyb-promotion/src/T116-promote-vectors.py

WHERE THIS FILE LIVES IS LOAD-BEARING (P-36). ROOT is derived from `__file__`, so a copy of this
script under /tmp resolves ROOT to somewhere under /tmp and writes nothing anybody will see — a
naive scratch test of it is a NULL CONTROL. If you want to test a change to this script, put the
variant in THIS directory as a sibling file (T161's shape, adopted by T180) and point its OUTDIR at
a scratch store.

EVERY expect cell is TRANSCRIBED from T116's own live-oracle capture
(`out/capture-t116-raw.json`). The ONLY transformation applied to a money value is exact TEXTUAL
major -> minor scaling, with an integrality assertion on every parse; the oracle's own emitted
characters are carried alongside in the `*_major_text` cross-check fields so the scaling is
mechanically re-checkable by a reader who trusts none of this. NOTHING here computes a schedule,
and no float is constructed anywhere in this file (P-25).

WHAT IS BEING PROMOTED, AND THE PARADOX THAT MUST BE STATED OUT LOUD:

  Two of the three vectors record a shape on which THE PORT IS FAITHFUL AND THE LOAN IS NOT REPAID.
  The reference oracle emits, for MNT 0.01 over 104 (resp. 108) monthly repayments at 600.0 % p.a.,
  a schedule in which every repayment row's principal is 0.00, the outstanding balance never leaves
  0.01, and interest is charged against a principal that is never repaid -- and the Go port
  reproduces that CELL FOR CELL. There is no port-vs-oracle divergence to arbitrate here, which is
  exactly why these cells are promotable by exemption; and the thing being recorded as parity is a
  schedule that does not repay the loan, which is exactly why the exemption must be loud.

  This is gate G-8 option (a). Options (b) (refuse the region from the graded domain) and (c)
  (diverge deliberately) amend the graded domain and are hard `user` gates. T116 does not decide,
  imply or prepare either.

THE EXEMPTION IS NARROW BY MEASUREMENT, NOT BY ASSERTION. Exactly TWO invariants go red on these
cells and exactly two are exempted: `principal_portions_sum_to_disbursed` and
`principal_amortizes_to_zero`. `balance_roll_forward` HOLDS unexempted (the balance column is
consistent with a principal column of zeros), and T100's proposed EX_B exempted it anyway; that
third exemption is dropped here and its absence is verified by the exemption demo. The four
remaining invariants are untouched on all three vectors.

"The oracle" is the Fineract reference implementation. Oracle Database is a prohibited product in
this program and appears nowhere in this stack.
"""
import hashlib
import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CAPREL = ".softhouse/capture/t116-familyb-promotion/out/capture-t116-raw.json"
CAP = os.path.join(ROOT, CAPREL)
CFREL = ".softhouse/capture/t116-familyb-promotion/out/counterfactuals-t116.json"
OUTDIR = os.path.join(ROOT, ".softhouse/vectors/loanschedule")


def minor(text):
    """Exact textual major -> integer minor units for a 2-dp currency. No float, ever."""
    text = str(text)
    neg = text.startswith("-")
    t = text.lstrip("-")
    whole, _, frac = t.partition(".")
    if len(frac) > 2 and set(frac[2:]) != {"0"}:
        sys.exit("OVER-SCALED money text %r: a significant digit beyond the currency scale is a "
                 "finding, never a rounding opportunity" % text)
    frac = (frac + "00")[:2]
    v = int(whole or 0) * 100 + int(frac)
    return -v if neg else v


def d(s):
    y, m, dd = s.split("-")
    return {"year": int(y), "month": int(m), "day": int(dd)}


def periods_of(cap):
    out = []
    for p in cap["observed"]["periods"]:
        if p["type"] == "DISBURSEMENT":
            out.append({
                "kind": "DISBURSEMENT", "installment_number": 0,
                "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                "principal_minor": str(minor(p["principal"])),
                "principal_major_text": p["principal"],
                "interest_minor": "", "interest_major_text": "",
                "outstanding_principal_minor": str(minor(p["balance"])),
                "outstanding_principal_major_text": p["balance"],
                # The oracle's DISBURSEMENT record type carries neither of these; they are
                # WITHDRAWN FROM GRADING rather than filled in with a plausible stand-in.
                "unrecorded_fields": ["installment_number", "interest_minor"],
                "observed_total_due_minor": None,
            })
        else:
            out.append({
                "kind": "REPAYMENT", "installment_number": p["periodNumber"],
                "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                "principal_minor": str(minor(p["principal"])),
                "principal_major_text": p["principal"],
                "interest_minor": str(minor(p["interest"])),
                "interest_major_text": p["interest"],
                "outstanding_principal_minor": str(minor(p["balance"])),
                "outstanding_principal_major_text": p["balance"],
                "unrecorded_fields": [],
                "observed_total_due_minor": str(minor(p["total"])),
            })
    return out


CAP_SHA = hashlib.sha256(open(CAP, "rb").read()).hexdigest()
with open(CAP) as fh:
    doc = json.load(fh)
CAPS = {c["id"]: c for c in doc["captures"]}
CAPTURED_AT = doc["attestation"]["capturedAtUtc"]
with open(os.path.join(ROOT, ".softhouse/vectors/PIN.json")) as fh:
    PIN_REV = json.load(fh)["dec1_revision"]

PROVENANCE_NOTE = (
    "TRANSCRIBED, never computed, from T116's OWN Path A capture "
    "(.softhouse/capture/t116-familyb-promotion/src/run-t116.sh, CaptureT116.java), taken from the "
    "live reference oracle at the pinned image and pinned Fineract commit on 2026-08-22. Every "
    "expect cell is a value literally present in the referenced capture for the named case; the "
    "only transformation is exact textual major->minor scaling, and the oracle's own emitted "
    "characters are carried alongside in the *_major_text cross-check fields so the scaling is "
    "mechanically re-checkable. The rig's two calibrations P-CAL-ZPA / P-CAL-ZPB reproduce the "
    "already-promoted T64-ZP-A / T64-ZP-B cell for cell with zero input differences, and the "
    "prediction (PREDICTION.md, prediction.json) was committed in a STRICT ANCESTOR of the commit "
    "carrying the capture, scoring 15 held / 0 refuted. Promotion script: "
    ".softhouse/capture/t116-familyb-promotion/src/T116-promote-vectors.py (task T116)."
)

CF_EVIDENCE_COMMON = (
    "Derived at the ratified production MathContext (19, HALF_UP), MNT, minorUnitDigits 2. Every "
    "OBSERVED value is transcribed from T116's own capture " + CAPREL + "; only the counterfactual "
    "value is derived.\n"
    "COUNTERFACTUAL PROVENANCE. The counterfactual value is MEASURED, not asserted: a scratch copy "
    "of the port under /tmp with exactly one named change applied, run on this vector's own "
    "request, by .softhouse/capture/t116-familyb-promotion/src/counterfactuals_t116.py with the "
    "patch set in src/T116-mutations.py and src/t116cf.go.txt. Raw per-cell output: " + CFREL + ". "
    "THE CONTROL IS THE LOAD-BEARING PART: with every change switched OFF the port reproduces all "
    "951 graded money cells of T116's three capture cases with ZERO mismatches, so the only thing a "
    "reported margin can be measuring is the named change.\n"
)

EX_FAMB = [
    {
        "invariant": "principal_portions_sum_to_disbursed",
        "reason": (
            "GATE G-8, FAMILY B, EXEMPTED BECAUSE THE REFERENCE ORACLE GENUINELY DOES NOT AMORTIZE "
            "THIS SHAPE -- not because the port is being excused. The oracle advances 1 minor unit "
            "and its own principal column repays 0: every repayment row carries principal 0.00 and "
            "its totalPrincipalAmount reads 0.00. The Go port reproduces that CELL FOR CELL (0 "
            "divergent cells over this vector's graded money cells, measured; see graded_against "
            "evidence), so there is no port-vs-oracle divergence for this invariant to arbitrate: "
            "asserting it here would be asserting that the ORACLE is wrong, which is a graded-domain "
            "amendment and a hard `user` gate (G-8 options (b) and (c)), not a check the harness may "
            "make on its own authority. THE EXEMPTION IS SCOPED TO THIS ONE CAPTURED SHAPE. It is "
            "NOT a statement that 600.0 % p.a. is exempt: the sibling vector T116-G8-CLEAN-N103, one "
            "repayment shorter at the same rate and the same principal, amortizes normally and "
            "carries NO exemption at all."
        ),
    },
    {
        "invariant": "principal_amortizes_to_zero",
        "reason": (
            "GATE G-8, FAMILY B, same shape and same reason. The final row's outstanding balance is "
            "1 minor unit because the loan was never repaid, not because a balance memo went stale: "
            "the balance column is 0.01 on EVERY row, the principal column is 0.00 on every row, and "
            "the port returns exactly that. Family A -- where the principal column DOES sum to the "
            "disbursement and only the final balance is stale -- is a different phenomenon, is a "
            "CELL DIFF rather than an invariant failure, and is NOT covered by this exemption; an "
            "exemption cannot cure a parity diff and T116 does not attempt one."
        ),
    },
]

VECTORS = [
    {
        "file": "T116-G8-CLEAN-nonexempt-mnt0pt01-103x600pct.json",
        "case_id": "T116-G8-CLEAN-N103",
        "capture_case": "T116-CLEAN-R600p0-N103-B1",
        "exemptions": [],
        "title": (
            "GATE G-8 BOUNDARY, THE AMORTIZING SIDE, AND THE CONTROL THAT KEEPS THE FAMILY-B "
            "EXEMPTION NARROW. MNT 0.01 over 103 monthly repayments at 600.0% p.a., schedule start "
            "== disbursement == 2024-01-01, entirely inside DEC-1's graded domain. This shape "
            "AMORTIZES: the principal column sums to the disbursed 1 minor unit and the final row's "
            "outstanding balance is 0, so this vector carries NO invariant exemption and all six "
            "invariants are asserted against it. ONE REPAYMENT LONGER -- n = 104, same rate, same "
            "principal, the sibling vector T116-G8-FAMB-N104 -- the oracle stops amortizing "
            "entirely. Promoting the exempt cells without this one would leave a reader unable to "
            "tell a narrow, measured exemption from a blanket 'this rate is exempt'."
        ),
        "note": (
            "PROMOTED BY T116 under gate G-8's option (a) mandate. Transcribed from T116's own "
            "live-oracle capture, case T116-CLEAN-R600p0-N103-B1. This is the CLEAN cell immediately "
            "below the family-B lower boundary: T84 and T117's CTRL re-ask both measured n = 103 "
            "clean, and T116 re-observed it. Its purpose in the corpus is twofold -- it grades "
            "ZP-RESIDUAL-NO-RECURSION over 88 divergent cells, and it is the unexempted control "
            "beside the two exempted family-B vectors."
        ),
        "graded_against": [{
            "id": "ZP-RESIDUAL-NO-RECURSION-AT-THE-G8-BOUNDARY",
            "capability": "schedule.core",
            "description": (
                "The final-period residual clamps a negative installment to zero but does not "
                "re-apply itself, so the residual it could not place is silently dropped. "
                "calculateLastUnpaidRepaymentPeriodEMI re-enters itself when the adjusted "
                "installment falls below what is already paid [ProgressiveEMICalculator.java:"
                "1211-1214]. MEASURED ON THIS VECTOR'S OWN REQUEST: this counterfactual diverges on "
                "88 of this vector's 311 graded money cells, the widest single-cell disagreement "
                "being at period[15].principal_minor, where the oracle OBSERVED 0 minor units "
                "against the counterfactual's 1. HONEST SCOPE: this counterfactual was ALREADY "
                "GRADED before T116 -- T64's four rounding-floor vectors kill it -- so this vector "
                "ADDS CELLS AND A SECOND RATE (600.0 %, where every prior kill sits at 16.8-36 %) "
                "and does NOT close a blind spot. It is recorded that way rather than claimed as new "
                "coverage."
            ),
            "margin_minor": "1",
            "evidence": CF_EVIDENCE_COMMON + (
                "MARGIN. Over this vector's 311 graded money cells the counterfactual diverges on "
                "88. The widest single-cell disagreement is at period[15], column principal_minor: "
                "the oracle OBSERVED 0 minor units against the counterfactual's 1, so the margin is "
                "|0 - 1| = 1 MINOR UNIT. The margin is one minor unit because the entire region is "
                "at the rounding floor -- MNT 0.01 is the smallest representable principal in MNT -- "
                "and a one-minor-unit margin on a one-minor-unit loan is a 100 % error, not a "
                "rounding quibble."
            ),
        }],
    },
    {
        "file": "T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct.json",
        "case_id": "T116-G8-FAMB-N104",
        "capture_case": "T116-FAMB-R600p0-N104-B1",
        "exemptions": EX_FAMB,
        "title": (
            "GATE G-8, FAMILY B: A GRADED-DOMAIN SHAPE ON WHICH THE REFERENCE ORACLE DOES NOT REPAY "
            "THE LOAN, AND THE GO PORT REPRODUCES IT CELL FOR CELL. MNT 0.01 over 104 monthly "
            "repayments at 600.0% p.a. All 104 repayment rows carry principal 0.00; the outstanding "
            "balance is 0.01 on every row including the last; totalPrincipalAmount reads 0.00 while "
            "MNT 0.01 of interest is scheduled against a principal that is never repaid. TWO "
            "INVARIANTS ARE EXEMPTED BY NAME AND ONLY TWO -- principal_portions_sum_to_disbursed and "
            "principal_amortizes_to_zero -- because the oracle, not the port, is what fails them. "
            "n = 104 is the LOWEST family-B cell ever observed, and the leading explanation for the "
            "region (a sub-ulp residual) provably does not reach it: the exact-rational residual "
            "here is 2.43 ulp at 19 significant digits [finding F-T114-1]. The region's cause "
            "remains UNKNOWN."
        ),
        "note": (
            "PROMOTED BY T116 under gate G-8's option (a) mandate. Transcribed from T116's own "
            "live-oracle capture, case T116-FAMB-R600p0-N104-B1. THE PARADOX THIS VECTOR RECORDS, "
            "STATED PLAINLY: it is a PARITY vector, and it passes, and the schedule it certifies "
            "does not repay the loan. Those are not in tension -- a parity vector asserts that the "
            "port reproduces the oracle, and here it does, exactly. What it does NOT assert, and "
            "what the two exemptions exist to stop it silently asserting, is that the resulting "
            "schedule is financially sound. It is not. G-8 stays OPEN. Whether this region should "
            "instead be REFUSED from the graded domain (option b) or deliberately diverged from "
            "(option c) amends the graded domain and is a hard `user` gate that T116 does not touch."
        ),
        "graded_against": [{
            "id": "G8-FINAL-ROW-SETTLES-THE-BALANCE",
            "capability": "schedule.core",
            "description": (
                "The final repayment row's principal is the whole remaining balance, instead of the "
                "balancing non-negative remainder of its own installment after interest. "
                "getDuePrincipal is negativeToZero(emiPlusCreditedAmounts - getDueInterest()) on "
                "EVERY row including the last [RepaymentPeriod.java:339-344]; the final row comes "
                "out even because calculateLastUnpaidRepaymentPeriodEMI adjusts the INSTALLMENT "
                "[ProgressiveEMICalculator.java:1210-1214], not because the principal is "
                "special-cased. 'The last row settles whatever is left' is the amortization-schedule "
                "folk rule and it agrees with the oracle to the minor unit on every shape where that "
                "adjustment succeeds. THE PORT'S OWN SOURCE NAMES THIS AS AN UNGRADED BLIND SPOT: "
                "emi.go:1832-1842, 'THERE IS NO SPECIAL CASE THAT SETS THE FINAL ROW'S PRINCIPAL TO "
                "THE WHOLE REMAINING BALANCE ... A port that special-cases the principal instead "
                "reproduces the same numbers on this corpus and is wrong in shape.' Family B is the "
                "first observed shape where the final-period adjustment does NOT settle the balance, "
                "so it is the first shape on which the two readings can be told apart at all. "
                "MEASURED: 0 divergent cells on the sibling clean vector T116-G8-CLEAN-N103, which "
                "is why 43 promoted vectors could not see it; 4 divergent cells here."
            ),
            "margin_minor": "1",
            "evidence": CF_EVIDENCE_COMMON + (
                "MARGIN. Over this vector's 314 graded money cells the counterfactual diverges on "
                "4: period[103].interest_minor (oracle OBSERVED 0, counterfactual 1), "
                "period[104].interest_minor (OBSERVED 1, counterfactual 0), "
                "period[104].principal_minor (OBSERVED 0, counterfactual 1) and "
                "period[104].outstanding_principal_minor (OBSERVED 1, counterfactual 0). The widest "
                "single-cell disagreement is 1 MINOR UNIT. The margin is one minor unit because the "
                "whole region sits at the rounding floor -- MNT 0.01 is the smallest representable "
                "principal in MNT -- so one minor unit here is the ENTIRE loan: the counterfactual "
                "repays 100 % of the principal where the oracle repays 0 %."
            ),
        }],
    },
    {
        "file": "T116-G8-FAMB-nonamortizing-mnt0pt01-108x600pct.json",
        "case_id": "T116-G8-FAMB-N108",
        "capture_case": "T116-FAMB-R600p0-N108-B1",
        "exemptions": EX_FAMB,
        "title": (
            "GATE G-8, FAMILY B, THE CELL T100 GRADED. MNT 0.01 over 108 monthly repayments at "
            "600.0% p.a. All 108 repayment rows carry principal 0.00, the outstanding balance is "
            "0.01 on every row including the last (due 2033-01-01), totalPrincipalAmount reads 0.00, "
            "and the Go port reproduces every cell. Same two exemptions as T116-G8-FAMB-N104 and no "
            "others. This is the shape T100's exemption demo measured at 761 graded cells / 2 "
            "ungraded / ZERO cell diffs, FAILING on exactly two invariants without an exemption; "
            "T116 re-observed it from the live oracle rather than inheriting those bytes, and "
            "re-measured the port against it."
        ),
        "note": (
            "PROMOTED BY T116 under gate G-8's option (a) mandate. Transcribed from T116's own "
            "live-oracle capture, case T116-FAMB-R600p0-N108-B1. Carried alongside "
            "T116-G8-FAMB-N104 deliberately: n = 104 is the region's lower boundary and n = 108 is "
            "four repayments inside it, so a future change that re-amortizes the region has to move "
            "both, and a change that moves only the boundary is visible as such. The same paradox "
            "applies -- the port is faithful and the loan is not repaid -- and the same two "
            "invariants, and only those two, are exempted."
        ),
        "graded_against": [{
            "id": "G8-FINAL-ROW-SETTLES-THE-BALANCE",
            "capability": "schedule.core",
            "description": (
                "The final repayment row's principal is the whole remaining balance, instead of the "
                "balancing non-negative remainder of its own installment after interest. "
                "getDuePrincipal is negativeToZero(emiPlusCreditedAmounts - getDueInterest()) on "
                "EVERY row including the last [RepaymentPeriod.java:339-344]; the final row comes "
                "out even because calculateLastUnpaidRepaymentPeriodEMI adjusts the INSTALLMENT "
                "[ProgressiveEMICalculator.java:1210-1214], not because the principal is "
                "special-cased. THE PORT'S OWN SOURCE NAMES THIS AS AN UNGRADED BLIND SPOT at "
                "emi.go:1832-1842: 'A port that special-cases the principal instead reproduces the "
                "same numbers on this corpus and is wrong in shape.' MEASURED: 0 divergent cells on "
                "the sibling clean vector T116-G8-CLEAN-N103 and on all 43 vectors promoted before "
                "T116; 4 divergent cells here."
            ),
            "margin_minor": "1",
            "evidence": CF_EVIDENCE_COMMON + (
                "MARGIN. Over this vector's 326 graded money cells the counterfactual diverges on "
                "4: period[107].interest_minor (oracle OBSERVED 0, counterfactual 1), "
                "period[108].interest_minor (OBSERVED 1, counterfactual 0), "
                "period[108].principal_minor (OBSERVED 0, counterfactual 1) and "
                "period[108].outstanding_principal_minor (OBSERVED 1, counterfactual 0). The widest "
                "single-cell disagreement is 1 MINOR UNIT -- which is the ENTIRE loan: the "
                "counterfactual repays 100 % of the principal where the oracle repays 0 %."
            ),
        }],
    },
]


def build(spec):
    cap = CAPS[spec["capture_case"]]
    o, i = cap["observed"], cap["inputs"]
    rate = Fraction(str(i["annualNominalInterestRate"])) / 100   # exact rational; never a float
    return {
        "schema": "gerege.loanschedule.vector/v1",
        "case_id": spec["case_id"],
        "context": "loanschedule",
        "class": "parity",
        "title": spec["title"],
        "dec1_revision": PIN_REV,
        "_note": spec["note"],
        "capabilities_required": ["schedule.core"],
        "graded_against": spec["graded_against"],
        "retires_when_capability_graded": "",
        "provenance": {
            "kind": "oracle-capture",
            "note": PROVENANCE_NOTE,
            "capture_ref": CAPREL,
            "capture_sha256": CAP_SHA,
            "capture_case_id": cap["id"],
            "citation": "",
        },
        "oracle": {
            "fineract_commit": "426a23544e8426a38ae43ae404670a0a7e85b9eb",
            "seam": "path_a_embeddable",
            "captured_at": CAPTURED_AT,
            "threaded_mathcontext": {"precision": 19, "rounding_mode": "HALF_UP"},
            "ambient_mathcontext": {"precision": 19, "rounding_mode": "HALF_UP"},
        },
        "request": {
            "time_zone": "Asia/Ulaanbaatar",
            "currency": {"code": "MNT", "minor_unit_digits": 2},
            "rounding": {"significant_digits": 19, "rate_factor_scale": 19, "mode": "HALF_UP"},
            "schedule_start_date": d(i["scheduleGenerationStartDate"]),
            "disbursements": [{"date": d(i["disbursementDate"]),
                               "amount_minor": str(minor(i["disbursementAmount"]))}],
            "number_of_repayments": i["numberOfRepayments"],
            "repayment_every": 1,
            "repayment_frequency_unit": "MONTHS",
            "annual_nominal_interest_rate": {"numerator": rate.numerator,
                                             "denominator": rate.denominator},
            "interest_method": "DECLINING_BALANCE",
            "day_count": "FIXED_30_360",
            "down_payment_percentage": {"numerator": 0, "denominator": 1},
            "installment_rounding_multiple_minor": "0",
        },
        "expect": {
            "kind": "schedule", "sentinel": "", "last_repayment_due_date": None,
            "observed_total_interest_minor": str(minor(o["totalInterestAmount"])),
            "periods": periods_of(cap),
        },
        "invariant_exemptions": spec["exemptions"],
    }


def main():
    if not os.path.isdir(OUTDIR):
        sys.exit("vector store not found at %s -- is ROOT (%s) really the repo root?" % (OUTDIR, ROOT))
    for spec in VECTORS:
        v = build(spec)
        # TRANSCRIPTION AUDIT, in this script, before the file is written: every money cell of the
        # built vector is re-derived from the capture a second time and compared as an INTEGER.
        cap = CAPS[spec["capture_case"]]
        rows = cap["observed"]["periods"]
        assert len(v["expect"]["periods"]) == len(rows), spec["case_id"]
        for got, src in zip(v["expect"]["periods"], rows):
            assert int(got["principal_minor"]) == minor(src["principal"])
            assert got["principal_major_text"] == src["principal"]
            assert int(got["outstanding_principal_minor"]) == minor(src["balance"])
            assert got["outstanding_principal_major_text"] == src["balance"]
            if src["type"] == "REPAYMENT":
                assert int(got["interest_minor"]) == minor(src["interest"])
                assert got["interest_major_text"] == src["interest"]
                assert int(got["observed_total_due_minor"]) == minor(src["total"])
        path = os.path.join(OUTDIR, spec["file"])
        with open(path, "w") as fh:
            json.dump(v, fh, indent=1)
            fh.write("\n")
        exempt = [e["invariant"] for e in v["invariant_exemptions"]]
        print("wrote %-56s  %3d rows  exemptions: %s"
              % (spec["file"], len(v["expect"]["periods"]),
                 ", ".join(exempt) if exempt else "NONE"))
    print("capture sha256 %s" % CAP_SHA)


if __name__ == "__main__":
    main()
