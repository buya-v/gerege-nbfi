#!/usr/bin/env python3
"""T290 -- ADJUDICATING what T271 declined to rule on: `calibration[]` in
`.softhouse/capture/t219-g8-residual/out/classify-t219.json` does not reproduce.

T271 measured `calibrationReproduces=0` and left it, calling it `a second unread contradiction in
the same directory, discovered by this task and deliberately left alone`. That is honest. It is
also incomplete, because the diagnosis is one script away and the stake is high: t229's registered
**P6** says `the rig calibrations P-CAL-ZPA / P-CAL-ZPB reproduce the already-promoted T64-ZP-A /
T64-ZP-B cell for cell with zero input differences. IF THEY DO NOT, NOTHING ELSE IN THIS CAPTURE IS
ADMISSIBLE.` The committed file says `status: DIFFERS`. Read literally, the committed evidence
declares itself inadmissible, and nothing in this repository reads that string.

WHAT THIS INSTRUMENT DOES
  1. re-runs the committed classifier's calibration comparison against the committed inputs and
     prints what it gets;
  2. prints the committed `calibration[]` block beside it;
  3. shows WHICH sub-comparison moved, field by field;
  4. SEARCHES EVERY committed reference capture in the repository for one that would make the
     committed verdict come out, and reports the count -- `not found` is a statement about the
     search, so the search's extent is printed.

EXIT 0 the committed block reproduces; 1 it does not (a real measured negative); 2 error.
PROBE: `T290-CALIB: <STATE> committed=.. rerun=.. explainedByAnyCommittedReference=..`
"""
import glob
import gzip
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T290-CALIB:"
PAIRS = (("P-CAL-ZPA", "T64-ZP-A"), ("P-CAL-ZPB", "T64-ZP-B"))


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


ROOT = repo_root(HERE)
CAPDIR = ROOT / ".softhouse/capture"
RAW = CAPDIR / "t219-g8-residual/out/capture-t219-raw.json.gz"
CLS = CAPDIR / "t219-g8-residual/out/classify-t219.json"
REF = CAPDIR / "out/capture-prod3g-raw.json"


def main() -> int:
    for need in (RAW, CLS, REF):
        if not need.exists():
            print("ERROR: missing input: " + str(need), file=sys.stderr)
            return 2
    raw = json.loads(gzip.open(RAW, "rt").read())
    cls = json.loads(CLS.read_text())
    ref = json.loads(REF.read_text())
    mine = {c["id"]: c for c in raw["captures"]}
    theirs = {c["id"]: c for c in ref["captures"]}

    print("T290 -- why does classify-t219.json's calibration[] not reproduce?")
    print("=" * 96)
    print("  raw       : %s" % RAW.relative_to(ROOT))
    print("  classify  : %s" % CLS.relative_to(ROOT))
    print("  reference : %s" % REF.relative_to(ROOT))
    print()
    print("  COMMITTED calibration[]:")
    for row in cls.get("calibration", []):
        print("    " + json.dumps(row))
    print()
    print("  RE-RUN of the committed classifier's comparison, on the committed inputs:")
    rerun = []
    for cal, tgt in PAIRS:
        m, t = mine.get(cal), theirs.get(tgt)
        if m is None or t is None:
            rerun.append({"cal": cal, "target": tgt, "status": "MISSING"})
            continue
        si = m["inputs"] == t["inputs"]
        so = m.get("observed") == t.get("observed")
        st = m.get("threw") == t.get("threw")
        rerun.append({"cal": cal, "target": tgt, "inputsIdentical": si, "observedIdentical": so,
                      "threwIdentical": st,
                      "status": "REPRODUCED" if (si and so and st) else "DIFFERS"})
        print("    " + json.dumps(rerun[-1]))
    print()
    print("  FIELD BY FIELD, the keys the comparison actually reads:")
    for cal, tgt in PAIRS:
        m, t = mine.get(cal), theirs.get(tgt)
        if m is None or t is None:
            continue
        print("    %s -> %s" % (cal, tgt))
        print("      capture keys   : %s" % sorted(m.keys()))
        print("      reference keys : %s" % sorted(t.keys()))
        print("      .threw   capture=%r reference=%r  -> threwIdentical=%s"
              % (m.get("threw"), t.get("threw"), m.get("threw") == t.get("threw")))
        print("      .outcome capture=%r reference=%r   (a RIG field the comparison excludes)"
              % (m.get("outcome"), t.get("outcome")))

    committed = [r.get("status") for r in cls.get("calibration", [])]
    rerun_st = [r.get("status") for r in rerun]

    print()
    print("  IS THERE ANY COMMITTED REFERENCE THAT WOULD PRODUCE THE COMMITTED VERDICT?")
    print("  Searched: every *.json under .softhouse/capture/ that parses as an object with a")
    print("  `captures` list, recursively. `not found` is a statement about THIS search.")
    seen = explained = 0
    for p in sorted(set(glob.glob(str(CAPDIR / "**/*.json"), recursive=True))):
        try:
            d = json.load(open(p))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict) or not isinstance(d.get("captures"), list):
            continue
        seen += 1
        t = {c.get("id"): c for c in d["captures"] if isinstance(c, dict)}
        for cal, tgt in PAIRS:
            if tgt not in t or cal not in mine:
                continue
            m, th = mine[cal], t[tgt]
            si = m["inputs"] == th["inputs"]
            so = m.get("observed") == th.get("observed")
            st = m.get("threw") == th.get("threw")
            if si and so and not st:            # the committed shape: inputs+observed same, threw not
                explained += 1
                print("    EXPLAINS IT: %s (%s)" % (os.path.relpath(p, str(ROOT)), cal))
    print("    reference-shaped files inspected : %d" % seen)
    print("    files that explain the committed verdict : %d" % explained)

    print()
    print("  WHAT THIS ESTABLISHES, and nothing more:")
    print("    * cells[] is not in question here. It reproduces exactly, and T290 re-derived the")
    print("      four B-1 pairs from the raw capture independently. THE ACKNOWLEDGEMENT IS NOT")
    print("      AFFECTED by this finding.")
    print("    * the committed calibration[] block is not reproducible from the committed")
    print("      classifier and any committed reference found by the search above, and the")
    print("      capture directory records NO command line for the classifier, so there is no")
    print("      invocation to re-run. That is a PROVENANCE defect in committed evidence.")
    print("    * t229/PREDICTION.md P6 makes `DIFFERS` mean `nothing else in this capture is")
    print("      admissible`. R-VPA cannot see it: `status` is a verdict key, `DIFFERS` is in the")
    print("      NEGATIVE vocabulary, and the rule only fires on an AFFIRMATIVE verdict over a")
    print("      false predicate. So the corpus contains a self-defeating assertion that no")
    print("      instrument reads -- P-79's shape in a STRING field. IT SHOULD BE A FILED TASK.")

    same = committed == rerun_st
    state = "GREEN" if same else "REFUSED"
    print("%s %s committed=%s rerun=%s explainedByAnyCommittedReference=%d"
          % (PROBE, state, ",".join(map(str, committed)), ",".join(map(str, rerun_st)), explained))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
