#!/usr/bin/env python3
"""T262 -- can T259's sha-pinned acknowledgement be satisfied by a file that has CHANGED?

Run entirely inside a scratch repo so the real committed evidence is never touched
(T114/T176, and A2-17: T262 may not edit anything T259 touched).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(".softhouse/capture/t256-verdict-predicate").resolve()
RULE = SRC / "check_verdict_predicate_agreement.py"
REG = SRC / "boolean-key-register.json"
ACK = SRC / "acknowledged.json"
EVID_REL = ".softhouse/capture/t229-g8-site3/out/classify-t229.json"
EVID = Path(EVID_REL).resolve()
PROBE = "T259-VPA:"

root = Path(tempfile.mkdtemp(prefix="t262-pin-"))
(root / ".git").mkdir()                      # repo_root() only tests existence
tgt = root / EVID_REL
tgt.parent.mkdir(parents=True, exist_ok=True)


def run(ackpath):
    p = subprocess.run([sys.executable, str(RULE), str(tgt),
                        "--register", str(REG), "--acknowledgements", str(ackpath)],
                       capture_output=True, text=True, cwd=str(root))
    pl = None
    for ln in p.stdout.splitlines():
        if ln.startswith(PROBE):
            pl = ln
    return p.returncode, pl, p.stdout


print("scratch repo:", root)
print()
print("CASE 1 -- unmodified evidence at the pinned path. Expect GREEN 0, ack applies.")
shutil.copy(EVID, tgt)
rc, pl, out = run(ACK)
print("  rc =", rc)
print("  probe:", pl)
print("  'ACKNOWLEDGEMENT BLOCK VOID' printed:", "VOID" in out)
print("  DISAGREEMENT [ACKNOWLEDGED] count:", out.count("[ACKNOWLEDGED]"))

print()
print("CASE 2 -- WHITESPACE-ONLY mutation (one trailing newline). Expect the pin to VOID.")
tgt.write_bytes(EVID.read_bytes() + b"\n")
rc, pl, out = run(ACK)
print("  rc =", rc)
print("  probe:", pl)
print("  'ACKNOWLEDGEMENT BLOCK VOID' printed:", "VOID" in out)
print("  DISAGREEMENT [UNACKNOWLEDGED] count:", out.count("[UNACKNOWLEDGED]"))

print()
print("CASE 3 -- SEMANTIC mutation: flip the ONE true P2 to false on a row NOT in the ack list,")
print("          and flip its verdict to affirmative. Expect VOID + RED.")
doc = json.loads(EVID.read_text())
for r in doc["cells"]:
    if r.get("id") == "T229-R36p0-N1400-B150":
        r["P2_totalInterestEqualsNEplusB"] = False
tgt.write_text(json.dumps(doc, indent=1) + "\n")
rc, pl, out = run(ACK)
print("  rc =", rc)
print("  probe:", pl)
print("  'ACKNOWLEDGEMENT BLOCK VOID' printed:", "VOID" in out)

print()
print("CASE 4 -- THE ATTACK: mutate the evidence AND update the ack's sha256 to match.")
print("          Does the rule have any defence left once the pin is re-pointed?")
newsha = __import__("hashlib").sha256(tgt.read_bytes()).hexdigest()
ackdoc = json.loads(ACK.read_text())
ackdoc["acknowledgements"][0]["sha256"] = newsha
# and acknowledge the newly-false row too
ackdoc["acknowledgements"][0]["rows"].append({
    "id": "T229-R36p0-N1400-B150", "predicate": "P2_totalInterestEqualsNEplusB",
    "disposition": "FABRICATED BY T262", "reason": "attack test"})
ack2 = root / "ack-repinned.json"
ack2.write_text(json.dumps(ackdoc, indent=1))
rc, pl, out = run(ack2)
print("  rc =", rc)
print("  probe:", pl)
print("  'VOID' printed:", "VOID" in out)
print("  >>> The pin binds the ack to the bytes, but NOTHING binds the ack file itself.")
print("  >>> Re-pointing the pin is a one-line edit and the rule reports GREEN again.")
print("  >>> The pin's force therefore rests entirely on REVIEW of acknowledged.json's diff,")
print("  >>> which is the same discipline it was written to replace. Bounded, not absent:")
print("  >>> the disagreement is still PRINTED, and the ack diff is visible in review.")

print()
print("CASE 5 -- evidence moved to a DIFFERENT path (ack matches on `file` too).")
alt = root / ".softhouse/capture/t229-g8-site3/out/classify-t229-copy.json"
shutil.copy(EVID, alt)
p = subprocess.run([sys.executable, str(RULE), str(alt), "--register", str(REG),
                    "--acknowledgements", str(ACK)], capture_output=True, text=True, cwd=str(root))
pl = [l for l in p.stdout.splitlines() if l.startswith(PROBE)]
print("  rc =", p.returncode, " (fail-closed: ack does not apply at a new path)")
print("  probe:", pl[0] if pl else "ABSENT")
