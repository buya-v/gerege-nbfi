#!/bin/bash
# T467 / F-T464-3 -- THE STALE SENTENCE IN THE FILE WHOSE SUBJECT IS STALE SENTENCES.
#
# verify-capture-integrity.py's own docstring said, of boundary (iv-b2):
#     rename the file AND replace its bytes wholly and git records a genuine ADD at the tip,
#     "which lands in (iv-a): reported UNGRADED, exit 0"
# That was true until T455 closed (iv-a). At the ref where T464 read it, section 9 asserts
# `not f_at_tip`, so the outcome is EXIT 1 on the named assertion. T455 measured that itself,
# as its own case 5, and left the docstring saying exit 0.
#
# THE CORRECTED SENTENCE IS MEASURED, NOT INHERITED. Re-quoting T455's table would repeat the
# mistake in the other direction: a sentence about a measurement somebody else took. This file
# builds the (iv-b2) shape -- rename a post-fork observation AND replace its bytes wholly, in
# ONE commit, with the manifest row moved -- and reads the grader's exit code and the named
# assertion at the ref that ships the corrected docstring.
#
# THE MUTATION SHAPE IS T455's (its 20-t455-iva-close-drive.sh case 4/5) because it is the
# shape the docstring describes; the MEASUREMENT is taken here, at this ref, on these bytes.
#
# No host path and no repo-path literal: paths are assembled from S. A location that does not
# resolve is exit 3, never a skipped case.
#
#   T467_SRC=<repo>  T467_SCRATCH=<dir OUTSIDE the repo>  T467_OUT=<dir> \
#   T467_AFTER=<commit-ish carrying the corrected docstring> \
#   bash 30-t467-ivb2-consequence.sh
#
# EXIT 0  the sentence as corrected is what the tree does.  EXIT 1  it is not.  EXIT 3 REFUSED.
set -u

SRC="${T467_SRC:?T467_SRC must name the source repository}"
SCRATCH="${T467_SCRATCH:?T467_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T467_OUT:?T467_OUT must name the directory to write transcripts into}"
AFTER="${T467_AFTER:?T467_AFTER must name the commit-ish carrying the corrected docstring}"

S=".softhouse"
A2="$S/reviews/A2-11"
INT="$A2/verify-capture-integrity.py"
CAP="$S/capture/tierA-a2"
MAN="$CAP/MANIFEST.sha256"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t467-ivb2"
FAILURES=0

verdict() {
  if [ "$2" = "$3" ]; then echo "  OK   $1 = $2 (expected $3)"
  else echo "  BAD  $1 = $2, EXPECTED $3"; FAILURES=$((FAILURES + 1)); fi
}

prepare() {
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --force --detach "$AFTER" || return 1
  git -C "$D" reset --quiet --hard "$AFTER" || return 1
  git -C "$D" clean -qfdx || return 1
  [ -f "$D/$INT" ] || { echo "REFUSED: $INT absent at $AFTER" >&2; return 1; }
  [ -f "$D/$MAN" ] || { echo "REFUSED: $MAN absent at $AFTER" >&2; return 1; }
  git -C "$D" config user.email t467@softhouse.invalid || return 1
  git -C "$D" config user.name "T467 drive" || return 1
  return 0
}

grade() {
  ( cd "$D" && python3 "$INT" ) > "$OUT/ivb2-$1.txt" 2>&1
  echo $?
}

echo "############ T467 / F-T464-3 -- (iv-b2): WHAT ACTUALLY HAPPENS, AT THIS REF"
echo "  ref = $AFTER"
echo

# CALIBRATION FIRST (P-72): the clean tree is green, so the red below is bought by the case.
prepare || { echo "REFUSED: could not prepare $AFTER" >&2; exit 3; }
RC_CAL="$(grade 0-clean)"
ATTIP_CAL="$(grep -F -- 'ARM F GRADED ITS WHOLE POPULATION: ' "$OUT/ivb2-0-clean.txt" | tail -1 | awk '{print $(NF-1)}')"
case "$ATTIP_CAL" in ''|*[!0-9]*) ATTIP_CAL=UNPRINTED ;; esac
echo "  0  clean tree: exit=$RC_CAL  born-at-tip=$ATTIP_CAL"
verdict "0 the clean tree is GREEN" "$RC_CAL" 0

# THE (iv-b2) SHAPE: rename a post-fork observation and replace its bytes WHOLLY, in one
# commit, so git records an ADD rather than an R and the new path is born at the tip.
python3 - "$D" "$CAP" "$MAN" <<'PYEOF' || exit 3
import hashlib, os, subprocess, sys
root, cap, man = sys.argv[1], sys.argv[2], sys.argv[3]
fork = "12a7f8d9a3af4665fd5281a9f9c001d4f1276a53"


