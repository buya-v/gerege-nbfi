#!/bin/bash
# T428: every PINNED/CENSUS/verdict figure in two bar transcripts, side by side.
set -u
a="$1"; b="$2"; out="$3"
pat='== pinned|VERDICT: |POPULATION|deadOccurrences|DEADPATH-CENSUS|parity vectors match|ledger parity |ledger oracle-refusal |divergence vectors |cells compared|DIED through this harness|forbidden identifiers|float-shaped tokens|NOT byte-preserved'
LC_ALL=C grep -hoE "conformance:.*($pat).*|VERDICT: .*|    ledger .*|      divergence .*" "$a" | LC_ALL=C sed 's/[0-9]\{1,\}/#/g' > /tmp/t428-a-shape.txt
LC_ALL=C grep -E "$pat" "$a" | LC_ALL=C sed 's/^ *//' | LC_ALL=C sort > /tmp/t428-a.txt
LC_ALL=C grep -E "$pat" "$b" | LC_ALL=C sed 's/^ *//' | LC_ALL=C sort > /tmp/t428-b.txt
{
  echo "T428 BAR FIGURE DIFF"
  echo "A = $a"
  echo "B = $b"
  echo
  echo "--- lines present in A but not B  (< A) and B but not A (> B) ---"
  diff /tmp/t428-a.txt /tmp/t428-b.txt
  echo "(empty means every graded figure is identical)"
} > "$out"
cat "$out"
