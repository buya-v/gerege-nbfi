#!/bin/sh
# T391 -- the NON-VACUITY drive for `ledger-wrong-slot-family-blind`, in BOTH
# directions, plus a control.
#
# A VECTOR NO WRONG IMPLEMENTATION CAN FAIL IS DECORATION, and a wrong
# implementation that fails EVERYTHING is decoration of the opposite kind: it
# proves the corpus discriminates something, not that these vectors do. So this
# script records three things, and a reader should demand all three:
#
#   ARM 1  THE KILL. -ledger-impl ledger-wrong-slot-family-blind against the FULL
#          committed corpus. LDG-ACC-01/02/03 must FAIL and every other vector
#          must PASS. If an unrelated vector fails, the kill has stopped being
#          load-bearing.
#
#   ARM 2  THE CONTROL, and it is the one that makes ARM 1 mean anything: the
#          same wrong implementation must be BYTE-IDENTICAL to ledger-go on the
#          seven parity vectors that predate T391. ARM 1 already shows this as
#          PASS/FAIL; this arm shows the CELLS, so "identical" is measured rather
#          than inferred from an outcome.
#
#   ARM 3  THE REFERENCE. -ledger-impl ledger-go must be green on everything.
#
# The WITHHELD-CORPUS direction -- the wrong implementation SURVIVING when these
# vectors do not exist -- is recorded separately and was taken BEFORE the vectors
# were written, at out/T391-10-RED-wrongimpl-survives-without-vectors.txt. It
# cannot be re-taken now without deleting the vectors, and a drive that deletes
# the evidence it is drives is not a drive.
set -eu
ROOT=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$ROOT/nexus"
CMD="./internal/apps/loanschedule/conformance/cmd/conformance"

# `-oracle-probe=up` IS NOT OPTIONAL AND IS NOT A LIE. .softhouse/conformance.sh
# probes the reference oracle itself and passes the RESULT to the binary
# (main_grade: `"$CONF_BIN" "-oracle-probe=$probe"`); a binary run without it
# defaults to "the oracle is unreachable" and returns EXIT 2 -- UNUSABLE, not a
# pass and not a failure. The first draft of this script omitted it, `go run`
# reported that 2 as its own exit 1, and both arms looked like ledger failures
# when the LEDGER section had in fact printed PASS 10 FAIL 0. That is P-84 in a
# second costume: read WHY the status is non-zero before reading it as a result.
# The probe below is asserted live before it is passed, so this script cannot
# claim `up` about an oracle that is down.
PROBE_URL="https://localhost:8443/fineract-provider/actuator/health"
if ! curl -sk --max-time 10 "$PROBE_URL" | grep -q '"status":"UP"'; then
  echo "REFUSING: the reference oracle is not UP at $PROBE_URL. This drive will not pass" >&2
  echo "  -oracle-probe=up about an oracle it has not seen." >&2
  exit 2
fi
echo "oracle probe = up (asserted live against $PROBE_URL)"


echo "================================================================"
echo "ARM 1 -- THE KILL: -ledger-impl ledger-wrong-slot-family-blind"
echo "================================================================"
set +e
go run "$CMD" -oracle-probe=up -ledger-impl ledger-wrong-slot-family-blind 2>&1 |
  sed -n '/--- LEDGER/,/ledger cells compared/p'
echo "ARM 1 exit status of the FULL run:"
go run "$CMD" -oracle-probe=up -ledger-impl ledger-wrong-slot-family-blind >/dev/null 2>&1
echo "  exit=$?"

echo
echo "================================================================"
echo "ARM 1b -- THE DIVERGENT CELLS, printed rather than summarised"
echo "================================================================"
go run "$CMD" -oracle-probe=up -ledger-impl ledger-wrong-slot-family-blind 2>&1 |
  grep -A 20 'LDG-ACC-01' | grep -iE 'slot_name|FAIL|want|got' | head -40

echo
echo "================================================================"
echo "ARM 3 -- THE REFERENCE: -ledger-impl ledger-go"
echo "================================================================"
go run "$CMD" -oracle-probe=up -ledger-impl ledger-go 2>&1 |
  sed -n '/--- LEDGER/,/ledger cells compared/p'
echo "ARM 3 exit status of the FULL run:"
go run "$CMD" -oracle-probe=up -ledger-impl ledger-go >/dev/null 2>&1
echo "  exit=$?"
set -e
