#!/usr/bin/env bash
# T283 -- THE REVIEW'S CORE: forge a sidecar that T274's RE-DERIVATION REPRODUCES.
#
# T274's root repair removed the "list of things we check", so an OMITTED
# assertion is no longer an attack -- this review re-ran all 18 of T274's arms
# live and every one reproduced.  What is left is a sidecar the re-derivation
# reproduces.  Every arm below builds one with `t283-forge.py`, which calls the
# verifier's OWN builder in its OWN "verify" mode, so nothing here guesses a
# string and nothing here is a shape the author could call unrepresentative.
#
# The arms are ordered by HOW MUCH the forger had to touch and by WHETHER THE
# ACCEPTED SIDECAR CONFESSES:
#
#   FP0  nothing touched                                     -> must be rc=0
#   FN   NAME.req swapped, sidecar NOT patched (calibration) -> must be rc=1
#        (if FN passed, the rig would be accepting everything and every arm
#         below would prove nothing)
#
#   CONFESSING FORGERIES -- accepted, but the accepted text contains a
#   `MISMATCH (...)` line that `derive` REFUSES to write, so the verifier
#   returns 0 over a sidecar whose own derivation says the wire record and the
#   committed artefact disagree:
#   FA   NAME.req swapped (different length) + sidecar re-derived
#   FB   NAME.status rewritten + sidecar re-derived
#   FC   NAME.json swapped for another capture's + sidecar re-derived
#
#   SILENT FORGERIES -- accepted, and NOTHING in the accepted sidecar differs in
#   shape from an honest one.  These are the sharp ones:
#   FA2  NAME.req swapped for the SAME NUMBER OF BYTES + sidecar re-derived
#   FC2  NAME.json swapped for the SAME NUMBER OF BYTES + sidecar re-derived
#
#   RECORD-SIDE FORGERIES -- the unforgeability limit T274 states, priced:
#   FD   the wire record's tenant rewritten + sidecar re-derived
#   FD2  the wire record's headers REVERSED and case-varied + sidecar re-derived
#        (T261's F-5 route re-opened from the record side)
#
#   CALLER-SIDE:
#   FE   schema-2 sidecar DOWNGRADED to schema 1 AND the response artefacts
#        withheld from the call.  T274's docstring says a downgrade "buys a
#        refusal, not a pass"; that holds only when the caller still presents a
#        response artefact, and the caller is the party being deceived.
#
# EXPECTED, STATED BEFORE THE RUN (P-76): FP0=0, FN=1, and FA FA2 FB FC FC2 FD
# FD2 FE all =0.  A NONZERO on any of those would falsify the finding and this
# review would report the measurement instead.
#
# NOTHING TAMPERED IS COMMITTED.  All artefacts live in $TMPDIR.  Committing
# tampered sidecars would inflate `attest_population.py`'s census and force
# T274's pin to move, which is not a reviewer's business; the transcript is the
# evidence.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
FORGE="$HERE/t283-forge.py"
TREE=${T274_TREE:?set T274_TREE to a checkout of softhouse/t274-attestation-failopen}
LIB="$TREE/.softhouse/capture/lib"
BASE_URL='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
HDRS="$AUTH
Fineract-Platform-TenantId: default
Content-Type: application/json"

for f in "$FORGE" "$LIB/wire_attestation.py" "$LIB/oracle_send.sh"; do
    [ -f "$f" ] || { echo "REFUSING: missing $f" >&2; exit 2; }
done

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t283forge.XXXXXX")
trap 'rm -rf "$WORK"' EXIT HUP INT TERM QUIT

pass=0; fail=0
judge() {  # judge ARM EXPECTED ACTUAL DESC
    if [ "$3" -eq "$2" ]; then j='ok'; pass=$((pass+1)); else j='*** UNEXPECTED ***'; fail=$((fail+1)); fi
    printf '  %-4s expected rc=%s  got rc=%s  %-20s %s\n' "$1" "$2" "$3" "$j" "$4"
}

