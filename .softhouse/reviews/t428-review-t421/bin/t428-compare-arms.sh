#!/bin/bash
# T428: for each wrong implementation registered on BOTH trees, compare the exact
# set of difference lines the arm reports. A "reason" here is the ordered list of
# FAILing case ids and the verbatim difference lines under them -- not just the
# FAIL count. Any change means the arm died for a DIFFERENT reason.
set -u
A="$1"   # main arms dir
B="$2"   # t421 arms dir
tmp=$(mktemp -d)
same=0; moved=0; onlyB=0
for f in "$B"/arm-*.txt; do
  n=$(basename "$f")
  if [ ! -f "$A/$n" ]; then
    echo "ONLY-ON-T421: $n"
    onlyB=$((onlyB+1))
    continue
  fi
  # Difference lines plus the FAIL case rows; repo paths differ between trees so
  # nothing path-shaped is compared.
  LC_ALL=C grep -E '^ +[^ ]+: (MONEY )?want |INVARIANT .*VIOLATED|  FAIL ' "$A/$n" > "$tmp/a"
  LC_ALL=C grep -E '^ +[^ ]+: (MONEY )?want |INVARIANT .*VIOLATED|  FAIL ' "$f"      > "$tmp/b"
  if cmp -s "$tmp/a" "$tmp/b"; then
    echo "IDENTICAL-REASON: $n  ($(LC_ALL=C grep -c '' "$tmp/a") difference/verdict lines)"
    same=$((same+1))
  else
    echo "REASON MOVED:     $n"
    diff "$tmp/a" "$tmp/b" | sed 's/^/      /'
    moved=$((moved+1))
  fi
done
echo
echo "ARMS COMPARED: identical=$same moved=$moved onlyOnT421=$onlyB"
rm -rf "$tmp"
