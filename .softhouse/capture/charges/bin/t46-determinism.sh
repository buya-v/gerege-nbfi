#!/bin/sh
# T46 -- determinism for the seven new A-3 / A-5 captures.
# The second issue of every request must be BYTE-IDENTICAL to the first.
set -eu
CH="${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}/.softhouse/capture/charges"
rc=0
n=0
same=0
for f in "$CH"/out/t46/T46-CH-*-raw.json; do
  b=$(basename "$f")
  n=$((n + 1))
  if cmp -s "$f" "$CH/out/t46-rerun/$b"; then
    same=$((same + 1))
    echo "  BYTE-IDENTICAL  $b  $(shasum -a 256 "$f" | awk '{print $1}')"
  else
    echo "  DIFFERS         $b" >&2
    rc=1
  fi
done
echo
if [ "$rc" != 0 ]; then echo "T46 DETERMINISM FAILED" >&2; exit 1; fi
echo "T46 DETERMINISM: $same of $n new captures reproduced byte-for-byte on a second issue."
