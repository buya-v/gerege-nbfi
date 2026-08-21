#!/usr/bin/env python3
"""T100 — does `invariant_exemptions` reach option (a)? Measured SEPARATELY ON EACH FAMILY.

Derived from T84's exemption-demo.py, which was itself derived from T83's run-exemption-demo.py.
Same machinery both times: the REAL `conformance.Run` and the REAL Go port over a throw-away
store under /tmp. NOTHING is written to `.softhouse/vectors`; `PIN.json` and `capabilities.json`
are copied read-only into the scratch store.

The point T83 and T84 each got half of:

  family B (600.0 % / MNT 0.01 / n = 108) — the port REPRODUCES the oracle, so there is no cell
      diff, the FAIL is purely invariant, and the exemption is therefore decisive.
  family A (3.6 % / MNT 1.09 / n = 360)  — the port does NOT reproduce the oracle's final-row
      balance, so there is a CELL DIFF, which `invariant_exemptions` has no power over.

Both cases are transcribed from T100's OWN capture (`out/capture-t100-raw.json`), whose two rig
calibrations reproduce the committed pass-3g T64-ZP-A / T64-ZP-B cell for cell.
"""
import hashlib, json, os, shutil, subprocess, sys
from fractions import Fraction

ROOT = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-a2cb1d0cfe5c2fec8'
CAP = os.path.join(ROOT, '.softhouse/capture/t100-g8-rescope/out/capture-t100-raw.json')
HERE = os.path.join(ROOT, '.softhouse/capture/t83-nonamortizing/src')   # t83grade.go.txt lives here
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"


def env():
    e = dict(os.environ)
    e.update(GOROOT=TC + "/go", GOPATH=TC + "/gopath", GOCACHE=TC + "/gocache",
             GOMODCACHE=TC + "/gomodcache", PATH=TC + "/go/bin:" + e.get("PATH", ""))
    return e


def minor(text):
    neg = text.startswith("-")
    t = text.lstrip("-")
    w, _, fr = t.partition(".")
    if len(fr) > 2 and set(fr[2:]) != {"0"}:
        sys.exit("OVER-SCALED %r" % text)
    fr = (fr + "00")[:2]
    v = int(w or 0) * 100 + int(fr)
    return -v if neg else v


def d(s):
    y, m, dd = s.split("-")
    return {"year": int(y), "month": int(m), "day": int(dd)}


