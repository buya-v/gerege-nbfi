#!/bin/sh
# T46 -- proof for T44 finding A-7 (and an independent third issue of the whole corpus).
#
# `bin/t46-fix-paths.py` rewrote the hard-coded worktree root in 11 bin/ scripts to a
# self-locating one.  A path fix must change nothing observable.  This re-issues all 21
# requests through the FIXED scripts into out/t46-reissue/ and compares them byte-for-byte
# with T40's committed out/fc/.
#
# It is also a THIRD independent issue of the corpus (T40 recorded two), taken on a different
# day by a different task, so a byte-identical result is determinism evidence in its own right.
set -eu
CH="${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}/.softhouse/capture/charges"
NEW=${1:-$CH/out/t46-reissue}

rc=0
n=0
same=0
for f in "$CH"/out/fc/FC-*-raw.json; do
  b=$(basename "$f")
  n=$((n + 1))
  if cmp -s "$f" "$NEW/$b"; then
    same=$((same + 1))
    echo "  BYTE-IDENTICAL  $b  $(shasum -a 256 "$f" | awk '{print $1}')"
  else
    echo "  DIFFERS         $b" >&2
    rc=1
  fi
done

echo
echo "T46 A-7 proof: $same of $n committed charge responses reproduced BYTE-FOR-BYTE"
echo "through the path-fixed scripts, on a third independent issue."
if [ "$rc" != 0 ]; then
  echo "RE-ISSUE IDENTITY FAILED -- the path fix or the oracle changed something." >&2
  exit 1
fi
