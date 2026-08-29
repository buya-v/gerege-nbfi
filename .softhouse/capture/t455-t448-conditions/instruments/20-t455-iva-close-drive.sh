#!/bin/bash
# T455 / C-T448-1 — THE (iv-a) FAIL-OPEN, DRIVEN BOTH WAYS, WITH THE CLEAN-TREE CONTROL.
#
# T433 disclosed (iv-a) — a fabricated post-fork observation added AT THE TIP with a matching
# MANIFEST.sha256 row — as an open fail-open, and wrote that it was "not closable by internal
# consistency". T448 said that conflates DETECTING a fabrication (external, and T433 is right)
# with REFUSING TO EXIT 0 OVER A POPULATION THE ARM DID NOT MEASURE (internal). This file
# establishes the second half by measurement rather than by agreement.
#
# WHAT IS ACTUALLY BEING TESTED: the difference between two refs of ONE shipped file,
# `.softhouse/reviews/A2-11/verify-capture-integrity.py`. Nothing here is a mock.
#
#   BEFORE  the ref WITHOUT T455's close      (ARM F prints born-at-tip, nothing asserts it)
#   AFTER   the ref WITH it                   (section 9 fails on an unadjudicated born-at-tip)
#
# THE LOAD-BEARING CASE IS THE CONTROL, NOT THE CATCH. A guard that reddens honest trees is a
# freeze, not a close; case 1 and case 6 exist so "it now goes red" cannot be bought by
# "it now always goes red".
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298). Every location is a required parameter and
# a value that does not resolve is exit 3 — never a skipped case, never a pass.
#
#   T455_SRC=<repo to clone>  T455_SCRATCH=<dir OUTSIDE the repo>  T455_OUT=<transcript dir> \
#   T455_BEFORE=<commit-ish without the close>  T455_AFTER=<commit-ish with it> \
#   bash 20-t455-iva-close-drive.sh
#
# ENGINE (P-33/P-53): every assertion is an exit code or a `grep -c -F` fixed-string count.
# No regex dialect is load-bearing. Digests are computed by python3's hashlib, never by a
# host tool whose flags differ between platforms.
#
# EXIT 0  every case produced the recorded outcome.
# EXIT 1  a case did not — the finding is printed by name.
# EXIT 3  REFUSED: the harness could not measure. NEVER read as a pass.
set -u

SRC="${T455_SRC:?T455_SRC must name the source repository}"
SCRATCH="${T455_SCRATCH:?T455_SCRATCH must name a scratch directory OUTSIDE the repository}"
OUT="${T455_OUT:?T455_OUT must name the directory to write transcripts into}"
BEFORE="${T455_BEFORE:?T455_BEFORE must name a commit-ish WITHOUT the (iv-a) close}"
AFTER="${T455_AFTER:?T455_AFTER must name a commit-ish WITH the (iv-a) close}"

INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
CAP=".softhouse/capture/tierA-a2"
MAN="$CAP/MANIFEST.sha256"
FAB="$CAP/out/A2-999-t455-fabricated-at-tip.txt"

mkdir -p "$OUT" "$SCRATCH" || exit 3
D="$SCRATCH/t455-iva"
FAILURES=0

echo "############ T455 — (iv-a) BORN AT THE TIP: the FAIL-OPEN, closed and controlled"
echo "  BEFORE = $BEFORE"
echo "  AFTER  = $AFTER"
echo

prepare() {   # prepare <ref>
  local ref="$1"
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 1
    git clone --quiet --shared "$SRC" "$D" || return 1
  fi
  git -C "$D" checkout --quiet --detach "$ref" || return 1
  git -C "$D" reset --quiet --hard "$ref" || return 1
  git -C "$D" clean -qfdx || return 1
  # A ref that does not carry the grader cannot be graded, and a missing file must never be
  # read as "the case did not fire".
  [ -f "$D/$INT" ] || { echo "REFUSED: $INT absent at $ref" >&2; return 1; }
  [ -f "$D/$MAN" ] || { echo "REFUSED: $MAN absent at $ref" >&2; return 1; }
  git -C "$D" config user.email t455@softhouse.invalid || return 1
  git -C "$D" config user.name "T455 drive" || return 1
  return 0
}

grade() {     # grade <case-name> ; echoes the grader's exit code
  local name="$1" rc
  ( cd "$D" && python3 "$INT" ) > "$OUT/iva-$name.txt" 2>&1
  rc=$?
  echo "$rc"
}

field() {     # field <case-name> <fixed-string prefix> ; echoes the trailing integer or UNPRINTED
  local v
  v="$(grep -F -- "$2" "$OUT/iva-$1.txt" | tail -1 | awk '{print $NF}')"
  # ABSENCE IS NOT ZERO (P-84). A line that never printed means the arm did not run, and an
  # unset variable must never be read as a clean number.
  case "$v" in
    ''|*[!0-9]*) echo "UNPRINTED" ;;
    *) echo "$v" ;;
  esac
}

