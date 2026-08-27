#!/usr/bin/env python3
"""T82 — drive T74-promote-vectors.py's D-1/D-2 guards red, and say honestly what each case proves.

    python3 prove-promote-guards.py <repo-root> <mode> [promoter.py]

Exit 1 means the promotion script REFUSED the mutated capture, which for a GUARD proof is the
passing outcome; the driver `prove-guards-go-red.sh` states the expected exit for each mode.

The optional third argument is the promotion script to load. It defaults to the branch's
`.softhouse/handoff/T74-promote-vectors.py`; the driver passes the FORK POINT'S REAL EXTRACTED BYTES
(`git show $(cat T82-guard-proofs/FORK-POINT-SHA):…`, a LITERAL 40-hex sha) to produce each
COUNTERPROOF. A counterproof run against a reconstruction of the old code proves less than one
against the old code, so nothing here reconstructs anything.

THE BASELINE IS A LITERAL SHA, NOT A COMPUTED REF, AND THAT DISTINCTION IS THE WHOLE POINT. `main:`
moves; so does `git merge-base main HEAD`, which is the fork point only while this branch is
UNMERGED — after the merge HEAD == main and the merge base is the merge commit itself, so every
COUNTERPROOF would compare the fixed code against ITSELF. Measured in T102: 25/25 on the branch,
18/7 on a scratch merge. The literal sha keeps these rows meaning the same thing in both states.

HOW IT AVOIDS TOUCHING THE STORE. The promotion script is loaded as a MODULE (so it is the real code
under test, not a copy of it), and only then are its two path globals repointed — `P3I_REF` at a
mutated capture under `scratch/`, `VECTORS` at a scratch output directory. The committed script gains
no environment-variable configurability from this.

Money is never mutated here. The modes edit day-count labels, a down-payment percentage, the
repayment-interval keys and a periodNumber. No principal, interest, balance or total is touched.

THE THREE KINDS OF CASE, kept apart on purpose — conflating them is what T87 rejected:

  GUARD        the new code REFUSES and the PRE-FIX code ACCEPTS. This is the only kind that
               demonstrates a guard curing a defect; each is paired with a fork-point counterproof.
  REGRESSION   both codebases behave identically and must go on doing so. It proves the rewrite
               BROKE NOTHING. It proves NOTHING about the defect and must never claim to.
  ASSERTION    a property of the emitted vector, checked in code rather than asserted in prose.
"""
import importlib.util
import json
import os
import shutil
import sys

MODES = ("day-count", "down-payment", "down-payment-enabled", "repayment-every-absent",
         "repayment-every-conflict", "period-number-zero", "period-number-bad",
         "period-number-absent-payable", "period-number-on-nonpayable")

GROUP_E = ("T74-E-P4", "T74-E-P59", "T74-E-P72", "T74-E-P340", "T74-E-P426", "T74-E-P6940")

SCRATCH = ".softhouse/capture/t74-multiplesof/T82-guard-proofs/scratch"
BASE_PROMOTER = SCRATCH + "/promote-BASE.py"


def load_promoter(root, path=None):
    path = path or os.path.join(root, ".softhouse/handoff/T74-promote-vectors.py")
    spec = importlib.util.spec_from_file_location("t74_promote_%d" % abs(hash(path)), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)      # __name__ != "__main__", so main() does not run
    return mod


def mutate(doc, mode):
    """Applied to every group-E case the promoter walks."""
    for c in doc["captures"]:
        if c["id"] not in GROUP_E:
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
        elif mode == "period-number-absent-payable":
            # THE case the `or 0` defect actually produced: a payable row with no periodNumber.
            for p in c["observed"]["periods"]:
                if p.get("type") == "REPAYMENT" and p.get("periodNumber") == 1:
                    del p["periodNumber"]
        elif mode == "period-number-on-nonpayable":
            for p in c["observed"]["periods"]:
                if p.get("type") == "DISBURSEMENT":
                    p["periodNumber"] = 0
        else:
            raise SystemExit("unknown mode %r" % mode)
    return doc


