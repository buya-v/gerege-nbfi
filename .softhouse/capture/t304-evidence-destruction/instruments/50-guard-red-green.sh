#!/usr/bin/env bash
# T304 instrument 50 — drive the guard itself RED and GREEN. A guard nobody drove is a
# claim, not a control (P-50/P-72 in spirit: running your own green arm is agreement).
#
# Arms:
#   G1  target with 0 tracked files            -> returns 0, echoes the target unchanged
#   G2  target with >0 tracked, scratch set    -> returns 0, echoes a path under scratch
#   R1  target with >0 tracked, no scratch     -> returns 2, prints the count
#   R2  no target at all                       -> returns 2
#   R3  not a git work tree                    -> returns 2  (cannot measure => refuse)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
G=".softhouse/capture/t304-evidence-destruction/instruments/refuse-if-tracked.sh"
# shellcheck source=/dev/null
. "$G"

PASS=0; FAIL=0
ok()  { echo "  OK   $*"; PASS=$((PASS+1)); }
bad() { echo "  ***  FAIL: $*"; FAIL=$((FAIL+1)); }

TRACKED_TARGET=".softhouse/capture/t274-attestation-failopen/evidence/wrap"
N_TRACKED="$(git ls-files -- "$TRACKED_TARGET" | wc -l | tr -d ' ')"
UNTRACKED_TARGET="$(mktemp -d)/looks-like-evidence"
mkdir -p "$UNTRACKED_TARGET"

echo "=== T304 GUARD RED/GREEN ==="
echo "tracked target   : $TRACKED_TARGET  ($N_TRACKED tracked files)"
echo "untracked target : $UNTRACKED_TARGET"
echo

echo "--- G1  0 tracked -> pass through"
out="$(T304_EVIDENCE_SCRATCH= t304_evidence_root "$UNTRACKED_TARGET" 2>/dev/null)"; rc=$?
[ "$rc" -eq 0 ] && [ "$out" = "$UNTRACKED_TARGET" ] \
  && ok "rc=0, echoed unchanged: $out" || bad "rc=$rc out=$out"

echo "--- G2  >0 tracked + scratch root -> redirected, never the committed path"
S="$(mktemp -d)"
out="$(T304_EVIDENCE_SCRATCH="$S" t304_evidence_root "$TRACKED_TARGET" 2>/dev/null)"; rc=$?
case "$out" in
  "$S"/*) [ "$rc" -eq 0 ] && ok "rc=0, redirected to $out" || bad "rc=$rc" ;;
  *)      bad "rc=$rc out=$out  (NOT under the scratch root)" ;;
esac

echo "--- R1  >0 tracked, no scratch root -> REFUSE 2"
err="$(T304_EVIDENCE_SCRATCH= t304_evidence_root "$TRACKED_TARGET" 2>&1 >/dev/null)"; rc=$?
if [ "$rc" -eq 2 ] && printf '%s' "$err" | grep -q "WOULD DESTROY COMMITTED EVIDENCE" \
   && printf '%s' "$err" | grep -q "holds  : $N_TRACKED TRACKED files"; then
  ok "rc=2 and the refusal names the count $N_TRACKED"
else
  bad "rc=$rc; stderr was: $err"
fi

echo "--- R2  no target -> REFUSE 2"
err="$(t304_evidence_root "" 2>&1 >/dev/null)"; rc=$?
[ "$rc" -eq 2 ] && ok "rc=2: $err" || bad "rc=$rc"

echo "--- R3  outside any git work tree -> REFUSE 2 (cannot measure => refuse)"
NOGIT="$(mktemp -d)"
err="$(cd "$NOGIT" && GIT_CEILING_DIRECTORIES="$NOGIT" t304_evidence_root "$NOGIT/x" 2>&1 >/dev/null)"; rc=$?
if [ "$rc" -eq 2 ]; then
  ok "rc=2: refused rather than assuming untracked"
else
  bad "rc=$rc — a guard that cannot measure MUST refuse"
fi

echo
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
