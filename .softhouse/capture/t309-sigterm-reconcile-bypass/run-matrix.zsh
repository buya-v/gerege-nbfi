#!/bin/zsh
# T309 — THE FULL RED/GREEN MATRIX, with the expected verdict declared per cell so the
# rig cannot pass by agreeing with whatever it observed.
#
#   cell                          expects
#   pre-fix (main), plain         NOT RECONCILED   (rc 10) — this is the defect
#   post-fix (HEAD), plain        RECONCILED       (rc 0)  — this is the fix
#   post-fix, foreign live claude NOT RECONCILED   (rc 10) — the REFUSAL must survive
#
# The third cell is the one that stops this from being a trade of P-85 for something
# worse: a reconciler that demotes while a live session owns the repo destroys work.
# It is graded with the SAME assertion as the defect cell on purpose — "tasks stayed
# in_progress" is a FAILURE in cell 1 and the CORRECT ANSWER in cell 3, and the only
# thing that distinguishes them is which one we asked for.
set -uo pipefail
HERE="${0:A:h}"
TRIALS="${TRIALS:-3}"
PASS=0; FAIL=0

cell() {                       # cell <label> <expected-rc> <args...>
  local label=$1 want=$2; shift 2
  local out rc got
  print -r -- "############################################################"
  print -r -- "# CELL: $label   (expecting VERDICT_RC=$want)"
  print -r -- "############################################################"
  out=$(zsh "$HERE/drive-sigterm.zsh" "$@" 2>&1)
  print -r -- "$out" | /usr/bin/awk '/^wrapper sha256|^resolver sha256|planted a foreign|^wrapper pid|parent pid|SIGTERM -> wrapper|still in_progress|^VERDICT|ELAPSED_SECONDS|reconcile: |NOT reconciling|REFUS/'
  got=$(print -r -- "$out" | /usr/bin/sed -n 's/^VERDICT_RC=//p' | tail -1)
  local el=$(print -r -- "$out" | /usr/bin/sed -n 's/^ELAPSED_SECONDS=//p' | tail -1)
  if [[ "$got" == "$want" ]]; then
    print -r -- ">>> CELL PASS: $label  (VERDICT_RC=$got, SIGTERM->exit ${el}s)"
    (( PASS++ ))
  else
    print -r -- ">>> CELL FAIL: $label  (VERDICT_RC=$got, wanted $want)"
    (( FAIL++ ))
    print -r -- "$out" | tail -50
  fi
  print -r -- ""
}

cell "PRE-FIX (main) — SIGTERM must LEAVE THE LIE"        10 --rev main
cell "POST-FIX (HEAD) — SIGTERM must RECONCILE"            0 --rev HEAD
cell "POST-FIX (HEAD) + live in-repo claude — must REFUSE" 10 --rev HEAD --foreign-claude

print -r -- "=============================================================="
print -r -- "MATRIX: $PASS passed, $FAIL failed"
(( FAIL == 0 )) || exit 1
print -r -- ""
print -r -- "=============================================================="
print -r -- "TIMING — $TRIALS trials per revision, SIGTERM to wrapper exit"
print -r -- "=============================================================="
for rev in main HEAD; do
  local -a samples; samples=()
  for t in {1..$TRIALS}; do
    s=$(zsh "$HERE/drive-sigterm.zsh" --rev $rev 2>&1 | /usr/bin/sed -n 's/^ELAPSED_SECONDS=//p' | tail -1)
    samples+=("$s")
  done
  print -r -- "  $rev: ${samples[*]}"
done
print -r -- ""
print -r -- "DONE"
