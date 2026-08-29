#!/bin/bash
# T464 — INDEPENDENT re-drive of T455's (iv-a) close. Does NOT reuse T455's instrument.
#
# Case 1  BEFORE, clean tree                     -> expect grader 0   (calibration)
# Case 2  BEFORE, fabricated obs born AT THE TIP,
#         MANIFEST laundered in the SAME commit  -> expect grader 0   (THE FAIL-OPEN)
# Case 3  AFTER,  the same mutation              -> expect grader 1   on the named assertion
# Case 4  AFTER,  clean tree                     -> expect grader 0   (THE P-98 CONTROL)
#
# No path under the reviewed tree is spelled as a literal here; every one is assembled.
set -u
S='.softhouse'
CAP="$S/capture/tierA-a2"
GRADER="$S/reviews/A2-11/verify-capture-integrity.py"
MAN="$CAP/MANIFEST.sha256"

SRC="${T464_SRC:?T464_SRC must name the source repository}"
SCRATCH="${T464_SCRATCH:?T464_SCRATCH must name a scratch dir OUTSIDE the repository}"
BEFORE_REF="${T464_BEFORE:?}"
AFTER_REF="${T464_AFTER:?}"
D="$SCRATCH/iva"
FAIL=0

prepare() {  # prepare <ref>
  if [ ! -d "$D/.git" ]; then
    rm -rf "$D" || return 3
    git clone --quiet --shared "$SRC" "$D" || return 3
  fi
  git -C "$D" checkout --quiet --force --detach "$1" || return 3
  git -C "$D" reset --quiet --hard "$1" || return 3
  git -C "$D" clean -qfdx || return 3
  [ -f "$D/$GRADER" ] || { echo "REFUSED: no grader at $1"; return 3; }
  [ -f "$D/$MAN" ]    || { echo "REFUSED: no manifest at $1"; return 3; }
  return 0
}

fabricate() {   # add a fabricated observation + its laundered manifest row, ONE commit
  local nm="A2-999-T464-FABRICATED.json"
  printf '{"fabricated":true,"note":"T464 drive"}\n' > "$D/$CAP/out/$nm" || return 3
  local h
  h="$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$D/$CAP/out/$nm")" || return 3
  printf '%s  out/%s\n' "$h" "$nm" >> "$D/$MAN" || return 3
  LC_ALL=C sort -k2 "$D/$MAN" -o "$D/$MAN" || return 3
  git -C "$D" add -- "$CAP/out/$nm" "$MAN" || return 3
  git -C "$D" -c user.name=t464 -c user.email=t464@local commit -q \
      -m "T464 drive: fabricated observation born at the tip, manifest laundered in the same commit" || return 3
  return 0
}

grade() {   # grade <label> ; prints exit code, keeps transcript
  local label="$1"
  ( cd "$D" && python3 "$GRADER" ) > "$SCRATCH/$label.txt" 2>&1
  echo $?
}

expect() {  # expect <label> <got> <want>
  if [ "$2" = "$3" ]; then echo "  OK   $1: grader exit $2 (expected $3)"
  else echo "  BAD  $1: grader exit $2, expected $3"; FAIL=$((FAIL+1)); fi
}

echo "############ T464 — INDEPENDENT (iv-a) DRIVE"
prepare "$BEFORE_REF" || exit 3
RC1="$(grade case1-before-clean)"; expect "case 1 BEFORE clean (calibration)" "$RC1" 0
grep -E 'graded=[0-9]+ of|born at the tip=' "$SCRATCH/case1-before-clean.txt" | head -2 | sed 's/^/       /'

prepare "$BEFORE_REF" || exit 3
fabricate || exit 3
RC2="$(grade case2-before-fabricated)"; expect "case 2 BEFORE fabricated+laundered (FAIL-OPEN)" "$RC2" 0
grep -E 'graded=[0-9]+ of|FABRICATED' "$SCRATCH/case2-before-fabricated.txt" | head -3 | sed 's/^/       /'

prepare "$AFTER_REF" || exit 3
fabricate || exit 3
RC3="$(grade case3-after-fabricated)"; expect "case 3 AFTER  fabricated+laundered (REFUSED)" "$RC3" 1
grep -n 'FAIL' "$SCRATCH/case3-after-fabricated.txt" | sed 's/^/       /' | head -6

prepare "$AFTER_REF" || exit 3
RC4="$(grade case4-after-clean)"; expect "case 4 AFTER  clean tree (P-98 CONTROL)" "$RC4" 0
grep -E 'graded=[0-9]+ of|born at the tip=' "$SCRATCH/case4-after-clean.txt" | head -2 | sed 's/^/       /'

echo
if [ "$FAIL" -ne 0 ]; then echo "T464 (iv-a) DRIVE: $FAIL case(s) did not behave as T455 recorded."; exit 1; fi
echo "T464 (iv-a) DRIVE: 4/4 as T455 recorded. EXIT 0"
