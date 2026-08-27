#!/usr/bin/env bash
# T274 -- everything T250's verifier ALREADY DETECTED must still be detected, and
# its ONE HONEST NEGATIVE must still be honest.
#
# A repair that turns four fail-opens into detections but loses a detection it
# already had is a trade, not a fix -- and one that turns the disclosed negative
# into a false pass would be a lie added to the module.  So the seven arms of
# T250's own `30-redB-mismatch-detected.sh` are re-run here against the T274 rig,
# with their ORIGINAL expected exit statuses:
#
#   0  POSITIVE CONTROL      untouched artefacts                       -> 0 VERIFIED
#   1  sidecar tenant edited to a tenant that was NOT sent             -> 1 MISMATCH
#   2  header record edited, sidecar left alone                        -> 1 MISMATCH
#   3  header record DELETED                                           -> 2 REFUSED
#   4  legacy-shaped sidecar, no derivation provenance at all          -> 2 REFUSED
#   5  body artefact swapped under a sidecar that hashed the original  -> 1 MISMATCH
#   6  Content-Length sent disagrees with the committed body artefact  -> 1 MISMATCH
#   7  HONEST NEGATIVE: sidecar AND record AND digest all forged
#      consistently                                                    -> 0 (NOT caught)
#
# Arm 7 is kept deliberately.  This module does not claim unforgeability and must
# not appear to: a consistent forgery of the whole artefact set is caught by the
# outer `MANIFEST.sha256` and the vectors' `capture_sha256` pins, not here.  That
# limit is in the module docstring, where a reader meets it.
#
# ARM 7a IS A CLAIM OF MINE THAT THE MEASUREMENT KILLED, KEPT HERE BECAUSE IT
# KILLED IT.  I predicted that attesting the response leg would make a
# REQUEST-ONLY consistent forgery detectable (rc=1), on the reasoning that the
# sidecar now carries assertions the forger did not touch.  IT DOES NOT, and the
# first run said so: rc=0.  The untouched response assertions still re-derive
# correctly from the untouched response artefacts, so they detect nothing about
# the request.  Attesting the response RAISES THE COST of forging a DIFFERENT
# RESPONSE -- five artefacts instead of three -- and does not narrow the
# unforgeability limit at all.  Arm 7a's expectation is therefore 0, and the
# module docstring states the limit in exactly those terms.
#   Transcript of the refuting run: ../evidence/30-arm7a-prediction-refuted.txt
#
# T250's own evidence tree is NOT touched (T114): this captures fresh.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TASK=$(cd "$HERE/.." && pwd)
ROOT=$(cd "$TASK/../../.." && pwd)
LIB="$ROOT/.softhouse/capture/lib"
WA="$LIB/wire_attestation.py"
EV="$TASK/evidence/t250arms"
# --- T304 FAIL-CLOSED GUARD (FU-T284-3) ---------------------------------------------
# This instrument rebuilds its evidence directory from scratch on every run, and that
# directory holds 91 TRACKED files. T114 binds: committed evidence is named and
# SUPERSEDED by a scratch copy, never rewritten in place. Documenting the hazard in a
# handoff enforces nothing (P-45: "A test-only guard is not a guard ... verify the path
# that actually executes ... calls it, not merely that a test does") -- so the refusal
# is here, on the executing path, ahead of the destruction.
#   run for a NEW answer:  T304_EVIDENCE_SCRATCH="$(mktemp -d)" bash "$0"
#   read the OLD answer :  do not run it; the corpus is at the path above.
. "$(git rev-parse --show-toplevel)/.softhouse/capture/t304-evidence-destruction/instruments/refuse-if-tracked.sh"
EV="$(t304_evidence_root "$EV")" || exit 2
# --- end T304 guard -----------------------------------------------------------------
BASE_URL='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='

rm -rf "$EV"
mkdir -p "$EV/req"