KIND = {
    "day-count": "GUARD",
    "down-payment": "GUARD",
    "down-payment-enabled": "GUARD",
    "repayment-every-absent": "GUARD",
    "repayment-every-conflict": "GUARD",
    "period-number-bad": "GUARD",
    "period-number-absent-payable": "GUARD",
    "period-number-on-nonpayable": "GUARD",
    "period-number-zero": "REGRESSION",
}

NOTES = {
    "day-count": "daysInMonth/daysInYear -> (ACTUAL, DAYS_365), a pair the contract does not name. "
                 "The OLD code wrote the constant \"FIXED_30_360\" regardless.",
    "down-payment": "downPaymentPercentage -> \"25\". The OLD code wrote {0, 1} regardless, so the "
                    "vector would have graded a schedule the request did not describe.",
    "down-payment-enabled": "downPaymentEnabled -> true, percentage still \"0\".",
    "repayment-every-absent": "both `repaymentEvery` and `repaymentFrequency` removed. The OLD "
                              "`i.get(\"repaymentEvery\", i.get(\"repaymentFrequency\"))` returned "
                              "None and wrote a null interval into the vector. (Note: "
                              "`repaymentEvery` is absent from ALL 36 committed cases, so that "
                              "fallback was load-bearing on every single one.)",
    "repayment-every-conflict": "`repaymentEvery` = 3 against the recorded `repaymentFrequency` = 1. "
                                "The OLD code silently preferred `repaymentEvery`.",
    "period-number-bad": "period 1's periodNumber -> the string \"1\". Must be refused, not coerced.",
    "period-number-absent-payable":
        "period 1's `periodNumber` KEY DELETED on a PAYABLE row. THIS IS THE DEFECT `or 0` "
        "ACTUALLY CAUSED: the old code evaluated `None or 0`, wrote installment_number 0, filed it "
        "under unrecorded_fields and promoted the vector without a word. An absent installment "
        "number on a payable row is a broken capture, not a value.",
    "period-number-on-nonpayable":
        "every DISBURSEMENT row given `periodNumber: 0`. The withdrawal of that cell is justified by "
        "the oracle emitting no periodNumber for a non-payable row; if one appears, the rig has "
        "changed and withdrawing the cell would be wrong.",
    "period-number-zero":
        "period 1's periodNumber -> 0, a LEGITIMATE zero. REGRESSION CONTROL, NOT A GUARD PROOF: "
        "the PRE-FIX code decided the VALUE with `or 0` (:255) but the WITHDRAWAL with a SEPARATE "
        "`is None` test (:260-261), so a recorded 0 already survived un-withdrawn there. This must stay "
        "green on BOTH codebases and is proved identical between them below. It demonstrates that "
        "the rewrite BROKE NOTHING; it demonstrates NOTHING about the `or 0` defect, and the guard "
        "that does is `period-number-absent-payable`.",
}


def build_vectors(root, promoter, doc, tmp, tag):
    """Run a promotion script over a mutated capture into a scratch dir."""
    cap = os.path.join(tmp, "capture-%s.json" % tag)
    json.dump(doc, open(cap, "w", encoding="utf-8"), indent=1)
    out = os.path.join(tmp, "vectors-%s" % tag)
    os.makedirs(out)
    mod = load_promoter(root, promoter)
    mod.P3I_REF = cap
    mod.VECTORS = out
    mod.main()
    return out, mod


