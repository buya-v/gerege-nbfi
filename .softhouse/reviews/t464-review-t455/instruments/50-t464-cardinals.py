"""T464 — THE CARDINALS, RE-COUNTED UNDER A THIRD PRIMITIVE.

T455 measured the matrix as 11 cases / 22 rows / 9 argued, and the grader's invokers at T433's
tip as 14 files / 18 lines, decomposing to 11 / 14 pre-existing. Its two legs were `git grep`
and a python walk over `git ls-files`. This file shares neither file-listing command nor regex
engine with LEG 1, and uses `git ls-tree` rather than `git ls-files` so it does not share LEG
2's either: the corpus is read out of the COMMIT with `git show`, not off the working tree, so
a dirty checkout cannot flatter the count.

Definition of an INVOCATION LINE is T455's, restated verbatim so the two counts are comparable:
a tracked, non-`out/` line in a `.sh` or `.py` that either RUNS the grader
(`python3 ... <grader>`) or BINDS its path to a shell variable (`VAR=...<grader>`). Anything
else naming it is a MENTION.

    python3 50-t464-cardinals.py <repo> <ref> <drive.sh-relpath> <MATRIX.tsv-relpath> <t433-dir-prefix>

Every repo-relative path is an ARGUMENT, never a literal, so this file adds no dead-path row.

EXIT 0  every figure reproduced.  EXIT 1  a figure disagreed.  EXIT 3  REFUSED.
"""
import re
import subprocess
import sys

ROOT, REF, DRIVE_REL, MATRIX_REL, T433_PREFIX = sys.argv[1:6]
GRADER = "verify-capture-integrity.py"
fails = []


def show(rel):
    r = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (REF, rel)],
                       capture_output=True)
    if r.returncode != 0:
        print("REFUSED: %s is not in the tree at %s" % (rel, REF))
        sys.exit(3)
    return r.stdout.decode("utf-8", "replace")


def agree(label, a, b):
    if a == b:
        print("  OK   %-56s both legs say %s" % (label, a))
    else:
        print("  BAD  %-56s leg1=%s leg2=%s" % (label, a, b))
        fails.append(label)


print("############ T464 — THE CARDINALS, THIRD DERIVATION")
print("  ref = %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", REF],
                                    capture_output=True, text=True).stdout.strip())
print()
print("--- 1. THE MATRIX: HOW MANY CASES, HOW MANY ROWS, HOW MANY ARGUED? ----------------")
drive = show(DRIVE_REL)
cases_src = [ln.split()[1] for ln in drive.split("\n") if ln.startswith("run_case ")]
matrix = [ln for ln in show(MATRIX_REL).split("\n") if ln.strip()]
rows = matrix[1:]
cases_out = sorted({ln.split("\t")[0] for ln in rows})
print("      run_case invocations in the SOURCE : %d" % len(cases_src))
print("      distinct case names in the OUTPUT  : %d" % len(cases_out))
print("      data rows in MATRIX.tsv            : %d" % len(rows))
agree("matrix cardinality (source vs committed output)", len(cases_src), len(cases_out))
agree("row count is cases x 2 refs", len(rows), len(cases_src) * 2)
driven = [c for c in cases_out if c == "control" or c.startswith("f1-13b")]
print("      driven through the whole runner by T433 : %s" % driven)
print("      ARGUED = %d - %d = %d" % (len(cases_src), len(driven), len(cases_src) - len(driven)))
print("      T433 restated this as a 13-case matrix with eleven argued.")
print("      It is %d cases, %d rows, %d argued — T455's figures." % (len(cases_src), len(rows),
                                                                     len(cases_src) - len(driven)))
if (len(cases_src), len(rows), len(cases_src) - len(driven)) != (11, 22, 9):
    fails.append("matrix cardinals are not 11/22/9")
print()

print("--- 2. WHAT INVOKES THE GRADER, AT THIS REF? --------------------------------------")
run = re.compile(r"python3[^|;]*" + re.escape(GRADER))
bind = re.compile(r"^\s*[A-Za-z_]+=[^=]*" + re.escape(GRADER))
listing = subprocess.run(["git", "-C", ROOT, "ls-tree", "-r", "--name-only", REF],
                         capture_output=True, text=True, check=True).stdout.split("\n")
files, lines, mentions = {}, 0, 0
for rel in listing:
    if not rel or "/out/" in rel or not (rel.endswith(".sh") or rel.endswith(".py")):
        continue
    for ln in show(rel).split("\n"):
        if GRADER not in ln:
            continue
        mentions += 1
        if run.search(ln) or bind.search(ln):
            lines += 1
            files[rel] = files.get(rel, 0) + 1
own = {f: n for f, n in files.items() if f.startswith(T433_PREFIX)}
print("      invoking files   : %d" % len(files))
print("      invocation lines : %d" % lines)
print("      total mentions   : %d   (the figure a bare grep produces)" % mentions)
print("      of which T433's OWN instruments under %s:" % T433_PREFIX)
for f in sorted(own):
    print("          %-88s x%d" % (f, own[f]))
print("          -> %d files / %d lines" % (len(own), sum(own.values())))
pre_f, pre_l = len(files) - len(own), lines - sum(own.values())
print("      ==> PRE-EXISTING : %d files / %d lines" % (pre_f, pre_l))
print()
print("      THE LIST, PRINTED BESIDE THE COUNT (a count with no list is the '17' again):")
for f in sorted(files):
    print("          %-88s x%d%s" % (f, files[f], "  (T433's own)" if f in own else ""))
print()
if (len(files), lines) != (14, 18):
    fails.append("invoker totals are not 14/18")
if (pre_f, pre_l) != (11, 14):
    fails.append("pre-existing decomposition is not 11/14")
print("      LIMIT, STATED: this leg searches .sh and .py only, exactly as T455's two do.")
print("      An invoker in another language is invisible to all three. That is a property of")
print("      the SEARCH, not of the world, and it goes stale.")
print()
if fails:
    print("T464 CARDINALS: %d disagreement(s): %s" % (len(fails), fails))
    sys.exit(1)
print("T464 CARDINALS: 11 / 22 / 9, and 14 files / 18 lines -> 11 / 14 pre-existing.")
print("T448's 11 / 14 is confirmed a second time. EXIT 0")