# Arms 1-7b tamper their artefacts on purpose, and arm 4 is a legacy-shaped
# FORGERY whose whole point is to carry no provenance line.  Counting these as
# unattested captures would be a false figure, so the tree declares itself and
# `attest_population.py` prints the exclusion and refuses an unpinned one.
printf '%s' 'This directory holds artefacts that were TAMPERED ON PURPOSE by the T274
red-drives. They are evidence of an attack, not captures. `attest_population.py`
excludes this directory from the sidecar census and PRINTS the exclusion; the
directory must appear in `.softhouse/capture/lib/attest_population_pin.json` or
the census FAILS. See ../../instruments/ and the T274 handoff.
' > "$EV/ATTEST-TAMPERED-EVIDENCE"
printf '{"invalid":"deliberately-not-a-valid-office"}\n' > "$EV/req/bad-office.json"

pass=0
fail=0

grab() {   # grab ARMDIR
    mkdir -p "$1"
    (
        OS_BASE="$BASE_URL"
        OS_OUTDIR="$1"
        OS_LIB_DIR="$LIB"
        OS_HEADERS="$AUTH
Fineract-Platform-TenantId: default
Content-Type: application/json"
        export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
        # shellcheck source=/dev/null
        . "$LIB/oracle_send.sh"
        oracle_send probe POST /offices "$EV/req/bad-office.json"
    ) > "$1/capture.log" 2>&1
}

run_arm() {  # run_arm N EXPECTED DIR DESC
    ra_n=$1; ra_exp=$2; ra_dir=$3; ra_desc=$4
    ra_rc=0
    python3 "$WA" verify --sidecar "$ra_dir/probe.http" --headers "$ra_dir/probe.reqhdr" \
        --req "$ra_dir/probe.req" --resp "$ra_dir/probe.json" \
        --resphdr "$ra_dir/probe.resphdr" --status "$ra_dir/probe.status" \
        > "$ra_dir/verify.out" 2> "$ra_dir/verify.err" || ra_rc=$?
    if [ "$ra_rc" -eq "$ra_exp" ]; then ra_ok='ok'; pass=$((pass + 1));
    else ra_ok='*** UNEXPECTED ***'; fail=$((fail + 1)); fi
    printf '  ARM %-3s expected rc=%s  got rc=%s  %-20s %s\n' \
        "$ra_n" "$ra_exp" "$ra_rc" "$ra_ok" "$ra_desc"
}

echo "T274 -- T250's seven redB arms, re-run against the T274 verifier"
shasum -a 256 "$WA" | sed 's/^/  /'
echo

for a in 0 1 2 3 4 5 6 7a 7b; do grab "$EV/arm-$a"; done

# ARM 1 -- sidecar says a tenant that was not sent.
python3 - "$EV/arm-1/probe.http" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read().replace("Fineract-Platform-TenantId: default",
                           "Fineract-Platform-TenantId: gerege")
open(p, "w").write(t)
PY

# ARM 2 -- the RECORD is edited; the sidecar is left alone.
python3 - "$EV/arm-2/probe.reqhdr" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read().replace("Fineract-Platform-TenantId: default",
                           "Fineract-Platform-TenantId: gerege")
open(p, "w").write(t)
PY

# ARM 3 -- the record is gone.
rm -f "$EV/arm-3/probe.reqhdr"

# ARM 4 -- a legacy-shaped sidecar: plausible text, no provenance line at all.
python3 - "$EV/arm-4/probe.http" <<'PY'
import sys
open(sys.argv[1], "w").write(
    "POST /fineract-provider/api/v1/offices HTTP/1.1\n"
    "Fineract-Platform-TenantId: gerege\n"
    "Content-Type: application/json\n")
PY

# ARM 5 -- the body artefact is swapped for different bytes.
printf '{"invalid":"a completely different body that was never sent at all"}\n' \
    > "$EV/arm-5/probe.req"

# ARM 6 -- the committed body no longer matches the Content-Length that was sent.
# It stays VALID JSON: the harness's wire-float round-trip guard parses every
# `*.req` under .softhouse/capture and REFUSES hard on one it cannot read, so an
# unparseable tamper here takes the whole BAR to exit 2 (measured; see handoff).
printf '{"x":1}\n' > "$EV/arm-6/probe.req"