def main(root, mode, promoter=None):
    if mode not in MODES:
        raise SystemExit("mode must be one of %r" % (MODES,))
    os.chdir(root)

    # A DETERMINISTIC scratch dir, not tempfile.mkdtemp(): the random suffix leaked into every
    # printed path and made TRANSCRIPT.txt unreproducible, so a reader could not tell a real change
    # from a fresh temp name. One mode, one fixed directory, wiped before use.
    tmp = os.path.join(root, SCRATCH, "promote-%s" % mode)
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    try:
        print("KIND:     %s" % KIND[mode])
        print("MUTATION: %s" % NOTES[mode])
        print("PROMOTER: %s" % (promoter or ".softhouse/handoff/T74-promote-vectors.py (this branch)"))
        print("          vectors written to a SCRATCH dir, never to the store")

        ref = load_promoter(root, promoter).P3I_REF
        doc = mutate(json.load(open(ref, encoding="utf-8")), mode)

        out, mod = build_vectors(root, promoter, doc, tmp, "under-test")
        # SystemExit(str) inside build_vectors == the guard fired; we only reach here on acceptance.

        if mode == "period-number-zero":
            # ASSERTION 1 — the emitted vector tells a legitimate 0 from an absent value.
            f = os.path.join(out, mod.FILENAMES["T74-E-P4"])
            rows = json.load(open(f, encoding="utf-8"))["expect"]["periods"]
            first = [r for r in rows if r["kind"] == "REPAYMENT"][0]
            disb = [r for r in rows if r["kind"] == "DISBURSEMENT"][0]
            print("\nASSERTIONS on the regenerated %s:" % os.path.basename(f))
            print("  payable row 1 installment_number = %r  unrecorded_fields = %r"
                  % (first["installment_number"], first.get("unrecorded_fields")))
            print("  DISBURSEMENT  installment_number = %r  unrecorded_fields = %r"
                  % (disb["installment_number"], disb.get("unrecorded_fields")))
            ok = (first["installment_number"] == 0
                  and "installment_number" not in (first.get("unrecorded_fields") or [])
                  and disb["installment_number"] == 0
                  and "installment_number" in (disb.get("unrecorded_fields") or []))
            if not ok:
                raise SystemExit("ASSERTION FAILED: a legitimate 0 is not distinguished from absence")

            # ASSERTION 2 — and the PRE-FIX code does EXACTLY THE SAME THING. T87's F-1 required this:
            # the case is a regression control, and the honest way to say so is to PROVE the two
            # codebases agree, not to print a claim that they differ.
            basep = os.path.join(root, BASE_PROMOTER)
            if not os.path.isfile(basep):
                raise SystemExit("scratch/promote-BASE.py missing; the driver extracts it with "
                                 "`git show $(cat T82-guard-proofs/FORK-POINT-SHA):"
                                 ".softhouse/handoff/T74-promote-vectors.py` — a LITERAL sha, "
                                 "NEVER `merge-base main HEAD` or any other computed ref, which "
                                 "resolve to the FIXED code once this branch merges (T102)")
            out_base, mod_base = build_vectors(
                root, basep, mutate(json.load(open(ref, encoding="utf-8")), mode), tmp, "base")
            same = diff = 0
            for cid in GROUP_E:
                a = json.load(open(os.path.join(out, mod.FILENAMES[cid]), encoding="utf-8"))
                b = json.load(open(os.path.join(out_base, mod_base.FILENAMES[cid]), encoding="utf-8"))
                if a["expect"]["periods"] == b["expect"]["periods"]:
                    same += 1
                else:
                    diff += 1
            print("  expect.periods identical between this branch and the FORK POINT: %d, differing: %d"
                  % (same, diff))
            if diff or same != len(GROUP_E):
                raise SystemExit("ASSERTION FAILED: the regression control is not a regression "
                                 "control — the two codebases disagree")
            print("  -> CONFIRMED A REGRESSION CONTROL, NOT A GUARD PROOF. Both codebases emit the")
            print("     same cells, because the pre-fix code decided the VALUE with `or 0` (:255) and")
            print("     the WITHDRAWAL with a separate `is None` test (:260-261). NO discriminating power")
            print("     over the `or 0` defect, and it no longer claims any. See period-number-absent-payable.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
