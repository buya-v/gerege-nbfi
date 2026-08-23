#!/usr/bin/env python3
"""T290 -- prove that F-T290-2's disposition repair moves NO measured number.

It applies `PROPOSED-disposition-repair.json` to a COPY of T271's register (the committed one is
never touched), runs the R-VPA rule and T271's 12-leg battery against both, and requires every
probe line to be byte-identical. A repair to a `reason` string that quietly changed a count would
be worse than the wording it fixes.

EXIT 0 the repair is inert; 1 it is not; 2 error. Never conflated (P-80).
PROBE: `T290-REPAIR-INERT: <STATE> ...`
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T290-REPAIR-INERT:"
PROBE_LINE = re.compile(r"^(T259-VPA|T271-TARGETS|T271-REDGREEN):.*$", re.M)


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


ROOT = repo_root(HERE)
RULE = ROOT / ".softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py"
ACK = ROOT / ".softhouse/capture/t271-b1-t219/acknowledged-t219.json"
EV = ROOT / ".softhouse/capture/t219-g8-residual/out/classify-t219.json"
REPAIR = HERE / "PROPOSED-disposition-repair.json"


def probes(text):
    return [m.group(0).strip() for m in PROBE_LINE.finditer(text)]


def main() -> int:
    for need in (RULE, ACK, EV, REPAIR):
        if not need.exists():
            print("ERROR: missing input: " + str(need), file=sys.stderr)
            return 2
    rep = json.loads(REPAIR.read_text())
    doc = json.loads(ACK.read_text())
    blk = doc["acknowledgements"][0]
    by_key = {(r["id"], r["predicate"]): r for r in blk["rows"]}
    applied = 0
    for new in rep["replaceRows"]:
        row = by_key.get((new["id"], new["predicate"]))
        if row is None:
            print("ERROR: the repair names a row that is not in the register: %s / %s"
                  % (new["id"], new["predicate"]), file=sys.stderr)
            return 2
        row["disposition"] = new["disposition"]
        row["reason"] = new["reason"]
        applied += 1

    work = Path(tempfile.mkdtemp(prefix=".t290-repair-", dir=str(ROOT)))
    try:
        repaired = work / "acknowledged-t219-REPAIRED.json"
        repaired.write_text(json.dumps(doc, indent=2) + "\n")

        a = subprocess.run([sys.executable, str(RULE), "--acknowledgements", str(ACK), str(EV)],
                           capture_output=True, text=True, cwd=str(ROOT))
        b = subprocess.run([sys.executable, str(RULE), "--acknowledgements", str(repaired),
                            str(EV)], capture_output=True, text=True, cwd=str(ROOT))
        pa, pb = probes(a.stdout), probes(b.stdout)

        print("T290 -- is the F-T290-2 disposition repair inert?")
        print("=" * 78)
        print("  register (committed) : %s" % ACK.relative_to(ROOT))
        print("  register (repaired)  : a temporary copy; the committed one is NOT touched")
        print("  rows replaced        : %d" % applied)
        print("  rule exit  before/after : %d / %d" % (a.returncode, b.returncode))
        for ln in pa:
            print("    before: " + ln)
        for ln in pb:
            print("    after : " + ln)
        problems = []
        if a.returncode != b.returncode:
            problems.append("the rule's exit code moved")
        if pa != pb:
            problems.append("a probe line moved")
        if not pa:
            problems.append("NO PROBE LINE in the before run -- nothing was measured (P-84)")
        # the dispositions must actually have reached the output, or the test is vacuous
        if rep["replaceRows"][0]["disposition"] not in b.stdout:
            problems.append("the repaired disposition never appeared in the rule's output, so "
                            "this proof measured nothing")
        for p in problems:
            print("  REFUSED: " + p)
        if not problems:
            print("  identical. The repair changes what the rule PRINTS about each disagreement")
            print("  and no number it MEASURES.")
        state = "REFUSED" if problems else "GREEN"
        print("%s %s rowsReplaced=%d probeLinesBefore=%d probeLinesAfter=%d identical=%d"
              % (PROBE, state, applied, len(pa), len(pb), int(pa == pb)))
        return 1 if problems else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
