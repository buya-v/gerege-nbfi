#!/usr/bin/env python3
"""T292 -- CALIBRATE THE HEADLINE NUMBER. Make `LOST REFUSALS` fire, and watch it.

`LOST REFUSALS: 0` is the single number this whole lineage turns on -- it is the criterion T281
used to REJECT T268 and the one T291 told the retry to adopt as its acceptance test. **A counter
that has only ever been observed reading zero is indistinguishable from a counter that cannot
count.** That is P-45's rule -- *"a test-only guard is not a guard… verify the path that actually
executes calls it"* -- pointed at a statistic instead of a guard, and it is the exact shape of
T286's `0 SKIPPED`, which T291 showed was an observation and not a guarantee.

The mutant suite does not close this on its own. `M1` restores T286's losing coverage metric and IS
killed -- but it is killed by the **post-condition** (`GREEN with an empty witness set` -> exit 2),
so `rc == 0` never happens and the lost-refusal counter still reads **0**. The kill is real and the
counter is still unexercised.

So this file builds the mutant that actually reproduces the lineage's defect end to end:

    M1  coverage reverted to the OBJECT CENSUS  (a header counts as coverage again)
  + M8  the belt-and-braces post-condition DELETED (so nothing converts the vacuous green to an
        error, exactly as in T259/T268/T286, none of which had one)

and runs the unmodified adversary against it. **The expected outcome is a NON-ZERO lost-refusal
count**, naming T291's own fixtures. If it comes back zero, the adversary cannot see the defect it
exists to see, and every `LOST REFUSALS: 0` in this branch is decoration.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parent
RULE = CAP / "check_verdict_predicate_agreement_t292.py"

M1_FIND = "    nil = 1 if rep.nil_files else 0"
M1_REPL = "    nil = 1 if rep.objects == 0 else 0"
M8_FIND = "    if not refused and (len(rep.witness) < 1 or rep.nil_files or rep.files < 1):"
M8_REPL = "    if False:"


def main():
    src = RULE.read_text(encoding="utf-8")
    for anchor in (M1_FIND, M8_FIND):
        if src.count(anchor) != 1:
            raise SystemExit("ERROR: anchor occurs %d times, expected 1: %r"
                             % (src.count(anchor), anchor[:80]))
    # Inside the repo: the rule refuses without a `.git` ancestor, and a mutant that errors on
    # everything would go red for a reason unrelated to its defect (see mutants_t292.py).
    tmp = Path(tempfile.mkdtemp(prefix=".t292-lostref-", dir=str(CAP)))
    try:
        mp = tmp / "M1-plus-M8-the-lineage-defect-restored.py"
        mp.write_text(src.replace(M1_FIND, M1_REPL).replace(M8_FIND, M8_REPL), encoding="utf-8")
        legs = tmp / "legs.json"
        print("T292 -- CALIBRATING `LOST REFUSALS`")
        print("=" * 96)
        print("  mutant: coverage reverted to the OBJECT CENSUS **and** the post-condition deleted")
        print("          -- i.e. the lineage's defect, restored end to end, with nothing to catch it")
        print()
        r = subprocess.run([sys.executable, str(HERE / "adversary_t292.py"),
                            "--rule", str(mp), "--seeds", "2", "--legs-out", str(legs)],
                           capture_output=True, text=True, timeout=3600)
        for ln in r.stdout.splitlines():
            if ("LOST REFUSAL" in ln or ln.startswith("T292 ADVERSARY") or ln.startswith("EXIT")
                    or "ADJUDICATED" in ln):
                print("  " + ln)
        d = json.loads(legs.read_text(encoding="utf-8"))
        lost = d["lost_refusals"]
        print()
        print("  LOST REFUSALS RECORDED: %d" % len(lost))
        for name, how in lost[:12]:
            print("     %-62s via %s" % (name, how))
        if len(lost) > 12:
            print("     ... and %d more" % (len(lost) - 12))
        print()
        named = sorted({n.split("#")[0] for n, _ in lost})
        print("  DISTINCT FIXTURES THAT LOST A REFUSAL: %d" % len(named))
        for n in named:
            print("     %s" % n)
        print()
        ok = len(lost) > 0 and r.returncode != 0
        print("  CALIBRATION %s -- the counter FIRES on a planted defect, so `LOST REFUSALS: 0`"
              % ("PASSED" if ok else "FAILED"))
        print("  on the shipped rule is a MEASUREMENT and not an unexercised zero.")
        print("EXIT %d" % (0 if ok else 1))
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
