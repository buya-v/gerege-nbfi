#!/usr/bin/env python3
"""T316 -- RED DRIVE. Three questions, eleven arms, and the first block REFUTES the task premise.

BLOCK F -- IS `guard_rvpa_floor_t290.py` ACTUALLY FAIL-OPEN? (FU-T299-2's claim)
    F1  untouched tree: does it exit 0, and WHICH runner does it say it used?
    F2  BOTH runner candidates removed: does it exit 0 (fail-open) or 2 (refuse)?
    F3  the same two questions for `red/drive-red-t290.py`.

    FU-T299-2 says: "a guard is resolving a dead path and passing anyway." If F2 shows exit 2
    with no probe line, that claim is FALSE and this drive says so.

BLOCK G -- DOES THE NEW FRONTIER GUARD DETECT A REAL REGRESSION?
    G1  calibration on an untouched tree: exit 0, probe PRESENT.
    G2  a NEW instrument naming a dead path is planted: exit 1, probe present, the row named.
    G3  a pinned dead path is MADE TO RESOLVE without the pin being updated: exit 1 -- because a
        frontier that silently shrinks starts excusing a weakness that is no longer there.

BLOCK V -- DOES THE NEW GUARD REFUSE WHEN ITS OWN DEPENDENCIES VANISH?
    This is the arm that decides whether the guard is worth adopting, because it is the exact
    defect the task was dispatched to fix. Every one of these must be exit 2 WITH NO PROBE LINE.
    V1  the census instrument deleted.
    V2  the pin file deleted.
    V3  the pin file emptied (an empty pin is a FAILED READ, never an empty frontier).
    V4  the census selector broken so calibration fails.
    V5  the census made to exit 0 while printing no probe line (presence before value, P-84).

RUNS IN A THROWAWAY CLONE IT MAKES ITSELF. It never touches the tree it is invoked from. Between
arms it resets with `git checkout -- .` and `git clean -fd`, and the reset is VERIFIED with
`git status --porcelain` before the next arm starts; a dirty carry-over would let one arm's plant
be read as the next arm's finding.

EXIT: 0 every arm behaved as predicted; 1 an arm did not; 2 the rig failed. Never conflated.
Probe line `T316-REDGREEN:`, printed only when every arm reached a verdict.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROBE = "T316-REDGREEN:"
GUARD_PROBE = "T316-DEADPATH-FRONTIER:"
T290_PROBE = "T290-RVPA-GUARD:"


def repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise SystemExit(2)


def run(cmd, cwd, timeout=300):
    try:
        pr = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return pr.returncode, pr.stdout + pr.stderr
    except subprocess.TimeoutExpired:
        return None, "(TIMED OUT)"


def reset(clone: Path):
    rc1, o1 = run(["git", "checkout", "--", "."], clone)
    rc2, o2 = run(["git", "clean", "-fdq"], clone)
    rc3, o3 = run(["git", "status", "--porcelain"], clone)
    if rc1 != 0 or rc2 != 0 or rc3 != 0:
        print("RIG FAILURE: could not reset the clone.\n%s\n%s\n%s" % (o1, o2, o3))
        raise SystemExit(2)
    if o3.strip():
        print("RIG FAILURE: the clone is DIRTY after reset. A carry-over would let one arm's")
        print("plant be read as the next arm's finding. Porcelain:\n%s" % o3)
        raise SystemExit(2)


def probe_present(out: str, needle: str) -> bool:
    return re.search(r"^%s" % re.escape(needle), out, re.M) is not None


def main() -> int:
    ap = argparse.ArgumentParser(description="T316 red drive")
    ap.add_argument("--keep", action="store_true", help="do not delete the throwaway clone")
    args = ap.parse_args()

    root = repo_root()
    tmp = tempfile.mkdtemp(prefix="t316-red-")
    clone = Path(tmp) / "clone"
    rc, out = run(["git", "clone", "--quiet", "--no-local", str(root), str(clone)], root,
                  timeout=600)
    if rc != 0:
        print("RIG FAILURE: clone failed:\n%s" % out)
        return 2
    # The clone lands on the source's HEAD branch; make sure the T316 artefacts are present.
    for need in (".softhouse/guards/check-dead-path-frontier.sh",
                 ".softhouse/guards/dead-path-frontier.pin",
                 ".softhouse/capture/t316-dead-path-guards/census_dead_paths.py",
                 ".softhouse/capture/t290-review-t271/guard_rvpa_floor_t290.py"):
        if not (clone / need).exists():
            print("RIG FAILURE: the clone lacks %s -- commit before driving." % need)
            return 2

    GUARD = ".softhouse/guards/check-dead-path-frontier.sh"
    PIN = clone / ".softhouse/guards/dead-path-frontier.pin"
    CENSUS = clone / ".softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
    T290 = ".softhouse/capture/t290-review-t271/guard_rvpa_floor_t290.py"
    T290RED = ".softhouse/capture/t290-review-t271/red/drive-red-t290.py"
    CAND = [".softhouse/capture/t256-verdict-predicate/run_rvpa_over_targets.py",
            ".softhouse/capture/t271-b1-t219/run_rvpa_over_targets.py"]

    rows = []          # (arm, what, expected, exit, probe, verdict)
    def record(arm, what, exp_exit, exp_probe, rc, out, probe_needle, note=""):
        pres = probe_present(out, probe_needle)
        ok = (rc == exp_exit) and (pres == exp_probe)
        rows.append({"arm": arm, "what": what, "expExit": exp_exit, "expProbe": exp_probe,
                     "exit": rc, "probe": pres, "ok": ok, "note": note, "out": out})
        return ok

    print("T316 RED DRIVE")
    print("=" * 92)
    print("clone: %s" % clone)
    print()

    # ---------------- BLOCK F: is the T290 guard fail-open? -----------------------------------
    reset(clone)
    rc, out = run([sys.executable, T290], clone)
    m = re.search(r"^\s*runner\s*:\s*(\S+)", out, re.M)
    runner_used = m.group(1) if m else "(not printed)"
    record("F1", "T290 guard, untouched tree", 0, True, rc, out, T290_PROBE,
           "runner it says it used: %s" % runner_used)

    reset(clone)
    for c in CAND:
        p = clone / c
        if p.exists():
            p.unlink()
    rc, out = run([sys.executable, T290], clone)
    record("F2", "T290 guard, BOTH runner candidates removed", 2, False, rc, out, T290_PROBE,
           "THE ARM THAT DECIDES FU-T299-2")

    reset(clone)
    for c in CAND:
        p = clone / c
        if p.exists():
            p.unlink()
    rc, out = run([sys.executable, T290RED], clone)
    record("F3", "T290 red drive, BOTH runner candidates removed", 2, False, rc, out, T290_PROBE)

    # ---------------- BLOCK G: does the frontier guard detect a regression? -------------------
    reset(clone)
    rc, out = run(["bash", GUARD], clone)
    record("G1", "frontier guard, untouched tree (CALIBRATION)", 0, True, rc, out, GUARD_PROBE)

    reset(clone)
    planted = clone / ".softhouse/capture/t316-dead-path-guards/planted_regression.py"
    planted.write_text(
        '#!/usr/bin/env python3\n'
        '"""A planted instrument naming a path that does not exist."""\n'
        'P = ".softhouse/capture/t316-dead-path-guards/no-such-file-planted-by-G2.json"\n')
    rc, out = run(["git", "add", "-f", str(planted.relative_to(clone))], clone)
    rc, out = run(["bash", GUARD], clone)
    saw_row = "planted_regression.py" in out
    record("G2", "a NEW instrument naming a dead path is planted", 1, True, rc, out, GUARD_PROBE,
           "the new row is named in the output: %s" % saw_row)

    reset(clone)
    # Make one pinned dead literal RESOLVE, without touching the pin.
    first_row = None
    for line in PIN.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        first_row = line
        break
    made = None
    if first_row and " | " in first_row:
        made = clone / first_row.split(" | ", 1)[1].strip()
        made.parent.mkdir(parents=True, exist_ok=True)
        made.write_text("planted by G3 so a pinned dead path RESOLVES\n")
        run(["git", "add", "-f", str(made.relative_to(clone))], clone)
    rc, out = run(["bash", GUARD], clone)
    record("G3", "a pinned dead path is MADE TO RESOLVE, pin not updated", 1, True, rc, out,
           GUARD_PROBE, "row made to resolve: %s" % (first_row or "(none)"))

    # ---------------- BLOCK V: does the guard refuse when ITS deps vanish? --------------------
    reset(clone)
    CENSUS.unlink()
    rc, out = run(["bash", GUARD], clone)
    record("V1", "the census instrument DELETED", 2, False, rc, out, GUARD_PROBE,
           "THE FAIL-DIRECTION ARM")

    reset(clone)
    PIN.unlink()
    rc, out = run(["bash", GUARD], clone)
    record("V2", "the pin file DELETED", 2, False, rc, out, GUARD_PROBE)

    reset(clone)
    PIN.write_text("# every row removed, nothing but this comment\n")
    rc, out = run(["bash", GUARD], clone)
    record("V3", "the pin file EMPTIED (comments only)", 2, False, rc, out, GUARD_PROBE,
           "an empty pin is a FAILED READ, never an empty frontier")

    reset(clone)
    txt = CENSUS.read_text()
    broken = txt.replace('LITERAL_RE = re.compile(r"""([\'"])',
                         'LITERAL_RE = re.compile(r"""(ZZZNOMATCH)(')
    if broken == txt:
        # Fall back to a selector break that is guaranteed to bite: empty the corpus globs.
        broken = txt.replace('".softhouse/*.py", ".softhouse/*.sh"',
                             '"no/such/glob/*.py", "no/such/glob/*.sh"')
    CENSUS.write_text(broken)
    rc, out = run(["bash", GUARD], clone)
    record("V4", "the census SELECTOR broken (calibration must fail)", 2, False, rc, out,
           GUARD_PROBE, "selector break took effect: %s" % (broken != txt))

    reset(clone)
    # A census that exits 0 but prints no probe line: it did not reach a count. P-84.
    txt = CENSUS.read_text()
    CENSUS.write_text(txt.replace('PROBE = "T316-DEADPATH-CENSUS:"', 'PROBE = "SILENCED:"'))
    rc, out = run(["bash", GUARD], clone)
    record("V5", "the census exits 0 but prints NO probe line", 2, False, rc, out, GUARD_PROBE,
           "presence before value (P-84)")

    reset(clone)

    # ---------------- report -------------------------------------------------------------------
    print("%-4s %-56s %-14s %-14s %s" % ("ARM", "WHAT", "EXPECTED", "OBSERVED", "VERDICT"))
    print("-" * 92)
    for r in rows:
        exp = "exit %s/%s" % (r["expExit"], "probe" if r["expProbe"] else "NO probe")
        obs = "exit %s/%s" % (r["exit"], "probe" if r["probe"] else "NO probe")
        print("%-4s %-56s %-14s %-14s %s"
              % (r["arm"], r["what"][:56], exp, obs, "PASS" if r["ok"] else "**FAIL**"))
        if r["note"]:
            print("     note: %s" % r["note"])
    print()

    bad = [r for r in rows if not r["ok"]]
    for r in bad:
        print("---- ARM %s OUTPUT ----" % r["arm"])
        print(r["out"][:3000])

    f2 = next(r for r in rows if r["arm"] == "F2")
    print("FU-T299-2 ADJUDICATION")
    print("-" * 92)
    if f2["exit"] == 2 and not f2["probe"]:
        print("  REFUTED. With BOTH candidates absent the T290 guard exits 2 and prints NO probe")
        print("  line -- it REFUSES. It is not fail-open. On the untouched tree it exits 0")
        print("  because it RESOLVED a real runner and ran it, and it PRINTS which one:")
        print("      %s" % next(r for r in rows if r["arm"] == "F1")["note"])
        print("  The dead literal is candidate #1 of an ordered two-candidate list.")
    else:
        print("  NOT REFUTED on this evidence: F2 gave exit=%s probe=%s" % (f2["exit"], f2["probe"]))

    if not args.keep:
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        print("\nclone kept at %s" % clone)

    print()
    print("%s arms=%d pass=%d fail=%d" % (PROBE, len(rows), len(rows) - len(bad), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
