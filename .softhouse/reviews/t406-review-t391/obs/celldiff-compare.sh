#!/bin/bash
# T406: for each of the 14 PRE-EXISTING wrong implementations, compare the FULL
# set of cell-diff / invariant lines produced on the PRE-T391 vectors, main vs
# T391. "None died for a new reason" is then a diff over the reasons themselves.
set -u
OUT=.softhouse/reviews/t406-review-t391/obs
IMPLS=$( (cd /tmp/t406-main && /tmp/t406-conf-main -list-implementations) \
  | sed -n 's/^\([a-z0-9-][a-z0-9-]*\) *\[-ledger-impl\] DELIBERATELY WRONG:.*$/\1/p' )

reasons() { # binary, tree, impl -> the cell-diff/invariant-FAIL lines, LDG-ACC excluded
  ( cd "$2" && "$1" -oracle-probe=up -ledger-impl="$3" ) 2>&1 \
    | awk '
        /^    LDG|^    A2/ { cur=$1 }
        /want|FAIL \(|INVARIANT .*(FAIL|VIOLAT)|HARNESS ERROR|REFUSAL/ {
            line=$0; sub(/^ +/,"",line);
            if (cur !~ /^LDG-ACC/) print cur" | "line
        }' | sort
}

for i in $IMPLS; do
  reasons /tmp/t406-conf-main /tmp/t406-main  "$i" > /tmp/t406-rm.txt
  reasons /tmp/t406-conf      /tmp/t406-t391  "$i" > /tmp/t406-rt.txt
  n=$(wc -l < /tmp/t406-rm.txt | tr -d ' ')
  if diff -q /tmp/t406-rm.txt /tmp/t406-rt.txt >/dev/null; then
    echo "IDENTICAL  ($n reason lines)  $i"
  else
    echo "CHANGED    $i"
    diff -u /tmp/t406-rm.txt /tmp/t406-rt.txt | grep -E '^[-+][^-+]' | sed 's/^/    /'
  fi
done
