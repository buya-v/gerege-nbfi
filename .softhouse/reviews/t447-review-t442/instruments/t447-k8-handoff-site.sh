#!/usr/bin/env bash
# =============================================================================================
# T447 -- F-T447-2: T442 OVERTURNED A CORRECT REVIEWER FINDING ON A SEARCH ARTEFACT.
#
# T440's `C-T440-2` says the wrong K8 decomposition `16 + 8 + 6 = 30` lives in
# "`AUDIT-CLASS.md` and T424's handoff". T442's erratum rejects the second half:
#
#     "I looked in `.softhouse/handoff/` and the sentence is not there -- `git grep` for
#      `all sixteen` under `.softhouse/handoff/` returns only unrelated T39/T242/T379 matches,
#      and T424's own handoff `T424-t408-conditions.md` states the K8 total (29) without
#      decomposing it. So there is ONE site to correct, not two."
#     -- .softhouse/capture/t424/ERRATUM-K8-DECOMPOSITION.md
#
# T424's handoff DOES decompose it. It spells the cardinals as WORDS in running prose --
# "Sixteen are the `sel` calls ... Eight are `SWEEP_*=$((...))` counters ... Six are parent-side
# assignments" -- so `git grep 'all sixteen'`, which looks for the ADJECTIVE PHRASE used in
# AUDIT-CLASS.md's table cell, cannot match it. "Not found" was a statement about the search.
#
# T440 was right, T442's rebuttal is wrong, and the consequence is operational: the erratum's
# own acceptance test checks only AUDIT-CLASS.md, so applying the erratum as written would go
# green while the wrong decomposition stayed on `main` in T424's handoff.
#
# Exit 0 = the finding reproduces. Exit 1 = it does not. Exit 2 = could not measure.
# =============================================================================================
set -uo pipefail
REPO=$(git rev-parse --show-toplevel) || exit 2
cd "$REPO" || exit 2
H='.softhouse/handoff/T424-t408-conditions.md'
A='.softhouse/capture/t402-t386-conditions/AUDIT-CLASS.md'
FAILED=0

check() {
  printf '  %-58s expected=%-10s actual=%-10s %s\n' "$1" "$2" "$3" \
    "$( if [ "$2" = "$3" ]; then echo OK; else echo '*** DRIVE DISAGREES'; fi )"
  [ "$2" = "$3" ] || FAILED=$((FAILED+1))
}

echo "=============================================================================="
echo "T447 F-T447-2 -- the K8 decomposition IS in T424's handoff"
echo "=============================================================================="
echo "repo   : $REPO"
echo "commit : $(git rev-parse HEAD)"
[ -r "$H" ] || { echo "REFUSED: cannot read $H" >&2; exit 2; }
[ -r "$A" ] || { echo "REFUSED: cannot read $A" >&2; exit 2; }
echo

echo "-- T442's recipe, run verbatim ------------------------------------------------"
n_t442=$(git grep -c 'all sixteen' -- "$H" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
echo "   git grep -c 'all sixteen' -- $H   ->   $n_t442"
check "T442's search really does return 0 on the handoff" "0" "$n_t442"
echo "   So the search T442 ran could not have found it. That is a fact about the SEARCH."
echo

echo "-- the same claim, searched for as the handoff actually spells it --------------"
s16=$(LC_ALL=C grep -c -F 'Sixteen are the `sel` calls' "$H")
s8=$(LC_ALL=C grep -c -F 'Eight are `SWEEP_*=$((' "$H")
s6=$(LC_ALL=C grep -c -F 'Six are parent-side assignments' "$H")
echo "   'Sixteen are the \`sel\` calls'        -> $s16   $(grep -n -F 'Sixteen are the `sel` calls' "$H" | cut -d: -f1 | tr '\n' ' ')"
echo "   'Eight are \`SWEEP_*=\$((' ...          -> $s8   $(grep -n -F 'Eight are `SWEEP_*=$((' "$H" | cut -d: -f1 | tr '\n' ' ')"
echo "   'Six are parent-side assignments'      -> $s6   $(grep -n -F 'Six are parent-side assignments' "$H" | cut -d: -f1 | tr '\n' ' ')"
check "the handoff carries the SIXTEEN cell"  "1" "$s16"
check "the handoff carries the EIGHT cell"    "1" "$s8"
check "the handoff carries the SIX cell"      "1" "$s6"
echo
echo "   the sentence, verbatim:"
sed -n '233,236p' "$H" | sed 's/^/     /'
echo

echo "-- the measured partition, for contrast ---------------------------------------"
S='.softhouse/capture/t363-oracle-baseline/instruments/casualty-sweep.sh'
sel_all=$(LC_ALL=C grep -cE '^sel +"S' "$S")
sel_nopipe=$(LC_ALL=C grep -nE '^sel +"S' "$S" | LC_ALL=C grep -vc '|')
inc=$(LC_ALL=C grep -cE 'SWEEP_[A-Z_]*=\$\(\(' "$S")
vars=$(LC_ALL=C grep -oE 'SWEEP_[A-Z_]*=\$\(\(' "$S" | sed 's/=.*//' | sort -u | grep -c '.')
echo "   sel \"S…\" calls in the subject file            : $sel_all"
echo "   of those whose pattern carries no '|'          : $sel_nopipe"
echo "   therefore reaching the wide K8 list            : $((sel_all - sel_nopipe))"
echo "   SWEEP_*=\$((…)) increment lines                 : $inc"
echo "   distinct counter variables                     : $vars"
check "sel calls in the file"                    "16" "$sel_all"
check "of those, no pipe in their pattern"       "3"  "$sel_nopipe"
check "16 - 3 == the census's sel rows"          "13" "$((sel_all - sel_nopipe))"
check "increment lines today"                    "10" "$inc"
check "distinct counter variables"               "3"  "$vars"
echo "   13 + 10 + 6 = $((sel_all - sel_nopipe + inc + 6))  (the census's own printed total is 29)"
check "the measured partition sums to 29"        "29" "$((sel_all - sel_nopipe + inc + 6))"
echo

echo "-- the erratum's acceptance test does not reach the handoff --------------------"
acc=$(git grep -c 'all sixteen `sel' -- "$A" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
echo "   the erratum's check   git grep -c 'all sixteen \`sel' -- AUDIT-CLASS.md  ->  $acc"
E='.softhouse/capture/t424/ERRATUM-K8-DECOMPOSITION.md'
# The erratum DOES name the handoff -- once, to DENY that it carries the decomposition. What it
# does not do is check it. Measure the acceptance-test block on its own.
n_deny=$(LC_ALL=C grep -c -F 'T424-t408-conditions.md' "$E"); true
n_acc=$(sed -n '/^## Acceptance test/,$p' "$E" | LC_ALL=C grep -c -F 'handoff'); true
echo "   the erratum mentions T424-t408-conditions.md         : $n_deny  (to DENY it, not to fix it)"
echo "   its Acceptance test block mentions the handoff       : $n_acc"
check "the acceptance test never checks the handoff" "0" "$n_acc"
check "the erratum's denial of the second site is present" "yes" \
      "$( [ "${n_deny:-0}" -ge 1 ] && echo yes || echo no )"

echo
echo "=============================================================================="
printf 'T447-K8-HANDOFF-SITE-RESULT: disagreements=%s\n' "$FAILED"
if [ "$FAILED" -gt 0 ]; then echo "*** THIS DRIVE FAILED."; exit 1; fi
echo "F-T447-2 reproduces: TWO sites carry the wrong decomposition, not one."
exit 0
