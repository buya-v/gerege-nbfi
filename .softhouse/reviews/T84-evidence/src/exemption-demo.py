#!/usr/bin/env python3
"""T84 counterexample to T83's 'invariant_exemptions is inert' conclusion.

Same machinery as T83's run-exemption-demo.py -- the REAL conformance.Run and the
REAL Go port over a scratch store under /tmp -- but on a G-8-family shape T83 never
measured: MNT 0.01 over 108 monthly repayments at 600.0% p.a., inside the graded
domain, where the ORACLE AND THE PORT AGREE CELL FOR CELL on a schedule whose
principal column never repays the disbursement.

Nothing is written to .softhouse/vectors.
"""
import hashlib, json, os, shutil, subprocess, sys

ROOT = '/Users/buv/gerege-nbfi/.claude/worktrees/agent-a6c2c61c89d384f71'
CAP = '/tmp/t84probe2/out/capture-t84b-raw.json'
CASE = 'T84B-NSW-R600p0-N108-B1'
HERE = os.path.join(ROOT, '.softhouse/capture/t83-nonamortizing/src')
TC = "/Users/buv/gerege-nbfi/.softhouse/toolchain"

def env():
    e = dict(os.environ)
    e.update(GOROOT=TC + "/go", GOPATH=TC + "/gopath", GOCACHE=TC + "/gocache",
             GOMODCACHE=TC + "/gomodcache", PATH=TC + "/go/bin:" + e.get("PATH", ""))
    return e

def minor(text):
    neg = text.startswith("-"); t = text.lstrip("-")
    w, _, fr = t.partition(".")
    if len(fr) > 2 and set(fr[2:]) != {"0"}: sys.exit("OVER-SCALED %r" % text)
    fr = (fr + "00")[:2]
    v = int(w or 0) * 100 + int(fr)
    return -v if neg else v

def d(s):
    y, m, dd = s.split("-"); return {"year": int(y), "month": int(m), "day": int(dd)}

def build(cap, exemptions, pin_rev, cid):
    o, i = cap["observed"], cap["inputs"]
    periods = []
    for p in o["periods"]:
        if p["type"] == "DISBURSEMENT":
            periods.append({"kind": "DISBURSEMENT", "installment_number": 0,
                "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                "principal_minor": str(minor(p["principal"])), "principal_major_text": p["principal"],
                "interest_minor": "", "interest_major_text": "",
                "outstanding_principal_minor": str(minor(p["balance"])),
                "outstanding_principal_major_text": p["balance"],
                "unrecorded_fields": ["installment_number", "interest_minor"],
                "observed_total_due_minor": None})
        else:
            periods.append({"kind": "REPAYMENT", "installment_number": p["periodNumber"],
                "from_date": d(p["periodFromDate"]), "due_date": d(p["dueDate"]),
                "principal_minor": str(minor(p["principal"])), "principal_major_text": p["principal"],
                "interest_minor": str(minor(p["interest"])), "interest_major_text": p["interest"],
                "outstanding_principal_minor": str(minor(p["balance"])),
                "outstanding_principal_major_text": p["balance"],
                "unrecorded_fields": [], "observed_total_due_minor": str(minor(p["total"]))})
    return {
        "schema": "gerege.loanschedule.vector/v1", "case_id": cid, "context": "loanschedule",
        "class": "parity",
        "title": "PROPOSED BY T84, NOT PROMOTED. Gate G-8, SECOND FAMILY: MNT 0.01 over 108 monthly "
                 "repayments at 600.0% p.a., strictly inside the graded domain, where the reference "
                 "oracle emits a schedule whose principal column NEVER repays the disbursement "
                 "(principal column sums to 0.00 against a 0.01 disbursement) and whose balance "
                 "column is 0.01 on every row -- and the Go port reproduces it cell for cell.",
        "dec1_revision": pin_rev,
        "_note": "PREPARED BY T84 to test whether `invariant_exemptions` is inert on the G-8 family, "
                 "as T83 concluded from a single shape. NOT PROMOTED. Every expect cell is "
                 "transcribed from capture case %s; the only transformation is exact textual "
                 "major->minor scaling." % CASE,
        "capabilities_required": ["schedule.core"],
        "graded_against": [{
            "id": "G8-NONAMORTIZING-PRINCIPAL-COLUMN", "capability": "schedule.core",
            "description": "An implementation that amortizes the principal on this shape returns a "
                           "principal column summing to the disbursement; the reference oracle "
                           "returns one summing to zero. Measured over 22 graded-domain cells at "
                           "600.0% p.a. / MNT 0.01 / n >= 104.",
            "margin_minor": "1",
            "evidence": "T84 Path A capture /tmp/t84probe2/out/capture-t84b-raw.json, calibrated "
                        "against pass 3g's committed T64-ZP-A / T64-ZP-B cell for cell.",
        }],
        "retires_when_capability_graded": "",
        "provenance": {"kind": "oracle-capture",
            "note": "TRANSCRIBED, never computed, from T84's independent Path A capture.",
            "capture_ref": ".softhouse/reviews/T84-evidence/out/capture-t84b-raw.json",
            "capture_sha256": hashlib.sha256(open(CAP, "rb").read()).hexdigest(),
            "capture_case_id": CASE, "citation": ""},
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
            "annual_nominal_interest_rate": {"numerator": 6, "denominator": 1},
            "interest_method": "DECLINING_BALANCE", "day_count": "FIXED_30_360",
            "down_payment_percentage": {"numerator": 0, "denominator": 1},
            "installment_rounding_multiple_minor": "0"},
        "expect": {"kind": "schedule", "sentinel": "", "last_repayment_due_date": None,
            "observed_total_interest_minor": str(minor(o["totalInterestAmount"])),
            "periods": periods},
        "invariant_exemptions": exemptions,
    }

