#!/usr/bin/env bash
# =============================================================================================
# T457 -- F-T447-2 RE-DERIVED, AND T452'S NEW ACCEPTANCE TEST DRIVEN RED.
#
# T452 replaced T442's erratum test with a SET-EQUALITY assertion against a site table parsed
# out of the erratum. A test nobody has seen FAIL is not a test (P-22), and the defect this one
# exists for is precisely a test that "applied as written GOES GREEN WITH THE DEFECT STILL ON
# MAIN". So:
#
#   ARM 1  the K8 partition, re-derived by THIS file's own parser from the census transcript --
#          a third route, independent of both of T452's. 13 + 10 + 6 = 29 or this arm fails.
#   ARM 2  RED. A throwaway worktree at the subject tip with the PRE-REPAIR handoff restored
#          into it. T452's drive must EXIT 1 there. If it exits 0 the test is a rubber stamp.
#   ARM 3  GREEN control, same drive, same worktree, handoff restored. Must exit 0. A red drive
#          without a healthy control beside it cannot tell "the test works" from "the test
#          always fails".
#   ARM 4  "NOT FOUND IS A STATEMENT ABOUT THE SEARCH." F-T447-2 exists because T442 searched
#          for one adjective phrase. T452's detector requires the word `sel` with word
#          boundaries, so a site spelling the same split as "sixteen SELECTORS" would be
#          invisible to it in turn. This arm searches that spelling, and the counter cell as
#          "eight counters", over the whole instrument tree, and reports every hit for a hand
#          read rather than asserting a zero.
#
# The subject tree and the pre-repair ref are REQUIRED PARAMETERS. Nothing under the instrument
# root is spelled as a literal path; every one is assembled from `$S`.
#
# EXIT 0 = every arm as declared.  1 = a disagreement.  2 = could not measure (NOT a pass).
# =============================================================================================
set -uo pipefail
S='.softhouse'
TREE="${1:-}"; BASE_REF="${2:-}"
[ -n "$TREE" ] && [ -n "$BASE_REF" ] || {
  echo "REFUSED (exit 2): usage: t457-k8-redrive.sh <subject-tree> <pre-repair-ref>" >&2; exit 2; }
