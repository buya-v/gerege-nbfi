#!/bin/sh
# T80 — run every attack against the HARDENED recipe and write one transcript per attack.
#
# "An attack you describe but did not run is UNVERIFIED."  This script is the thing that was
# actually run; the transcripts in out/ are its output, verbatim, including the exit codes.
#
# It sends only POST /loans?command=calculateLoanSchedule (a pure calculation endpoint) and
# read-only docker/psql queries.  It creates no tenant, restarts nothing, writes no oracle row.
#
# Usage:  sh t80/run-attacks.sh      /      bash t80/run-attacks.sh
set -u
T80=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$T80/.." && pwd)
O=$T80/out
mkdir -p "$O"
cd "$W"

CANON=$W/t22-audit/req/calc-pmode2-gerege.json
PIN=2a6621beb48f753c5a078b0b6ca775c317d36f815f08be3c6ce6e8ab93352154

# The mutated canary: ONE character.  1162502.5 -> 1162502.55.  x 0.018 = 20925.0459, which is not
# a half-minor-unit tie, so it rounds to 20925.05 under HALF_UP *and* HALF_EVEN.  This is exactly
# T77's P0-T77-1 exploit against T76's substring pin.
sed 's/"principal": 1162502.5,/"principal": 1162502.55,/' "$CANON" > "$O/attack-2-req-mutated.json"
# The swapped canary: another COMMITTED, VALID request that is simply not the pinned tie.
SWAP=$W/t22-audit/req/calc-pmode-gerege.json

# THE INTERPRETER UNDER TEST.  `sh` on this machine is GNU bash 3.2.57 in POSIX mode; `bash` is
# the same binary out of POSIX mode.  The recipe must behave identically under both, so the inner
# invocation uses $SH and the whole suite is run twice.
SH=${SH:-sh}

hdr() {
  echo "=== $1"
  echo "runner shell: ${SHELLNAME:-sh}   recipe interpreter: $SH   cwd: $W"
  echo
}

run() {   # run <transcript> <caption> ; command comes from stdin via eval of $CMD
  t=$O/$1; shift
  cap=$1; shift
  { hdr "$cap"; echo "\$ $CMD"; echo; eval "$CMD"; st=$?; echo; echo "EXIT=$st"; } > "$t" 2>&1
  echo "  wrote $t  (exit $(tail -1 "$t" | sed 's/EXIT=//'))"
}

echo "== T80 attack suite, runner=${SHELLNAME:-sh} recipe-interpreter=$SH =="

# --------------------------------------------------------------------- ATTACK 1: wrong tenant
CMD='TENANT=default "$SH" t36/recapture.sh'
run "attack-1a-wrong-tenant-$SH.txt" \
    "ATTACK 1a — capture on the HALF_EVEN 'default' tenant, default output-dir derivation"

CMD='TENANT=default RECAPTURE_OUT='"$W"'/t36/out/recapture-gerege "$SH" t36/recapture.sh'
run "attack-1b-wrong-tenant-into-gerege-dir-$SH.txt" \
    "ATTACK 1b — capture on 'default' but FILED UNDER recapture-gerege (T77's provenance hazard)"

# Seed a directory whose NAME says 'default' but whose provenance stamp says 'gerege'.  The
# name guard alone would let this through; the stamp is the second, independent operand.
mkdir -p "$O/stamp-probe-default"
printf 'gerege\n' > "$O/stamp-probe-default/CAPTURED-FROM-TENANT"
CMD='TENANT=default RECAPTURE_OUT='"$O"'/stamp-probe-default "$SH" t36/recapture.sh'
run "attack-1c-stamp-mismatch-$SH.txt" \
    "ATTACK 1c — a directory already stamped 'gerege', re-used for a 'default' capture"

# ------------------------------------------------------------- ATTACK 2: mutated canary request
CMD='CANARY_REQ='"$O"'/attack-2-req-mutated.json "$SH" t36/preconditions.sh gerege'
run "attack-2a-mutated-canary-gerege-$SH.txt" \
    "ATTACK 2a — one character changed in the canary principal (1162502.5 -> 1162502.55), tenant gerege"

CMD='CANARY_REQ='"$O"'/attack-2-req-mutated.json "$SH" t36/preconditions.sh default'
run "attack-2b-mutated-canary-default-$SH.txt" \
    "ATTACK 2b — the same mutated canary on the HALF_EVEN 'default' tenant (T77's exact exploit)"

# ------------------------------------------------------------------- ATTACK 3: swapped canary
CMD='CANARY_REQ='"$SWAP"' "$SH" t36/preconditions.sh gerege'
run "attack-3a-swapped-canary-gerege-$SH.txt" \
    "ATTACK 3a — canary swapped for another committed, valid, NON-TIE request"

CMD='CANARY_REQ=/nonexistent/canary.json "$SH" t36/preconditions.sh gerege'
run "attack-3b-missing-canary-$SH.txt" \
    "ATTACK 3b — canary path points at nothing"

CMD='"$SH" t36/preconditions.sh gerege'
run "attack-3c-no-canary-$SH.txt" \
    "ATTACK 3c — canary omitted entirely (CANARY_REQ unset)"

# ------------------------------------------------- ATTACK 4: talk the expectation out of failing
CMD='CANARY_EXPECT=20925.04 CANARY_REQ='"$CANON"' "$SH" t36/preconditions.sh default'
run "attack-4a-expect-override-default-$SH.txt" \
    "ATTACK 4a — CANARY_EXPECT=20925.04 (tell the script to expect HALF_EVEN) on tenant default"

CMD='CANARY_EXPECT=20925.04 CANARY_REQ='"$CANON"' "$SH" t36/preconditions.sh gerege'
run "attack-4b-expect-override-gerege-$SH.txt" \
    "ATTACK 4b — the same override on tenant gerege"

CMD='CANARY_EXPECT_OVERRIDE=20925.04 CANARY_REQ='"$CANON"' "$SH" t36/preconditions.sh gerege'
run "attack-4c-decoy-variable-$SH.txt" \
    "ATTACK 4c — T76's DECOY variable name, which no attacker would use: it must now be INERT"

echo "== done, recipe-interpreter=$SH =="