verdict() {   # verdict <label> <got> <want>
  if [ "$2" = "$3" ]; then
    echo "  OK   $1 = $2 (expected $3)"
  else
    echo "  BAD  $1 = $2, EXPECTED $3"
    FAILURES=$((FAILURES + 1))
  fi
}

# --- the two mutations, as python string/byte surgery so no shell quoting is load-bearing ---
fabricate_at_tip() {
  python3 - "$D" "$FAB" "$MAN" <<'PYEOF' || return 1
import hashlib, os, sys
root, fab, man = sys.argv[1], sys.argv[2], sys.argv[3]
body = (b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
        b'{"t455":"FABRICATED AT THE TIP — this file was never observed from any oracle"}\n')
p = os.path.join(root, fab)
if os.path.exists(p):
    print("REFUSED: %s already exists; the case would not be a NEW birth." % fab)
    sys.exit(3)
with open(p, "wb") as fh:
    fh.write(body)
rel = fab.split("/tierA-a2/", 1)[1]
mp = os.path.join(root, man)
with open(mp, "r", encoding="utf-8") as fh:
    rows = fh.read().rstrip("\n").split("\n")
rows.append("%s  %s" % (hashlib.sha256(body).hexdigest(), rel))
with open(mp, "w", encoding="utf-8") as fh:
    fh.write("\n".join(sorted(rows)) + "\n")
print("fabricated %s and LAUNDERED its manifest row" % rel)
PYEOF
  git -C "$D" add -A -- "$CAP" || return 1
  git -C "$D" commit -q -m "T455 drive: fabricated observation added AT THE TIP, manifest laundered" || return 1
  return 0
}

rename_and_rewrite() {
  # (iv-b2): rename a post-fork observation AND replace its bytes wholly, so git records a
  # genuine ADD at the tip rather than a rename — which lands in (iv-a) by the other route.
  python3 - "$D" "$CAP" "$MAN" <<'PYEOF' || return 1
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
dst = os.path.dirname(src) + "/A2-998-t455-renamed-and-rewritten.txt"
body = (b"HTTP/1.1 200 OK\r\n\r\n" + b'{"t455":"wholly new bytes, no similarity to the '
        b'original, so git records an ADD and not an R"}\n' + b"x" * 4096 + b"\n")
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
  git -C "$D" add -A -- "$CAP" || return 1
  git -C "$D" commit -q -m "T455 drive: (iv-b2) rename + whole rewrite in one commit" || return 1
  return 0
}

adjudicate_the_tip_entry() {
  # Record the fabricated file in ARM_F_BORN_AT_TIP_ADJUDICATED by name AND digest. This is
  # what a HUMAN does for a legitimately new capture, and it must take the grader back to 0 —
  # otherwise the close is a freeze on every capture-adding commit.
  python3 - "$D" "$INT" "$FAB" <<'PYEOF' || return 1
import hashlib, os, sys
root, intp, fab = sys.argv[1], sys.argv[2], sys.argv[3]
name = fab.split("/tierA-a2/", 1)[1]
with open(os.path.join(root, fab), "rb") as fh:
    digest = hashlib.sha256(fh.read()).hexdigest()
p = os.path.join(root, intp)
with open(p, "r", encoding="utf-8") as fh:
    src = fh.read()
anchor = "ARM_F_BORN_AT_TIP_ADJUDICATED = {}"
if anchor not in src:
    print("REFUSED: the adjudication table is not in its expected empty form; edit is a no-op.")
    sys.exit(3)
src = src.replace(anchor, 'ARM_F_BORN_AT_TIP_ADJUDICATED = {\n    "%s": "%s",\n}'
                  % (name, digest), 1)
with open(p, "w", encoding="utf-8") as fh:
    fh.write(src)
print("adjudicated %s -> %s" % (name, digest))
PYEOF
  return 0
}

move_the_adjudicated_bytes() {
  python3 - "$D" "$FAB" "$MAN" <<'PYEOF' || return 1
import hashlib, os, sys
root, fab, man = sys.argv[1], sys.argv[2], sys.argv[3]
p = os.path.join(root, fab)
with open(p, "ab") as fh:
    fh.write(b"T455-MUTATION-AFTER-ADJUDICATION\n")
with open(p, "rb") as fh:
    digest = hashlib.sha256(fh.read()).hexdigest()
rel = fab.split("/tierA-a2/", 1)[1]
mp = os.path.join(root, man)
with open(mp, "r", encoding="utf-8") as fh:
    rows = [r for r in fh.read().rstrip("\n").split("\n") if not r.endswith("  " + rel)]
rows.append("%s  %s" % (digest, rel))
with open(mp, "w", encoding="utf-8") as fh:
    fh.write("\n".join(sorted(rows)) + "\n")
print("mutated the ADJUDICATED bytes and relaundered its row -> %s" % digest)
PYEOF
  return 0
}

