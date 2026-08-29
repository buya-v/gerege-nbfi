#!/bin/bash
# T433 — the wiring guard, DRIVEN RED. P-22: a guard nobody has seen fail is not a guard, and
# 30-t433-armf-wiring-guard.sh is itself a guard, so it is held to its own standard.
#
# FOUR mutations, in scratch clones, never in the tree. Each removes exactly one thing the
# guard claims to protect, and each must produce EXIT 1 for a DIFFERENT named reason. A guard
# that goes red for the same reason on every mutation is one assertion wearing four hats.
#
#   R1  ARM F deleted from the shipped grader        -> section 8 gone
#   R2  the correction reverted to the FALSE claim   -> an untagged assertion reappears
#   R3  the verbatim QUOTE deleted, claim still gone -> a bare negation removed
#   R4  the f1-13b expectation put back to `0 0`     -> the drive matrix stops tripping
#
# NO HOST PATH IS WRITTEN IN THIS FILE (T256/T298).
#   T433_SRC=<repo>  T433_CLONE=<scratch OUTSIDE the repo>  T433_OUT=<dir> \
#   bash 31-t433-wiring-guard-red-drive.sh
#
# EXIT 0 the guard was GREEN unmutated and RED, for the right reason, on all four.
# EXIT 1 it was not. EXIT 3 the harness could not run.
set -u
SRC="${T433_SRC:?}"; SCROOT="${T433_CLONE:?}"; OUT="${T433_OUT:?}"
GUARD=".softhouse/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh"
INT=".softhouse/reviews/A2-11/verify-capture-integrity.py"
DRIVE=".softhouse/capture/t393-t382-conditions/instruments/10-drive-conditions.sh"
mkdir -p "$OUT" "$SCROOT" || exit 3

D="$SCROOT/wiring"
FAIL=0
prep() {
  rm -rf "$D" || return 1
  git clone --quiet --shared "$SRC" "$D" || return 1
  git -C "$D" checkout --quiet --detach HEAD || return 1
}

run() {   # run <name> <mutfn> <expected-exit> <must-print>
  local name="$1" fn="$2" want="$3" pat="$4" t rc got
  prep || { echo "HARNESS FAILURE cloning" >&2; exit 3; }
  "$fn" || { echo "HARNESS FAILURE applying $fn — an unmutated case is a null control" >&2; exit 3; }
  t="$OUT/wiring-$name.txt"
  ( T433_ROOT="$D" bash "$D/$GUARD" ) > "$t" 2>&1
  rc=$?
  got="$(grep -c -- "$pat" "$t")"
  if [ "$rc" = "$want" ] && [ "$got" -ge 1 ]; then
    printf '  OK   %-26s exit %s, and it says why: %s\n' "$name" "$rc" "$pat"
  else
    printf '  BAD  %-26s exit %s (wanted %s); reason line x%s for: %s\n' "$name" "$rc" "$want" "$got" "$pat"
    FAIL=$((FAIL + 1))
  fi
}

m_none() { return 0; }
m_r1_delete_armf()  { perl -pi -e 's/=== 8\. ARM F/=== 8. ARM-F-DELETED/' "$D/$INT"; }
m_r2_restore_claim() {
  # Put the FALSE assertion back, UNTAGGED, exactly as T393 shipped it.
  printf '\n# There is no committed baseline older than HEAD for those 632.\n' >> "$D/$DRIVE"
}
m_r3_delete_quote() { perl -pi -e 's/\[QUOTED-FALSE-CLAIM\]/[redacted]/g' "$D/$INT"; }
m_r4_revert_row() {
  perl -pi -e 's/^run_case f1-13b-postfork-laundered-CLOSED-BY-ARM-F(\s+\S+\s+)0 1$/run_case f1-13b-postfork-laundered-CLOSED-BY-ARM-F${1}0 0/' "$D/$DRIVE"
}

echo "############ T433 WIRING-GUARD RED DRIVE"
echo "  src $SRC"
echo
echo "--- GREEN control: unmutated, the guard must PASS -------------------------------"
run control                m_none              0 "WIRING GUARD: PASS"
echo
echo "--- RED: each mutation removes ONE protected thing, for a DIFFERENT reason -------"
run R1-armf-deleted        m_r1_delete_armf    1 "carries ARM F as section 8"
run R2-false-claim-back    m_r2_restore_claim  1 "still asserts the impossibility"
run R3-quote-deleted       m_r3_delete_quote   1 "no longer quotes the false text"
run R4-row-reverted        m_r4_revert_row     1 "the f1-13b row expects 0 -> 1"

echo
if [ "$FAIL" -ne 0 ]; then
  echo "T433 WIRING-GUARD RED DRIVE: FAIL — $FAIL case(s) did not behave."
  exit 1
fi
echo "T433 WIRING-GUARD RED DRIVE: PASS. The wiring guard passes an unmutated tree and goes"
echo "RED on all four removals, each naming a DIFFERENT assertion — so it is four checks, not"
echo "one check printed four times, and none of them is a negative that cannot fail."
exit 0