def grade(store):
    scratch = "/tmp/t84grade"
    shutil.rmtree(scratch, ignore_errors=True); os.makedirs(scratch)
    shutil.copytree(os.path.join(ROOT, "nexus"), os.path.join(scratch, "nexus"))
    dd = os.path.join(scratch, "nexus", "cmd", "t83grade"); os.makedirs(dd)
    shutil.copy(os.path.join(HERE, "t83grade.go.txt"), os.path.join(dd, "main.go"))
    p = subprocess.run(["go", "run", "./cmd/t83grade", ROOT, store],
                       cwd=os.path.join(scratch, "nexus"), env=env(), capture_output=True, text=True)
    shutil.rmtree(scratch, ignore_errors=True)
    if not p.stdout.strip(): sys.exit("grader no output (%d):\n%s" % (p.returncode, p.stderr[:4000]))
    return json.loads(p.stdout)

caps = {c["id"]: c for c in json.load(open(CAP))["captures"]}
pin_rev = json.load(open(os.path.join(ROOT, ".softhouse/vectors/PIN.json")))["dec1_revision"]
variants = {
    "NO-EXEMPTION": ("T84-NONAMORT-B-NOEXEMPT", []),
    "WITH-EXEMPTION": ("T84-NONAMORT-B", [
        {"invariant": "principal_amortizes_to_zero",
         "reason": "GATE G-8, second family. The reference oracle emits a schedule for this "
                   "graded-domain shape whose principal column never repays the disbursement; the "
                   "Go port reproduces it cell for cell, so the divergence is not port-vs-oracle."},
        {"invariant": "principal_portions_sum_to_disbursed",
         "reason": "GATE G-8, second family. Same shape: the oracle's own principal column sums to "
                   "0.00 against a 0.01 disbursement, and the port agrees."},
        {"invariant": "balance_roll_forward",
         "reason": "GATE G-8, second family. The balance column is constant at the disbursed amount "
                   "on every row."},
    ]),
}
results = {}
for name, (cid, ex) in variants.items():
    v = build(caps[CASE], ex, pin_rev, cid)
    path = "/tmp/t84-proposed-%s.json" % name.lower()
    json.dump(v, open(path, "w"), indent=1)
    store = "/tmp/t84store-%s" % name.lower()
    shutil.rmtree(store, ignore_errors=True)
    os.makedirs(os.path.join(store, "loanschedule"))
    for f_ in ("PIN.json", "capabilities.json"):
        shutil.copy(os.path.join(ROOT, ".softhouse/vectors", f_), os.path.join(store, f_))
    shutil.copy(path, os.path.join(store, "loanschedule", "T84-PROPOSED.json"))
    results[name] = grade(store)
    shutil.rmtree(store, ignore_errors=True)

for name, r in results.items():
    print("=== %s ===" % name)
    print("  exit %s  parityPass %s parityFail %s inadmissible %s refused %s invariantViolations %s"
          % (r["exitCode"], r["parityPass"], r["parityFail"], r["inadmissible"], r["refused"],
             r["invariantViolations"]))
    for le in r.get("loadErrors") or []: print("  LOAD ERROR:", le)
    for res in r.get("results") or []:
        print("  %s -> %s (graded %s cells, ungraded %s)"
              % (res["case_id"], res["outcome"], res["graded_cells"], res["ungraded_cells"]))
        for dtl in (res.get("detail") or [])[:6]: print("      detail: " + dtl[:220])
        for iv in res.get("invariants") or []:
            print("      invariant %-36s %s" % (iv["name"], iv["status"]),
                  ("  <-- " + (iv.get("detail") or "")[:150]) if iv["status"] not in ("HOLD", "EXEMPT") else "")
    print()
json.dump(results, open('/tmp/t84-exemption-demo.json', 'w'), indent=1)
