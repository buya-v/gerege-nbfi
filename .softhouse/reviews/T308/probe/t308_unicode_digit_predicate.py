#!/usr/bin/env python3
"""T308 -- THE AUTO-CLASSIFIER IS WIDER THAN THE PATTERN THE RULE VERIFIES.

`load_registers` refuses to run unless the register declares

    "autoPredicatePattern": "^P[0-9]+_"

-- `[0-9]` is ASCII-only -- and then `key_class` implements it as

    head = key.split("_", 1)[0]
    if len(head) > 1 and head[1:].isdigit():  -> PREDICATE

`str.isdigit()` is TRUE for Unicode digits that `[0-9]` does not match (superscripts, Arabic-Indic
digits, and others).  So the IMPLEMENTATION admits keys the DECLARED pattern excludes.

WHY IT MATTERS.  G2 is the guard T259 exists for: "Everything else is UNCLASSIFIED until written
down here, and UNCLASSIFIED is a REFUSAL, not a pass."  A boolean key that is not in the register
and does not match the declared pattern must REFUSE.  A homoglyph key silently becomes a PREDICATE
witness instead -- G2 does not fire, and the document buys coverage from a key no human reading
`boolean-key-register.json` would recognise as classified.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent
CAP = ROOT / ".softhouse" / "capture" / "t286-t268-retry"
RULE = CAP / "check_verdict_predicate_agreement_t292.py"
T256 = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate"

CASES = {
    "ascii P2_x (the declared pattern)":
        {"cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]},
    "SUPERSCRIPT P²_x":
        {"cells": [{"id": "c1", "P²_x": True, "verdict": "AS PREDICTED"}]},
    "ARABIC-INDIC P٢_x":
        {"cells": [{"id": "c1", "P٢_x": True, "verdict": "AS PREDICTED"}]},
    "plainly unregistered key zz_x (control)":
        {"cells": [{"id": "c1", "zz_x": True, "verdict": "AS PREDICTED"}]},
    "SUPERSCRIPT P²_x = FALSE under an affirmative verdict":
        {"cells": [{"id": "c1", "P²_x": False, "verdict": "AS PREDICTED"}]},
}


def run(doc, tmp, name):
    p = tmp / (name + ".json")
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, str(RULE),
                        "--register", str(T256 / "boolean-key-register.json"),
                        "--acknowledgements", str(T256 / "acknowledged.json"), str(p)],
                       capture_output=True, text=True, timeout=60)
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith("T259-VPA:"):
            probe = ln
    return r.returncode, probe


def field(probe, name):
    if not probe:
        return None
    for tok in probe.split():
        if tok.startswith(name + "="):
            return tok.split("=", 1)[1]
    return None


def main():
    import re
    print("T308 -- UNICODE DIGITS PASS `isdigit()` AND FAIL `^P[0-9]+_`")
    print("=" * 96)
    reg = json.loads((T256 / "boolean-key-register.json").read_text(encoding="utf-8"))
    pat = reg["autoPredicatePattern"]
    print("  register declares autoPredicatePattern = %r" % pat)
    for k in ("P2_x", "P²_x", "P٢_x"):
        head = k.split("_", 1)[0]
        print("    %-8s  re.match(%s) = %-5s   head[1:].isdigit() = %s"
              % (k, pat, bool(re.match(pat, k)), head[1:].isdigit()))
    print()
    tmp = Path(tempfile.mkdtemp(prefix=".t308-uni-", dir=str(CAP)))
    bad = 0
    try:
        print("  %-52s %-4s %-8s %-9s %s" % ("document", "rc", "state", "witness",
                                             "unclassifiedKeys"))
        print("  " + "-" * 92)
        for label, doc in CASES.items():
            rc, probe = run(doc, tmp, label.replace(" ", "_").replace("(", "").replace(")", ""))
            print("  %-52s %-4s %-8s %-9s %s"
                  % (label, rc, (probe.split()[1] if probe else "-"),
                     field(probe, "witness"), field(probe, "unclassifiedKeys")))
        print()
        print("READ THE CONTROL ROW FIRST: `zz_x` must REFUSE with unclassifiedKeys=1. If it does")
        print("  not, this probe is measuring nothing and the rows above mean nothing.")
        print()
        print("THE FINDING: a Unicode-digit key is admitted as an AUTO PREDICATE even though the")
        print("  register's own declared pattern `^P[0-9]+_` does not match it. The declared")
        print("  contract and the implemented contract are different sets. Direction: the")
        print("  implementation is WIDER, so G2 -- the guard T259 exists for -- does not fire on a")
        print("  key nobody classified, and the document buys coverage from it.")
        print()
        print("  Severity is LOW because buying coverage still requires ASSERTING A BOOLEAN FACT,")
        print("  which is the forgery floor T292 declares and prints. It is a finding because the")
        print("  RULE VERIFIES THE PATTERN STRING AT STARTUP (`load_registers` refuses an")
        print("  unexpected `autoPredicatePattern`) and then does not implement it.")
        print()
        print("  FIX, mechanical: replace `head[1:].isdigit()` with")
        print("      re.match(reg['autoPredicatePattern'], key)")
        print("  so the one declared pattern is the one enforced.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