def build(cap, exemptions, pin_rev, cid, title, note, graded_against):
    o, i = cap["observed"], cap["inputs"]
    periods = []
    for p in o["periods"]:
        if p["type"] == "DISBURSEMENT":
            periods.append({"kind": "DISBURSEMENT", "installment_number": 0,
                            "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                            "principal_minor": str(minor(p["principal"])),
                            "principal_major_text": p["principal"],
                            "interest_minor": "", "interest_major_text": "",
                            "outstanding_principal_minor": str(minor(p["balance"])),
                            "outstanding_principal_major_text": p["balance"],
                            "unrecorded_fields": ["installment_number", "interest_minor"],
                            "observed_total_due_minor": None})
        else:
            periods.append({"kind": "REPAYMENT", "installment_number": p["periodNumber"],
                            "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                            "principal_minor": str(minor(p["principal"])),
                            "principal_major_text": p["principal"],
                            "interest_minor": str(minor(p["interest"])),
                            "interest_major_text": p["interest"],
                            "outstanding_principal_minor": str(minor(p["balance"])),
                            "outstanding_principal_major_text": p["balance"],
                            "unrecorded_fields": [], "observed_total_due_minor": str(minor(p["total"]))})
    rate = Fraction(i["annualNominalInterestRate"]) / 100     # exact; never float
    return {
        "schema": "gerege.loanschedule.vector/v1", "case_id": cid, "context": "loanschedule",
        "class": "parity",
        "title": title,
        "dec1_revision": pin_rev,
        "_note": note,
        "capabilities_required": ["schedule.core"],
        "graded_against": [graded_against],
        "retires_when_capability_graded": "",
        "provenance": {"kind": "oracle-capture",
                       "note": "TRANSCRIBED, never computed, from T100's own Path A capture.",
                       "capture_ref": ".softhouse/capture/t100-g8-rescope/out/capture-t100-raw.json",
                       "capture_sha256": hashlib.sha256(open(CAP, "rb").read()).hexdigest(),
                       "capture_case_id": cap["id"], "citation": ""},
        "oracle": {"fineract_commit": "426a23544e8426a38ae43ae404670a0a7e85b9eb",
                   "seam": "path_a_embeddable",
                   "captured_at": json.load(open(CAP))["attestation"]["capturedAtUtc"],
                   "threaded_mathcontext": {"precision": 19, "rounding_mode": "HALF_UP"},
                   "ambient_mathcontext": {"precision": 19, "rounding_mode": "HALF_UP"}},
        "request": {"time_zone": "Asia/Ulaanbaatar",
                    "currency": {"code": "MNT", "minor_unit_digits": 2},
                    "rounding": {"significant_digits": 19, "rate_factor_scale": 19, "mode": "HALF_UP"},
                    "schedule_start_date": d(i["scheduleGenerationStartDate"]),
                    "disbursements": [{"date": d(i["disbursementDate"]),
                                       "amount_minor": str(minor(i["disbursementAmount"]))}],
                    "number_of_repayments": i["numberOfRepayments"], "repayment_every": 1,
                    "repayment_frequency_unit": "MONTHS",
                    "annual_nominal_interest_rate": {"numerator": rate.numerator,
                                                     "denominator": rate.denominator},
                    "interest_method": "DECLINING_BALANCE", "day_count": "FIXED_30_360",
                    "down_payment_percentage": {"numerator": 0, "denominator": 1},
                    "installment_rounding_multiple_minor": "0"},
        "expect": {"kind": "schedule", "sentinel": "", "last_repayment_due_date": None,
                   "observed_total_interest_minor": str(minor(o["totalInterestAmount"])),
                   "periods": periods},
        "invariant_exemptions": exemptions,
    }


def grade(store):
    scratch = "/tmp/t100grade"
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
    dd = os.path.join(scratch, "nexus", "cmd", "t83grade")
    os.makedirs(dd)
    shutil.copy(os.path.join(HERE, "t83grade.go.txt"), os.path.join(dd, "main.go"))
    p = subprocess.run(["go", "run", "./cmd/t83grade", ROOT, store],
                       cwd=os.path.join(scratch, "nexus"), env=env(), capture_output=True, text=True)
    shutil.rmtree(scratch, ignore_errors=True)
    if not p.stdout.strip():
        sys.exit("grader no output (%d):\n%s" % (p.returncode, p.stderr[:4000]))
    return json.loads(p.stdout)


EX_B = [
    {"invariant": "principal_amortizes_to_zero",
     "reason": "GATE G-8, family B. The reference oracle emits a schedule for this graded-domain "
               "shape whose principal column never repays the disbursement; the Go port reproduces "
               "it cell for cell, so the divergence is not port-vs-oracle."},
    {"invariant": "principal_portions_sum_to_disbursed",
     "reason": "GATE G-8, family B. The oracle's own principal column sums to 0.00 against a 0.01 "
               "disbursement, and the port agrees."},
    {"invariant": "balance_roll_forward",
     "reason": "GATE G-8, family B. The balance column is constant at the disbursed amount on every row."},
]
EX_A = [
    {"invariant": "principal_amortizes_to_zero",
     "reason": "GATE G-8, family A. The reference oracle's final-row balance column is stale with "
               "respect to its own final EMI adjustment on this shape."},
    {"invariant": "balance_roll_forward",
     "reason": "GATE G-8, family A. The balance column is constant at the disbursed amount on every row."},
]