# =========================================================================================
# CASE 1 — CALIBRATION. The grader is GREEN on an unmutated clone at BEFORE.
# Without this every "it went red" below would be free (P-72).
# =========================================================================================
prepare "$BEFORE" || { echo "REFUSED: could not prepare $BEFORE" >&2; exit 3; }
RC1="$(grade 1-control-BEFORE)"
G1="$(field 1-control-BEFORE 'GRADED against a birth blob older than HEAD')"
T1="$(field 1-control-BEFORE 'UNGRADED, born AT THE TIP (boundary iv-a)')"
echo "  1 CONTROL at BEFORE, clean tree            grader exit = $RC1  graded=$G1 at-tip=$T1"
verdict "1 grader exit on a clean tree at BEFORE" "$RC1" 0
if [ "$G1" = "UNPRINTED" ] || [ "$G1" = "0" ]; then
  echo "REFUSED: ARM F's GRADED line is $G1 at BEFORE. Absence is not zero and zero is not a" >&2
  echo "REFUSED: measurement; no verdict from this run is interpretable." >&2
  exit 3
fi
echo

# =========================================================================================
# CASE 2 — THE FAIL-OPEN, REPRODUCED AT BEFORE. A fabricated observation born at the tip,
# with its manifest row laundered in the same commit. Expect exit 0: T433's disclosure.
# =========================================================================================
prepare "$BEFORE" || { echo "REFUSED: could not prepare $BEFORE" >&2; exit 3; }
fabricate_at_tip || { echo "REFUSED: could not build the (iv-a) case" >&2; exit 3; }
RC2="$(grade 2-fabricated-BEFORE)"
T2="$(field 2-fabricated-BEFORE 'UNGRADED, born AT THE TIP (boundary iv-a)')"
N2="$(grep -c -F -- 'UNGRADED-BORN-AT-TIP' "$OUT/iva-2-fabricated-BEFORE.txt")"
echo "  2 FABRICATED at the tip, at BEFORE         grader exit = $RC2  at-tip=$T2 named=$N2"
verdict "2 the fail-open reproduces at BEFORE (exit 0 over an unmeasured row)" "$RC2" 0
verdict "2 ARM F PRINTS it, which is all BEFORE does" "$T2" 1
echo

# =========================================================================================
# CASE 3 — THE SAME TREE AT AFTER. One check() is the whole difference. Expect exit 1.
# =========================================================================================
prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER" >&2; exit 3; }
fabricate_at_tip || { echo "REFUSED: could not build the (iv-a) case at AFTER" >&2; exit 3; }
RC3="$(grade 3-fabricated-AFTER)"
T3="$(field 3-fabricated-AFTER 'UNGRADED, born AT THE TIP (boundary iv-a)')"
A3="$(grep -c -F -- 'FAIL  ARM F GRADED ITS WHOLE POPULATION' "$OUT/iva-3-fabricated-AFTER.txt")"
echo "  3 FABRICATED at the tip, at AFTER          grader exit = $RC3  at-tip=$T3 named-assertion=$A3"
verdict "3 the grader REFUSES to pass over a row ARM F did not measure" "$RC3" 1
verdict "3 it fails on the NAMED assertion, x1 — not on some other check" "$A3" 1
echo

# =========================================================================================
# CASE 4 — (iv-b2), THE OTHER ROUTE INTO (iv-a), AT BEFORE. Expect exit 0.
# =========================================================================================
prepare "$BEFORE" || { echo "REFUSED: could not prepare $BEFORE" >&2; exit 3; }
rename_and_rewrite || { echo "REFUSED: could not build the (iv-b2) case" >&2; exit 3; }
RC4="$(grade 4-ivb2-BEFORE)"
T4="$(field 4-ivb2-BEFORE 'UNGRADED, born AT THE TIP (boundary iv-a)')"
echo "  4 (iv-b2) rename+whole rewrite, at BEFORE  grader exit = $RC4  at-tip=$T4"
verdict "4 (iv-b2) lands in (iv-a) and passes at BEFORE" "$RC4" 0
verdict "4 exactly one row is born at the tip" "$T4" 1
echo