# ARM 7a -- the REQUEST leg forged consistently (sidecar + record + digest), the
# response leg left alone.  I expected the new response attestation to catch this.
# IT DOES NOT (measured rc=0, first run).  See the header: the expectation in this
# file is the measurement, not the prediction.
python3 - "$EV/arm-7a" <<'PY'
import hashlib, os, sys
d = sys.argv[1]
rec = os.path.join(d, "probe.reqhdr")
sc = os.path.join(d, "probe.http")
t = open(rec).read().replace("Fineract-Platform-TenantId: default",
                             "Fineract-Platform-TenantId: gerege")
open(rec, "w").write(t)
dig = hashlib.sha256(open(rec, "rb").read()).hexdigest()
out = []
for line in open(sc).read().split("\n"):
    if line.startswith("request-headers-sha256: "):
        line = "request-headers-sha256: " + dig
    elif line == "Fineract-Platform-TenantId: default":
        line = "Fineract-Platform-TenantId: gerege"
    out.append(line)
open(sc, "w").write("\n".join(out))
PY

# ARM 7b -- the WHOLE artefact set forged consistently: request record, sidecar,
# every digest, the response body, the response record and the status file.
python3 - "$EV/arm-7b" <<'PY'
import hashlib, os, sys
d = sys.argv[1]
rec, sc = os.path.join(d, "probe.reqhdr"), os.path.join(d, "probe.http")
resp, rhdr = os.path.join(d, "probe.json"), os.path.join(d, "probe.resphdr")

t = open(rec).read().replace("Fineract-Platform-TenantId: default",
                             "Fineract-Platform-TenantId: gerege")
open(rec, "w").write(t)

forged = b'{"forged":"this response never came back from any oracle"}\n'
open(resp, "wb").write(forged)
rt = open(rhdr).read().replace("Content-Length: %d" % 468,
                               "Content-Length: %d" % len(forged))
open(rhdr, "w").write(rt)

reqdig = hashlib.sha256(open(rec, "rb").read()).hexdigest()
rhdig = hashlib.sha256(open(rhdr, "rb").read()).hexdigest()
rdig = hashlib.sha256(forged).hexdigest()
out = []
for line in open(sc).read().split("\n"):
    if line.startswith("request-headers-sha256: "):
        line = "request-headers-sha256: " + reqdig
    elif line.startswith("response-headers-sha256: "):
        line = "response-headers-sha256: " + rhdig
    elif line.startswith("response-sha256: "):
        line = "response-sha256: " + rdig
    elif line.startswith("response-bytes: "):
        line = "response-bytes: %d" % len(forged)
    elif line.startswith("response-content-length-crosscheck: "):
        line = "response-content-length-crosscheck: MATCH (%d bytes)" % len(forged)
    elif line == "Fineract-Platform-TenantId: default":
        line = "Fineract-Platform-TenantId: gerege"
    out.append(line)
open(sc, "w").write("\n".join(out))
PY

run_arm 0  0 "$EV/arm-0"  "POSITIVE CONTROL, untouched"
run_arm 1  1 "$EV/arm-1"  "sidecar claims a tenant that was not sent"
run_arm 2  1 "$EV/arm-2"  "record edited, sidecar left alone"
run_arm 3  2 "$EV/arm-3"  "header record DELETED"
run_arm 4  2 "$EV/arm-4"  "legacy sidecar, no derivation provenance"
run_arm 5  1 "$EV/arm-5"  "body artefact swapped"
run_arm 6  1 "$EV/arm-6"  "Content-Length sent != committed body bytes"
run_arm 7a 0 "$EV/arm-7a" "REQUEST leg forged consistently -- STILL NOT CAUGHT (my prediction of rc=1 was wrong; see the header)"
run_arm 7b 0 "$EV/arm-7b" "HONEST NEGATIVE: all five artefacts forged consistently"

echo
echo "SCORE: $pass as expected, $fail unexpected"
if [ "$fail" -ne 0 ]; then
    echo "INSTRUMENT VERDICT: FAIL"
    exit 1
fi
echo "INSTRUMENT VERDICT: PASS"
exit 0
