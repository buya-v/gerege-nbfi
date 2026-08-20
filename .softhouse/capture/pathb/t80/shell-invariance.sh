#!/bin/sh
# T80 — ATTACK 4 of the acceptance test: the recipe must not behave differently under `sh` and
# `bash`.  Compares every attack transcript pair, ignoring only line 2 (which records which
# interpreter produced it) and the interpreter name inside the echoed command line.
#
# NOTE, deliberately not fixed here: `.softhouse/conformance.sh` must be invoked as
# `bash .softhouse/conformance.sh` — under `sh` it dies on process substitution and exits 2,
# which is the harness's "oracle unusable" fatal code and would read as a false oracle-down
# park.  That is T81's fix (T77 P2-T77-5); it is a different script and out of T80's scope.
set -u
T80=$(cd "$(dirname "$0")" && pwd)
O=$T80/out
diffs=0
n=0
for f in "$O"/attack-*-sh.txt; do
  b=$(echo "$f" | sed 's/-sh\.txt$/-bash.txt/')
  n=$((n+1))
  if [ ! -f "$b" ]; then
    echo "MISSING bash counterpart for $(basename "$f")"
    diffs=$((diffs+1))
    continue
  fi
  # Normalise: drop the "runner shell / recipe interpreter" line, and rewrite the echoed
  # interpreter token so the two commands read the same.
  sed -e '2d' -e 's/"\$SH"/<SHELL>/g' "$f" > "$O/.norm-sh.$$"
  sed -e '2d' -e 's/"\$SH"/<SHELL>/g' "$b" > "$O/.norm-bash.$$"
  if diff -q "$O/.norm-sh.$$" "$O/.norm-bash.$$" > /dev/null; then
    echo "IDENTICAL  $(basename "$f")  vs  $(basename "$b")"
  else
    echo "DIFFERS    $(basename "$f")  vs  $(basename "$b")"
    diff "$O/.norm-sh.$$" "$O/.norm-bash.$$"
    diffs=$((diffs+1))
  fi
  rm -f "$O/.norm-sh.$$" "$O/.norm-bash.$$"
done
echo
echo "pairs compared: $n   differing: $diffs"
[ "$diffs" = "0" ] || exit 1
echo "RESULT: the recipe behaves IDENTICALLY under sh and bash across every attack."
exit 0
