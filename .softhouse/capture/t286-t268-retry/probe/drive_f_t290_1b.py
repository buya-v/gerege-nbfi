#!/usr/bin/env python3
"""T292 -- IS F-T290-1b STILL OPEN UNDER THE T292 RULE?  DRIVEN, NOT ASSUMED.

T290 found a fail-open that survives BOTH the live T259 rule and T286's rewrite: the CONSISTENT
TWO-FILE EDIT.  Retro-edit the evidence so the disagreement disappears, AND re-pin the
acknowledgement register to the new bytes with its rows removed.  Nothing goes VOID, `unacknowledged`
is 0, and the run is GREEN.  T290's conclusion: "Only a FLOOR on `disagreements` catches it", and
"T269 MUST NOT BE WIRED until F-T290-1b's floor exists".

T292's coverage inversion is about a DIFFERENT question (did the document grade anything), so there
is no reason to expect it to close this, and claiming it would be exactly the overstatement T291
rejected guard #10 for.  This file MEASURES the answer instead of predicting it, on a COPY -- the
committed evidence is never touched (T114/T176).

It also measures the ONE thing T292 does contribute here: `coverageDigest`.
"""
import hashlib
import json
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
REAL = ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json"


def run(target, reg, ack):
    r = subprocess.run([sys.executable, str(RULE), "--register", str(reg),
                        "--acknowledgements", str(ack), str(target)],
                       capture_output=True, text=True, timeout=60)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    return r.returncode, probe


def field(probe, name):
    if not probe:
        return None
    for t in probe.split():
        if t.startswith(name + "="):
            return t.split("=", 1)[1]
    return None


