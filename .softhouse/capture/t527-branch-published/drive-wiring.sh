#!/bin/sh
# T527 -- DRIVE THE WIRING, NOT THE TOOL.
#
# `check-branch-published.py --selftest` proves the CHECK works. This script proves the
# CALLER carries its verdict, which is the half this program keeps getting wrong: T303,
# T311, T313, T333 and T425 are all guards that were built and never wired, and T399
# censused seven of them. So every cell below runs `ready-tasks.py` -- the thing an
# orchestrator actually executes at STEP 0/1 -- and reads ITS exit code, never the
# checker's.
#
# Five cells, and the last two are the ones that make the other three mean anything:
#   A  the real repo               -> 5, REFUSE, the 2026-09-04 incident named
#   B  origin unreachable          -> 5, CANNOT ESTABLISH ORIGIN (fail closed, distinct)
#   C  a clean record              -> 0, CLEAN            <- the control that can PASS
#   D  the checker deleted         -> 5, "not on disk"    <- the wiring's own fail-closed
#   E  the checker REPLACED by a silent exit-0 stub, over a DIRTY record
#                                  -> 5, "never printed its verdict line"
#
# E is T536, closing T528 F-5. D covered the checker being DELETED and not the checker
# being REPLACED, and `import sys; sys.exit(0)` in place of the tool made this wiring
# report a pass over a branch that was never pushed -- a two-line de-facto disable in a
# program whose recorded failure mode is a red guard being "fixed" instead of the red
# thing. The caller now requires the checker's own verdict line before it believes an
# exit code of 0.
#
# Usage:  sh .softhouse/capture/t527-branch-published/drive-wiring.sh [<repo-root>]
# Exit 0 iff all five cells behave as stated.

set -u
REPO=${1:-$(cd "$(dirname "$0")/../../.." && pwd)}
RT="$REPO/.softhouse/bin/ready-tasks.py"
CB="$REPO/.softhouse/bin/check-branch-published.py"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/t527-wiring.XXXXXX")
FAILED=0

say() { printf '%s\n' "$*"; }
cell() {
  name=$1; want=$2; got=$3; needle=$4; out=$5
  if [ "$got" = "$want" ] && grep -q "$needle" "$out"; then
    say "  $name: PASS  (ready-tasks.py exit $got, saw \"$needle\")"
  else
    say "  $name: FAIL  (ready-tasks.py exit $got, wanted $want, needle \"$needle\")"
    sed 's/^/      /' "$out" | head -30
    FAILED=$((FAILED + 1))
  fi
}

say "T527 wiring drive -- every verdict below is ready-tasks.py's own exit code."
say "repo: $REPO"
say ""

# ---- A. the real repository -------------------------------------------------------
say "A. the real record, real origin"
python3 "$RT" --repo "$REPO" > "$TMP/a.txt" 2>&1
cell "A-real-repo-refuses" 5 $? "check-branch-published: REFUSE" "$TMP/a.txt"
say "     findings named: $(grep -c '^  UNBACKED-' "$TMP/a.txt")"
grep -E '^  UNBACKED-(BRANCH|COMMIT)' "$TMP/a.txt" | sed 's/^/     /'
say ""

# ---- fixture builder for B, C, D --------------------------------------------------
# $1 = fixture root, $2 = "broken" | "ok". The work tree is <root>/work and the bare
# origin is <root>/origin.git -- OUTSIDE the work tree, because a bare repo sitting inside
# it is not named `.git` and `git add -A` swallows it whole.
mkfixture() {
  d=$1
  w=$d/work
  mkdir -p "$w/.softhouse/bin"
  git -C "$w" init --quiet -b main
  cp "$CB" "$RT" "$w/.softhouse/bin/"
  printf '{"gates_pending":[]}' > "$w/.softhouse/program.json"
  if [ "$2" = "broken" ]; then
    git -C "$w" remote add origin "$d/no-such-origin.git"
    printf '{"run_id":"x","tasks":[{"id":"TN","status":"done","branch":"softhouse/TN-never-pushed"}]}' \
      > "$w/.softhouse/tasks.json"
    return
  fi
  git init --quiet --bare -b main "$d/origin.git"
  git -C "$w" remote add origin "$d/origin.git"
  : > "$w/README"
  git -C "$w" add -A
  git -C "$w" -c user.email=t527@example.invalid -c user.name=t527 \
      commit --quiet -m root
  git -C "$w" push --quiet -u origin main 2>/dev/null
  git -C "$w" checkout --quiet -b softhouse/TP-pushed
  echo p > "$w/p.txt"
  git -C "$w" add -A
  git -C "$w" -c user.email=t527@example.invalid -c user.name=t527 \
      commit --quiet -m "TP work"
  git -C "$w" push --quiet origin softhouse/TP-pushed 2>/dev/null
  git -C "$w" checkout --quiet main
  printf '{"run_id":"x","tasks":[{"id":"TP","status":"done","branch":"softhouse/TP-pushed"}]}' \
    > "$w/.softhouse/tasks.json"
}

# ---- B. origin unreachable --------------------------------------------------------
say "B. origin unreachable -- must be a DISTINCT refusal, never a pass"
mkfixture "$TMP/b" broken
python3 "$TMP/b/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/b/work" > "$TMP/b.txt" 2>&1
cell "B-unreachable-fails-closed" 5 $? "CANNOT ESTABLISH ORIGIN" "$TMP/b.txt"
say ""

# ---- C. a clean record ------------------------------------------------------------
say "C. a record whose one branch IS on origin -- the control that must PASS"
mkfixture "$TMP/c" ok
python3 "$TMP/c/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/c/work" > "$TMP/c.txt" 2>&1
cell "C-clean-record-passes" 0 $? "check-branch-published: CLEAN" "$TMP/c.txt"
say ""

# ---- D. the checker is gone -------------------------------------------------------
say "D. the checker deleted -- the WIRING's own fail-closed arm"
rm -rf "$TMP/d"
cp -R "$TMP/c" "$TMP/d"
rm -f "$TMP/d/work/.softhouse/bin/check-branch-published.py"
python3 "$TMP/d/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/d/work" > "$TMP/d.txt" 2>&1
cell "D-missing-checker-is-not-a-pass" 5 $? "checker is not on disk" "$TMP/d.txt"
say ""

# ---- E. the checker REPLACED by a silent stub, over a DIRTY record -----------------
# T536 / T528 F-5. The record here CLAIMS a branch that was never pushed, so the only
# way this cell can go green is the stub being believed.
say "E. the checker replaced by a silent exit-0 stub, over a record that is DIRTY"
rm -rf "$TMP/e"
cp -R "$TMP/c" "$TMP/e"
printf 'import sys\nsys.exit(0)\n' > "$TMP/e/work/.softhouse/bin/check-branch-published.py"
printf '{"run_id":"x","tasks":[{"id":"TN","status":"done","branch":"softhouse/TN-never-pushed"}]}' \
  > "$TMP/e/work/.softhouse/tasks.json"
python3 "$TMP/e/work/.softhouse/bin/ready-tasks.py" --repo "$TMP/e/work" > "$TMP/e.txt" 2>&1
cell "E-silent-stub-is-not-a-pass" 5 $? "never printed its verdict line" "$TMP/e.txt"
say ""

say "$FAILED cell(s) failed. fixtures: $TMP"
[ "$FAILED" -eq 0 ]