def tree(ref):
    out = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", ref, "--",
                          cap + "/out", cap + "/req"], capture_output=True, check=True)
    return set(out.stdout.decode().split())


post = sorted(tree("HEAD") - tree(fork))
if not post:
    print("REFUSED: no post-fork observation to rename; the case cannot be built.")
    sys.exit(3)
src = post[len(post) // 2]
dst = os.path.dirname(src) + "/A2-997-t467-renamed-and-rewritten.txt"
body = (b"HTTP/1.1 200 OK\r\n\r\n" + b'{"t467":"wholly new bytes, no similarity to the '
        b'original, so git records an ADD and not an R"}\n' + b"y" * 4096 + b"\n")
subprocess.run(["git", "-C", root, "rm", "-q", "--", src], check=True)
with open(os.path.join(root, dst), "wb") as fh:
    fh.write(body)
srel, drel = src.split("/tierA-a2/", 1)[1], dst.split("/tierA-a2/", 1)[1]
mp = os.path.join(root, man)
with open(mp, "r", encoding="utf-8") as fh:
    rows = [r for r in fh.read().rstrip("\n").split("\n") if not r.endswith("  " + srel)]
rows.append("%s  %s" % (hashlib.sha256(body).hexdigest(), drel))
with open(mp, "w", encoding="utf-8") as fh:
    fh.write("\n".join(sorted(rows)) + "\n")
print("renamed %s -> %s with WHOLLY NEW BYTES, manifest row moved" % (srel, drel))
PYEOF
git -C "$D" add -A -- "$CAP" || exit 3
git -C "$D" commit -q -m "T467 drive: (iv-b2) rename + whole rewrite in one commit" || exit 3

# git's OWN account of the change, so the premise of the sentence is measured too: the claim
# is that git records an ADD (not an R), which is what puts the file in (iv-a).
ADDS="$(git -C "$D" show --name-status --diff-filter=A --format= HEAD | grep -c '^A')"
RENAMES="$(git -C "$D" show --name-status --diff-filter=R --format= HEAD | grep -c '^R')"
echo "  1  git's account of the mutating commit: ADDs=$ADDS  renames=$RENAMES"
verdict "1 git records an ADD, x1 -- the PREMISE of the sentence" "$ADDS" 1
verdict "1 and NOT a rename" "$RENAMES" 0

RC="$(grade 1-ivb2)"
NAMED="$(grep -c -F -- 'FAIL  ARM F GRADED ITS WHOLE POPULATION' "$OUT/ivb2-1-ivb2.txt")"
UNGRADED="$(grep -c -F -- 'UNGRADED-BORN-AT-TIP' "$OUT/ivb2-1-ivb2.txt")"
echo "  2  the (iv-b2) tree: grader exit=$RC  named assertion fired=$NAMED  UNGRADED lines=$UNGRADED"
verdict "2 THE OUTCOME IS EXIT 1, not exit 0 as the docstring said" "$RC" 1
verdict "2 on the named section-9 assertion, x1" "$NAMED" 1
echo "     (the observation is still REPORTED UNGRADED -- that half of the old sentence was"
echo "      right and is kept. What moved is the CONSEQUENCE: reporting it is no longer a pass.)"
echo

# THE CORRECTED SENTENCE IS IN THE SHIPPED FILE, AND THE STALE ONE IS NOT. A correction that
# lives only in a handoff is a correction the next reader of the file will not see.
STALE="$(grep -c -F -- 'lands in (iv-a): reported UNGRADED, exit 0' "$D/$INT")"
CORRECTED="$(grep -c -F -- 'EXIT 1 on the named assertion, not exit 0' "$D/$INT")"
echo "  3  the docstring itself: stale sentence x$STALE  corrected sentence x$CORRECTED"
verdict "3 the stale sentence is GONE from the shipped file" "$STALE" 0
verdict "3 and the corrected one is present, x1" "$CORRECTED" 1
echo

echo "############ COVERAGE -- the graded bytes, named (T467 / F-T464-5)"
prepare >/dev/null || exit 3
echo "  graded ref resolves to: $(git -C "$D" rev-parse HEAD)"
printf '  %-62s blob %s\n' "$INT" "$(git -C "$D" rev-parse "HEAD:$INT")"
printf '  %-62s last touched at this ref by %s\n' "" "$(git -C "$D" log -1 --format='%h %s' -- "$INT")"
echo

if [ "$FAILURES" -ne 0 ]; then
  echo "T467 (iv-b2) DRIVE: FAIL -- $FAILURES case(s) did not behave as recorded."
  exit 1
fi
echo "T467 (iv-b2) DRIVE: PASS. git records an ADD, the file lands in (iv-a), and at this ref"
echo "that is EXIT 1 on the named assertion -- which is what the docstring now says."
exit 0