TREE=$(cd "$TREE" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || TREE=""
[ -n "$TREE" ] || { echo "REFUSED (exit 2): argument 1 is not a git work tree" >&2; exit 2; }
git -C "$TREE" rev-parse --verify "$BASE_REF^{commit}" >/dev/null 2>&1 || {
  echo "REFUSED (exit 2): '$BASE_REF' does not resolve in $TREE" >&2; exit 2; }

CENSUS="$S/capture/t424/out/T424-CENSUS-after-with-K8.txt"
HANDOFF="$S/handoff/T424-t408-conditions.md"
DRIVE="$S/capture/t452-t447-conditions/instruments/t452-k8-sites-drive.sh"
for f in "$CENSUS" "$HANDOFF" "$DRIVE"; do
  [ -r "$TREE/$f" ] || { echo "REFUSED (exit 2): cannot read $f under $TREE" >&2; exit 2; }
done

W=$(mktemp -d "${TMPDIR:-/tmp}/t457-k8.XXXXXXXX") || exit 2
case "$W" in "$TREE"/*) echo "REFUSED (exit 2): scratch inside the subject tree" >&2; exit 2 ;; esac
cleanup() { git -C "$TREE" worktree remove --force "$W/red" >/dev/null 2>&1; rm -rf "$W"; }
trap cleanup EXIT

FAILED=0
check() {
  printf '  %-56s expected=%-9s actual=%-9s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

echo "=============================================================================="
echo "T457 K8 RE-DERIVATION AND RED DRIVE"
echo "subject tree : $TREE"
echo "commit       : $(git -C "$TREE" rev-parse HEAD)"
echo "dirty        : $(git -C "$TREE" status --porcelain | grep -c '' | tr -d ' ') path(s)"
echo "pre-repair   : $(git -C "$TREE" rev-parse --short "$BASE_REF^{commit}")"
echo "=============================================================================="
echo

# ------------------------------------------------------------------------------------ ARM 1
echo "ARM 1 -- the K8 partition, parsed by THIS file, from the census transcript"
LC_ALL=C awk '/^--- K8 /{f=1;next} /^ *\(state-mutating lines:/{f=0} f && /^ *[0-9]+ \|/{print}' \
  "$TREE/$CENSUS" >"$W/k8.txt"
k8_rows=$(grep -c '' "$W/k8.txt")
printed=$(LC_ALL=C sed -n 's/.*== K8 SITES: \([0-9]*\).*/\1/p' "$TREE/$CENSUS" | head -1)
k8_sel=$(LC_ALL=C grep -c '| *sel "' "$W/k8.txt")
k8_ctr=$(LC_ALL=C grep -c 'SWEEP_[A-Za-z_]*=\$((' "$W/k8.txt")
k8_res=$((k8_rows - k8_sel - k8_ctr))
if [ "$k8_rows" -lt 5 ]; then
  echo "REFUSED (exit 2): the K8 block parser extracted $k8_rows rows. A partition of nothing" >&2
  echo "  sums to anything; the transcript format has changed." >&2; exit 2
fi
echo "   rows extracted from the --- K8 block : $k8_rows   (census printed: ${printed:-?})"
echo "   of them, sel rows                    : $k8_sel"
echo "   of them, SWEEP_*=\$((...)) counters    : $k8_ctr"
echo "   residual, parent-side                : $k8_res"
sed 's/^/       /' "$W/k8.txt" | LC_ALL=C grep -v '| *sel "' | LC_ALL=C grep -v 'SWEEP_[A-Za-z_]*=\$(('
check "extracted rows == the census's own total"   "$printed" "$k8_rows"
check "sel cell"                                   "13" "$k8_sel"
check "counter cell"                               "10" "$k8_ctr"
check "residual cell"                              "6"  "$k8_res"
check "the three cells sum to the census total"    "$printed" "$((k8_sel + k8_ctr + k8_res))"
echo "   PARTITION: $k8_sel + $k8_ctr + $k8_res = $((k8_sel + k8_ctr + k8_res))"
echo "   the published split was 16 + 8 + 6 = 30 -- wrong in all three cells and in the total."
echo

# ------------------------------------------------------------------------------------ ARM 2/3
echo "ARM 2/3 -- T452's site test, driven RED on the un-repaired handoff and GREEN beside it"
git -C "$TREE" worktree add --detach -q "$W/red" HEAD 2>/dev/null || {
  echo "REFUSED (exit 2): could not create a throwaway worktree at the subject tip" >&2; exit 2; }
( cd "$W/red" && T452_REPO="$W/red" bash "$DRIVE" ) >"$W/green.txt" 2>&1
green_rc=$?
git -C "$TREE" show "$BASE_REF:$HANDOFF" >"$W/red/$HANDOFF" 2>/dev/null || {
  echo "REFUSED (exit 2): the pre-repair handoff does not exist at $BASE_REF" >&2; exit 2; }
if cmp -s "$W/red/$HANDOFF" "$TREE/$HANDOFF"; then
  echo "REFUSED (exit 2): the handoff is byte-identical before and after. There is no repair" >&2
  echo "  to drive red, so a green here would be a green nobody measured." >&2; exit 2
fi
( cd "$W/red" && T452_REPO="$W/red" bash "$DRIVE" ) >"$W/red.txt" 2>&1
red_rc=$?
red_dis=$(LC_ALL=C sed -n 's/.*disagreements=\([0-9]*\).*/\1/p' "$W/red.txt" | tail -1)
green_dis=$(LC_ALL=C sed -n 's/.*disagreements=\([0-9]*\).*/\1/p' "$W/green.txt" | tail -1)
echo "   GREEN control (repaired handoff)  : exit=$green_rc disagreements=${green_dis:-?}"
echo "   RED     (pre-repair handoff)      : exit=$red_rc disagreements=${red_dis:-?}"
LC_ALL=C grep 'DRIVE DISAGREES' "$W/red.txt" | sed 's/^/       /'
check "the test PASSES on the repaired tree"        "0" "$green_rc"
check "and FAILS on the un-repaired tree"           "1" "$red_rc"
check "it is not merely noisy: green has 0 disagreements" "0" "${green_dis:-x}"
echo

# ------------------------------------------------------------------------------------- ARM 4
echo "ARM 4 -- spellings T452's OWN detector cannot see (\\bsel\\b misses 'selectors')"
git -C "$TREE" grep -n -I -i -E \
  '(sixteen|\b16\b)[^.]{0,80}selector|selector[^.]{0,80}(sixteen|\b16\b)' -- "$S" \
  >"$W/alt1.txt" 2>/dev/null
git -C "$TREE" grep -n -I -i -E \
  '(\beight\b|\b8\b)[^.]{0,60}counters|counters[^.]{0,60}(\beight\b|\b8\b)' -- "$S" \
  >"$W/alt2.txt" 2>/dev/null
a1=$(grep -c '' "$W/alt1.txt"); a2=$(grep -c '' "$W/alt2.txt")
echo "   'sixteen/16' within 80 chars of 'selector' : $a1 line(s)"
LC_ALL=C cut -c1-150 "$W/alt1.txt" | sed 's/^/       /'
echo "   'eight/8' within 60 chars of 'counters'    : $a2 line(s)"
LC_ALL=C cut -c1-150 "$W/alt2.txt" | sed 's/^/       /'
# P-72: this arm must be able to FIND something before its silence means anything.
cal=$(printf 'Sixteen of the selectors reach the wide list.\n' \
      | LC_ALL=C grep -c -i -E '(sixteen|\b16\b)[^.]{0,80}selector')
echo "   P-72 calibration of THIS arm's selector    : $cal (must be 1)"
check "arm 4's selector can find a known positive"  "1" "$cal"
echo "   NOTE: this arm REPORTS; it asserts no zero. Every line above is for a hand read."
echo

echo "=============================================================================="
echo "T457-K8-RESULT: partition=$k8_sel+$k8_ctr+$k8_res=$((k8_sel+k8_ctr+k8_res)) census=$printed green=$green_rc red=$red_rc alt_spelling_lines=$((a1+a2)) disagreements=$FAILED"
echo "=============================================================================="
[ "$FAILED" -eq 0 ] || exit 1
exit 0
