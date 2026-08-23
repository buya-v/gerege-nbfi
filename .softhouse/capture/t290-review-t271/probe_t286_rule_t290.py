#!/usr/bin/env python3
"""T290 -- is F-T290-1 STILL LIVE against the rule T269 will actually install?

`main` moved under this review. `softhouse/t286-t268-retry` (T268's retry, itself in review as
T291) REWRITES `check_verdict_predicate_agreement.py`, and its own docstring says it closes
`R3 MED: void_acks ... was incremented, printed as !! ACKNOWLEDGEMENT BLOCK VOID and summarised,
but appeared in NEITHER the gate expression NOR the probe line`. A reviewer who shipped
F-T290-1 without checking that would be shipping a stale finding -- `P-80`, a corrected cardinal
rots in every place it was restated, applied to a FINDING.

So this MEASURES it, on three trees, against BOTH rules, rather than reading either docstring:

  CASE 0  clean tree                              -- the positive control (P-72)
  CASE A  the evidence retro-edited ALONE, register untouched. The block goes VOID.
  CASE B  the CONSISTENT TWO-FILE EDIT: the evidence retro-edited AND the register re-pinned to
          the new bytes with its rows removed. `voidAcks` is 0 -- there is nothing to void,
          because the register was updated to match. This is what "regenerate the evidence and
          update the register" looks like, and it looks like MAINTENANCE, not tampering.

WHERE T286's RULE COMES FROM: `git show softhouse/t286-t268-retry:<path>` into a temp directory
INSIDE the repository, because the rule locates the repo root by walking up for `.git` and a copy
under /tmp exits 2 with `no .git ancestor` -- an environment artefact that would read as a
divergence. The temp directory is removed on every exit path. `t256-verdict-predicate/` itself is
CONTENDED (T286) and is READ ONLY here.

EXIT 0 the measurement completed and matched this review's prediction; 1 it did not; 2 error
(including: the T286 branch is not present, which is an ABSENCE and must not be read as a pass).
PROBE: `T290-T286: <STATE> caseA_live=.. caseA_t286=.. caseB_live=.. caseB_t286=..`
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T290-T286:"
BRANCH = "softhouse/t286-t268-retry"
T256 = ".softhouse/capture/t256-verdict-predicate"
NEEDED = ["check_verdict_predicate_agreement.py", "boolean-key-register.json", "acknowledged.json"]
VPA = re.compile(r"^T259-VPA: (?P<state>\S+) .*?\bdisagreements=(?P<dis>\d+)\b", re.M)


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


ROOT = repo_root(HERE)
LIVE = ROOT / T256 / "check_verdict_predicate_agreement.py"
EV = ROOT / ".softhouse/capture/t219-g8-residual/out/classify-t219.json"
ACK = ROOT / ".softhouse/capture/t271-b1-t219/acknowledged-t219.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(rule: Path, ack: Path):
    p = subprocess.run([sys.executable, str(rule), "--acknowledgements", str(ack), str(EV)],
                       capture_output=True, text=True, cwd=str(ROOT))
    m = VPA.search(p.stdout)
    if not m:
        return p.returncode, "NO-PROBE-LINE", "?", p.stdout + p.stderr
    return p.returncode, m.group("state"), m.group("dis"), p.stdout + p.stderr


def main() -> int:
    for need in (LIVE, EV, ACK):
        if not need.exists():
            print("ERROR: missing input: " + str(need), file=sys.stderr)
            return 2

    work = Path(tempfile.mkdtemp(prefix=".t290-t286-", dir=str(ROOT)))
    backup = work / "classify-t219.ORIGINAL.json"
    shutil.copy2(EV, backup)
    before = sha(EV)
    try:
        t286 = work / "t286"
        t286.mkdir()
        for name in NEEDED:
            p = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s/%s" % (BRANCH, T256, name)],
                               capture_output=True, text=True)
            if p.returncode != 0:
                print("ERROR: %s:%s/%s did not resolve (git exit %d). THIS IS AN ABSENCE, not a"
                      % (BRANCH, T256, name, p.returncode), file=sys.stderr)
                print("       pass: the T286 branch is not in this repository, so nothing was"
                      " measured about it.", file=sys.stderr)
                return 2
            (t286 / name).write_text(p.stdout)
        rule286 = t286 / "check_verdict_predicate_agreement.py"

        print("T290 -- is the invisible route to green still live against T286's rewritten rule?")
        print("=" * 100)
        print("  live rule  : %s" % LIVE.relative_to(ROOT))
        print("  T286 rule  : %s:%s/… (extracted read-only into a temp dir inside the repo)"
              % (BRANCH, T256))
        print("  evidence   : %s  sha %s" % (EV.relative_to(ROOT), before[:16]))
        print()

        results = {}

        def measure(case):
            for tag, rule, ack in (("live", LIVE, ACK), ("t286", rule286, results["_ack"])):
                rc, st, dis, _out = run(rule, ack if tag == "t286" else ACK)
                results["%s_%s" % (case, tag)] = (rc, st, dis)
                print("  %-6s %-5s exit %d  %-8s disagreements=%s" % (case, tag, rc, st, dis))

        results["_ack"] = ACK
        print("  CASE 0 -- clean tree (the positive control)")
        measure("case0")
        print()

        print("  CASE A -- the evidence retro-edited ALONE; the register still pins the old bytes")
        doc = json.loads(backup.read_text())
        n = 0
        for row in doc["cells"]:
            for k, v in list(row.items()):
                if k.startswith("P2_") and v is False:
                    row[k] = True
                    n += 1
        EV.write_text(json.dumps(doc, indent=1) + "\n")
        print("         (%d false P2_* flipped to true)" % n)
        measure("caseA")
        print()

        print("  CASE B -- the CONSISTENT TWO-FILE EDIT: evidence retro-edited AND the register")
        print("         re-pinned to the NEW bytes with its rows removed. Nothing is VOID.")
        ad = json.loads(ACK.read_text())
        ad["acknowledgements"][0]["sha256"] = sha(EV)
        ad["acknowledgements"][0]["rows"] = []
        repinned = work / "acknowledged-REPINNED.json"
        repinned.write_text(json.dumps(ad, indent=2))
        results["_ack"] = repinned
        for tag, rule in (("live", LIVE), ("t286", rule286)):
            rc, st, dis, _out = run(rule, repinned)
            results["caseB_%s" % tag] = (rc, st, dis)
            print("  %-6s %-5s exit %d  %-8s disagreements=%s" % ("caseB", tag, rc, st, dis))
        print()

        shutil.copy2(backup, EV)
        if sha(EV) != before:
            print("  !! RESTORE FAILED")
            print("%s ERROR" % PROBE)
            return 2
        print("  committed evidence restored and VERIFIED by sha256: %s" % sha(EV)[:16])
        print()

        problems = []
        # what this review predicts
        if results["case0_live"][0] != 0 or results["case0_t286"][0] != 0:
            problems.append("CASE 0 did not green on both rules -- the control failed, so no "
                            "negative below is trustworthy (P-72)")
        if results["caseA_live"][0] != 0:
            problems.append("CASE A did not go GREEN on the LIVE rule; F-T290-1a would then be "
                            "wrong about the rule on main")
        if results["caseA_t286"][0] != 1:
            problems.append("CASE A did not REFUSE on T286's rule; T286's own R3 claim would then "
                            "be wrong")
        if results["caseB_live"][0] != 0 or results["caseB_t286"][0] != 0:
            problems.append("CASE B refused somewhere -- the FLOOR half of F-T290-1 would then "
                            "already be closed and must not be sent to T269")
        for p in problems:
            print("  REFUSED: " + p)
        if not problems:
            print("  CASE A: GREEN on the live rule, REFUSED on T286's. **T286 ALREADY CLOSES THE")
            print("  void_acks HALF**, independently and before this review. F-T290-1a is live")
            print("  only against the rule on main today, and T269 must state WHICH rule it")
            print("  installs.")
            print()
            print("  CASE B: GREEN ON BOTH. The consistent two-file edit leaves nothing to void,")
            print("  so `voidAcks` cannot see it and `unacknowledged=0` is satisfied. **ONLY A")
            print("  FLOOR ON `disagreements` CATCHES THIS**, and no rule on any branch has one.")
            print("  This is the half of F-T290-1 that survives everything, and it is the shape a")
            print("  well-meaning worker reaches for: regenerate the evidence, update the")
            print("  register. It looks like maintenance.")
        state = "REFUSED" if problems else "GREEN"
        print("%s %s caseA_live=%s caseA_t286=%s caseB_live=%s caseB_t286=%s"
              % (PROBE, state,
                 results["caseA_live"][1], results["caseA_t286"][1],
                 results["caseB_live"][1], results["caseB_t286"][1]))
        return 1 if problems else 0
    finally:
        try:
            shutil.copy2(backup, EV)
        except OSError:
            pass
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
