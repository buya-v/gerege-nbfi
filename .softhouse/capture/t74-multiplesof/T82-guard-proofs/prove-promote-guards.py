#!/usr/bin/env python3
"""T82 — make T74-promote-vectors.py's D-1/D-2 guards go red, and prove the honest cases stay green.

    python3 prove-promote-guards.py <repo-root> <mode>

Exit 1 means the promotion script REFUSED the mutated capture, which for a guard proof is the
PASSING outcome; the driver `prove-guards-go-red.sh` states the expected exit for each mode.

HOW IT AVOIDS TOUCHING THE STORE. The promotion script is loaded as a MODULE (so it is the real code
under test, not a copy of it), and only then are its two path globals repointed — `P3I_REF` at a
mutated capture under `scratch/`, `VECTORS` at a scratch output directory. The committed script gains
no environment-variable configurability from this: a proof harness reaching in is not the same as the
script offering a way to promote from an arbitrary capture.

Money is never mutated here. The modes edit day-count labels, a down-payment percentage, the
repayment-interval keys and a periodNumber. No principal, interest, balance or total is touched.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

MODES = ("day-count", "down-payment", "down-payment-enabled", "repayment-every-absent",
         "repayment-every-conflict", "period-number-zero", "period-number-bad")


def load_promoter(root):
    path = os.path.join(root, ".softhouse/handoff/T74-promote-vectors.py")
    spec = importlib.util.spec_from_file_location("t74_promote", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)      # __name__ != "__main__", so main() does not run
    return mod


def mutate(doc, mode):
    """Return (doc, note). Applied to every group-E case the promoter walks."""
    ids = {"T74-E-P4", "T74-E-P59", "T74-E-P72", "T74-E-P340", "T74-E-P426", "T74-E-P6940"}
    for c in doc["captures"]:
        if c["id"] not in ids:
            continue
        i = c["inputs"]
        if mode == "day-count":
            i["daysInMonth"], i["daysInYear"] = "ACTUAL", "DAYS_365"
        elif mode == "down-payment":
            i["downPaymentPercentage"] = "25"
        elif mode == "down-payment-enabled":
            i["downPaymentEnabled"] = True
        elif mode == "repayment-every-absent":
            i.pop("repaymentEvery", None)
            i.pop("repaymentFrequency", None)
        elif mode == "repayment-every-conflict":
            i["repaymentEvery"] = 3          # the capture already records repaymentFrequency = 1
        elif mode == "period-number-zero":
            for p in c["observed"]["periods"]:
                if p.get("type") == "REPAYMENT" and p.get("periodNumber") == 1:
                    p["periodNumber"] = 0
        elif mode == "period-number-bad":
            for p in c["observed"]["periods"]:
                if p.get("type") == "REPAYMENT" and p.get("periodNumber") == 1:
                    p["periodNumber"] = "1"
        else:
            raise SystemExit("unknown mode %r" % mode)
    return doc


NOTES = {
    "day-count": "daysInMonth/daysInYear -> (ACTUAL, DAYS_365), a pair the contract does not name. "
                 "The OLD code wrote the constant \"FIXED_30_360\" regardless.",
    "down-payment": "downPaymentPercentage -> \"25\". The OLD code wrote {0, 1} regardless, so the "
                    "vector would have graded a schedule the request did not describe.",
    "down-payment-enabled": "downPaymentEnabled -> true, percentage still \"0\".",
    "repayment-every-absent": "both `repaymentEvery` and `repaymentFrequency` removed. The OLD "
                              "`i.get(\"repaymentEvery\", i.get(\"repaymentFrequency\"))` returned "
                              "None and wrote a null interval into the vector.",
    "repayment-every-conflict": "`repaymentEvery` = 3 against the recorded `repaymentFrequency` = 1. "
                                "The OLD code silently preferred `repaymentEvery`.",
    "period-number-zero": "period 1's periodNumber -> 0, a LEGITIMATE zero. It must survive as 0 and "
                          "must NOT be reported as unrecorded. The OLD `or 0` could not tell it "
                          "from an absent value.",
    "period-number-bad": "period 1's periodNumber -> the string \"1\". Must be refused, not coerced.",
}


def main(root, mode):
    if mode not in MODES:
        raise SystemExit("mode must be one of %r" % (MODES,))
    os.chdir(root)
    mod = load_promoter(root)

    doc = json.load(open(mod.P3I_REF, encoding="utf-8"))
    doc = mutate(doc, mode)

    tmp = tempfile.mkdtemp(prefix="t82promote")
    try:
        cap = os.path.join(tmp, "mutated-capture.json")
        json.dump(doc, open(cap, "w", encoding="utf-8"), indent=1)
        out = os.path.join(tmp, "vectors")
        os.makedirs(out)

        print("MUTATION: %s" % NOTES[mode])
        print("          mutated capture -> %s" % cap)
        print("          vectors written to a SCRATCH dir, never to the store")

        mod.P3I_REF = cap
        mod.VECTORS = out

        mod.main()      # SystemExit(str) here == the guard fired

        # Only the honest modes get this far. For period-number-zero, assert the point of the fix:
        # the legitimate 0 survived AND was not filed as unrecorded.
        if mode == "period-number-zero":
            f = os.path.join(out, mod.FILENAMES["T74-E-P4"])
            v = json.load(open(f, encoding="utf-8"))
            rows = v["expect"]["periods"]
            payable = [r for r in rows if r["kind"] == "REPAYMENT"]
            first = payable[0]
            disb = [r for r in rows if r["kind"] == "DISBURSEMENT"][0]
            print("\nASSERTIONS on the regenerated %s:" % os.path.basename(f))
            print("  payable row 1 installment_number = %r  (a LEGITIMATE 0, transcribed)"
                  % first["installment_number"])
            print("  payable row 1 unrecorded_fields  = %r  (installment_number NOT withdrawn)"
                  % first.get("unrecorded_fields"))
            print("  DISBURSEMENT  installment_number = %r  unrecorded_fields = %r  (absence IS "
                  "withdrawn)" % (disb["installment_number"], disb.get("unrecorded_fields")))
            ok = (first["installment_number"] == 0
                  and "installment_number" not in (first.get("unrecorded_fields") or [])
                  and disb["installment_number"] == 0
                  and "installment_number" in (disb.get("unrecorded_fields") or []))
            if not ok:
                raise SystemExit("ASSERTION FAILED: a legitimate 0 is not distinguished from absence")
            print("  -> a legitimate 0 and an absent value are DISTINGUISHED. "
                  "`p.get(\"periodNumber\") or 0` could not do this.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
