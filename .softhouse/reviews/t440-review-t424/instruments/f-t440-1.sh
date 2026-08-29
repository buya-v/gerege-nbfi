#!/usr/bin/env bash
# =============================================================================================
# T440 F-T440-1. `t424-comment-claims-drive.sh`'s CLAIM-3 "no match" probe uses the literal
# `zzq-no-such-token-t424`, which is COMMITTED IN THE DRIVE'S OWN SOURCE -- so `git grep` finds
# it and the arm cannot be a no-match. This bounds the finding: the CLAIM is still true; only
# the PROBE is defeated.
#
# BOTH PATHS ARE REQUIRED ARGUMENTS AND THERE IS NO DEFAULT. The subject drive exists only on
# the branch under review; a hardcoded path to it would be a DEAD REPO-PATH REFERENCE on every
# tree that does not carry T424, and `guard_dead_path_frontier` would refuse -- correctly. It
# did: T440's first draft of this file hardcoded the path and turned the bar RED on T440's own
# branch (exit 2, +1 frontier row). Rather than spell the literal in pieces to slip past the
# census -- which would be gaming a guard this program pays for -- the path is simply an
# argument, and this script REFUSES when it does not resolve. That is the remedy the guard
# itself names.
#
#   usage: f-t440-1.sh <repo-root-of-the-tree-under-review> <path-to-the-drive, repo-relative>
#
# EXIT: 0 the probe was examined and the claim was driven; 2 an argument did not resolve.
# =============================================================================================
set -uo pipefail
REPO=${1:?usage: f-t440-1.sh <repo-root> <drive-path-relative-to-repo>}
DRIVE_REL=${2:?usage: f-t440-1.sh <repo-root> <drive-path-relative-to-repo> -- no default; see the header}
[ -d "$REPO/.git" ] || [ -f "$REPO/.git" ] || { echo "REFUSED: $REPO is not a checkout" >&2; exit 2; }
DRIVE="$REPO/$DRIVE_REL"
[ -r "$DRIVE" ] || { echo "REFUSED: cannot read the drive under review at [$DRIVE]." >&2
                     echo "  Pass its path as \$2. This script does not guess." >&2; exit 2; }

cd "$REPO" || exit 2
echo "repo : $REPO   head: $(git rev-parse --short HEAD)   git: $(git --version)"
echo "drive: $DRIVE_REL"
echo

echo "== the probe AS SHIPPED =="
SENT=$(grep -oE "zzq-no-such-token-[a-z0-9]+" "$DRIVE" | head -1)
[ -n "$SENT" ] || { echo "REFUSED: no zzq-no-such-token-* sentinel found in the drive." >&2; exit 2; }
printf '  sentinel read out of the drive: [%s]\n' "$SENT"
git grep -q "$SENT" -- .softhouse >/dev/null 2>&1; a=$?
printf '  git grep -q <sentinel> -- .softhouse   -> rc=%s\n' "$a"
git grep -n "$SENT" -- .softhouse | sed 's/^/    hit: /'
if [ "$a" = 0 ]; then
  echo "  -> THE SENTINEL MATCHES THE DRIVE'S OWN COMMITTED SOURCE."
  echo "     The no-match arm cannot be a no-match, so CLAIM 3 scores DRIVE DISAGREES."
else
  echo "  -> no self-collision on this tree."
fi
echo

echo "== the CLAIM itself, probed with a token built at RUN TIME so it is in no file =="
tok="zz$$-$RANDOM-$(date +%s)-t440"
git grep -q -- "$tok" -- .softhouse >/dev/null 2>&1; b=$?
printf '  genuine NO MATCH   -> rc=%s   (the claim says 1)\n' "$b"
git grep -q -E '[' -- .softhouse >/dev/null 2>&1; c=$?
printf '  invalid pattern    -> rc=%s   (the claim says >1)\n' "$c"
git grep -q 'Gerege' -- CLAUDE.md >/dev/null 2>&1; d=$?
printf '  genuine MATCH      -> rc=%s   (the claim says 0)\n' "$d"
if [ "$b" = 1 ] && [ "$c" -gt 1 ] && [ "$d" = 0 ]; then
  echo "  -> CLAIM 3 IS TRUE. The finding is confined to the PROBE, not to the claim."
else
  echo "  -> CLAIM 3 does NOT hold on this host. That would be a LARGER finding."
fi
echo

echo "== the drive's own verdict, on the COMMITTED tree =="
T424_REPO="$REPO" bash "$DRIVE" >/dev/null 2>&1
echo "  drive exit = $?   (its shipped transcript records disagreements=0, exit 0)"
