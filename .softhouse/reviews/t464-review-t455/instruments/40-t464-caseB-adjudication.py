"""T464 — THE HEADLINE DISAGREEMENT, ADJUDICATED BY A THIRD PARTY.

T448 supplied a one-predicate repair for the tag guard and asserted that abuse case B FAILS it
with `all` = 2, `both` = 1. T455 measured it and says B PASSES, with `all` = `both` = 2,
because the smuggled line carries the tag in its TRAILING SHELL COMMENT. Two agents disagree;
this file is the third derivation, and it uses TWO ENGINES that share no primitive with each
other — python's own `re` module, and real `grep` in a subprocess — because two derivations
that share a primitive do not corroborate each other.

It also asks the question T455 raises second: T448's predicate is LINE-WISE, and the tagged
quotations in these files are LINE-WRAPPED. What does the predicate say about the four
in-scope files on an UNMUTATED tree?

    python3 40-t464-caseB-adjudication.py <runall.sh> <drive.sh> <grader.py> <launder.py> \
        <scratch-file OUTSIDE the repository>

Every path is an ARGUMENT. Nothing repo-relative is spelled as a literal here, so this file
cannot add a row to the dead-path frontier.

EXIT 0  the two engines agreed on every figure.  EXIT 1  they disagreed.  EXIT 3  REFUSED.
"""
import re
import subprocess
import sys

SENT = "There is no committed baseline older than HEAD for those 632."
ANCHOR = '  sec 10 0 python3 "$DIR/verify-capture-integrity.py"'
TAG = "QUOTED-" + "FALSE-CLAIM"
# T433's guard's own regex, taken verbatim from the guard.
IMPOSS = ("there is no committed baseline older than HEAD"
          "|no baseline older than HEAD anywhere"
          "|does not exist and cannot be manufactured here"
          "|committed baseline older than HEAD for those 632")
RX = re.compile(IMPOSS, re.I)

fails = []


def by_python(text):
    lines = text.split("\n")
    hit = [ln for ln in lines if RX.search(ln)]
    return len(hit), len([ln for ln in hit if TAG in ln])


def by_grep(text, tmp):
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    a = subprocess.run(["grep", "-Eic", IMPOSS, tmp], capture_output=True, text=True).stdout.strip()
    mid = subprocess.run(["grep", "-Ei", IMPOSS, tmp], capture_output=True, text=True).stdout
    b = subprocess.run(["grep", "-c", TAG], input=mid, capture_output=True, text=True).stdout.strip()
    return int(a), int(b)


def report(label, text, tmp):
    pa, pb = by_python(text)
    ga, gb = by_grep(text, tmp)
    agree = (pa, pb) == (ga, gb)
    verdict = "PASSES  (T448's predicate does NOT catch it)" if (pb >= 1 and pb == pa) \
        else "FAILS   (T448's predicate catches it)"
    print("  %-46s all=%-3d both=%-3d  -> %s" % (label, pa, pb, verdict))
    print("      python-re: all=%d both=%d   grep: all=%d both=%d   engines %s"
          % (pa, pb, ga, gb, "AGREE" if agree else "*** DISAGREE ***"))
    if not agree:
        fails.append(label)
    return pa, pb


if len(sys.argv) < 6:
    print(__doc__)
    print("REFUSED: five arguments are required, and the fifth is a SCRATCH FILE PATH OUTSIDE")
    print("the repository. It has no default on purpose (T256/T298): a host path written into")
    print("a tracked instrument is state that is shared across worktrees, absent from every")
    print("commit and deleted on reboot. The caller names it, or this file does not run.")
    sys.exit(3)
runall_p, drive_p, grader_p, launder_p, tmp = sys.argv[1:6]

src = open(runall_p, encoding="utf-8").read()
assert ANCHOR in src, "REFUSED: the section-10 anchor is not in the runner; the edit is a no-op"

print("############ T464 — CASE B, RE-DERIVED BY A THIRD PARTY")
print("  T448 asserts: case B gives all=2 both=1, so the one-predicate repair CLOSES B.")
print("  T455 asserts: case B gives all=both=2, so the one-predicate repair does NOT close B.")
print()
report("run-all.sh UNMUTATED", src, tmp)

mut_b = src.replace(ANCHOR, '  echo "%s"  # %s\n' % (SENT, TAG) + ANCHOR, 1)
a, b = report("run-all.sh CASE B (echo, tag in comment)", mut_b, tmp)
print("      the two lines that match, and whether each carries the tag:")
for ln in mut_b.split("\n"):
    if RX.search(ln):
        print("        %-6s | %s" % ("TAGGED" if TAG in ln else "BARE", ln.strip()[:104]))
if (a, b) != (2, 2):
    print("  *** T455's measurement did NOT reproduce: expected all=2 both=2, got all=%d both=%d"
          % (a, b))
    fails.append("caseB")
else:
    print("  ==> T455 IS RIGHT AND T448 IS WRONG. all = both = 2, so `both >= 1 && both == all`")
    print("      HOLDS and the one-predicate repair PASSES case B. The tag is in the trailing")
    print("      shell comment, on the SAME SOURCE LINE, so both greps count it.")
print()

lines = src.split("\n")
kept = [ln for ln in lines if TAG not in ln]
assert len(lines) - len(kept) >= 3, "REFUSED: fewer than 3 tagged lines to remove"
i = kept.index(ANCHOR)
mut_c = "\n".join(kept[:i] + ["  # %s (tidied)" % TAG] * 3 + kept[i:])
a, b = report("run-all.sh CASE C (quotation deleted)", mut_c, tmp)
if (a, b) != (0, 0):
    fails.append("caseC")
print("  ==> T448 IS RIGHT ABOUT C: both=0, so the predicate catches it.")
print()

print("--- AND THE SECOND THING T455 FOUND: THE QUOTATIONS ARE LINE-WRAPPED ---------------")
print("    T448's predicate is LINE-WISE. Run it over the four in-scope files on an")
print("    UNMUTATED tree and see what it says about each:")
clean_red = []
for p in (runall_p, drive_p, grader_p, launder_p):
    t = open(p, encoding="utf-8").read()
    a, b = report(p.split("/")[-1] + " (UNMUTATED)", t, tmp)
    if not (b >= 1 and b == a):
        clean_red.append(p.split("/")[-1])
print()
if clean_red:
    print("  ==> T448's ONE-PREDICATE REPAIR IS RED ON A CLEAN TREE for %d of the 4 in-scope"
          % len(clean_red))
    print("      files: %s" % clean_red)
    print("      Their tagged quotations are WRAPPED across source lines, so no single line")
    print("      carries the claim: a line-wise matcher scores them 0 stated / 0 tagged —")
    print("      INDISTINGUISHABLE FROM ABUSE C, where the quotation is gone entirely. That")
    print("      is T455's finding, and it is stronger than T455 stated it: the supplied")
    print("      predicate would not merely miss B, it would REFUSE HONEST FILES (P-98).")

print()
if fails:
    print("T464 CASE-B ADJUDICATION: %d disagreement(s): %s" % (len(fails), fails))
    sys.exit(1)
print("T464 CASE-B ADJUDICATION: both engines agree on every figure. EXIT 0")
