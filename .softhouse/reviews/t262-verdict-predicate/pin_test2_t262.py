#!/usr/bin/env python3
"""T262 -- pin test, CORRECTED setup.

First attempt (pin_test_t262.py) was INVALID and is kept for the record: `repo_root()` walks up
from the RULE's own __file__, not from the target, so with the rule left in the real repo the
scratch target's `rel` became an absolute path, no acknowledgement ever matched, and CASE 1
refused for the wrong reason. Here the whole instrument directory is copied INTO the scratch repo
so `rel` resolves the way it does in production.

Nothing under the real .softhouse/capture/t229-g8-site3/ is written at any point.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_INSTR = Path(".softhouse/capture/t256-verdict-predicate").resolve()
EVID_REL = ".softhouse/capture/t229-g8-site3/out/classify-t229.json"
EVID = Path(EVID_REL).resolve()
PROBE = "T259-VPA:"

root = Path(tempfile.mkdtemp(prefix="t262-pin2-"))
(root / ".git").mkdir()
instr = root / ".softhouse/capture/t256-verdict-predicate"
instr.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(REAL_INSTR, instr)
RULE = instr / "check_verdict_predicate_agreement.py"
REG = instr / "boolean-key-register.json"
ACK = instr / "acknowledged.json"
tgt = root / EVID_REL
tgt.parent.mkdir(parents=True, exist_ok=True)


def run(ackpath=None):
    p = subprocess.run([sys.executable, str(RULE), str(tgt), "--register", str(REG),
                        "--acknowledgements", str(ackpath or ACK)],
                       capture_output=True, text=True, cwd=str(root))
    pl = next((l for l in p.stdout.splitlines() if l.startswith(PROBE)), None)
    return p.returncode, pl, p.stdout


def show(label, rc, pl, out):
    print("  rc = {}   VOID printed = {}   [ACK]={}  [UNACK]={}".format(
        rc, "VOID" in out, out.count("[ACKNOWLEDGED]"), out.count("[UNACKNOWLEDGED]")))
    print("  probe:", pl)


print("scratch repo:", root)
print()
print("CASE 1 -- unmodified evidence at the pinned path. Expect GREEN 0, 3 ACKNOWLEDGED.")
shutil.copy(EVID, tgt)
show("c1", *run())

print()
print("CASE 2 -- WHITESPACE-ONLY mutation (one appended newline). Expect VOID + RED 1.")
tgt.write_bytes(EVID.read_bytes() + b"\n")
show("c2", *run())

print()
print("CASE 3 -- SEMANTIC mutation on a row NOT in the ack list (flip the one true P2).")
doc = json.loads(EVID.read_text())
for r in doc["cells"]:
    if r.get("id") == "T229-R36p0-N1400-B150":
        r["P2_totalInterestEqualsNEplusB"] = False
tgt.write_text(json.dumps(doc, indent=1) + "\n")
show("c3", *run())

print()
print("CASE 4 -- THE ATTACK: mutate the evidence AND re-point the ack sha256 to the new bytes,")
print("          adding an acknowledgement for the row just falsified.")
newsha = hashlib.sha256(tgt.read_bytes()).hexdigest()
ackdoc = json.loads(ACK.read_text())
ackdoc["acknowledgements"][0]["sha256"] = newsha
ackdoc["acknowledgements"][0]["rows"].append({
    "id": "T229-R36p0-N1400-B150", "predicate": "P2_totalInterestEqualsNEplusB",
    "disposition": "FABRICATED BY T262", "reason": "attack test"})
ack2 = instr / "ack-repinned.json"
ack2.write_text(json.dumps(ackdoc, indent=1))
show("c4", *run(ack2))
print("  >>> If rc is 0 here, the pin binds the ack to the bytes but NOTHING binds the ack file")
print("  >>> itself: re-pointing it is a one-line edit. Force rests on REVIEWING the ack diff.")

print()
print("CASE 5 -- restore the true bytes but keep the re-pointed (now stale) ack. Expect VOID.")
shutil.copy(EVID, tgt)
show("c5", *run(ack2))
