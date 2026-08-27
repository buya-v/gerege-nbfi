#!/usr/bin/env python3
"""T308 session-2 -- F-T290-1b re-derived FROM SCRATCH, not by re-running T292's driver.

T292's `drive_f_t290_1b.py` proves the hole is open by mutating the COMMITTED corpus
`classify-t229.json` and re-pinning `acknowledged.json`.  That inherits T292's framing:
it presents F-T290-1b as necessarily a TWO-FILE edit, because the corpus it attacks
happens to be pinned in the acknowledgement register.

This file builds its own minimal fixtures instead, and asks the sharper question:

  Q1  Is `disagreements` a term in the gate at all?           (read, then driven)
  Q2  Can a disagreement be erased with a ONE-FILE edit --
      no register, no acknowledgement, nothing re-pinned?     (T290 says two files)
  Q3  Does the erased document still buy full coverage,
      i.e. does the witness set survive the erasure?          (if yes, no guard sees it)
  Q4  CONTROL: does the honest fixture actually REFUSE?       (else the probe is vacuous)

Exit 0 means every arm behaved as this file claims, INCLUDING the arms showing the hole.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent          # repo root
CAP = ROOT / ".softhouse" / "capture" / "t286-t268-retry"
RULE = CAP / "check_verdict_predicate_agreement_t292.py"
T256 = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate"
REG = T256 / "boolean-key-register.json"
ACK = T256 / "acknowledged.json"


def run(target):
    r = subprocess.run([sys.executable, str(RULE), "--register", str(REG),
                        "--acknowledgements", str(ACK), str(target)],
                       capture_output=True, text=True, timeout=60)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    return r.returncode, probe, r.stdout, r.stderr


def f(probe, name):
    if not probe:
        return None
    for t in probe.split():
        if t.startswith(name + "="):
            return t.split("=", 1)[1]
    return None


def main():
    print("T308 -- F-T290-1b RE-DERIVED FROM SCRATCH (independent of T292's driver)")
    print("=" * 96)

    # ---- Q1: read the gate before driving it. -------------------------------------------
    src = RULE.read_text(encoding="utf-8").splitlines()
    gate = []
    for i, ln in enumerate(src, 1):
        if ln.strip().startswith("refused = bool("):
            gate = [(i, src[i - 1]), (i + 1, src[i])]
            break
    print("Q1  THE GATE, READ AT SOURCE (before any run):")
    for n, ln in gate:
        print("      %d: %s" % (n, ln.rstrip()))
    gate_txt = " ".join(l for _, l in gate)
    disagreements_in_gate = "rep.disagreements" in gate_txt
    print("      'rep.disagreements' appears in the gate disjunction: %s"
          % ("YES" if disagreements_in_gate else "NO  <- there is NO FLOOR on disagreements"))
    print()

    tmp = Path(tempfile.mkdtemp(prefix=".t308-f290-",
                                dir=str(ROOT / ".softhouse" / "reviews" / "T308")))
    try:
        # ---- Q4 CONTROL: an honest document carrying a real, unacknowledged disagreement.
        honest = {"cells": [{"P1_principalAmortizesToZero": False, "verdict": "AS PREDICTED"}]}
        ph = tmp / "honest.json"
        ph.write_text(json.dumps(honest, indent=1), encoding="utf-8")
        rc_h, p_h, _, _ = run(ph)
        print("Q4  CONTROL -- honest fixture, one false predicate under an affirmative verdict:")
        print("      rc=%s state=%s disagreements=%s unacknowledged=%s witness=%s"
              % (rc_h, (p_h or " ?").split()[1] if p_h else "NO PROBE",
                 f(p_h, "disagreements"), f(p_h, "unacknowledged"), f(p_h, "witness")))
        control_fires = (rc_h == 1 and f(p_h, "unacknowledged") == "1")
        print("      control %s" % ("FIRES -- the probe is not vacuous"
                                    if control_fires else "DID NOT FIRE -- probe is vacuous"))
        print()

        # ---- Q2/Q3: the ONE-FILE erasure. Same document, verdict word rewritten to agree.
        erased = {"cells": [{"P1_principalAmortizesToZero": False, "verdict": "REFUTED"}]}
        pe = tmp / "erased.json"
        pe.write_text(json.dumps(erased, indent=1), encoding="utf-8")
        rc_e, p_e, _, _ = run(pe)
        print("Q2  THE ERASURE -- ONE FILE EDITED, nothing re-pinned, no register touched:")
        print("      rc=%s state=%s disagreements=%s unacknowledged=%s voidAcks=%s witness=%s"
              % (rc_e, (p_e or " ?").split()[1] if p_e else "NO PROBE",
                 f(p_e, "disagreements"), f(p_e, "unacknowledged"),
                 f(p_e, "voidAcks"), f(p_e, "witness")))
        one_file_open = (rc_e == 0 and f(p_e, "disagreements") == "0")
        print("      one-file erasure lands GREEN: %s" % ("YES" if one_file_open else "no"))
        print()

        print("Q3  DID THE ERASURE COST ANY COVERAGE? (if not, no coverage guard can see it)")
        print("      honest  witness=%s coverageDigest=%s"
              % (f(p_h, "witness"), f(p_h, "coverageDigest")))
        print("      erased  witness=%s coverageDigest=%s"
              % (f(p_e, "witness"), f(p_e, "coverageDigest")))
        coverage_unchanged = (f(p_h, "witness") == f(p_e, "witness")
                              and f(p_h, "coverageDigest") == f(p_e, "coverageDigest"))
        print("      witness AND coverageDigest both unchanged: %s"
              % ("YES -- the erasure is INVISIBLE to every coverage quantity the rule prints"
                 if coverage_unchanged else "no"))
        print()

        print("RESULT, STATED AS MEASURED AND NOT WIDER:")
        print("  F-T290-1b is STILL OPEN under the T292 rule -- confirmed independently, and")
        print("  confirmed at SOURCE: `rep.disagreements` is not a term in the gate, so no")
        print("  document can be refused for having lost a disagreement.")
        print("  WIDER THAN T290 STATED: for a document NOT pinned in the acknowledgement")
        print("  register, the erasure needs ONE file edit, not two. T290's two-file framing is")
        print("  an artefact of attacking a PINNED corpus. The register is not a precondition of")
        print("  the attack; it is only a precondition of the attack ON PINNED EVIDENCE.")
        print("  The verdict-word rewrite is invisible to `witness` AND to `coverageDigest`,")
        print("  so T292's contribution (pin the digest) does not reach this half either --")
        print("  which is exactly what T292's own ARM 2 reports.")
        print()
        print("  THE FLOOR T290 REQUIRES, restated from this measurement: the wiring must pin an")
        print("  EXPECTED MINIMUM `disagreements` (and `acknowledged`) per graded corpus, so that")
        print("  a corpus known to carry N acknowledged disagreements REFUSES when it reports")
        print("  fewer. Nothing inside a rule reading only (document, register) can supply N.")
        ok = (disagreements_in_gate is False and control_fires
              and one_file_open and coverage_unchanged)
        print()
        print("EXIT %d   (0 means every arm behaved as claimed, INCLUDING the arms showing the "
              "hole)" % (0 if ok else 1))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
