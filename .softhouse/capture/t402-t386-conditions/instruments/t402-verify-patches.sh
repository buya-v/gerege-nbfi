#!/usr/bin/env bash
# T402 -- VERIFY THE FOUR OUT-OF-GRANT PATCHES BEFORE ANYONE APPLIES THEM.
#
#   bash .softhouse/capture/t402-t386-conditions/instruments/t402-verify-patches.sh <repo-root>
#
# T402's grant is `.softhouse/capture/t363-oracle-baseline/instruments/` and its own capture
# directory. Four of T386's eight follow-ups land OUTSIDE it -- in T381's capture directory and
# in two merged handoffs -- so they ship as patches rather than as edits, exactly as the brief
# instructs for `conformance.sh`.
#
# A PATCH SHIPPED UNVERIFIED IS A CLAIM, and one of the four is executable. So this drive:
#   * `git apply --check`s every patch against the tree, and
#   * for the one that changes an EXECUTABLE file, applies it to a scratch copy, syntax-checks
#     the result, and drives the guard it adds through all three of its outcomes -- including
#     the "no log configured" outcome, because a guard that silently does nothing when it is not
#     wired is the P-45 shape the patch exists to remove.
#
# ENGINE DECLARED: `git apply`, `bash -n`, and fixed-string `grep` over scratch files. No
# repository search, no backslash-class.
#
# EXIT: 0 all patches check and the executable one behaves; 1 something did not; 2 rig failure.
set -uo pipefail

REPO=${1:-.}
PD="$REPO/.softhouse/capture/t402-t386-conditions/patches"
TARGET="$REPO/.softhouse/capture/t381-t379-conditions/instruments/t381-red-drives.sh"

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t402-verify.XXXXXXXX") || exit 2
trap 'rm -rf "$WORK"' EXIT

FAILS=0
note() { printf '  %-56s %s\n' "$1" "$2"; }
bad()  { printf '  %-56s *** %s\n' "$1" "$2"; FAILS=$((FAILS+1)); }

echo 'T402 PATCH VERIFICATION'
echo
echo '=== 1. git apply --check, every patch ====================================='
for p in "$PD"/*.patch; do
  b=$(basename "$p")
  if git -C "$REPO" apply --check "$p"; then note "$b" 'APPLIES CLEAN'; else bad "$b" 'DOES NOT APPLY'; fi
done
echo

echo '=== 2. the one EXECUTABLE patch, applied to a scratch copy ================'
if [ ! -f "$TARGET" ]; then
  bad 't381-red-drives.sh' 'TARGET NOT FOUND -- nothing verified'
else
  # Applied BY CONTENT, not by path, so this works from any worktree layout and so the
  # anchor is re-asserted at apply time rather than trusted from the patch header.
  python3 - "$PD/FU-T386-7-red-drive-must-report-failure.patch" "$TARGET" "$WORK/patched.sh" <<'PY'
import sys
patch, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
added = [l[1:] for l in open(patch, encoding='utf-8').read().splitlines()
         if l.startswith('+') and not l.startswith('+++')]
s = open(src, encoding='utf-8').read()
anchor = 'echo\necho "END OF DRIVES."\n'
if s.count(anchor) != 1:
    print('REFUSED: anchor occurs %d times' % s.count(anchor)); sys.exit(2)
# the patch's added lines begin with the blank line + the guard block
tail = '\n'.join(added) + '\n'
open(out, 'w', encoding='utf-8').write(s.replace(anchor, anchor + tail, 1))
print('  scratch copy built: %d added lines' % len(added))
PY
  if [ $? -ne 0 ]; then bad 'scratch build' 'REFUSED'; fi

  if bash -n "$WORK/patched.sh"; then note 'patched drive' 'bash -n SYNTAX OK'
  else bad 'patched drive' 'SYNTAX ERROR -- do not apply this patch'; fi

  # Extract just the guard block and drive its three outcomes.
  awk '/T402 GUARD, closing FU-T386-7|closing FU-T386-7/{f=1} f' "$WORK/patched.sh" > "$WORK/guard.sh"
  if [ "$(grep -c '' "$WORK/guard.sh")" -lt 10 ]; then
    # fall back: everything after the final "END OF DRIVES." echo
    awk '/^echo "END OF DRIVES."$/{f=1;next} f' "$WORK/patched.sh" > "$WORK/guard.sh"
  fi
  note 'guard block extracted' "$(grep -c '' "$WORK/guard.sh") line(s)"

  printf '%s\n' 'arm 1 ok' '  >>> RED CONFIRMED: everything reproduced.' > "$WORK/clean.log"
  printf '%s\n' '  >>> D-R5 DID NOT REPRODUCE in the RED specimen.'      > "$WORK/bad.log"

  T381_DRIVE_LOG="$WORK/clean.log" bash "$WORK/guard.sh" > "$WORK/o1" 2>&1; rc1=$?
  T381_DRIVE_LOG="$WORK/bad.log"   bash "$WORK/guard.sh" > "$WORK/o2" 2>&1; rc2=$?
  env -u T381_DRIVE_LOG            bash "$WORK/guard.sh" > "$WORK/o3" 2>&1; rc3=$?

  [ "$rc1" -eq 0 ] && note 'guard, CLEAN transcript      -> exit 0' 'OK' \
                   || bad  'guard, CLEAN transcript' "exit $rc1, wanted 0 -- it would refuse a good drive"
  [ "$rc2" -eq 1 ] && note 'guard, FAILING transcript    -> exit 1' 'OK' \
                   || bad  'guard, FAILING transcript' "exit $rc2, wanted 1"
  [ "$rc3" -eq 2 ] && note 'guard, NO log configured     -> exit 2' 'OK' \
                   || bad  'guard, NO log configured' "exit $rc3, wanted 2 -- an unwired guard must not read as a pass"

  echo '  -- guard output, failing transcript --'
  sed 's/^/      /' "$WORK/o2"
fi

echo
echo "VERIFY-RESULT: failures=$FAILS"
if [ "$FAILS" -eq 0 ]; then
  echo '*** ALL FOUR PATCHES CHECK, AND THE EXECUTABLE ONE BEHAVES IN ALL THREE OUTCOMES.'
else
  echo "*** $FAILS CHECK(S) FAILED. Reported through this drive's exit status."
fi
exit $(( FAILS > 0 ? 1 : 0 ))
