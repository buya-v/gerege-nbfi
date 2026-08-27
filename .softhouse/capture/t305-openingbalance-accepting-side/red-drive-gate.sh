#!/bin/sh
# T305 -- RED-DRIVE OF guard-accepting-capture.sh.
#
# P-22: "a control that cannot fail is worse than none". A gate that refuses everything is
# indistinguishable from a gate that is broken, and this one refuses everything TODAY, so
# the distinction has to be MEASURED rather than asserted.
#
# THIS RIG SUBSTITUTES NOTHING INTO THE MEASURED CONDITIONS, ON PURPOSE. T294's fence
# carried `T294_WHATIF_*` override variables; this one deliberately does not, because a
# gate whose greens can be manufactured by an environment variable is a gate the next task
# can talk its way past. Four of the five conditions are driven BOTH WAYS by the two REAL
# tenants, which is stronger evidence than any fabricated arm:
#
#   C1 rounding-mode   ok on gerege (4 = HALF_UP)      REFUSE on default (6 = HALF_EVEN)
#   C2 timezone        ok on gerege (Asia/Ulaanbaatar) REFUSE on default (Asia/Kolkata)
#   C3 empty ledger    ok on default (0 ids)           REFUSE on gerege (26 ids)
#   C4 type-300 EQUITY ok on gerege (GL 15, enum 3)    REFUSE on default (UNMAPPED)
#
# C5 (the disposability attestation) has never been seen `ok`, because no attestation
# exists and none should. ARM 3 below creates one in a temp file, proves C5 flips, and
# REMOVES IT AGAIN -- so the wiring is demonstrated without leaving a live authorisation
# for an irreversible capture lying in the tree.
#
# WHAT IS NOT DRIVEN, AND IT IS SAID HERE RATHER THAN LEFT TO BE DISCOVERED: the guard's
# EXIT 0 branch is UNREACHED. Reaching it needs a tenant passing all five at once and no
# such tenant exists on this rig. The first task that creates a qualifying tenant is the
# task that exercises that branch, and it should say so in its handoff.
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
G="$DIR/guard-accepting-capture.sh"
FAILED=0

check() { # check LABEL EXPECTED_EXIT ACTUAL_EXIT
  if [ "$2" = "$3" ]; then printf 'ok      %-58s exit %s\n' "$1" "$3"
  else printf 'NOT OK  %-58s exit %s, expected %s\n' "$1" "$3" "$2"; FAILED=1; fi
}
grepcheck() { # grepcheck LABEL FILE PATTERN
  if grep -q "$3" "$2"; then printf 'ok      %-58s\n' "$1"
  else printf 'NOT OK  %-58s (pattern absent: %s)\n' "$1" "$3"; FAILED=1; fi
}

TMPD=$(mktemp -d "${TMPDIR:-/tmp}/t305rd.XXXXXX")
trap 'rm -rf "$TMPD"; rm -f "$DIR/attest/default.disposable"; rmdir "$DIR/attest" 2>/dev/null' EXIT HUP INT TERM QUIT

echo "--- ARM 1: BASELINE, as the tree stands. Expect REFUSED, exit 1."
rc=0; sh "$G" > "$TMPD/arm1.txt" 2>&1 || rc=$?
check "ARM 1 baseline refuses" 1 "$rc"
grepcheck "ARM 1 measured 2 tenants, 0 qualify"   "$TMPD/arm1.txt" 'measured 2 tenant(s); 0 qualify'
grepcheck "ARM 1 C1 ok on gerege (HALF_UP)"       "$TMPD/arm1.txt" 'ok    C1 rounding-mode = 4'
grepcheck "ARM 1 C1 REFUSE on default (HALF_EVEN)" "$TMPD/arm1.txt" 'REFUSE C1 rounding-mode = 6'
grepcheck "ARM 1 C2 ok on gerege"                 "$TMPD/arm1.txt" 'ok    C2 timezone Asia/Ulaanbaatar'
grepcheck "ARM 1 C2 REFUSE on default"            "$TMPD/arm1.txt" 'REFUSE C2 timezone Asia/Kolkata'
grepcheck "ARM 1 C3 ok on default (EMPTY)"        "$TMPD/arm1.txt" 'ok    C3 findNonContraTransactionIds is EMPTY'
grepcheck "ARM 1 C3 REFUSE on gerege (26 ids)"    "$TMPD/arm1.txt" 'REFUSE C3 findNonContraTransactionIds has 26'
grepcheck "ARM 1 C4 ok on gerege (GL 15 EQUITY)"  "$TMPD/arm1.txt" 'ok    C4 type 300 -> GL 15'
grepcheck "ARM 1 C4 REFUSE on default (UNMAPPED)" "$TMPD/arm1.txt" 'REFUSE C4 financial-activity type 300 is UNMAPPED'
grepcheck "ARM 1 C5 REFUSE on both"               "$TMPD/arm1.txt" 'REFUSE C5 NO disposability attestation'
echo ""

echo "--- ARM 2: unreachable database. Expect EXIT 2 -- CANNOT MEASURE, not a refusal."
rc=0
DBC=no-such-container-t305 sh "$G" > "$TMPD/arm2.txt" 2>&1 || rc=$?
check "ARM 2 fails CLOSED on an unreachable database" 2 "$rc"
grepcheck "ARM 2 says so in words"  "$TMPD/arm2.txt" 'CANNOT MEASURE'
grepcheck "ARM 2 refuses to call it a pass" "$TMPD/arm2.txt" 'not a refusal and not a pass'
echo ""

echo "--- ARM 3: C5 WIRING. A disposability attestation is created for 'default', then removed."
mkdir -p "$DIR/attest"
cat > "$DIR/attest/default.disposable" <<'ATT'
RED-DRIVE ARTEFACT ONLY. If you are reading this file in a committed tree, something is
wrong: red-drive-gate.sh creates it and deletes it in the same run. It is NOT an
authorisation to fire anything.
ATT
rc=0; sh "$G" > "$TMPD/arm3.txt" 2>&1 || rc=$?
check "ARM 3 STILL refuses (C1/C2/C4 unchanged on default)" 1 "$rc"
grepcheck "ARM 3 C5 FLIPPED to ok on default"     "$TMPD/arm3.txt" 'ok    C5 a disposability attestation exists'
grepcheck "ARM 3 default is still REFUSED overall" "$TMPD/arm3.txt" "tenant 'default' REFUSED"
rm -f "$DIR/attest/default.disposable"; rmdir "$DIR/attest" 2>/dev/null
rc=0; sh "$G" > "$TMPD/arm3b.txt" 2>&1 || rc=$?
grepcheck "ARM 3b C5 back to REFUSE once removed" "$TMPD/arm3b.txt" 'REFUSE C5 NO disposability attestation'
echo ""

if [ "$FAILED" -eq 0 ]; then
  echo "RED-DRIVE PASS: every assertion above held. The gate refuses BY MEASUREMENT and each"
  echo "of C1-C4 was observed in BOTH states without substituting anything; C5's wiring was"
  echo "demonstrated and its authorisation removed again."
  exit 0
fi
echo "RED-DRIVE FAILED. The gate is not behaving as documented; do not trust its verdict."
exit 1
