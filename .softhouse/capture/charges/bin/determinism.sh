#!/bin/sh
# T40 — determinism: the second issue of every request must be BYTE-IDENTICAL to the first.
# Compares out/fc (first issue) with out/fc-rerun (second issue), byte-for-byte.
set -eu
CH="${T40_WORKTREE:-$(cd "$(dirname "$0")/../../../.." && pwd)}/.softhouse/capture/charges"
rc=0
for f in "$CH"/out/fc/FC-*-raw.json; do
  n=$(basename "$f")
  if cmp -s "$f" "$CH/out/fc-rerun/$n"; then
    echo "  BYTE-IDENTICAL  $n  $(shasum -a 256 "$f" | awk '{print $1}')"
  else
    echo "  DIFFERS         $n" >&2; rc=1
  fi
done
echo
if [ "$rc" != 0 ]; then echo "DETERMINISM FAILED" >&2; exit 1; fi
echo "DETERMINISM: every capture reproduced byte-for-byte on a second issue."
