#!/bin/sh
# T305 -- RED-DRIVE the STEP 4 contra expansion and the two wrong implementations.
#
# P-22, verbatim: "A guard, a canary, or a control that cannot fail is worse than none -- because
# it is believed." STEP 4 is a NEW behaviour on a money path. This script deletes it, shows the
# tests and the corpus going RED, and puts it back -- so the green run above it is a measurement
# and not a hope.
#
# FOUR ARMS:
#   1  BASELINE          the committed tree: ledger tests green, LDG-05 PASS
#   2  NO CONTRA         STEP 4 removed from GoPoster: LDG-05 must FAIL
#   3  ARM A             -ledger-impl ledger-wrong-openingbalance-always-refusing: must FAIL
#   4  NO-CONTRA IMPL    -ledger-impl ledger-wrong-openingbalance-no-contra: must FAIL
#
# It edits impl.go IN PLACE and restores it from a backup in a trap, so an interrupted run cannot
# leave the port mutated. The restore is verified by sha256, not assumed.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$DIR/../../../.." && pwd)
IMPL="$REPO/nexus/internal/apps/ledger/conformance/impl.go"
BAK=$(mktemp "${TMPDIR:-/tmp}/t305-impl.XXXXXXXX")
BEFORE=$(shasum -a 256 "$IMPL" | awk '{print $1}')
cp "$IMPL" "$BAK"
restore() {
  cp "$BAK" "$IMPL"
  AFTER=$(shasum -a 256 "$IMPL" | awk '{print $1}')
  rm -f "$BAK"
  if [ "$AFTER" = "$BEFORE" ]; then
    printf 'RESTORED: impl.go sha256 %s == before\n' "$AFTER"
  else
    printf '*** IMPL.GO NOT RESTORED: before %s after %s ***\n' "$BEFORE" "$AFTER"
    exit 1
  fi
}
trap restore EXIT INT TERM

cd "$REPO/nexus"
BIN="./internal/apps/loanschedule/conformance/cmd/conformance"

printf '\n=== ARM 1  BASELINE -- the committed tree\n'
go test ./internal/apps/ledger/... 2>&1 | tail -3
go run "$BIN" -oracle-probe=up 2>&1 | grep -E 'LDG-05|ledger parity ' || true

printf '\n=== ARM 2  NO CONTRA -- STEP 4 deleted from GoPoster\n'
python3 - "$IMPL" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
start = s.index('\tif req.Command == "defineOpeningBalance" {\n\t\tcontra, ok := chart[req.ContraGLAccountID]')
end = s.index("\n\treturn out, nil, nil\n}", start)
open(p, "w").write(s[:start] + s[end:].lstrip("\n"))
print("STEP 4 removed")
PY
go test ./internal/apps/ledger/... 2>&1 | grep -E 'FAIL|ok ' | head -6 || true
go run "$BIN" -oracle-probe=up 2>&1 | grep -E 'LDG-05|ledger parity ' || true
restore
trap - EXIT INT TERM
trap 'true' EXIT

printf '\n=== ARM 3  ledger-wrong-openingbalance-always-refusing (T296 arm A)\n'
go run "$BIN" -oracle-probe=up -ledger-impl=ledger-wrong-openingbalance-always-refusing 2>&1 \
  | grep -E 'LDG-05|LDG-REFUSE-03|ledger parity |ledger oracle-refusal ' || true

printf '\n=== ARM 4  ledger-wrong-openingbalance-no-contra\n'
go run "$BIN" -oracle-probe=up -ledger-impl=ledger-wrong-openingbalance-no-contra 2>&1 \
  | grep -E 'LDG-05|total_|leg_count|ledger parity ' || true

printf '\n=== impl.go final sha256: %s (before: %s)\n' "$(shasum -a 256 "$IMPL" | awk '{print $1}')" "$BEFORE"
