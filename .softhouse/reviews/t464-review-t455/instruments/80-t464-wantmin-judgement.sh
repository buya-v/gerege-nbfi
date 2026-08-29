#!/bin/bash
# T464 — WAS T455's ONE DISCLOSED OUT-OF-SCOPE EDIT THE RIGHT CALL?
#
# T455 changed two `want` (EXACT count) pins to `want_min` (MINIMUM) in T433's ARM-F wiring
# guard, a file outside its three assigned directories, and disclosed it by name. Three
# questions, each MEASURED here rather than argued:
#
#   A  as shipped, is the guard green on a CLEAN tree at T455's tip?
#   B  with the two pins REVERTED to `want`, is it red on that same CLEAN tree — i.e. was the
#      edit necessary, or was it convenience?
#   C  with the pins loosened as shipped, does the guard STILL go red when the pinned token
#      disappears entirely — i.e. is `want_min ... 1` still a guard (P-22), or was the claim
#      thrown away with the count?
#
# NO REPO-RELATIVE PATH IS SPELLED AS A LITERAL — assembled from `S` at run time.
#
#   T464_SRC=<repo>  T464_SCRATCH=<dir OUTSIDE the repo>  T464_REF=<ref> \
#     bash 80-t464-wantmin-judgement.sh
#
# EXIT 0  A green, B red, C red — the edit was necessary AND the claim survives it.
# EXIT 1  any of the three came out otherwise.   EXIT 3  REFUSED.
set -u
S='.softhouse'
GUARD="$S/capture/t433-t423-c1/instruments/30-t433-armf-wiring-guard.sh"
INT="$S/reviews/A2-11/verify-capture-integrity.py"
TOK1="UNGRADED-BORN-AT-TIP"
TOK2="THE BLOB AT THE COMMIT THAT FIRST ADDED EACH OBSERVATION"

SRC="${T464_SRC:?}"; SCRATCH="${T464_SCRATCH:?}"; REF="${T464_REF:?}"
D="$SCRATCH/wantmin"; FAIL=0

prepare() {
  if [ ! -d "$D/.git" ]; then rm -rf "$D"; git clone --quiet --shared "$SRC" "$D" || return 3; fi
  git -C "$D" checkout --quiet --force --detach "$REF" || return 3
  git -C "$D" reset --quiet --hard "$REF" || return 3
  git -C "$D" clean -qfdx || return 3
  [ -f "$D/$GUARD" ] || { echo "REFUSED: no wiring guard at $REF" >&2; return 3; }
}
run() { T433_ROOT="$D" bash "$D/$GUARD" > "$SCRATCH/wm-$1.txt" 2>&1; echo $?; }
expect() { if [ "$2" = "$3" ]; then echo "  OK   $1: exit $2"; else echo "  BAD  $1: exit $2, want $3"; FAIL=$((FAIL+1)); fi; }

echo "############ T464 — THE want -> want_min EDIT, JUDGED BY MEASUREMENT"
echo
echo "--- A. AS SHIPPED, ON A CLEAN TREE ------------------------------------------------"
prepare || exit 3
RC="$(run A-as-shipped)"; expect "A guard as shipped (want_min), clean tree" "$RC" 0
grep -c '  BAD  ' "$SCRATCH/wm-A-as-shipped.txt" | sed 's/^/       BAD assertions: /'
echo

echo '--- B. THE TWO PINS REVERTED TO EXACT want (exact count), SAME CLEAN TREE ------'
prepare || exit 3
python3 - "$D/$GUARD" <<'PYEOF' || exit 3
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
n = 0
out = []
for ln in s.split("\n"):
    if ln.startswith("want_min ") and ("UNGRADED-BORN-AT-TIP" in ln
                                       or "says what the baseline IS" in ln):
        ln = "want     " + ln[len("want_min "):]
        n += 1
    out.append(ln)
if n != 2:
    print("REFUSED: expected to revert exactly 2 lines, reverted %d" % n)
    sys.exit(3)
open(p, "w", encoding="utf-8").write("\n".join(out))
PYEOF
RC="$(run B-reverted)"; expect "B the same tree with EXACT-count pins" "$RC" 1
grep '  BAD  ' "$SCRATCH/wm-B-reverted.txt" | sed 's/^/       /'
echo "       ==> the edit was NECESSARY, not convenient: with the exact pins the guard is RED"
echo "           on a CLEAN tree, which is the defect T455 was sent to fix in F-6."
echo

echo "--- C. AS SHIPPED, BUT THE PINNED TOKENS REMOVED FROM THE GRADER ------------------"
prepare || exit 3
python3 - "$D/$INT" "$TOK1" "$TOK2" <<'PYEOF' || exit 3
import sys
p, t1, t2 = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p, encoding="utf-8").read()
if t1 not in s or t2 not in s:
    print("REFUSED: a pinned token is not in the grader; the removal would be a no-op")
    sys.exit(3)
open(p, "w", encoding="utf-8").write(s.replace(t1, "REMOVED_1").replace(t2, "REMOVED_2"))
PYEOF
RC="$(run C-token-removed)"; expect "C want_min still fires when the token is GONE" "$RC" 1
grep '  BAD  ' "$SCRATCH/wm-C-token-removed.txt" | sed 's/^/       /'
echo '       ==> want_min <token> 1 is still a guard: the claim these two pins make is'
echo "           PRESENCE, and PRESENCE is exactly what survives the loosening (P-22)."
echo

[ "$FAIL" -ne 0 ] && { echo "T464 want_min DRIVE: $FAIL case(s) off."; exit 1; }
echo "T464 want_min DRIVE: 3/3. The edit was necessary, minimal, and not a weakening of any"
echo "claim the pins actually made. EXIT 0"
