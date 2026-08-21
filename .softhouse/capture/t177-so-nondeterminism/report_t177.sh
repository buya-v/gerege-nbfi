#!/bin/bash
# T177 — regenerate the committed analysis transcripts from the committed raw evidence.
# Every number in the handoff comes out of these files; nothing is retyped by hand (P-46).
set -uo pipefail
REPO="$1"
RIG="$REPO/.softhouse/capture/t177-so-nondeterminism"
OUT="$RIG/out"

python3 "$RIG/calibrate_t177.py" "$REPO" "$OUT/pilot/raw/calib-0.stdout" > "$OUT/ANALYSIS-calibration.txt" 2>&1
echo "calibration exit $?" >> "$OUT/ANALYSIS-calibration.txt"

for m in pilot matrixA matrixB matrixC; do
  python3 "$RIG/analyze_t177.py" "$REPO" "$OUT/$m" > "$OUT/ANALYSIS-$m.txt" 2>&1
  echo "analyzer exit $? for $m" >> "$OUT/ANALYSIS-$m.txt"
done

python3 "$RIG/analyze_t177.py" "$REPO" "$OUT/pilot" "$OUT/matrixA" "$OUT/matrixB" "$OUT/matrixC" \
  > "$OUT/ANALYSIS-ALL.txt" 2>&1
echo "analyzer exit $? for the union of all four matrices" >> "$OUT/ANALYSIS-ALL.txt"

python3 "$RIG/t159_context.py" "$REPO" \
  T159-R600p0-N3000-B10001 T159-R600p0-N3000-B1001 T159-R600p0-N2000-B10001 T159-R600p0-N3000-B100001 \
  > "$OUT/ANALYSIS-t159-context.txt" 2>&1
echo "t159_context exit $?" >> "$OUT/ANALYSIS-t159-context.txt"

python3 "$REPO/.softhouse/capture/lib/check_no_narrow_catch.py" "$REPO" > "$OUT/ANALYSIS-lint-no-narrow-catch.txt" 2>&1
echo "lint exit $?" >> "$OUT/ANALYSIS-lint-no-narrow-catch.txt"

python3 "$RIG/build_harness_t177b.py" "$RIG" > "$OUT/ANALYSIS-harness-pair.txt" 2>&1
echo "builder exit $?" >> "$OUT/ANALYSIS-harness-pair.txt"

python3 "$RIG/check_claims_t177.py" "$REPO" > "$OUT/ANALYSIS-claim-check.txt" 2>&1
echo "claim check exit $?" >> "$OUT/ANALYSIS-claim-check.txt"

python3 "$RIG/verify_quotes_t177.py" "$REPO" > "$OUT/ANALYSIS-quote-check.txt" 2>&1
echo "quote check exit $?" >> "$OUT/ANALYSIS-quote-check.txt"

grep -c . "$OUT"/ANALYSIS-*.txt
