#!/bin/sh
# T180 — run `t80/prove-f1.sh` END TO END, in a THROWAWAY CLONE, and print the live
# attester's sha256 before and after.
#
# WHY THIS EXISTS.  `REPRODUCE.md` documents the F-1 proof as `sh t80/prove-f1.sh`, and the
# committed transcript `out/F1-attest-gate-order.txt` was taken that way — against a real
# worktree rig, before T161.  T161's standing instruction is that the proof is never run
# against the real t36 rig again, because an interruption inside it IS the corruption under
# test.  So the green transcript is taken here instead: same script, same invocation, same
# evidence set, in a clone that is deleted afterwards.
#
# This is NOT a substitute for `prove-f1-noswap.py`.  That prover is what grades the claim,
# with a RED arm, an ablation and a null control.  This script only produces the ordinary
# end-to-end transcript, and it asserts one thing: the clone's `t36/attest.py` hashes the
# same before and after.
#
# Usage:  sh t80/prove-f1-sandbox-run.sh
# Exit 0 only if prove-f1.sh exited 0 AND the attester digest did not move.
set -u
T80=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$T80/../../../.." && pwd)
REL_A=.softhouse/capture/pathb/t36/attest.py
REL_SCRIPT=.softhouse/capture/pathb/t80/prove-f1.sh
WANT=567e4cf04a8704742800e9492fb18c252de7618ffba36a3d812c85b1320502c2

# P-58: name the binary behind any digest asserted here.  `shasum` on $PATH is not good
# enough for evidence; the rig's own hardened instrument is.
. "$REPO/.softhouse/capture/pathb/t36/sha256.sh"
sha256_init || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }
digest() { sha256_file "$1" || { echo "REFUSED: $SHA256_ERROR" >&2; exit 1; }; printf '%s\n' "$SHA256_RESULT"; }

SB=$(mktemp -d "${TMPDIR:-/tmp}/t180-green.XXXXXXXX") || exit 1
cleanup() { rm -rf "$SB"; }
trap cleanup EXIT INT TERM HUP QUIT PIPE

git clone --shared --quiet "$REPO" "$SB/repo" || { echo "REFUSED: could not clone a sandbox" >&2; exit 1; }
# The working tree's prove-f1.sh, not the committed one: this transcript must describe the
# bytes under review, and refusing to say so would make it a transcript of something else.
cp "$REPO/$REL_SCRIPT" "$SB/repo/$REL_SCRIPT" || exit 1

echo "=== T180 — green transcript: t80/prove-f1.sh end to end, in a throwaway clone"
echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "source repo : $REPO"
echo "sandbox     : $SB/repo   (clone at $(git -C "$SB/repo" rev-parse --short=12 HEAD))"
echo "script under test: $REL_SCRIPT sha256 $(digest "$REPO/$REL_SCRIPT")"
echo

BEFORE=$(digest "$SB/repo/$REL_A")
echo "live $REL_A"
echo "  BEFORE: $BEFORE"
[ "$BEFORE" = "$WANT" ] || { echo "REFUSED: the clone's attester is not the pinned $WANT" >&2; exit 1; }
echo

sh "$SB/repo/$REL_SCRIPT"
st=$?
echo
echo "prove-f1.sh EXIT=$st"
echo

AFTER=$(digest "$SB/repo/$REL_A")
echo "live $REL_A"
echo "  BEFORE: $BEFORE"
echo "  AFTER : $AFTER"
echo "  sibling t36/.f1-prefix-attest.py present after the run: $( [ -e "$SB/repo/.softhouse/capture/pathb/t36/.f1-prefix-attest.py" ] && echo YES || echo no )"
echo "  in-flight marker present after the run                : $( [ -e "$SB/repo/.softhouse/capture/pathb/t80/.f1-swap-in-progress" ] && echo YES || echo no )"
echo "  git status over the whole capture tree:"
git -C "$SB/repo" status --porcelain -- .softhouse/capture/pathb | sed 's/^/    /'
echo "    (the line above for t80/prove-f1.sh is this script copying the bytes under test in;"
echo "     anything else would be residue the proof failed to clean)"
echo

rc=0
if [ "$AFTER" = "$BEFORE" ]; then
  echo "VERDICT: the live attester did NOT move — $AFTER"
else
  echo "VERDICT: THE LIVE ATTESTER MOVED, $BEFORE -> $AFTER"; rc=1
fi
[ "$st" = 0 ] || { echo "VERDICT: prove-f1.sh did not exit 0"; rc=1; }
[ "$rc" = 0 ] && echo "RESULT: GREEN"
[ "$rc" = 0 ] || echo "RESULT: FAILED"
exit "$rc"