confession() {  # confession DIR NAME -- how many MISMATCH lines the ACCEPTED sidecar carries
    n=$(/usr/bin/grep -c 'MISMATCH (' "$1/$2.http" || true)
    echo "    the accepted sidecar's own confession: $n line(s) containing 'MISMATCH ('"
}

capture() {  # capture OUTDIR NAME METHOD PATH BODY
    mkdir -p "$1"
    (
        OS_BASE="$BASE_URL"; OS_OUTDIR="$1"; OS_LIB_DIR="$LIB"; OS_HEADERS="$HDRS"
        export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
        # shellcheck source=/dev/null
        . "$LIB/oracle_send.sh"
        oracle_send "$2" "$3" "$4" "$5"
    ) > "$1/capture.log" 2>&1
}

verify_full() {  # verify_full DIR NAME -> rc
    v_rc=0
    python3 "$LIB/wire_attestation.py" verify \
        --sidecar "$1/$2.http" --headers "$1/$2.reqhdr" --req "$1/$2.req" \
        --resp "$1/$2.json" --resphdr "$1/$2.resphdr" --status "$1/$2.status" \
        > "$1/verify.out" 2> "$1/verify.err" || v_rc=$?
    echo "$v_rc"
}

verify_request_only() {  # the schema-1 call shape
    v_rc=0
    python3 "$LIB/wire_attestation.py" verify \
        --sidecar "$1/$2.http" --headers "$1/$2.reqhdr" --req "$1/$2.req" \
        > "$1/verify.out" 2> "$1/verify.err" || v_rc=$?
    echo "$v_rc"
}

echo "T283 -- can a forgery survive T274's exact re-derivation?"
echo "date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "curl:   $(curl --version | head -1)"
echo "oracle: $BASE_URL"
echo "rig under test:"
shasum -a 256 "$LIB/wire_attestation.py" "$LIB/oracle_send.sh" | sed 's/^/  /'
echo "scratch: $WORK"
echo

BODY="$WORK/bad-office.json"
printf '{"invalid":"deliberately-not-a-valid-office"}\n' > "$BODY"

# ---- FP0 positive control --------------------------------------------------
d="$WORK/FP0"; capture "$d" probe POST /offices "$BODY"
judge FP0 0 "$(verify_full "$d" probe)" "untouched artefacts must verify"

# ---- FN calibration --------------------------------------------------------
d="$WORK/FN"; capture "$d" probe POST /offices "$BODY"
python3 "$FORGE" "$LIB" "$d" probe body-swap-naive
judge FN 1 "$(verify_full "$d" probe)" "body swapped, sidecar NOT patched"

# ---- FA request body forged (different length), WIRE RECORD untouched ------
d="$WORK/FA"; capture "$d" probe POST /offices "$BODY"
python3 "$FORGE" "$LIB" "$d" probe body-swap
judge FA 0 "$(verify_full "$d" probe)" "req forged; reqhdr UNTOUCHED"
echo "    wire record still says: $(/usr/bin/grep -i '^Content-Length:' "$d/probe.reqhdr" | tr -d '\r')"
echo "    committed artefact is:  $(wc -c < "$d/probe.req" | tr -d ' ') bytes"
echo "    the ACCEPTED sidecar asserts: $(/usr/bin/grep '^content-length-crosscheck:' "$d/probe.http")"
echo "    verifier said:                $(tail -1 "$d/verify.out")"
confession "$d" probe

# ---- FA2 SAME-LENGTH request body forged -- no confession anywhere ----------
d="$WORK/FA2"; capture "$d" probe POST /offices "$BODY"
before=$(shasum -a 256 "$d/probe.req" | cut -c1-16)
python3 "$FORGE" "$LIB" "$d" probe body-swap-samelen
judge FA2 0 "$(verify_full "$d" probe)" "SAME-LENGTH req forged"
echo "    body digest before/after: $before -> $(shasum -a 256 "$d/probe.req" | cut -c1-16)"
echo "    the ACCEPTED sidecar asserts: $(/usr/bin/grep '^content-length-crosscheck:' "$d/probe.http")"
echo "    committed body is now:        $(cat "$d/probe.req")"
echo "    verifier said:                $(tail -1 "$d/verify.out")"
confession "$d" probe

