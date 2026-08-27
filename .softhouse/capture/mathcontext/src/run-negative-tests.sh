#!/usr/bin/env bash
#
# T42 -- PROVING THE TWO RECIPES AND THE CONTROL SUITE ARE FAILABLE.
#
# "An assertion suite that has never failed has not been tested" (.softhouse/patterns.md).
# Each leg below injects one deliberate breach and records the transcript.  A leg that exits 0
# is itself a failure of this script.
#
# Writes transcripts under out/negative/ and a summary to stdout.  Never touches the recorded
# capture payloads: every negative run uses its own T42_OUT_PREFIX.

set -u
CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$CAPDIR/out/negative"
mkdir -p "$OUT"

PASS=0
FAILED=0

leg() {
  local name="$1"; shift
  local file="$OUT/$name.txt"
  echo "### $name" > "$file"
  echo "\$ $*" >> "$file"
  ( "$@" ) >> "$file" 2>&1
  local rc=$?
  echo "exit=$rc" >> "$file"
  if [ "$rc" = "0" ]; then
    echo "  LEG DID NOT FAIL: $name  (exit 0 -- the assertion it targets does not work)"
    FAILED=$((FAILED + 1))
  else
    echo "  ok  $name exited $rc -- $(grep -m1 '^BREACH\|^  MISMATCH\|^FAIL' "$file" | cut -c1-140)"
    PASS=$((PASS + 1))
  fi
}

run1() { env "$@" bash "$CAPDIR/src/run-mathcontext.sh"; }
run2() { env "$@" bash "$CAPDIR/src/run-mathcontext2.sh"; }

echo "== T42 negative tests =="

# N1  wrong pin -- capture 1
leg n1-wrong-pin run1 T42_EXPECT_COMMIT=0000000000000000000000000000000000000000 T42_OUT_PREFIX=t42-neg1

# N2  wrong image id -- capture 1
leg n2-wrong-image run1 \
  T42_EXPECT_IMAGE=sha256:1111111111111111111111111111111111111111111111111111111111111111 \
  T42_OUT_PREFIX=t42-neg2

# N3  seam-class drift -- capture 1.  Append a byte, run, restore, and prove the digest returned.
SEAM="$CAPDIR/src/EmbeddableProgressiveLoanScheduleGenerator.java"
BEFORE="$(shasum -a 256 "$SEAM" | awk '{print $1}')"
echo "// T42 deliberate drift -- must be removed" >> "$SEAM"
leg n3-seam-drift run1 T42_OUT_PREFIX=t42-neg3
# restore byte for byte from the pinned original, then prove it
cp "${T42_FINERACT_DIR:-/Users/buv/fineract}/fineract-progressive-loan-embeddable-schedule-generator/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/EmbeddableProgressiveLoanScheduleGenerator.java" "$SEAM"
AFTER="$(shasum -a 256 "$SEAM" | awk '{print $1}')"
echo "seam sha256 before=$BEFORE after=$AFTER" >> "$OUT/n3-seam-drift.txt"
if [ "$BEFORE" != "$AFTER" ]; then
  echo "  SEAM NOT RESTORED: $BEFORE -> $AFTER"
  FAILED=$((FAILED + 1))
else
  echo "  ok  seam restored, sha256 $AFTER"
fi

# N4  the ABSENCE PROBE's own assertion.  Assert the canary does NOT throw; it does, so the
#     run must fail.  This is the assertion that guards the central experiment.
leg n4-canary-assertion-inverted run1 T42_EXPECT_CANARY_THROWS=0 T42_OUT_PREFIX=t42-neg4

# N5  THE WIRING ASSERTION -- capture 2.  -Dt42.breakWiring=true silently turns the Path B
#     cases into Path A cases; assertion 5 must catch it.
leg n5-broken-wiring run2 T42_JAVA_PROPS=-Dt42.breakWiring=true T42_OUT_PREFIX=t42-neg5

# N6  THE CONTROL SUITE.  Point controls.py at a payload with ONE cell corrupted.
python3 - "$CAPDIR/out/t42-mathcontext.json" "$OUT/t42-corrupted-payload.json" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
for c in doc["captures"]:
    if c["id"] == "T42-CAL":
        # 2.05 is the shipped literal; make it 2.06
        c["observed"]["totalInterestAmount"] = "2.06"
json.dump(doc, open(sys.argv[2], "w"))
print("wrote corrupted payload with T42-CAL totalInterestAmount 2.05 -> 2.06")
PY
leg n6-controls-corrupted env T42_CONTROLS_PAYLOAD="$OUT/t42-corrupted-payload.json" \
  python3 "$CAPDIR/analysis/controls.py"

echo
echo "legs that correctly failed: $PASS ; legs that did NOT fail (bad): $FAILED"
[ "$FAILED" = "0" ] || exit 1
