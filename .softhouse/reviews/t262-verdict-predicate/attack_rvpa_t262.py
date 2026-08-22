#!/usr/bin/env python3
"""T262 -- ADVERSARIAL attack on T259's R-VPA selector (P-76).

Not a re-run of T259's own battery. Every shape below is INVENTED BY THE REVIEWER and is a
disagreement a careful author could plausibly emit. The question each asks is the same:
does R-VPA notice, or does it print GREEN over a live disagreement?

Ground truth for every fixture: it contains AT LEAST ONE affirmative verdict sitting over a
predicate the row itself recorded as not-holding. The correct answer is therefore ALWAYS
"REFUSED, exit 1". Anything else is a MISS.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RULE = Path(".softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py").resolve()
REG = Path(".softhouse/capture/t256-verdict-predicate/boolean-key-register.json").resolve()
ACK = Path(".softhouse/capture/t256-verdict-predicate/acknowledged.json").resolve()
PROBE = "T259-VPA:"

TMP = Path(tempfile.mkdtemp(prefix="t262-attack-"))

# ---------------------------------------------------------------- fixtures
FIXTURES = {}

# A1 -- the row is one level deeper than walk_rows descends.
FIXTURES["A1-nested-one-level-deeper"] = {
    "results": {"cells": [
        {"id": "A1-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": False}]}}

# A2 -- the document is a top-level JSON ARRAY of rows (prediction.json's own shape).
FIXTURES["A2-toplevel-array"] = [
    {"id": "A2-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": False}]

# A3 -- the verdict is an ENUM/int, not a string.
FIXTURES["A3-verdict-as-int-enum"] = {"cells": [
    {"id": "A3-1", "verdict": 0, "verdictWord": "AS PREDICTED",
     "P2_totalInterestEqualsNEplusB": False}]}

# A3b -- the verdict is an OBJECT carrying the affirmative word.
FIXTURES["A3b-verdict-as-object"] = {"cells": [
    {"id": "A3b-1", "verdict": {"word": "AS PREDICTED", "code": 0},
     "P2_totalInterestEqualsNEplusB": False}]}

# A4 -- the verdict key is named something a human reads as a verdict but the rule does not.
FIXTURES["A4-verdict-key-named-result"] = {"cells": [
    {"id": "A4-1", "result": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": False}]}
FIXTURES["A4b-verdict-key-named-conclusion"] = {"cells": [
    {"id": "A4b-1", "conclusion": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": False}]}

# A5 -- the predicate is null (measured, did not hold, recorded as absence of a hold).
FIXTURES["A5-predicate-null"] = {"cells": [
    {"id": "A5-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": None}]}

# A6 -- the boolean is stored as the STRING "false".
FIXTURES["A6-predicate-string-false"] = {"cells": [
    {"id": "A6-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": "false"}]}

# A7 -- the predicate is 0 (JSON number) rather than false.
FIXTURES["A7-predicate-zero"] = {"cells": [
    {"id": "A7-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": 0}]}

# A8 -- the false predicate lives in a nested list INSIDE the row.
FIXTURES["A8-predicate-in-nested-list"] = {"cells": [
    {"id": "A8-1", "verdict": "AS PREDICTED",
     "conjuncts": [{"P2_totalInterestEqualsNEplusB": False}]}]}

# CONTROL -- exactly the shape T259 designed for. MUST be caught, or the harness is broken.
FIXTURES["C0-control-flat-shape"] = {"cells": [
    {"id": "C0-1", "verdict": "AS PREDICTED", "P2_totalInterestEqualsNEplusB": False}]}


def run(args, cwd=None):
    p = subprocess.run([sys.executable, str(RULE)] + args, capture_output=True, text=True,
                       cwd=cwd or os.getcwd())
    return p.returncode, p.stdout, p.stderr


def probe_line(out):
    """P-83: PRESENCE first, then value."""
    for ln in out.splitlines():
        if ln.startswith(PROBE):
            return ln
    return None


print("R-VPA under review:", RULE)
print("scratch:", TMP)
print()
print("PART A -- invented adversarial shapes. Ground truth for all: REFUSED (exit 1).")
print("=" * 100)
hdr = "{:36} {:>4} {:>8} {:>8} {:>7} {:>8}  {}"
print(hdr.format("fixture", "rc", "probe", "state", "rows", "disagr", "OUTCOME"))
misses = []
for name, doc in FIXTURES.items():
    f = TMP / (name + ".json")
    f.write_text(json.dumps(doc, indent=1) + "\n")
    rc, out, err = run([str(f), "--register", str(REG), "--acknowledgements", str(ACK)])
    pl = probe_line(out)
    present = pl is not None
    state = pl.split()[1] if present else "-"
    def field(k):
        if not present:
            return "-"
        for tok in pl.split():
            if tok.startswith(k + "="):
                return tok.split("=", 1)[1]
        return "?"
    caught = (rc == 1)
    verdict = "CAUGHT" if caught else ("MISS -- GREEN over a live disagreement" if rc == 0
                                       else "ERROR rc=%d" % rc)
    if not caught:
        misses.append((name, rc, state))
    print(hdr.format(name, rc, "PRESENT" if present else "ABSENT", state,
                     field("rows"), field("disagreements"), verdict))

print()
print("PART B -- the batching fail-open: a NIL-COVERAGE file alongside a populated one")
print("=" * 100)
empty = TMP / "B1-empty.json"
empty.write_text(json.dumps({"cells": []}, indent=1) + "\n")
good = TMP / "B1-populated-clean.json"
good.write_text(json.dumps({"cells": [{"id": "B1-ok", "verdict": "REFUTED",
                                       "P2_x": False}]}, indent=1) + "\n")
rc, out, err = run([str(empty), "--register", str(REG), "--acknowledgements", str(ACK)])
pl = probe_line(out)
print("  empty file ALONE                  : rc={} probe={} state={}".format(
    rc, "PRESENT" if pl else "ABSENT", pl.split()[1] if pl else "-"))
rc2, out2, err2 = run([str(empty), str(good), "--register", str(REG),
                       "--acknowledgements", str(ACK)])
pl2 = probe_line(out2)
printed_nil_refusal = "NIL COVERAGE" in out2
print("  empty file BATCHED with a populated one:")
print("    rc                              :", rc2)
print("    body printed 'REFUSED  NIL COVERAGE' :", printed_nil_refusal)
print("    probe line                      :", pl2)
if printed_nil_refusal and rc2 == 0:
    print("    >>> FAIL-OPEN: the body prints REFUSED and the exit code and probe say GREEN.")
    misses.append(("B1-nil-coverage-batched", rc2, "GREEN"))

print()
print("PART C -- exit-code classification (P-80: 1 = measured negative, >1 = ERROR, never mixed)")
print("=" * 100)
rc, out, err = run([str(TMP / "does-not-exist.json"), "--register", str(REG),
                    "--acknowledgements", str(ACK)])
print("  E1 missing target        : rc={} probeAbsent={} stderr={!r}".format(
    rc, probe_line(out) is None, err.strip()[:70]))
bad = TMP / "unreadable-register.json"
bad.write_text("{ this is not json\n")
rc, out, err = run([str(TMP / "C0-control-flat-shape.json"), "--register", str(bad),
                    "--acknowledgements", str(ACK)])
print("  E2 unreadable register   : rc={} probeAbsent={} stderr={!r}".format(
    rc, probe_line(out) is None, err.strip()[:70]))
# E3 -- a register whose autoPredicatePattern differs: hits raise SystemExit(str)
bad2 = TMP / "wrong-pattern-register.json"
reg = json.loads(REG.read_text())
reg["autoPredicatePattern"] = "^Q[0-9]+_"
bad2.write_text(json.dumps(reg, indent=1))
rc, out, err = run([str(TMP / "C0-control-flat-shape.json"), "--register", str(bad2),
                    "--acknowledgements", str(ACK)])
print("  E3 wrong autoPredicatePattern (an ERROR by the module's own words):")
print("     rc={}  probeAbsent={}  stderr={!r}".format(rc, probe_line(out) is None,
                                                      err.strip()[:80]))
if rc == 1:
    print("     >>> CONFLATION: an ERROR exits 1, the code reserved for a REAL measured negative.")
# E4 -- no .git ancestor
iso = Path(tempfile.mkdtemp(prefix="t262-nogit-"))
shutil.copy(TMP / "C0-control-flat-shape.json", iso / "c.json")
rulecopy = iso / "rule.py"
shutil.copy(RULE, rulecopy)
p = subprocess.run([sys.executable, str(rulecopy), str(iso / "c.json"),
                    "--register", str(REG), "--acknowledgements", str(ACK)],
                   capture_output=True, text=True, cwd=str(iso))
print("  E4 rule run with NO .git ancestor (repo_root raises SystemExit(str)):")
print("     rc={}  probeAbsent={}  stderr={!r}".format(
    p.returncode, probe_line(p.stdout) is None, p.stderr.strip()[:80]))
if p.returncode == 1:
    print("     >>> CONFLATION: an ERROR exits 1, same code as a measured refusal.")

print()
print("PART D -- does R-VPA, AS WIRED, ever open t219? (default target when run.sh calls it)")
print("=" * 100)
rc, out, err = run([], cwd=str(RULE.parent))
files_line = [ln for ln in out.splitlines() if ln.startswith("FILE ")]
print("  files opened with no args:", files_line)
print("  t219 mentioned anywhere in output:", "t219" in out)

print()
print("=" * 100)
print("MISSES ({}):".format(len(misses)))
for n, rc, st in misses:
    print("  - {:38} rc={} state={}".format(n, rc, st))
print("TOTAL SHAPES TRIED: {} (part A) + 1 (part B batching)".format(len(FIXTURES)))
sys.exit(0)