def main():
    tmp = Path(tempfile.mkdtemp(prefix=".t292-f290-", dir=str(CAP)))
    try:
        ackdoc = json.loads((T256 / "acknowledged.json").read_text(encoding="utf-8"))
        reg = T256 / "boolean-key-register.json"
        base_rc, base_p = run(REAL, reg, T256 / "acknowledged.json")
        print("T292 -- F-T290-1b DRIVEN AGAINST THE T292 RULE")
        print("=" * 96)
        print("  BASELINE committed evidence, committed register")
        print("     rc=%s disagreements=%s unacknowledged=%s voidAcks=%s coverageDigest=%s"
              % (base_rc, field(base_p, "disagreements"), field(base_p, "unacknowledged"),
                 field(base_p, "voidAcks"), field(base_p, "coverageDigest")))

        # ---- ARM 1: the INCONSISTENT edit -- evidence changed, register not re-pinned.
        doc = json.loads(REAL.read_text(encoding="utf-8"))
        for c in doc["cells"]:
            if c.get("P2_totalInterestEqualsNEplusB") is False and c.get("verdict") == "AS PREDICTED":
                c["verdict"] = "REFUTED"
        tampered = tmp / "classify-t229.json"
        tampered.write_text(json.dumps(doc, indent=1), encoding="utf-8")
        # keep the ORIGINAL relative path in the ack so the block still applies by name
        ack1 = tmp / "ack-not-repinned.json"
        a1 = json.loads(json.dumps(ackdoc))
        a1["acknowledgements"][0]["file"] = str(tampered.resolve().relative_to(ROOT))
        ack1.write_text(json.dumps(a1, indent=1), encoding="utf-8")
        rc1, p1 = run(tampered, reg, ack1)
        print("  ARM 1  evidence retro-edited, register NOT re-pinned  (the ordinary tamper)")
        print("     rc=%s state=%s voidAcks=%s   <- the sha pin fires"
              % (rc1, (p1 or " ?").split()[1] if p1 else "NO PROBE", field(p1, "voidAcks")))

        # ---- ARM 2: F-T290-1b, the CONSISTENT two-file edit.
        newsha = hashlib.sha256(tampered.read_bytes()).hexdigest()
        a2 = json.loads(json.dumps(ackdoc))
        a2["acknowledgements"][0]["file"] = str(tampered.resolve().relative_to(ROOT))
        a2["acknowledgements"][0]["sha256"] = newsha
        a2["acknowledgements"][0]["rows"] = []
        ack2 = tmp / "ack-repinned.json"
        ack2.write_text(json.dumps(a2, indent=1), encoding="utf-8")
        rc2, p2 = run(tampered, reg, ack2)
        print("  ARM 2  evidence retro-edited AND register re-pinned   (F-T290-1b)")
        print("     rc=%s state=%s disagreements=%s unacknowledged=%s voidAcks=%s "
              "coverageDigest=%s"
              % (rc2, (p2 or " ?").split()[1] if p2 else "NO PROBE",
                 field(p2, "disagreements"), field(p2, "unacknowledged"),
                 field(p2, "voidAcks"), field(p2, "coverageDigest")))
        open_here = (rc2 == 0)

        # ---- ARM 3: the same attack aimed at a PREDICATE instead of a verdict word.
        doc3 = json.loads(REAL.read_text(encoding="utf-8"))
        for c in doc3["cells"]:
            if c.get("P2_totalInterestEqualsNEplusB") is False:
                c["P2_totalInterestEqualsNEplusB"] = True
        t3 = tmp / "classify-t229-predicate-flipped.json"
        t3.write_text(json.dumps(doc3, indent=1), encoding="utf-8")
        a3 = json.loads(json.dumps(ackdoc))
        a3["acknowledgements"][0]["file"] = str(t3.resolve().relative_to(ROOT))
        a3["acknowledgements"][0]["sha256"] = hashlib.sha256(t3.read_bytes()).hexdigest()
        a3["acknowledgements"][0]["rows"] = []
        ack3 = tmp / "ack3.json"
        ack3.write_text(json.dumps(a3, indent=1), encoding="utf-8")
        rc3, p3 = run(t3, reg, ack3)
        print("  ARM 3  the same consistent edit aimed at the PREDICATE, not the verdict word")
        print("     rc=%s coverageDigest=%s   (baseline was %s)"
              % (rc3, field(p3, "coverageDigest"), field(base_p, "coverageDigest")))
        digest_moved = field(p3, "coverageDigest") != field(base_p, "coverageDigest")
        digest_blind = field(p2, "coverageDigest") == field(base_p, "coverageDigest")

        print()
        print("RESULT, STATED AS MEASURED AND NOT WIDER:")
        print("  F-T290-1b is %s under the T292 rule. rc=%s."
              % ("STILL OPEN" if open_here else "CLOSED", rc2))
        print("  It is a different defect from the one T292 closes: it does not manufacture")
        print("  coverage, it REMOVES a disagreement by consistently rewriting both files. T290's")
        print("  FLOOR on `disagreements` remains the correct closure and T292 does not replace it.")
        print("  T269 MUST NOT WIRE ANY R-VPA RULE, INCLUDING THIS ONE, UNTIL THAT FLOOR EXISTS.")
        print()
        print("  WHAT T292 DOES CONTRIBUTE: `coverageDigest` is a pinnable fingerprint of the")
        print("  GRADED FACTS, so half of the two-file edit becomes detectable by pinning one")
        print("  probe-line field -- no change to the contended rule and no new instrument:")
        print("     verdict-word half  (ARM 2): digest %s  -> %s"
              % ("UNCHANGED" if digest_blind else "moved",
                 "NOT caught by the digest; needs T290's floor" if digest_blind else "caught"))
        print("     predicate half     (ARM 3): digest %s  -> %s"
              % ("moved" if digest_moved else "UNCHANGED",
                 "CAUGHT by pinning coverageDigest" if digest_moved else "not caught"))
        ok = open_here and digest_moved and digest_blind and rc1 == 1
        print()
        print("EXIT %d   (0 means every arm behaved as this file claims, INCLUDING the arm that "
              "shows the hole is open)" % (0 if ok else 1))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
