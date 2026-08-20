#!/usr/bin/env python3
"""T83 STEP 5 — does `invariant_exemptions` actually reach the G-8 divergence?

    python3 .softhouse/capture/t83-nonamortizing/src/run-exemption-demo.py

WHAT THIS IS. A PREPARATION, not a promotion. It builds the vector option (a)
would need — a parity vector for MNT 0.01 / 6 x 21.6%, transcribed from the
committed T83 capture — in two variants, one with `invariant_exemptions: []` and
one exempting `principal_amortizes_to_zero` and `balance_roll_forward`, and grades
each with the REAL conformance harness and the REAL Go port over a SCRATCH store
under /tmp.

NOTHING IS WRITTEN TO .softhouse/vectors. The committed corpus count does not
change. The proposed vector files are written into this capture directory as
`proposed-vector-*.json` so a reviewer can read exactly what was graded.

Every expect cell is TRANSCRIBED from the capture, never computed: the only
transformation is exact textual major->minor scaling, and the oracle's own emitted
characters are carried alongside in the *_major_text fields so the scaling is
mechanically re-checkable.

Money is int64 minor units. No floating point in this file.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CAPDIR = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(CAPDIR, "out", "capture-t83-raw.json")
CAP_REL = ".softhouse/capture/t83-nonamortizing/out/capture-t83-raw.json"
CASE = "T83-SW-R21p6-N6-B1"
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"


def env():
    e = dict(os.environ)
    e.update(GOROOT=TC + "/go", GOPATH=TC + "/gopath", GOCACHE=TC + "/gocache",
             GOMODCACHE=TC + "/gomodcache", PATH=TC + "/go/bin:" + e.get("PATH", ""))
    return e


def minor(text):
    """Exact major-unit decimal text -> int64 minor units. No float, ever."""
    neg = text.startswith("-")
    t = text.lstrip("-")
    whole, _, frac = t.partition(".")
    if len(frac) > 2 and set(frac[2:]) != {"0"}:
        sys.exit("OVER-SCALED wire text %r" % text)
    frac = (frac + "00")[:2]
    v = int(whole or 0) * 100 + int(frac)
    return -v if neg else v


def d(s):
    y, m, dd = s.split("-")
    return {"year": int(y), "month": int(m), "day": int(dd)}


def build(cap, exemptions, pin_rev):
    o = cap["observed"]
    i = cap["inputs"]
    periods = []
    for idx, p in enumerate(o["periods"]):
        if p["type"] == "DISBURSEMENT":
            periods.append({
                "kind": "DISBURSEMENT", "installment_number": 0,
                "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                "principal_minor": str(minor(p["principal"])), "principal_major_text": p["principal"],
                "interest_minor": "", "interest_major_text": "",
                "outstanding_principal_minor": str(minor(p["balance"])),
                "outstanding_principal_major_text": p["balance"],
                # The oracle's LoanSchedulePlanDisbursementPeriod returns null for
                # periodNumber and has no interest accessor at all, so those two
                # cells were never observed. Same withdrawal the promoted T64-ZP
                # vectors make.
                "unrecorded_fields": ["installment_number", "interest_minor"],
                "observed_total_due_minor": None,
            })
        else:
            periods.append({
                "kind": "REPAYMENT", "installment_number": p["periodNumber"],
                "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                "principal_minor": str(minor(p["principal"])), "principal_major_text": p["principal"],
                "interest_minor": str(minor(p["interest"])), "interest_major_text": p["interest"],
                "outstanding_principal_minor": str(minor(p["balance"])),
                "outstanding_principal_major_text": p["balance"],
                "unrecorded_fields": [],
                "observed_total_due_minor": str(minor(p["total"])),
            })
    return {
        "schema": "gerege.loanschedule.vector/v1",
        "case_id": "T83-NONAMORT-A" if exemptions else "T83-NONAMORT-NOEXEMPT",
        "context": "loanschedule",
        "class": "parity",
        "title": "PROPOSED, NOT PROMOTED. Gate G-8: MNT 0.01 over 6 monthly repayments at 21.6% p.a., "
                 "strictly inside the graded domain, where the reference oracle emits an "
                 "outstanding-balance column that never reaches zero (0.01 on every row including "
                 "the last) while its own principal column amortizes fully and its own "
                 "totalOutstandingAmount reads 0.",
        "dec1_revision": pin_rev,
        "_note": "PREPARED BY T83 FOR GATE G-8. NOT PROMOTED and NOT part of the conformance corpus. "
                 "Every expect cell is transcribed from capture case %s of %s; the only "
                 "transformation is exact textual major->minor scaling. The final row's "
                 "outstanding_principal_minor is 1, which is what the reference oracle emitted and "
                 "what T83's order-dependence probe showed to be a STALE MEMO "
                 "(RepaymentPeriod.java:400 omits emi from the balance memo's dependency array; "
                 "ProgressiveEMICalculator.java:1180 reads the balance before :1210 raises the EMI). "
                 "This file exists to MEASURE what the harness does with such a vector, not to be "
                 "merged." % (CASE, CAP_REL),
        "capabilities_required": ["schedule.core"],
        "graded_against": [{
            "id": "G8-STALE-BALANCE-MEMO",
            "capability": "schedule.core",
            "description": "A port that recomputes the final row's outstanding balance AFTER the "
                           "final-period EMI adjustment (as the Go port does) returns 0 where the "
                           "reference oracle returns the whole principal. Measured across T83's "
                           "sweep: 198 of 330 graded-domain cells diverge, every one of them in the "
                           "outstanding-principal column of the FINAL ROW ONLY, one cell per case.",
            "margin_minor": "1",
            "evidence": "Observed at the ratified production MathContext (19, HALF_UP) in "
                        "%s (capture case %s) and in "
                        ".softhouse/capture/t83-nonamortizing/out/port-vs-oracle.json. The port's "
                        "control on the two already-promoted rounding-floor parity vectors "
                        "T64-ZP-A / T64-ZP-B is 0 mismatch cells, so the divergence is not the port "
                        "being broken on graded ground." % (CAP_REL, CASE),
        }],
        "retires_when_capability_graded": "",
        "provenance": {
            "kind": "oracle-capture",
            "note": "TRANSCRIBED, never computed, from Path A capture T83 "
                    "(.softhouse/capture/t83-nonamortizing/src/run-t83.sh, CaptureT83.java), whose "
                    "two rig calibrations reproduce pass 3g's committed T64-ZP-A and T64-ZP-B cell "
                    "for cell with zero input differences.",
            "capture_ref": CAP_REL,
            "capture_sha256": hashlib.sha256(open(CAP, "rb").read()).hexdigest(),
            "capture_case_id": CASE,
            "citation": "",
        },
        "oracle": {
            "fineract_commit": "426a23544e8426a38ae43ae404670a0a7e85b9eb",
            "seam": "path_a_embeddable",
            "captured_at": json.load(open(CAP))["attestation"]["capturedAtUtc"],
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
            "annual_nominal_interest_rate": {"numerator": 27, "denominator": 125},
            "interest_method": "DECLINING_BALANCE",
            "day_count": "FIXED_30_360",
            "down_payment_percentage": {"numerator": 0, "denominator": 1},
            "installment_rounding_multiple_minor": "0",
        },
        "expect": {
            "kind": "schedule", "sentinel": "", "last_repayment_due_date": None,
            "observed_total_interest_minor": str(minor(o["totalInterestAmount"])),
            "periods": periods,
        },
        "invariant_exemptions": exemptions,
    }


def grade(store):
    scratch = "/tmp/t83grade"
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
    dd = os.path.join(scratch, "nexus", "cmd", "t83grade")
    os.makedirs(dd)
    shutil.copy(os.path.join(HERE, "t83grade.go.txt"), os.path.join(dd, "main.go"))
    p = subprocess.run(["go", "run", "./cmd/t83grade", ROOT, store],
                       cwd=os.path.join(scratch, "nexus"), env=env(), capture_output=True, text=True)
    shutil.rmtree(scratch, ignore_errors=True)
    if p.returncode not in (0, 1, 2):
        sys.exit("grader failed (%d):\n%s" % (p.returncode, p.stderr[:4000]))
    if not p.stdout.strip():
        sys.exit("grader produced no output:\n%s" % p.stderr[:4000])
    return json.loads(p.stdout)


def main():
    caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}
    pin = json.load(open(os.path.join(ROOT, ".softhouse/vectors/PIN.json")))
    pin_rev = pin["dec1_revision"]

    variants = {
        "NO-EXEMPTION": [],
        "WITH-EXEMPTION": [
            {"invariant": "principal_amortizes_to_zero",
             "reason": "GATE G-8. The reference oracle emits a non-zero outstanding balance on the "
                       "final row of this graded-domain shape. T83 observed the cause to be a stale "
                       "memo, not a genuine failure to amortize: the same schedule's principal "
                       "column sums to the disbursed amount and its own totalOutstandingAmount "
                       "reads 0."},
            {"invariant": "balance_roll_forward",
             "reason": "GATE G-8, same shape. The final row's outstanding is the value carried in "
                       "rather than max(0, carried in - principal), because the oracle's balance "
                       "memo was populated before the final-period EMI adjustment."},
        ],
    }

    results = {}
    for name, ex in variants.items():
        v = build(caps[CASE], ex, pin_rev)
        path = os.path.join(CAPDIR, "proposed-vector-%s.json" % name.lower())
        with open(path, "w") as f:
            json.dump(v, f, indent=1)
            f.write("\n")
        store = "/tmp/t83store-%s" % name.lower()
        shutil.rmtree(store, ignore_errors=True)
        os.makedirs(os.path.join(store, "loanschedule"))
        for f_ in ("PIN.json", "capabilities.json"):
            shutil.copy(os.path.join(ROOT, ".softhouse/vectors", f_), os.path.join(store, f_))
        shutil.copy(path, os.path.join(store, "loanschedule", "T83-PROPOSED.json"))
        results[name] = grade(store)
        shutil.rmtree(store, ignore_errors=True)

    out = os.path.join(CAPDIR, "out", "exemption-demo.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
        f.write("\n")

    for name, r in results.items():
        print("=== %s ===" % name)
        print("  harness exit code: %s   parityPass %s parityFail %s inadmissible %s refused %s "
              "invariantViolations %s"
              % (r["exitCode"], r["parityPass"], r["parityFail"], r["inadmissible"],
                 r["refused"], r["invariantViolations"]))
        for fr in r.get("fatalReasons") or []:
            print("  FATAL: " + fr[:200])
        for le in r.get("loadErrors") or []:
            print("  LOAD ERROR: %s" % le)
        for res in r.get("results") or []:
            print("  %s -> %s (graded %s cells, ungraded %s)"
                  % (res["case_id"], res["outcome"], res["graded_cells"], res["ungraded_cells"]))
            for dtl in res.get("detail") or []:
                print("      detail: " + dtl[:220])
            for iv in res.get("invariants") or []:
                print("      invariant %-34s %s" % (iv["name"], iv["status"]))
        print()
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
