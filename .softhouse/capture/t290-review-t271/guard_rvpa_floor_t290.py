#!/usr/bin/env python3
"""T290 -- the guard condition T269 must wire, instead of the one T271's handoff section 5
specifies.

WHAT T271 SPECIFIED, AND WHY IT IS NOT ENOUGH
    T271 tells T269 to call `run_rvpa_over_targets.py` from `run_guards()` and to pin
    `unacknowledged=0`, explicitly NOT `disagreements=0`. The second half of that advice is right
    -- pinning zero disagreements would demand a clean corpus and would be the bar lowered. The
    first half leaves an INVISIBLE ROUTE TO GREEN, measured at T290:

        retro-edit `.softhouse/capture/t219-g8-residual/out/classify-t219.json` so the four false
        `P2_*` booleans read `true`
          -> the acknowledgement block goes VOID (the rule prints `!! ACKNOWLEDGEMENT BLOCK VOID`)
          -> but `check_verdict_predicate_agreement.py`'s `refused` expression is
             `(unacknowledged or unclassified_keys or unclassified_verdicts or nil)` -- `void_acks`
             is counted, PRINTED, and then not consulted
          -> rule exits 0, `disagreements=0 acknowledged=0 unacknowledged=0`
          -> `T271-TARGETS: GREEN targets=2 inspected=2 ruleExit=0`
          -> a guard pinning only `unacknowledged=0` PASSES.

    That is the T114/T176 retro-edit evasion the sha pin was built to stop, arriving by the one
    door the pin does not watch: erase the disagreement and there is nothing left for the pin to
    void loudly enough to matter. It is P-88's shape -- `an instrument's verdict must depend on
    nothing outside` what it claims to measure -- and P-261's rule that an orphan may not acquire a
    caller until the fail-opens in it are repaired, because wiring a liar is strictly worse than
    leaving it unwired.

WHAT THIS GUARD ADDS, and each one closes a specific door
    1. PRESENCE BEFORE VALUE. No `T271-TARGETS:` probe line is an INSTRUMENT FAILURE, never a pass
       and never an absence (P-84: `exit 2 with no probe line` is the guard working -- read the
       absence, not the value).
    2. VOID ACKNOWLEDGEMENT BLOCKS > 0 IS A REFUSAL. The rule already measures and prints this and
       then drops it on the floor. Reading it back out of the rule's own output needs no edit to
       the rule, which is contended by T286.
    3. A FLOOR ON `disagreements`, from `floor-t290.json`. The count may RISE -- a new disagreement
       is then unacknowledged and the rule refuses on its own -- but it may not FALL. `0` is not
       the pin; a FLOOR is.
    4. `unacknowledged == 0`, which is T271's condition, kept.
    5. NIL COVERAGE: `rows` below the committed minimum is a refusal, so a runner that hands over
       an empty file cannot green.

    NO PIPELINE ANYWHERE. `cmd | sed` discards the producer's status unless `pipefail` happens to
    be set, and an instrument whose status depends on a shell option set sixty lines away is one
    `set +o pipefail` from fail-open (P-81).

EXIT CODES, never conflated (P-80): 0 GREEN, 1 a REAL measured refusal, 2 ERROR (usage, IO, or the
runner dying before it measured). Exit 2 NEVER reports an absence.

PROBE LINE, always last:
    T290-RVPA-GUARD: <STATE> runnerExit=.. disagreements=.. floor=.. acknowledged=..
                     unacknowledged=.. voidBlocks=.. rows=..
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = "T290-RVPA-GUARD:"

TARGETS_RE = re.compile(r"^T271-TARGETS: (?P<state>\S+) .*?\bruleExit=(?P<rc>-|\d+)", re.M)
VPA_RE = re.compile(
    r"^T259-VPA: (?P<state>\S+) files=(?P<files>\d+) rows=(?P<rows>\d+) "
    r"predicates=(?P<predicates>\d+) disagreements=(?P<dis>\d+) acknowledged=(?P<ack>\d+) "
    r"unacknowledged=(?P<unack>\d+) unclassifiedKeys=(?P<uk>\d+) "
    r"unclassifiedVerdicts=(?P<uv>\d+) nilCoverage=(?P<nil>\d+)", re.M)
VOID_RE = re.compile(r"^\s*void acknowledgement blocks:\s*(?P<n>\d+)\s*$", re.M)


def repo_root(p: Path) -> Path:
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    print("ERROR: no .git ancestor of " + str(HERE), file=sys.stderr)
    raise SystemExit(2)


def find_runner(root):
    """The runner moves in T269 (t271-b1-t219/ -> t256-verdict-predicate/). Look in BOTH, and say
    which one was found. `not found` is a statement about the search, so both paths are printed."""
    cands = [
        root / ".softhouse/capture/t256-verdict-predicate/run_rvpa_over_targets.py",
        root / ".softhouse/capture/t271-b1-t219/run_rvpa_over_targets.py",
    ]
    for c in cands:
        if c.exists():
            return c
    print("ERROR: run_rvpa_over_targets.py is on neither known path. Looked at:", file=sys.stderr)
    for c in cands:
        print("         " + str(c), file=sys.stderr)
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="R-VPA target-list guard with a disagreement FLOOR")
    ap.add_argument("--runner", default=None)
    ap.add_argument("--floor", default=str(HERE / "floor-t290.json"))
    ap.add_argument("--targets", default=None,
                    help="passed through to the runner; omit to use the runner's default")
    args = ap.parse_args(argv)

    root = repo_root(HERE)
    runner = Path(args.runner) if args.runner else find_runner(root)
    if runner is None:
        return 2
    fpath = Path(args.floor)
    if not fpath.exists():
        print("ERROR: the committed floor is absent: " + str(fpath), file=sys.stderr)
        return 2
    try:
        floor_doc = json.loads(fpath.read_text())
        floor = int(floor_doc["floor"]["disagreements"])
        rows_min = int(floor_doc["floor"]["rowsMinimum"])
        void_max = int(floor_doc["floor"]["voidAcknowledgementBlocksMaximum"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: floor unreadable: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2

    cmd = [sys.executable, str(runner)]
    if args.targets:
        cmd += ["--targets", args.targets]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    out = proc.stdout + proc.stderr
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)

    print()
    print("T290 -- R-VPA guard condition (floor + void-block, over T271's runner)")
    print("=" * 78)
    print("  runner : %s" % runner.relative_to(root))
    print("  floor  : %s  (disagreements >= %d, rows >= %d, voidBlocks <= %d)"
          % (fpath.relative_to(root) if str(fpath).startswith(str(root)) else fpath,
             floor, rows_min, void_max))

    tm = TARGETS_RE.search(out)
    vm = VPA_RE.search(out)
    problems = []
    if not tm:
        print("  !! NO `T271-TARGETS:` PROBE LINE. The runner died BEFORE it measured. That is an")
        print("  !! INSTRUMENT FAILURE, not a measured refusal and not an absence (P-84).")
        print("%s ERROR runnerExit=%d disagreements=? floor=%d acknowledged=? unacknowledged=? "
              "voidBlocks=? rows=?" % (PROBE, proc.returncode, floor))
        return 2
    if not vm:
        print("  !! NO `T259-VPA:` PROBE LINE inside the runner's output. The rule died before it")
        print("  !! measured. INSTRUMENT FAILURE (P-84).")
        print("%s ERROR runnerExit=%d disagreements=? floor=%d acknowledged=? unacknowledged=? "
              "voidBlocks=? rows=?" % (PROBE, proc.returncode, floor))
        return 2

    dis = int(vm.group("dis"))
    ack = int(vm.group("ack"))
    unack = int(vm.group("unack"))
    rows = int(vm.group("rows"))
    voidm = VOID_RE.search(out)
    if voidm is None:
        print("  !! the rule printed no `void acknowledgement blocks:` line. This guard will not")
        print("  !! assume zero for a number it did not read (P-81: an absence you did not")
        print("  !! measure is not a zero).")
        print("%s ERROR runnerExit=%d disagreements=%d floor=%d acknowledged=%d unacknowledged=%d "
              "voidBlocks=? rows=%d" % (PROBE, proc.returncode, dis, floor, ack, unack, rows))
        return 2
    voids = int(voidm.group("n"))

    if proc.returncode not in (0, 1):
        problems.append("the runner exited %d, which is an ERROR, not a measurement"
                        % proc.returncode)
    if proc.returncode == 1:
        problems.append("the runner REFUSED (exit 1) -- read its own output above")
    if unack != 0:
        problems.append("unacknowledged=%d, wanted 0" % unack)
    if voids > void_max:
        problems.append("voidAcknowledgementBlocks=%d, wanted <= %d. AN ACKNOWLEDGEMENT REGISTERED "
                        "FOR BYTES THAT ARE NO LONGER ON DISK IS NOT AN ACKNOWLEDGEMENT. The rule "
                        "prints this and does not act on it; this guard acts on it."
                        % (voids, void_max))
    if dis < floor:
        problems.append("disagreements=%d has FALLEN BELOW THE COMMITTED FLOOR %d. The corpus did "
                        "not get cleaner by itself: either committed evidence was retro-edited "
                        "(T114/T176) or the rule stopped looking. Neither is a pass. If the drop "
                        "is legitimate, LOWER THE FLOOR IN A TASK, with a reason, in writing."
                        % (dis, floor))
    if rows < rows_min:
        problems.append("rows=%d below the committed minimum %d -- the rule inspected less than "
                        "the corpus it is pinned to" % (rows, rows_min))

    print("  measured: disagreements=%d acknowledged=%d unacknowledged=%d voidBlocks=%d rows=%d "
          "runnerExit=%d" % (dis, ack, unack, voids, rows, proc.returncode))
    for p in problems:
        print("  REFUSED: " + p)
    if not problems:
        print("  every condition held. NOTE WHAT THIS DOES NOT ESTABLISH: that any acknowledgement")
        print("  is right in SUBSTANCE. It establishes only that no disagreement is unremarked, no")
        print("  acknowledgement is registered against bytes that moved, and the count did not")
        print("  quietly fall.")
    state = "REFUSED" if problems else "GREEN"
    print("%s %s runnerExit=%d disagreements=%d floor=%d acknowledged=%d unacknowledged=%d "
          "voidBlocks=%d rows=%d"
          % (PROBE, state, proc.returncode, dis, floor, ack, unack, voids, rows))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
