#!/bin/bash
# T428: extract the COMPLETE difference set an arm transcript reports, in every
# format the report uses:
#     "<cell>: want X, got Y"            non-money cells
#     "<cell>: MONEY want X, got Y"      money cells
#     "INVARIANT <name> VIOLATED..."     invariant breaks
# and print the counts by cell name with leg indices collapsed.
set -u
f="$1"
echo "FILE $f"
echo
echo "--- ALL indented difference lines, verbatim ---"
LC_ALL=C grep -nE '^ +[^ ].*(: want |: MONEY want |INVARIANT .*VIOLATED)' "$f"
echo
echo "--- COUNTS ---"
echo -n "non-money 'X: want' lines : "
LC_ALL=C grep -cE '^ +[^ ]+: want ' "$f"
echo -n "money     'X: MONEY want' : "
LC_ALL=C grep -cE '^ +[^ ]+: MONEY want ' "$f"
echo -n "INVARIANT VIOLATED lines  : "
LC_ALL=C grep -cE 'INVARIANT .*VIOLATED' "$f"
echo
echo "--- CELL NAMES (leg index collapsed) ---"
LC_ALL=C grep -oE '^ +[^ ]+: (MONEY )?want ' "$f" \
  | LC_ALL=C sed 's/^ *//; s/: \(MONEY \)*want $//' \
  | LC_ALL=C sed 's/\[[0-9][0-9]*\]/[i]/g' \
  | LC_ALL=C sort | LC_ALL=C uniq -c