GA_B = {"id": "G8-FAMILY-B-NONAMORTIZING-PRINCIPAL-COLUMN", "capability": "schedule.core",
        "description": "An implementation that amortizes the principal on this shape returns a "
                       "principal column summing to the disbursement; the reference oracle returns "
                       "one summing to zero, and so does the Go port.",
        "margin_minor": "1",
        "evidence": "T100 Path A capture out/capture-t100-raw.json, case T100-FAMB-R600p0-N108-B1."}
GA_A = {"id": "G8-FAMILY-A-STALE-BALANCE-COLUMN", "capability": "schedule.core",
        "description": "An implementation that recomputes the final row's balance after the final "
                       "EMI adjustment returns 0; the reference oracle returns the disbursed amount.",
        "margin_minor": "1",
        "evidence": "T100 Path A capture out/capture-t100-raw.json, case T100-FAMA-R3p6-N360-B109."}

VARIANTS = {
    "FAMILY-B-NO-EXEMPTION": ("T100-G8-FAMB-NOEXEMPT", "T100-FAMB-R600p0-N108-B1", [], GA_B),
    "FAMILY-B-WITH-EXEMPTION": ("T100-G8-FAMB", "T100-FAMB-R600p0-N108-B1", EX_B, GA_B),
    "FAMILY-A-NO-EXEMPTION": ("T100-G8-FAMA-NOEXEMPT", "T100-FAMA-R3p6-N360-B109", [], GA_A),
    "FAMILY-A-WITH-EXEMPTION": ("T100-G8-FAMA", "T100-FAMA-R3p6-N360-B109", EX_A, GA_A),
}

caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}
pin_rev = json.load(open(os.path.join(ROOT, ".softhouse/vectors/PIN.json")))["dec1_revision"]
results = {}
for name, (cid, case, ex, ga) in VARIANTS.items():
    fam = 'B' if 'FAMB' in case else 'A'
    v = build(caps[case], ex, pin_rev, cid,
              "PROPOSED BY T100, NOT PROMOTED. Gate G-8, family %s, from capture case %s." % (fam, case),
              "PREPARED to measure whether `invariant_exemptions` is decisive on family %s. NOT "
              "PROMOTED. Every expect cell is transcribed from capture case %s; the only "
              "transformation is exact textual major->minor scaling." % (fam, case), ga)
    path = "/tmp/t100-proposed-%s.json" % name.lower()
    json.dump(v, open(path, "w"), indent=1)
    store = "/tmp/t100store-%s" % name.lower()
    shutil.rmtree(store, ignore_errors=True)
    os.makedirs(os.path.join(store, "loanschedule"))
    for f_ in ("PIN.json", "capabilities.json"):
        shutil.copy(os.path.join(ROOT, ".softhouse/vectors", f_), os.path.join(store, f_))
    shutil.copy(path, os.path.join(store, "loanschedule", "T100-PROPOSED.json"))
    results[name] = grade(store)
    shutil.rmtree(store, ignore_errors=True)

for name, r in results.items():
    print("=== %s ===" % name)
    print("  exit %s  parityPass %s parityFail %s inadmissible %s refused %s invariantViolations %s"
          % (r["exitCode"], r["parityPass"], r["parityFail"], r["inadmissible"], r["refused"],
             r["invariantViolations"]))
    for le in r.get("loadErrors") or []:
        print("  LOAD ERROR:", le)
    for res in r.get("results") or []:
        print("  %s -> %s (graded %s cells, ungraded %s)"
              % (res["case_id"], res["outcome"], res["graded_cells"], res["ungraded_cells"]))
        for dtl in (res.get("detail") or [])[:6]:
            print("      detail: " + dtl[:220])
        for iv in res.get("invariants") or []:
            print("      invariant %-36s %s" % (iv["name"], iv["status"]))
    print()
json.dump(results, open(os.path.join(ROOT, '.softhouse/capture/t100-g8-rescope/out/exemption-demo-t100.json'),
                        'w'), indent=1)