# ---- FB status file forged, response wire record untouched -----------------
d="$WORK/FB"; capture "$d" probe POST /offices "$BODY"
python3 "$FORGE" "$LIB" "$d" probe status-swap 201
judge FB 0 "$(verify_full "$d" probe)" "NAME.status forged"
echo "    the ACCEPTED sidecar asserts: $(/usr/bin/grep '^response-status-crosscheck:' "$d/probe.http")"
echo "    and:                          $(/usr/bin/grep '^response-status-line:' "$d/probe.http")"
confession "$d" probe

# ---- FC the T261 F-6 / T274 R4 shape, with the sidecar patched -------------
d="$WORK/FC"; capture "$d" probe POST /offices "$BODY"
capture "$d" other GET /offices ""
python3 "$FORGE" "$LIB" "$d" probe resp-swap "$d/other.json"
judge FC 0 "$(verify_full "$d" probe)" "response swapped for another capture's"
echo "    the ACCEPTED sidecar asserts: $(/usr/bin/grep '^response-content-length-crosscheck:' "$d/probe.http")"
confession "$d" probe

# ---- FC2 SAME-LENGTH response forged -- the oracle's ANSWER, silently -------
d="$WORK/FC2"; capture "$d" probe POST /offices "$BODY"
before=$(shasum -a 256 "$d/probe.json" | cut -c1-16)
python3 "$FORGE" "$LIB" "$d" probe resp-swap-samelen
judge FC2 0 "$(verify_full "$d" probe)" "SAME-LENGTH response forged"
echo "    response digest before/after: $before -> $(shasum -a 256 "$d/probe.json" | cut -c1-16)"
echo "    the ACCEPTED sidecar asserts: $(/usr/bin/grep '^response-content-length-crosscheck:' "$d/probe.http")"
echo "    committed response now reads: $(cut -c1-60 < "$d/probe.json")"
confession "$d" probe

# ---- FD the stated unforgeability limit, priced ----------------------------
d="$WORK/FD"; capture "$d" probe POST /offices "$BODY"
python3 "$FORGE" "$LIB" "$d" probe reqhdr-tenant gerege
judge FD 0 "$(verify_full "$d" probe)" "wire record's tenant rewritten"
echo "    the ACCEPTED sidecar asserts: $(/usr/bin/grep -i '^Fineract-Platform-TenantId:' "$d/probe.http")"
echo "    files the forger had to touch: probe.reqhdr, probe.http  (2 of 6)"

# ---- FD2 header ORDER and CASE, attacked from the record side --------------
d="$WORK/FD2"; capture "$d" probe POST /offices "$BODY"
python3 "$FORGE" "$LIB" "$d" probe reqhdr-case
judge FD2 0 "$(verify_full "$d" probe)" "record headers reversed + upper-cased"
echo "    the ACCEPTED sidecar's wire block now reads:"
sed -n '3,12p' "$d/probe.http" | sed 's/^/      /'

# ---- FE downgrade WITH the response artefacts withheld ---------------------
d="$WORK/FE"; capture "$d" probe POST /offices "$BODY"
python3 "$FORGE" "$LIB" "$d" probe drop-response
judge FE 0 "$(verify_request_only "$d" probe)" "downgrade + response withheld"
echo "    verifier said:                $(tail -1 "$d/verify.out")"
echo "    RESPONSE LEG line printed:    $(/usr/bin/grep -c 'NOT ATTESTED' "$d/verify.out") occurrence(s)"
echo "    the response artefacts are still on disk, unmentioned:"
ls "$d" | tr '\n' ' ' | sed 's/^/      /'; echo

echo
echo "SCORE: $pass as expected, $fail unexpected"
if [ "$fail" -ne 0 ]; then
    echo "INSTRUMENT VERDICT: FAIL -- at least one predicted forgery was DETECTED;"
    echo "the finding as written is falsified and must be rewritten to the measurement."
    exit 1
fi
echo "INSTRUMENT VERDICT: PASS -- every arm behaved as predicted."
exit 0
