#!/usr/bin/env python3
"""T262 -- the COMPOUND attack. A1/A2 were caught only by NIL COVERAGE, which is a per-file
condition the rule evaluates GLOBALLY (`nil = 1 if rep.rows == 0`). Batch a blind-shaped file
with any populated file and the only thing that caught it disappears.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RULE = Path(".softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py").resolve()
REG = Path(".softhouse/capture/t256-verdict-predicate/boolean-key-register.json").resolve()
ACK = Path(".softhouse/capture/t256-verdict-predicate/acknowledged.json").resolve()
REAL = Path(".softhouse/capture/t229-g8-site3/out/classify-t229.json").resolve()
TMP = Path(tempfile.mkdtemp(prefix="t262-compound-"))
PROBE = "T259-VPA:"


def run(args):
    return subprocess.run([sys.executable, str(RULE)] + args, capture_output=True, text=True)


def probe(out):
    for ln in out.splitlines():
        if ln.startswith(PROBE):
            return ln
    return None


cases = {
    "A1-nested-one-level-deeper": {"results": {"cells": [
        {"id": "A1-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": False}]}},
    "A2-toplevel-array": [
        {"id": "A2-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": False}],
    "A3c-verdict-as-int-only": {"cells": [
        {"id": "A3c-1", "verdict": 0, "P2_totalInterestEqualsNEplusB": False}]},
}

print("COMPOUND: <blind fixture> batched with the REAL committed classify-t229.json")
print("Ground truth: every fixture carries an affirmative verdict over a false predicate.")
print("=" * 96)
print("{:34} {:>6} {:>8} {:>9} {:>7} {:>8}  {}".format(
    "fixture (batched with real file)", "rc", "probe", "state", "rows", "disagr", "OUTCOME"))
for name, doc in cases.items():
    f = TMP / (name + ".json")
    f.write_text(json.dumps(doc, indent=1) + "\n")
    # ALONE
    p1 = run([str(f), "--register", str(REG), "--acknowledgements", str(ACK)])
    # BATCHED with the real evidence
    p2 = run([str(f), str(REAL), "--register", str(REG), "--acknowledgements", str(ACK)])
    pl = probe(p2.stdout)
    st = pl.split()[1] if pl else "-"
    dis = "?"
    if pl:
        for t in pl.split():
            if t.startswith("disagreements="):
                dis = t.split("=")[1]
    rows = "?"
    if pl:
        for t in pl.split():
            if t.startswith("rows="):
                rows = t.split("=")[1]
    outcome = "CAUGHT" if p2.returncode == 1 else "MISS"
    # the real file's own 3 disagreements are all ACKNOWLEDGED, so they do not refuse
    print("{:34} {:>6} {:>8} {:>9} {:>7} {:>8}  {}   (alone: rc={})".format(
        name, p2.returncode, "PRESENT" if pl else "ABSENT", st, rows, dis, outcome, p1.returncode))

print()
print("Reading: any fixture that flips from rc=1 ALONE to rc=0 BATCHED was being caught ONLY by")
print("the global nil-coverage test, which one populated file in the same invocation switches off.")
sys.exit(0)
