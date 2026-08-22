#!/usr/bin/env python3
"""T252 instrument 40 -- DRIVE C6 RED, ON SHAPES AND TYPES IT WAS NOT BUILT FROM.

P-76 in its sharpest form, which is the lesson T252 inherits from T248: T248's driver drove
both arms of a rule as STRINGS and the defect turned out to be in the TYPES -- `None`,
`False`, `0`, `[]`, `{}` all stringify truthy. A rule tested only on the specimen it was
written from tests the author's memory, not the rule.

C6 was written from ONE specimen: `cd "$R"` at rederive-provenance.sh:24, where `R` is a
literal absolute path assigned at :11 and the shell runs under `set -u` with no `-e`. Every
RED row below is deliberately NOT that:

  SHAPES not designed around -- the VERB and the SYNTACTIC CATEGORY of the entry:
    R1  `pushd` -- a different builtin
    R2  `git -C DIR` -- the entry is an ARGUMENT to a program, not a shell builtin at all
    R3  `--work-tree=DIR` -- the entry is a FLAG
    R4  `cd "${V}/sub"` -- brace form, through a variable, with a subpath appended

  TYPES not designed around -- and this is the P-76 arm proper, because "type" here is not
  the type of a python value but the type of the THING BEING TESTED:
    R5  errexit is a STATE THAT CHANGES, not a string that is present or absent. `set -e`
        ... `set +e` ... `cd DEAD`. Reading the file for the substring `set -e` would call a
        DISABLED shell option a protection. This is the exact shape of T248's bug: the
        truthy-looking token whose value is false.
    R6  `|| true` -- an arm that HAS the swallowing syntax and is not fatal. A rule that
        keyed on "is there a `||`" rather than on "does it terminate" passes this and is
        wrong.
    R7  THE CLAIM'S OWN TYPE. C2 keys on a SENTENCE; T252's brief proposed keying on a COUNT.
        R7's only output after the dead entry is `{"violations": []}` -- an EMPTY STRUCTURED
        VALUE. Not English, not a number, not a printable claim at all, and read by a machine
        rather than a person. C6 must still fire, because C6 never looks at output. This row
        is what turns "C6 is blind to words" from an assumption into a measurement.

  GREEN rows (C6 must NOT fire). P-72's trap is live here on purpose: G1 and G2 CONTAIN the
  red entry line verbatim (see DEAD below) and differ only by the thing that makes them safe.
  A negative that is a substring of the positive matches both and proves nothing, so "green
  = red PLUS a guard" is the only arrangement in which a non-firing result means anything.
  [The dead path is written ONCE, as the DEAD constant, and never spelled out in this prose:
  a path literal in a docstring after the word "cd" is a C1 hit in this very file, which is
  how the first draft of this instrument put itself in TIER 3.]

  A KNOWN LIMIT is also driven, and reported as a limit rather than as a pass, because
  recording it is worth more than the false comfort of a green row.

MECHANISM: variants are planted in a scratch directory, staged with `git add -N` so
`git ls-files` -- the linter's own corpus selector -- can see them, linted, and then
UNSTAGED AND DELETED in a `finally`. Nothing planted here is ever committed: a tracked red
file would join the frontier and break the very pin this task is moving.

ENGINE (P-33/P-53): `python3` + `git` plumbing only. No text search engine is used to decide
any row; each row is decided by the linter's own JSON.
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
assert ROOT and os.path.isdir(ROOT), "T252-40 ABORT: not in a git work tree"
os.chdir(ROOT)
LINT = ".softhouse/capture/t238-failopen/instruments/50-failopen-lint.py"
SCRATCH = ".softhouse/capture/t252-tier3/evidence/red-drive-scratch"
DEAD = "/nonexistent/t252/no-such-corpus"

SEARCH = 'git grep -n -F "needle" -- . | sed "s/^/  /"\n'

VARIANTS = [
    # (id, expect_c6, headline, body)
    ("R1", True, "pushd -- a builtin C6 was not written from",
     "#!/usr/bin/env bash\nset -u\npushd %s\n%secho done\n" % (DEAD, SEARCH)),
    ("R2", True, "git -C DIR -- the entry is an ARGUMENT to a program, not a shell builtin",
     "#!/usr/bin/env bash\nset -u\ngit -C %s grep -n -F 'needle' -- . \nprintf 'done\\n'\n" % DEAD),
    ("R3", True, "--work-tree=DIR -- the entry is a FLAG",
     "#!/usr/bin/env bash\nset -u\ngit --work-tree=%s grep -n -F 'needle' -- .\n%s" % (DEAD, SEARCH)),
    ("R4", True, "cd \"${V}/sub\" -- brace form, through a variable, with a subpath",
     "#!/usr/bin/env bash\nset -u\nV=%s\ncd \"${V}/sub\"\n%secho done\n" % (DEAD, SEARCH)),
    ("R5", True, "TYPE: errexit is a STATE THAT CHANGES. `set -e` then `set +e` then cd.",
     "#!/usr/bin/env bash\nset -euo pipefail\necho 'the -e above is real, and then:'\n"
     "set +e\ncd %s\n%secho done\n" % (DEAD, SEARCH)),
    ("R6", True, "`|| true` -- has the swallowing syntax, is NOT fatal",
     "#!/usr/bin/env bash\nset -u\ncd %s || true\n%secho done\n" % (DEAD, SEARCH)),
    ("R7", True, "TYPE: the CLAIM is an EMPTY STRUCTURED VALUE -- no sentence, no count, no words",
     "#!/usr/bin/env bash\nset -u\ncd %s\n%s"
     "python3 -c 'import json,sys; sys.stdout.write(json.dumps({\"violations\": [], \"n\": 0}))'\n"
     % (DEAD, SEARCH)),
    ("G1", False, "the red string PLUS a fatal arm (`|| exit 1`) -- P-72: green CONTAINS red",
     "#!/usr/bin/env bash\nset -u\ncd %s || exit 1\n%secho done\n" % (DEAD, SEARCH)),
    ("G2", False, "the red string PLUS errexit in force -- P-72: green CONTAINS red",
     "#!/usr/bin/env bash\nset -euo pipefail\ncd %s\n%secho done\n" % (DEAD, SEARCH)),
    ("G3", False, "the file OWNS the path (`mkdir -p` then cd) -- scratch, not corpus",
     "#!/usr/bin/env bash\nset -u\nmkdir -p %s\ncd %s\n%secho done\n" % (DEAD, DEAD, SEARCH)),
    ("G4", False, "the path EXISTS (/tmp) -- a dead-path rule must not fire on a live path",
     "#!/usr/bin/env bash\nset -u\ncd /tmp\n%secho done\n" % SEARCH),
    ("G5", False, "NARRATION: the dead `cd` is inside an echo, not executed",
     "#!/usr/bin/env bash\nset -u\necho \"cd %s\"\n%secho done\n" % (DEAD, SEARCH)),
    ("L1", False, "KNOWN LIMIT: same dead `cd`, but the file is NOT a repo-wide search "
                  "instrument, so the POPULATION SELECTOR never offers it to any rule",
     "#!/usr/bin/env bash\nset -u\ncd %s\ncat somefile\necho done\n" % DEAD),
]


def lint_all():
    j = "/tmp/t252-reddrive.json"
    r = subprocess.run([sys.executable, LINT], capture_output=True, text=True,
                       env=dict(os.environ, FAILOPEN_LINT_JSON=j))
    d = json.load(open(j))
    by = {}
    for e in d["detail"]:
        by[e["file"]] = [(c, i, m) for c, i, m in e["violations"]]
    # THREE fields, not two: `FAILOPEN-FRONTIER <TIER> <path>`. The first draft of this line
    # split into two and compared "TIER1B .softhouse/..." against a bare path, so every RED row
    # read "on frontier: False" while the same row read "in TIER 1B: True" -- a self-
    # contradicting probe, and a FALSE NEGATIVE printed by this instrument about the very
    # property T252 exists to check. Caught because the two columns disagreed; kept in the
    # comment because a probe that once lied is worth a sentence.
    front = set(l.split(None, 2)[2] for l in r.stdout.splitlines()
                if l.startswith("FAILOPEN-FRONTIER "))
    tier1b = set(d.get("entering", []))
    return by, front, tier1b, r.returncode


print("T252 -- C6 RED DRIVE")
print("commit : %s" % subprocess.run(["git", "rev-parse", "HEAD"],
                                     capture_output=True, text=True).stdout.strip())
print("dead   : %s   exists now? %s" % (DEAD, os.path.exists(DEAD)))
assert not os.path.exists(DEAD), "T252-40 ABORT: the 'dead' path EXISTS; every row below would be a lie."
print()

paths = []
try:
    os.makedirs(SCRATCH, exist_ok=True)
    for vid, _exp, _hl, body in VARIANTS:
        p = os.path.join(SCRATCH, "%s.sh" % vid)
        open(p, "w", encoding="utf-8").write(body)
        paths.append(p)
    subprocess.run(["git", "add", "-N"] + paths, check=True)
    seen = subprocess.run(["git", "ls-files", SCRATCH], capture_output=True, text=True).stdout.split()
    print("### PLANTED AND VISIBLE TO THE LINTER'S OWN CORPUS SELECTOR (`git ls-files`)")
    print("  planted: %d   visible: %d   <-- BOTH TERMS (P-67); if these differ the drive is void"
          % (len(paths), len(seen)))
    assert len(seen) == len(paths), "T252-40 ABORT: planted files are not in `git ls-files`"
    print()

    by, front, tier1b, rc = lint_all()
    print("### RESULTS  (C6 = did the new rule fire? expected vs measured)")
    print("  %-4s %-8s %-8s %-9s %s" % ("id", "EXPECT", "C6?", "VERDICT", "what it tests"))
    bad = 0
    for vid, exp, hl, _body in VARIANTS:
        p = os.path.join(SCRATCH, "%s.sh" % vid)
        vs = by.get(p, [])
        got = any(c == "C6" for c, _i, _m in vs)
        ok = (got == exp)
        if vid == "L1":
            ok = (got is False)          # a limit, recorded, not a pass to be proud of
        if not ok:
            bad += 1
        print("  %-4s %-8s %-8s %-9s %s" % (vid, "FIRE" if exp else "quiet",
                                            "FIRED" if got else "quiet",
                                            "OK" if ok else "*** WRONG ***", hl))
        for c, i, m in vs:
            if c in ("C6",):
                print("           %s :%s %s" % (c, i, m[:150]))
    print()
    print("  rows wrong: %d   (must be 0)" % bad)
    print()

    print("### DOES EACH RED ROW REACH THE FRONTIER? (a detection that changes no tier is not a gate)")
    for vid, exp, _hl, _b in VARIANTS:
        p = os.path.join(SCRATCH, "%s.sh" % vid)
        print("  %-4s on frontier: %-5s   in TIER 1B: %-5s"
              % (vid, str(p in front), str(p in tier1b)))
    print()
    print("### THE KNOWN LIMIT, STATED AS A LIMIT (P-66/P-70: this is a statement about the rule)")
    p = os.path.join(SCRATCH, "L1.sh")
    print("  L1 carries the SAME non-fatal dead `cd` as R7 and C6 does not fire, because the file")
    print("  contains no `git grep` / `git ls-files` / `grep -r` and RE_REPOWIDE therefore never")
    print("  admits it. That is T248's own P-76 addendum -- a rule's blind spots live in its")
    print("  POPULATION SELECTOR as much as in its conditions -- and C6 inherits that selector")
    print("  unchanged. It is recorded here as the next widening, not discovered later as a defect.")
    print("  L1 in linter output at all: %s" % (p in by))
    print()
    print("### LINTER EXIT WITH THE RED FILES PLANTED: %d  (1 = violations found)" % rc)
    sys.exit(0 if bad == 0 else 1)
finally:
    if paths:
        subprocess.run(["git", "rm", "-q", "--cached", "--force"] + paths,
                       capture_output=True)
    shutil.rmtree(SCRATCH, ignore_errors=True)
    left = subprocess.run(["git", "ls-files", SCRATCH], capture_output=True, text=True).stdout.split()
    st = subprocess.run(["git", "status", "--porcelain", SCRATCH],
                        capture_output=True, text=True).stdout.strip()
    print("### CLEANUP -- nothing planted may survive; a tracked red file would break the pin")
    print("  scratch dir exists : %s" % os.path.isdir(SCRATCH))
    print("  still in ls-files  : %d" % len(left))
    print("  git status residue : %r" % st)
