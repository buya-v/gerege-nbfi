#!/usr/bin/env python3
"""T292 -- BREAK THE RULE ON PURPOSE AND WATCH THE ADVERSARY GO RED.

P-45, in the form this program keeps re-learning it: "a guard that only works when someone
remembers to run it enforces nothing" -- and its harder sibling, a guard nobody has ever watched
FAIL. Every claim below is a claim about the ADVERSARY, not about the rule: if the adversary
cannot see a defect that is deliberately planted, then a green adversary run is worth nothing and
every number in the handoff is decoration.

Each mutant is a MINIMAL source edit that re-introduces exactly one defect from the lineage. The
mutant is applied to a COPY; the live rule is never touched. A mutant that the adversary passes is
reported as SURVIVED and is a FAILURE of this file.

**A KILL FOR THE WRONG REASON IS NOT A KILL, AND THIS FILE'S FIRST DRAFT PRODUCED NINE OF THEM.**
It built the mutants in `/tmp`. The rule computes `repo_root()` by walking up for a `.git` ancestor
and refuses without one -- so every mutant returned **exit 2 on every input**, the adversary went
red nine times out of nine, and the transcript said `9 killed, 0 SURVIVED`. Every one of those kills
was the `no .git ancestor` error, not the planted defect: all nine legs files were byte-for-byte the
same failure list, which is what gave it away. That is P-76's rule -- *"a guard driven red only on
the shape it was built from proves the wiring, not the coverage"* -- one layer further out: a red
drive that fires for a reason unrelated to the defect is a TAUTOLOGY WITH A TRANSCRIPT.

Two fences, both driven:
  1. Mutants are built INSIDE the repo, so `repo_root()` resolves exactly as it does for the live
     rule.
  2. **VIABILITY CALIBRATION (P-72).** Before any kill is accepted, each mutant is run on the real
     evidence and must still produce a PROBE LINE. A mutant that cannot measure anything is
     reported `NON-VIABLE`, is NOT counted as a kill, and fails this file -- because a corpse
     proves nothing about the murder weapon.

**TWO MUTANTS ARE NEGATIVE CONTROLS AND MUST SURVIVE** (`--EXPECTED-TO-SURVIVE` in the id). A suite
in which every edit kills cannot distinguish *"the adversary is sharp"* from *"the adversary reds
out on anything"*, which is the failure its own first draft had. `M8` and `M5` are deliberate
no-ops; if either is KILLED, a guard the rule treats as belt-and-braces is actually load-bearing,
which is a finding about the RULE, and it is reported as `UNEXPECTED-KILL`.

`M5` earned that status the hard way: it was written as a kill, **it survived**, and driving all
three arms showed why -- `_assert_no_float` catches NaN by TYPE ABSENCE whether or not
`parse_constant` is set. `M10` plants the real defect. The suite told me which of my two float
guards was doing the work; that is the suite earning its keep, and it is recorded rather than
tidied away.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = HERE.parent
ROOT = CAP.parent.parent.parent
RULE = CAP / "check_verdict_predicate_agreement_t292.py"
T256 = CAP.parent / "t256-verdict-predicate"
REAL = ROOT / ".softhouse" / "capture" / "t229-g8-site3" / "out" / "classify-t229.json"


def viable(rule: Path):
    """Can this mutant still MEASURE? It must print a probe line on the real evidence. A mutant
    that errors on everything would make the adversary go red for a reason that has nothing to do
    with the defect -- see the module docstring."""
    r = subprocess.run([sys.executable, str(rule),
                        "--register", str(T256 / "boolean-key-register.json"),
                        "--acknowledgements", str(T256 / "acknowledged.json"), str(REAL)],
                       capture_output=True, text=True, timeout=120)
    probe = [l for l in r.stdout.splitlines() if l.startswith("T259-VPA:")]
    return (bool(probe), r.returncode, (probe[-1] if probe else r.stderr.strip()[-160:]))

# (id, why it matters, [(find, replace)])  -- every `find` must occur EXACTLY ONCE.
MUTANTS = [
    ("M1-coverage-is-the-object-census",
     "T259/T268's metric: coverage = 'did I recognise any row'. Re-nesting manufactures it. "
     "This is the bracket, restored.",
     [("    nil = 1 if rep.nil_files else 0",
       "    nil = 1 if rep.objects == 0 else 0")]),

    ("M2-coverage-is-a-row-reached-through-a-list",
     "T286's exact phrasing -- 'a record is a row reached through a list' -- which T291 beat with "
     "two characters. Restored verbatim as a coverage metric.",
     [("    nil = 1 if rep.nil_files else 0",
       "    nil = 0 if _t286_records(_LAST_DOC[0]) else 1")]),

    ("M3-nil-coverage-gated-globally-not-per-file",
     "T268's F-1, the SECOND fail-open in the lineage: measure per file, gate across the batch, "
     "and one populated file switches the refusal off for every other.",
     [("    if len(rep.witness) == witness_at_entry:\n        rep.nil_files += 1",
       "    if len(rep.witness) == 0:\n        rep.nil_files += 1")]),

    ("M4-duplicate-keys-last-wins",
     "F-T291-4. json.loads keeps the LAST duplicate, so a recorded `false` predicate is dropped "
     "without a word and the affirmative verdict stands.",
     [("                         object_pairs_hook=_no_duplicate_keys)",
       "                         object_pairs_hook=None)")]),

    # M5 WAS WRITTEN AS A KILL AND IT SURVIVED. THE SUITE WAS RIGHT AND I WAS WRONG.
    # Removing `parse_constant` alone does NOT re-open F-T291-5, because `_assert_no_float`
    # catches NaN/Infinity by TYPE ABSENCE a moment later. Driven, all three arms:
    #     shipped rule                              -> exit 2  "JSON constant 'NaN'"
    #     parse_constant removed                    -> exit 2  "a float survived the parse at $.cells[0].v: nan"
    #     parse_constant AND _assert_no_float removed -> exit 0 GREEN, floats in the graded document
    # So `_assert_no_float` is the LOAD-BEARING defence and `parse_constant` is belt-and-braces.
    # M5 is therefore reclassified as a SECOND NEGATIVE CONTROL, and M10 below plants the real
    # defect. A mutant suite that told me which of my two guards was doing the work is the suite
    # earning its keep; recording that is worth more than quietly deleting the mutant.
    ("M5-parse_constant-removed--EXPECTED-TO-SURVIVE",
     "Belt-and-braces only. `_assert_no_float` still refuses NaN/Infinity by TYPE ABSENCE, so no "
     "verdict changes. Kept as a negative control and as the record of which guard is "
     "load-bearing. The REAL defect is M10.",
     [("                         parse_constant=_refuse_constant,", "")]),

    ("M10-BOTH-float-guards-removed-NaN-enters-a-GREEN-run",
     "F-T291-5 for real, and a MONEY NON-NEGOTIABLE in CLAUDE.md -- 'no floating-point in any "
     "monetary code path… including intermediate calculation'. With both guards gone, NaN and "
     "Infinity reach the graded document AS FLOATS and the run exits 0 GREEN.",
     [("                         parse_constant=_refuse_constant,", ""),
      ("    _assert_no_float(doc)", "")]),

    ("M6-read_text-with-no-encoding",
     "F-T291-6. Mongolian names are Cyrillic and are three fields -- ovog, patronymic, given "
     "name. Under LC_ALL=C the guard exits 2 on a name.",
     [("        raw = path.read_bytes()",
       "        raw = path.read_text().encode('utf-8')")]),

    ("M7-help-exits-0-with-no-probe-line",
     "T286's FOURTH fail-open: the one exit code a caller reads as 'measured, GREEN', printed "
     "with no probe line at all.",
     [("        ap.print_help(sys.stderr)\n        print(\"\\nERROR: --help is not a measurement. "
       "Exit 2, no probe line.\", file=sys.stderr)\n        return 2",
       "        ap.print_help(sys.stderr)\n        return 0")]),

    # M8 IS THE CONTROL IN THE OTHER DIRECTION AND IT IS EXPECTED TO **SURVIVE**.
    # A suite in which every mutant dies cannot distinguish "the adversary is sharp" from "the
    # adversary reds out on anything", which is exactly the failure its own first draft had. So
    # one mutant is a deliberate NO-OP: deleting the belt-and-braces post-condition must change
    # no verdict, because the primary gate already refuses an empty witness. If M8 is KILLED, the
    # post-condition was load-bearing -- meaning the PRIMARY gate is wrong -- and that is a
    # finding about the rule, reported as `UNEXPECTED-KILL`.
    ("M8-post-condition-deleted--EXPECTED-TO-SURVIVE",
     "The belt-and-braces check that GREEN cannot be printed over an empty witness. Deleting it "
     "must NOT change any verdict; the primary gate already covers it. This mutant is the "
     "suite's negative control -- it proves the adversary does not simply red out on any edit.",
     [("    if not refused and (len(rep.witness) < 1 or rep.nil_files or rep.files < 1):",
       "    if False:")]),

    ("M9-affirmation-detection-narrowed-back-to-top-level-lists",
     "T259's partial walk. Detection must be TOTAL; narrowing it hides an affirmative verdict "
     "one container down.",
     [("    if isinstance(v, dict):\n        yield path, v\n        for k, x in v.items():\n"
       "            yield from walk_objects(x, path + \".\" + k)",
       "    if isinstance(v, dict):\n        yield path, v\n        for k, x in v.items():\n"
       "            if isinstance(x, list):\n                yield from walk_objects("
       "x, path + \".\" + k)")]),
]

# helper injected for M2 so the mutant can express T286's phrasing without a rewrite
M2_HELPER = '''

_LAST_DOC = [None]


def _t286_records(doc):
    """T286's coverage metric, restored verbatim: 'a record is a row reached through a LIST'."""
    out = []

    def walk(v, via_list=False):
        if isinstance(v, dict):
            if via_list:
                out.append(v)
            for x in v.values():
                walk(x, False)
        elif isinstance(v, list):
            for x in v:
                walk(x, True)
    walk(doc)
    return out
