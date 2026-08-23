#!/usr/bin/env python3
"""T308 -- DID T292 BREAK THE STREAK, OR DEFER THE TRADE?  MEASURE BOTH AXES ON FOUR ARMS.

The lineage's signature failure: every fix wins on one axis and silently loses on the other.
So both axes are measured on the SAME populations, for FOUR arms, from PINNED blobs:

    T259  blob 86f4285  (the PRE pin the T292 adversary already uses)
    T268  81eb16f:.softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py
    T286  73483f5:.softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py
    T292  the shipped file

AXIS 1 -- COVERAGE STRICTNESS.  Population: documents that GRADE NOTHING (a header, however
    nested).  A correct rule REFUSES every one.  Score = how many it refuses, out of N.
    HIGHER IS STRICTER.

AXIS 2 -- DETECTION GENEROSITY.  Population: documents that DO grade something and contain a
    genuine unacknowledged disagreement (an affirmative verdict over that object's own false
    predicate), each re-nested to a range of depths.  A correct rule REFUSES every one.
    Score = how many it refuses, out of N.  HIGHER IS MORE GENEROUS.

AXIS 3 -- CONTROL (must not move).  Population: the committed evidence and a genuine green.
    A correct rule GREENS every one.  A rule that scores 0 on axes 1 and 2 by refusing
    everything is caught here.

Every arm is unpacked INSIDE the repo: all four resolve `repo_root()` by walking up from their
own location and error out with no `.git` ancestor, which would silently turn a whole column
into a constant (the defect T292 recorded in extract_pre).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent
CAP = ROOT / ".softhouse" / "capture" / "t286-t268-retry"
T256 = ROOT / ".softhouse" / "capture" / "t256-verdict-predicate"
T291FIX = ROOT / ".softhouse" / "reviews" / "t291-review-t286" / "probe" / "fixtures"
REAL_229 = ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json"
REAL_219 = ROOT / ".softhouse" / "capture" / "t219-g8-residual" / "out" / "classify-t219.json"
RULEPATH = ".softhouse/capture/t256-verdict-predicate/check_verdict_predicate_agreement.py"
PROBE = "T259-VPA:"

ARMS = [
    ("T259", "86f4285", None),
    ("T268", "81eb16f", RULEPATH),
    ("T286", "73483f5", RULEPATH),
    ("T292", None, None),          # the shipped file
]


def git_show(spec):
    r = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", spec],
                       capture_output=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit("ERROR: cannot resolve %r -- an ABSENT arm is a constant column, "
                         "not a measurement. Refusing to continue." % spec)
    return r.stdout


def hash_object(p):
    r = subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, timeout=60)
    return r.stdout.strip()


def unpack(arms_dir):
    out = []
    for name, blob, path in ARMS:
        if blob is None:
            p = CAP / "check_verdict_predicate_agreement_t292.py"
        else:
            spec = blob if path is None else "%s:%s" % (blob, path)
            p = arms_dir / ("ARM-%s.py" % name)
            p.write_bytes(git_show(spec))
        out.append((name, p, hash_object(p)))
    return out


def run(rule, target, timeout=20):
    env = dict(os.environ)
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    cmd = [sys.executable, str(rule),
           "--register", str(T256 / "boolean-key-register.json"),
           "--acknowledgements", str(T256 / "acknowledged.json"), str(target)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None
    probe = None
    for ln in r.stdout.splitlines():
        if ln.startswith(PROBE):
            probe = ln
    return r.returncode, probe


# ---------------------------------------------------------------------------------------
# populations
# ---------------------------------------------------------------------------------------

def nest(doc, depth, mode):
    """Container-only re-nesting, the family this whole lineage kept losing to."""
    cur = doc
    for i in range(depth):
        if mode == "list":
            cur = [cur]
        elif mode == "object":
            cur = {"_h%d" % i: cur}
        else:
            cur = [{"_h%d" % i: cur}]
    return cur


HEADER_SEEDS = {
    "header-meta-empty": {"meta": {"verdict": "AS PREDICTED"}, "cells": []},
    "header-root-verdict": {"verdict": "AS PREDICTED"},
    "header-descriptive-bool-only": {
        "cells": [{"id": "c1", "t223RulePredictedRescue": True, "verdict": "AS PREDICTED"}]},
    "header-predicate-as-a-string": {
        "cells": [{"id": "c1", "P2_x": "false", "verdict": "AS PREDICTED"}]},
}

DISAGREEMENT_SEED = {
    "cells": [{"id": "c1", "P2_x": False, "verdict": "AS PREDICTED"}]}


def build_populations():
    strict, generous, control = {}, {}, {}
    # AXIS 1 -- nothing is graded, however it is nested.
    for p in sorted(T291FIX.glob("*.json")):
        strict["T291/" + p.stem] = json.loads(p.read_text(encoding="utf-8"))
    for nm, seed in HEADER_SEEDS.items():
        for mode in ("list", "object", "mixed"):
            for d in (0, 1, 2, 4):
                strict["%s/%s/d%d" % (nm, mode, d)] = nest(seed, d, mode)
    # AXIS 2 -- a genuine unacknowledged disagreement, re-nested.
    for mode in ("list", "object", "mixed"):
        for d in (0, 1, 2, 4, 6):
            generous["disagreement/%s/d%d" % (mode, d)] = nest(DISAGREEMENT_SEED, d, mode)
    generous["disagreement/verdict-value-in-a-list"] = {
        "cells": [{"id": "c1", "P2_x": False, "verdict": ["AS PREDICTED"]}]}
    generous["disagreement/verdict-key-renamed"] = {
        "cells": [{"id": "c1", "P2_x": False, "conclusion": "everything is fine"}]}
    # AXIS 3 -- must stay green.
    # THE COMMITTED CORPORA ARE PASSED **IN PLACE**, NOT RE-SERIALISED.  The first draft of this
    # probe wrote them to a temp path, which changes BOTH the relative path and the sha256, so
    # every acknowledgement block stopped applying and all four arms "refused committed correct
    # evidence".  That was my instrument lying, not a finding; recorded rather than tidied away.
    if REAL_229.exists():
        control["REAL/classify-t229"] = REAL_229
    if REAL_219.exists():
        control["REAL/classify-t219"] = REAL_219
    control["genuine-green"] = {
        "cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]}
    control["genuine-green/nested-d3"] = nest(
        {"cells": [{"id": "c1", "P2_x": True, "verdict": "AS PREDICTED"}]}, 3, "mixed")
    return strict, generous, control


def score(arm_path, pop, tmp, want):
    """want='REFUSE' -> count rc==1 with a probe line. want='GREEN' -> count rc==0."""
    hits, misses = 0, []
    for name in sorted(pop):
        doc = pop[name]
        if isinstance(doc, Path):
            p = doc                     # committed evidence, graded WHERE IT LIVES
        else:
            p = tmp / (name.replace("/", "__") + ".json")
            p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        rc, probe = run(arm_path, p)
        if want == "REFUSE":
            ok = (rc == 1 and probe is not None)
        else:
            ok = (rc == 0 and probe is not None)
        if ok:
            hits += 1
        else:
            misses.append((name, rc, probe is not None))
    return hits, misses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show-misses", type=int, default=8)
    args = ap.parse_args()
    armdir = Path(tempfile.mkdtemp(prefix=".t308-arms-", dir=str(HERE.parent)))
    tmp = Path(tempfile.mkdtemp(prefix="t308-pop-"))
    try:
        arms = unpack(armdir)
        strict, generous, control = build_populations()
        print("T308 -- BOTH AXES, FOUR ARMS, PINNED BLOBS")
        print("=" * 100)
        for name, p, sha in arms:
            print("  ARM %-5s %s" % (name, sha))
        print()
        print("  AXIS 1  COVERAGE STRICTNESS   population %d  (grade nothing -> must REFUSE)"
              % len(strict))
        print("  AXIS 2  DETECTION GENEROSITY  population %d  (real disagreement -> must REFUSE)"
              % len(generous))
        print("  AXIS 3  CONTROL               population %d  (real evidence -> must GREEN)"
              % len(control))
        print()
        print("  %-6s %14s %14s %14s" % ("arm", "STRICTNESS", "GENEROSITY", "CONTROL"))
        print("  " + "-" * 52)
        rows = {}
        for name, p, sha in arms:
            s, sm = score(p, strict, tmp, "REFUSE")
            g, gm = score(p, generous, tmp, "REFUSE")
            c, cm = score(p, control, tmp, "GREEN")
            rows[name] = (s, len(strict), g, len(generous), c, len(control), sm, gm, cm)
            print("  %-6s %9d/%-4d %9d/%-4d %9d/%-4d"
                  % (name, s, len(strict), g, len(generous), c, len(control)))
        print()
        for name, p, sha in arms:
            s, ns, g, ng, c, nc, sm, gm, cm = rows[name]
            print("  %s misses:" % name)
            for lbl, ms in (("STRICTNESS", sm), ("GENEROSITY", gm), ("CONTROL", cm)):
                if not ms:
                    print("     %-11s none" % lbl)
                    continue
                print("     %-11s %d" % (lbl, len(ms)))
                for m in ms[:args.show_misses]:
                    print("        %-52s rc=%-8s probe=%s" % m)
                if len(ms) > args.show_misses:
                    print("        ... and %d more" % (len(ms) - args.show_misses))
            print()
        print("=" * 100)
        print("THE STREAK TEST -- T292 must not be BELOW an earlier arm on EITHER axis.")
        t = rows["T292"]
        verdicts = []
        for other in ("T259", "T268", "T286"):
            o = rows[other]
            ds = t[0] - o[0]
            dg = t[2] - o[2]
            dc = t[4] - o[4]
            verdicts.append((other, ds, dg, dc))
            print("  vs %-5s  strictness %+d   generosity %+d   control %+d"
                  % (other, ds, dg, dc))
        regress = [(o, ds, dg, dc) for o, ds, dg, dc in verdicts
                   if ds < 0 or dg < 0 or dc < 0]
        print()
        if regress:
            print("  *** T292 IS BELOW AN EARLIER ARM ON AT LEAST ONE AXIS ***")
            for o, ds, dg, dc in regress:
                print("      vs %s: strictness %+d generosity %+d control %+d" % (o, ds, dg, dc))
        else:
            print("  T292 is >= every earlier arm on BOTH axes and on the control.")
            print("  THE TRADE IS NOT VISIBLE ON THESE POPULATIONS.")
        print("EXIT %d" % (1 if regress else 0))
        return 1 if regress else 0
    finally:
        shutil.rmtree(armdir, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
