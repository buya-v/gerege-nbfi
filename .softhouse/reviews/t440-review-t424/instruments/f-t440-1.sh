#!/usr/bin/env bash
# T440 F-T440-1: t424-comment-claims-drive.sh's CLAIM-3 "no match" probe collides with the
# drive's own committed source. Bound the finding: the CLAIM ITSELF is still true; only the
# probe is defeated.
set -uo pipefail
REPO=$1
cd "$REPO" || exit 2
echo "repo: $REPO   head: $(git rev-parse --short HEAD)   git: $(git --version)"
echo
echo "== the probe as shipped =="
git grep -q 'zzq-no-such-token-t424' -- .softhouse >/dev/null 2>&1; a=$?
printf '  git grep -q %s -- .softhouse   -> rc=%s\n' "'zzq-no-such-token-t424'" "$a"
git grep -n 'zzq-no-such-token-t424' -- .softhouse | sed 's/^/    hit: /'
[ "$a" = 0 ] && echo "  -> the sentinel MATCHES THE DRIVE'S OWN SOURCE. The no-match arm cannot be no-match." \
             || echo "  -> no self-collision here."
echo
echo "== the claim itself, probed with a token built at RUN TIME so it cannot be in any file =="
tok="zz$$-$RANDOM-$(date +%s%N 2>/dev/null || date +%s)-t440"
git grep -q -- "$tok" -- .softhouse >/dev/null 2>&1; b=$?
printf '  genuine NO MATCH   -> rc=%s   (claim says 1)\n' "$b"
git grep -q -E '[' -- .softhouse >/dev/null 2>&1; c=$?
printf '  invalid pattern    -> rc=%s   (claim says >1)\n' "$c"
git grep -q 'Gerege' -- CLAUDE.md >/dev/null 2>&1; d=$?
printf '  genuine MATCH      -> rc=%s   (claim says 0)\n' "$d"
if [ "$b" = 1 ] && [ "$c" -gt 1 ] && [ "$d" = 0 ]; then
  echo "  -> CLAIM 3 IS TRUE. The finding is confined to the PROBE, not to the claim."
else
  echo "  -> CLAIM 3 does NOT hold on this host. That would be a larger finding."
fi
echo
echo "== the drive's own verdict, on the committed tree =="
T424_REPO="$REPO" bash "$REPO/.softhouse/capture/t424/instruments/t424-comment-claims-drive.sh" >/dev/null 2>&1
echo "  drive exit = $?  (its shipped transcript records disagreements=0, exit 0)"