# =========================================================================================
# CASE 5 — (iv-b2) AT AFTER. The same close catches the same hole by the other route.
# =========================================================================================
prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER" >&2; exit 3; }
rename_and_rewrite || { echo "REFUSED: could not build the (iv-b2) case at AFTER" >&2; exit 3; }
RC5="$(grade 5-ivb2-AFTER)"
A5="$(grep -c -F -- 'FAIL  ARM F GRADED ITS WHOLE POPULATION' "$OUT/iva-5-ivb2-AFTER.txt")"
echo "  5 (iv-b2) rename+whole rewrite, at AFTER   grader exit = $RC5  named-assertion=$A5"
verdict "5 (iv-b2) is refused at AFTER too" "$RC5" 1
verdict "5 by the same named assertion" "$A5" 1
echo

# =========================================================================================
# CASE 6 — THE CONTROL THAT MAKES THE CLOSE WORTH LANDING. A CLEAN tree at AFTER must still
# be GREEN, with the whole population graded and nothing at the tip. A close that reddens
# honest trees is a freeze, not a close.
# =========================================================================================
prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER" >&2; exit 3; }
RC6="$(grade 6-control-AFTER)"
G6="$(field 6-control-AFTER 'GRADED against a birth blob older than HEAD')"
T6="$(field 6-control-AFTER 'UNGRADED, born AT THE TIP (boundary iv-a)')"
P6="$(field 6-control-AFTER 'post-fork population (HEAD minus the fork sha)')"
echo "  6 CONTROL at AFTER, clean tree             grader exit = $RC6  pop=$P6 graded=$G6 at-tip=$T6"
verdict "6 THE CLOSE COSTS NOTHING: a clean tree still exits 0 at AFTER" "$RC6" 0
verdict "6 and the graded count is unchanged from the BEFORE control" "$G6" "$G1"
verdict "6 with nothing born at the tip" "$T6" 0
echo

# =========================================================================================
# CASE 7 — THE ADJUDICATION TABLE, DRIVEN BOTH WAYS. A legitimately new capture is recorded
# by name AND digest and the grader returns to 0; then the adjudicated BYTES are changed and
# it goes red again. A table that could only ever say yes would be the fail-open re-spelled.
# =========================================================================================
prepare "$AFTER" || { echo "REFUSED: could not prepare $AFTER" >&2; exit 3; }
fabricate_at_tip || { echo "REFUSED: could not build the (iv-a) case for case 7" >&2; exit 3; }
adjudicate_the_tip_entry || { echo "REFUSED: could not adjudicate the entry" >&2; exit 3; }
RC7A="$(grade 7a-adjudicated-AFTER)"
J7="$(grep -c -F -- 'ADJUDICATED-BORN-AT-TIP' "$OUT/iva-7a-adjudicated-AFTER.txt")"
echo "  7a ADJUDICATED by name+digest, at AFTER    grader exit = $RC7A  adjudicated-lines=$J7"
verdict "7a an adjudicated born-at-tip capture is accepted" "$RC7A" 0
verdict "7a and it is NAMED as adjudicated, not silently folded into the equal count" "$J7" 1
move_the_adjudicated_bytes || { echo "REFUSED: could not move the adjudicated bytes" >&2; exit 3; }
RC7B="$(grade 7b-adjudication-moved)"
M7="$(grep -c -F -- 'BORN-AT-TIP ADJUDICATION MOVED' "$OUT/iva-7b-adjudication-moved.txt")"
echo "  7b the ADJUDICATED BYTES changed           grader exit = $RC7B  moved-lines=$M7"
verdict "7b changing an adjudicated capture's bytes MOVES the adjudication" "$RC7B" 1
verdict "7b and the move is named" "$M7" 1
echo

echo "############ SUMMARY"
echo "  1 clean tree   at BEFORE  exit $RC1   (calibration: the grader is green to begin with)"
echo "  2 fabricated   at BEFORE  exit $RC2   THE FAIL-OPEN, reproduced"
echo "  3 fabricated   at AFTER   exit $RC3   CLOSED"
echo "  4 (iv-b2)      at BEFORE  exit $RC4   the same hole by the other route"
echo "  5 (iv-b2)      at AFTER   exit $RC5   CLOSED"
echo "  6 clean tree   at AFTER   exit $RC6   THE CLOSE COSTS NOTHING"
echo "  7a adjudicated at AFTER   exit $RC7A  a legitimate new capture is admissible"
echo "  7b bytes moved at AFTER   exit $RC7B  and only the adjudicated bytes are"
echo
if [ "$FAILURES" -ne 0 ]; then
  echo "T455 (iv-a) DRIVE: FAIL — $FAILURES case(s) did not behave as recorded."
  exit 1
fi
echo "T455 (iv-a) DRIVE: PASS. The fail-open reproduces at BEFORE by two routes, is REFUSED at"
echo "AFTER by both, the clean tree is unchanged in exit code and in graded count, and the"
echo "adjudication list is falsifiable in both directions. DETECTION of a fabricated capture is"
echo "still external and is named at boundary (iv-a-anchor); this drive is about the VERDICT."
exit 0