'''


def build(mid, edits, tmp: Path) -> Path:
    src = RULE.read_text(encoding="utf-8")
    for find, repl in edits:
        n = src.count(find)
        if n != 1:
            raise SystemExit("ERROR: mutant %s anchor occurs %d times, expected exactly 1:\n%r"
                             % (mid, n, find[:120]))
        src = src.replace(find, repl)
    if mid.startswith("M2"):
        src = src.replace('if __name__ == "__main__":', M2_HELPER + '\nif __name__ == "__main__":')
        src = src.replace("    sha, doc = read_once(path)",
                          "    sha, doc = read_once(path)\n    _LAST_DOC[0] = doc")
    p = tmp / (mid + ".py")
    p.write_text(src, encoding="utf-8")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()
    # INSIDE the repo -- the mutant must see the same `.git` ancestor the live rule sees.
    tmp = Path(tempfile.mkdtemp(prefix=".t292-mut-", dir=str(CAP)))
    # FOUR BUCKETS, NOT THREE. The first draft put the negative controls in `killed`, so the
    # summary read `10 killed, 0 SURVIVED` directly above two lines reading `SURVIVED`. That is
    # T259's FOUNDING DEFECT -- "the summary line above it said the opposite" -- reproduced in the
    # instrument written to grade the fix for it. Counted separately now.
    survived, killed, broken, nonviable, controls_held = [], [], [], [], []
    try:
        print("MUTANT KILL -- each mutant re-introduces ONE defect from the R-VPA lineage.")
        print("A mutant the adversary PASSES is a hole in the adversary, reported as SURVIVED.")
        print("=" * 96)
        # control: the unmutated rule must PASS, or nothing below means anything
        r = subprocess.run([sys.executable, str(HERE / "adversary_t292.py"),
                            "--rule", str(RULE), "--seeds", str(args.seeds),
                            "--legs-out", str(tmp / "control-legs.json")],
                           capture_output=True, text=True, timeout=3600)
        ctl = r.returncode
        head = [l for l in r.stdout.splitlines() if l.startswith("T292 ADVERSARY")]
        print("  CONTROL  unmutated rule -> adversary exit %d   %s"
              % (ctl, head[0] if head else "(no summary line)"))
        if ctl != 0:
            print("  CONTROL FAILED -- the adversary does not pass the rule it is grading; every "
                  "kill below is uninterpretable.")
        print()
        for mid, why, edits in MUTANTS:
            try:
                mp = build(mid, edits, tmp)
            except SystemExit as exc:
                broken.append((mid, str(exc)))
                print("  BROKEN   %-52s %s" % (mid, exc))
                continue
            syn = subprocess.run([sys.executable, "-c", "compile(open(%r).read(),%r,'exec')"
                                  % (str(mp), str(mp))], capture_output=True, text=True)
            if syn.returncode != 0:
                broken.append((mid, syn.stderr.strip()[-200:]))
                print("  BROKEN   %-52s does not compile" % mid)
                continue
            v_ok, v_rc, v_msg = viable(mp)
            if not v_ok:
                nonviable.append((mid, "rc=%s %s" % (v_rc, v_msg)))
                print("  NONVIABLE %-51s no probe line on the real evidence (rc=%s) -- a red "
                      "drive against it would be a TAUTOLOGY" % (mid, v_rc))
                continue
            r = subprocess.run([sys.executable, str(HERE / "adversary_t292.py"),
                                "--rule", str(mp), "--seeds", str(args.seeds),
                                "--legs-out", str(tmp / (mid + "-legs.json"))],
                               capture_output=True, text=True, timeout=3600)
            fails = [l.strip() for l in r.stdout.splitlines()
                     if l.strip().startswith("FAILED") or l.strip().startswith("SKIPPED")]
            lost = [l for l in r.stdout.splitlines() if l.startswith("LOST REFUSALS")]
            expect_survive = "EXPECTED-TO-SURVIVE" in mid
            if expect_survive:
                if r.returncode == 0:
                    controls_held.append(mid)
                    print("  SURVIVED %-52s adversary exit 0 -- AS REQUIRED (negative control)"
                          % mid)
                else:
                    survived.append((mid, "UNEXPECTED KILL: the post-condition is load-bearing, "
                                          "which means the PRIMARY gate is wrong. " + why))
                    print("  UNEXPECTED-KILL %-45s adversary exit %d  <-- FINDING ABOUT THE RULE"
                          % (mid, r.returncode))
                print("           why it matters: %s" % why)
                continue
            if r.returncode != 0:
                killed.append(mid)
                print("  KILLED   %-52s adversary exit %d, %d failing legs   [viable: %s]"
                      % (mid, r.returncode, len(fails), v_msg.split()[1] if " " in v_msg else "?"))
                print("           %s" % (lost[0] if lost else ""))
                for f in fails[:4]:
                    print("             %s" % f[:150])
            else:
                survived.append((mid, why))
                print("  SURVIVED %-52s adversary exit 0  <-- HOLE IN THE ADVERSARY" % mid)
            print("           why it matters: %s" % why)
        print()
        print("=" * 96)
        n_kill_targets = len([m for m in MUTANTS if "EXPECTED-TO-SURVIVE" not in m[0]])
        n_controls = len(MUTANTS) - n_kill_targets
        print("MUTANTS (%d total = %d kill targets + %d negative controls):"
              % (len(MUTANTS), n_kill_targets, n_controls))
        print("  KILLED as required            : %d of %d" % (len(killed), n_kill_targets))
        print("  NEGATIVE CONTROLS that SURVIVED as required : %d of %d"
              % (len(controls_held), n_controls))
        print("  SURVIVED but should NOT have  : %d   <-- each is a hole in the adversary"
              % len(survived))
        print("  NON-VIABLE                    : %d" % len(nonviable))
        print("  BROKEN                        : %d" % len(broken))
        for mid, why in survived:
            print("  SURVIVED  %s -- %s" % (mid, why))
        for mid, msg in nonviable:
            print("  NONVIABLE %s -- %s" % (mid, msg))
        for mid, err in broken:
            print("  BROKEN    %s -- %s" % (mid, err))
        rc = 0 if (not survived and not broken and not nonviable and ctl == 0
                   and len(killed) == n_kill_targets
                   and len(controls_held) == n_controls) else 1
        print("EXIT %d   (non-zero unless EVERY kill target died, EVERY negative control survived, "
              "no mutant was NON-VIABLE or broken, and the unmutated control passed)" % rc)
        return rc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
