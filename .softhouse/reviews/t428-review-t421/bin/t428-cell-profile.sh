#!/bin/bash
# T428: for every arm transcript in a directory, print the FAIL cases, the count
# of "want/got" cell differences, and the distinct cell names (leg indices
# collapsed to [i]). Purely textual; nothing here parses a number as a number.
set -u
d="$1"
cd "$d" || exit 9
for f in arm-*.txt; do
  n=$(LC_ALL=C grep -cE '^ +[A-Za-z_][A-Za-z0-9_.]*(\[[0-9]+\])?(\.[A-Za-z0-9_]+)*: want ' "$f")
  c=$(LC_ALL=C grep -oE '^ +[A-Za-z_][A-Za-z0-9_.]*(\[[0-9]+\])?(\.[A-Za-z0-9_]+)*: want ' "$f" \
      | LC_ALL=C sed 's/^ *//; s/: want $//' | LC_ALL=C sed 's/\[[0-9][0-9]*\]/[i]/g' \
      | LC_ALL=C sort | LC_ALL=C uniq -c | LC_ALL=C tr '\n' ';')
  p=$(LC_ALL=C sed -n 's/^ *ledger parity  *\(PASS [0-9]* *FAIL [0-9]*\).*/\1/p' "$f" | head -1)
  o=$(LC_ALL=C sed -n 's/^ *ledger oracle-refusal  *\(PASS [0-9]* *FAIL [0-9]*\).*/\1/p' "$f" | head -1)
  fails=$(LC_ALL=C grep -oE '^ +[A-Z0-9-]+[^ ]* +(parity|oracle_refusal|refusal|divergence) ' "$f" | true)
  echo "### $f"
  echo "    parity: $p | refusal: $o"
  echo "    want/got cell differences: $n"
  echo "    cells: $c"
  LC_ALL=C grep -E '  FAIL ' "$f" | LC_ALL=C sed 's/^/    FAILCASE /' | head -20
done
