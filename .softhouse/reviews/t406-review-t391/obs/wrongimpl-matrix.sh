#!/bin/bash
# T406: run EVERY registered wrong ledger implementation on BOTH trees and record
# its failure SIGNATURE (which vectors failed, on which cells), so "the other 14
# still die and none died for a NEW reason" is a diff and not an assertion.
set -u
OUT=.softhouse/reviews/t406-review-t391/obs
mkdir -p "$OUT/sig-main" "$OUT/sig-t391"

sig() { # $1 = binary, $2 = tree, $3 = impl, $4 = outfile
  ( cd "$2" && "$1" -oracle-probe=up -ledger-impl="$3" ) > /tmp/t406-sig.raw 2>&1
  echo "exit=$?" > "$4"
  grep -E '^    (LDG|A2)[^ ]* +(parity|oracle-refusal|divergence) ' /tmp/t406-sig.raw \
    | sed -E 's/ +/ /g' | awk '{print $1, $NF=="money)"?$(NF-2):$0}' >/dev/null 2>&1
  # the verdict line per vector, normalised
  grep -E '^ +LDG[^ ]* +(parity|oracle-refusal|divergence) ' /tmp/t406-sig.raw \
    | sed -E 's/^ +//; s/ +/ /g' | cut -d' ' -f1,2,4 >> "$4"
  echo '--- cell diffs ---' >> "$4"
  grep -E 'want ".*", got ".*"|: want |INVARIANT .* FAIL|HARNESS ERROR' /tmp/t406-sig.raw \
    | sed -E 's/^ +//' | sort >> "$4"
  echo '--- tallies ---' >> "$4"
  grep -E 'ledger parity +PASS|ledger inadmissible|ledger harness errors' /tmp/t406-sig.raw \
    | sed -E 's/^ +//; s/ +/ /g' >> "$4"
}

MAINIMPLS=$( (cd /tmp/t406-main && /tmp/t406-conf-main -list-implementations) \
  | sed -n 's/^\([a-z0-9-][a-z0-9-]*\) *\[-ledger-impl\] DELIBERATELY WRONG:.*$/\1/p' )
T391IMPLS=$( (cd /tmp/t406-t391 && /tmp/t406-conf -list-implementations) \
  | sed -n 's/^\([a-z0-9-][a-z0-9-]*\) *\[-ledger-impl\] DELIBERATELY WRONG:.*$/\1/p' )

echo "MAIN wrong impls: $(echo "$MAINIMPLS" | wc -l | tr -d ' ')"
echo "T391 wrong impls: $(echo "$T391IMPLS" | wc -l | tr -d ' ')"
echo "NEW on T391:"
comm -13 <(echo "$MAINIMPLS" | sort) <(echo "$T391IMPLS" | sort) | sed 's/^/  + /'
echo "REMOVED on T391:"
comm -23 <(echo "$MAINIMPLS" | sort) <(echo "$T391IMPLS" | sort) | sed 's/^/  - /'
echo

for i in $MAINIMPLS; do sig /tmp/t406-conf-main /tmp/t406-main "$i" "$OUT/sig-main/$i.txt"; done
for i in $T391IMPLS; do sig /tmp/t406-conf      /tmp/t406-t391 "$i" "$OUT/sig-t391/$i.txt"; done

echo "=== per-implementation SIGNATURE DIFF (main -> T391) ==="
for i in $MAINIMPLS; do
  echo "--- $i"
  if diff -u "$OUT/sig-main/$i.txt" "$OUT/sig-t391/$i.txt" > /tmp/t406-d.txt; then
    echo "    IDENTICAL signature"
  else
    grep -E '^[-+][^-+]' /tmp/t406-d.txt | sed 's/^/    /'
  fi
done
