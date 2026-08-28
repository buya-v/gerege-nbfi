#!/usr/bin/env python3
"""T397 -- A17, the attack F-T387-2 is ABOUT, driven end to end after the fix.

T387's A17 replaced both request legs' amount_major_text with "100.12" -- a
PREFIX of the captured "100.125" -- and reported that verbatimInCapture DID NOT
COMPLAIN, leaving the class to save itself downstream (the port accepts, the
comparator FAILs the vector, exit 1).

After T397 the vector must be REFUSED ADMISSION instead, and the run must say
which byte rule refused it. Recorded here as the before/after of the finding.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OUT = os.path.join(ROOT, ".softhouse", "capture", "t397-t387-conditions", "out", "attacks")
VEC = os.path.join(ROOT, ".softhouse", "vectors", "ledger",
                   "LDG-DIV-01-oracle-accepts-sub-minor-unit-residue.json")
BIN = sys.argv[1] if len(sys.argv) > 1 else "/tmp/t397-conf"

os.makedirs(OUT, exist_ok=True)
subprocess.check_call(["git", "checkout", "--", ".softhouse/vectors/"], cwd=ROOT)

with open(VEC) as f:
    d = json.load(f)
for leg in d["request"]["legs"]:
    leg["amount_major_text"] = "100.12"
with open(VEC, "w") as f:
    f.write(json.dumps(d, indent=2) + "\n")

proc = subprocess.run([BIN, "-oracle-probe", "up"], cwd=ROOT, capture_output=True, text=True)
log = proc.stdout + proc.stderr
with open(os.path.join(OUT, "A17-request-prefix-substring.log"), "w") as f:
    f.write(log)
    f.write("\nexit=%d\n" % proc.returncode)
subprocess.check_call(["git", "checkout", "--", ".softhouse/vectors/"], cwd=ROOT)

print("exit =", proc.returncode)
for line in log.splitlines():
    if ("ONLY GLUED TO A LONGER NUMBER" in line or "INADMISSIBLE" in line
            or "ledger inadmissible" in line or "LDG-DIV-01" in line
            or "ledger parity " in line):
        print("   ", line.strip()[:170])

ok = proc.returncode != 0 and "ONLY GLUED TO A LONGER NUMBER" in log
print("A17 CLOSED AT ADMISSION:", ok)
sys.exit(0 if ok else 1)
