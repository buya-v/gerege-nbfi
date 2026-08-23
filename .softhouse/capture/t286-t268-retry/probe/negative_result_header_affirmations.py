#!/usr/bin/env python3
"""T292 -- THE MEASURED NEGATIVE RESULT.

The brief allows either a fail-closed-by-construction formulation OR a measured argument that none
exists. The honest answer is BOTH, for two DIFFERENT questions, and this file measures the second.

  QUESTION 1  "did this document GRADE anything?"        -> fail-closed by construction. YES.
              Coverage is the WITNESS SET; container rewritings act trivially on it (proved in the
              rule's docstring, measured by probe/adversary_t292.py over ~1000 generated shapes).

  QUESTION 2  "is this affirmative word a HEADER standing over records it does not grade?"
              -- T286's guard #10, which T291 measured false as stated -> NO CONTAINER-BLIND RULE
              CAN ANSWER IT, and the proof is in this program's own committed evidence.

THE PROOF IS A DEMONSTRATION, NOT AN ARGUMENT.  Take the T292 rule and promote `headerAffirmations`
from a census counter to a refusal -- the strongest form of the guard T286 wanted -- then run it on
T291's X5 fixture AND on `classify-t229.json`. If it refuses X5 it must also refuse the committed
evidence, because THE TWO CONTAIN THE SAME SHAPE:

    X5's header          {"verdict": "AS PREDICTED"}                   <- no predicate boolean
    classify-t229 cells[0] {"id": "...B301", ..., "verdict": "AS PREDICTED"}  <- no predicate boolean

The P-keys are ABSENT BY DESIGN on the three RESCUED_BY_SITE3 rows (T259 established the
denominator is 6, not 9, for exactly this reason). So a rule that separates the two must consult
something OUTSIDE the document -- a declaration of which containers hold graded records. That is a
change to `boolean-key-register.json`'s contract, which is committed evidence outside T292's
`files_hint`; it is specified in the handoff and NOT done here.

Run it. Read the exit codes. Do not reason about them (P-83).
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parent
ROOT = CAP.parent.parent.parent
RULE = CAP / "check_verdict_predicate_agreement_t292.py"
T256 = CAP.parent / "t256-verdict-predicate"
REAL_229 = ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json"
X5 = ROOT / ".softhouse" / "reviews" / "t291-review-t286" / "probe" / "fixtures" / \
    "X5-affirmation-in-list-over-refuted-record.json"
X5B = ROOT / ".softhouse" / "reviews" / "t291-review-t286" / "probe" / "fixtures" / \
    "X5b-affirmation-as-mapping-key-over-refuted-record.json"

ANCHOR = ("    refused = bool(rep.unacknowledged or rep.unclassified_keys or "
          "rep.unclassified_verdicts\n                   or rep.void_acks or "
          "rep.mute_refutations or nil)")
GATED = ("    refused = bool(rep.unacknowledged or rep.unclassified_keys or "
         "rep.unclassified_verdicts\n                   or rep.void_acks or "
         "rep.mute_refutations or nil or rep.header_affirmations)")


def run(rule, target):
    r = subprocess.run([sys.executable, str(rule),
                        "--register", str(T256 / "boolean-key-register.json"),
                        "--acknowledgements", str(T256 / "acknowledged.json"), str(target)],
                       capture_output=True, text=True, timeout=60)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    return r.returncode, probe


def main():
    src = RULE.read_text(encoding="utf-8")
    if src.count(ANCHOR) != 1:
        raise SystemExit("ERROR: gate anchor not found exactly once; this probe measures nothing")
    tmp = Path(tempfile.mkdtemp(prefix=".t292-neg-", dir=str(CAP)))
    try:
        gated = tmp / "rule-with-header-affirmations-GATED.py"
        gated.write_text(src.replace(ANCHOR, GATED), encoding="utf-8")
        print("T292 NEGATIVE RESULT -- what gating `headerAffirmations` costs, MEASURED")
        print("=" * 96)
        print("ARM A: the shipped rule (headerAffirmations is CENSUS ONLY)")
        print("ARM B: the same rule with ONE token added to the gate expression -- "
              "`or rep.header_affirmations`")
        print()
        rows = [("T291 X5   (affirmation in a LIST over a refuted record)", X5),
                ("T291 X5b  (the same as a MAPPING KEY)", X5B),
                ("REAL      classify-t229.json  -- COMMITTED EVIDENCE", REAL_229)]
        results = {}
        print("  %-58s %-22s %-22s" % ("document", "ARM A (shipped)", "ARM B (gated)"))
        print("  " + "-" * 94)
        for label, path in rows:
            if not path.exists():
                print("  %-58s ABSENT -- NOT MEASURED" % label)
                results[label] = None
                continue
            a_rc, a_p = run(RULE, path)
            b_rc, b_p = run(gated, path)

            def st(rc, p):
                if p is None:
                    return "exit %s, NO PROBE" % rc
                return "exit %s %s" % (rc, p.split()[1])
            results[label] = (a_rc, b_rc)
            print("  %-58s %-22s %-22s" % (label, st(a_rc, a_p), st(b_rc, b_p)))
        print()
        _, real229 = [v for k, v in results.items() if "classify-t229" in k][0] or (None, None)
        _, x5 = [v for k, v in results.items() if "X5 " in k or "X5  " in k][0] or (None, None)
        print("READ THE TABLE, NOT THE PROSE:")
        print("  ARM B refuses X5 -- which is what T286's guard #10 CLAIMED to do and, as T291")
        print("  measured, did not. It buys that by ALSO refusing `classify-t229.json`, whose")
        print("  three RESCUED_BY_SITE3 rows carry `verdict: AS PREDICTED` and no P-key BY DESIGN.")
        print("  There is no container-blind predicate that separates them: they are the same")
        print("  shape. Guard #10's ambition is UNREACHABLE without an EXTERNAL declaration of")
        print("  which containers hold graded records.")
        print()
        ok = (real229 == 1 and x5 == 1)
        print("DEMONSTRATED: %s   (ARM B refuses X5 -> %s, and refuses committed evidence -> %s)"
              % ("YES" if ok else "NOT AS EXPECTED -- re-read the table", x5, real229))
        print("EXIT %d" % (0 if ok else 1))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
