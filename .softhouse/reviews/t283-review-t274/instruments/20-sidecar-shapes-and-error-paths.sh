#!/usr/bin/env bash
# T283 -- THE ABSENCE-ATTACK CLASS AND THE VERIFIER'S OWN ERROR PATHS.
#
# Two jobs, and the first one is COVERAGE EVIDENCE, not a hunt for a win:
#
# S-arms: the absence class the original defect belonged to -- delete the
#   sidecar, empty it, keep valid syntax and assert NOTHING, truncate it,
#   duplicate an assertion, remove the one assertion that cannot be re-derived.
#   Every one of these is EXPECTED TO BE CAUGHT.  They are recorded because an
#   adversarial review that reports only its wins is not a measurement.
#
# E-arms: the error paths.  Three instruments in this program have already
#   failed open on an error mistaken for a negative result (P-81 is the `git
#   grep` case: exit 1 = no match, >1 = ERROR).  Two of these arms drive the two
#   `content_length()` repairs T274 shipped and flagged [UNVERIFIED] in its own
#   handoff -- a non-integer `Content-Length` and two of them -- which is the
#   cheapest way to close a stated gap in the work under review.
#
# EXPECTED, STATED BEFORE THE RUN (P-76): every S-arm 1 or 2 (never 0), every
# E-arm 2 (REFUSED -- no verdict), except E1 (unreadable sidecar) where the
# prediction is that Python raises rather than refusing and the process exits 1,
# which would MISREPORT a refusal as a verdict of NO.  A 0 anywhere is a
# fail-open and would be the headline finding.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TREE=${T274_TREE:?set T274_TREE to a checkout of softhouse/t274-attestation-failopen}
LIB="$TREE/.softhouse/capture/lib"
WA="$LIB/wire_attestation.py"
BASE_URL='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
HDRS="$AUTH
Fineract-Platform-TenantId: default
Content-Type: application/json"

[ -f "$WA" ] || { echo "REFUSING: missing $WA" >&2; exit 2; }

# T283_FIXED=1: after the micro-fix an unreadable artefact must REFUSE (2) rather
# than exit 1 through a traceback.  Nothing else may move.
if [ "${T283_FIXED:-0}" = "1" ]; then E_E1=2; ARM=GREEN; else E_E1=1; ARM=RED; fi

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t283shapes.XXXXXX")
cleanup() { chmod -R u+rwX "$WORK" 2>/dev/null || true; rm -rf "$WORK"; }
trap cleanup EXIT HUP INT TERM QUIT

pass=0; fail=0
judge() {
    if [ "$3" -eq "$2" ]; then j='ok'; pass=$((pass+1)); else j='*** UNEXPECTED ***'; fail=$((fail+1)); fi
    printf '  %-4s expected rc=%s  got rc=%s  %-20s %s\n' "$1" "$2" "$3" "$j" "$4"
}

echo "T283 -- absence attacks and error paths.  ARM: $ARM"
echo "date:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "rig under test:"
shasum -a 256 "$WA" | sed 's/^/  /'
echo

GOLD="$WORK/gold"
mkdir -p "$GOLD"
BODY="$WORK/bad-office.json"
printf '{"invalid":"deliberately-not-a-valid-office"}\n' > "$BODY"
(
    OS_BASE="$BASE_URL"; OS_OUTDIR="$GOLD"; OS_LIB_DIR="$LIB"; OS_HEADERS="$HDRS"
    export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
    # shellcheck source=/dev/null
    . "$LIB/oracle_send.sh"
    oracle_send probe POST /offices "$BODY"
) > "$GOLD/capture.log" 2>&1
echo "one live capture taken; every arm below is a COPY of it, tampered one way."
echo

arm() {  # arm NAME -> makes $d a fresh copy of the gold set
    d="$WORK/$1"
    rm -rf "$d"; mkdir -p "$d"
    cp "$GOLD"/probe.* "$d"/
}

run_full() {  # -> rc
    r_rc=0
    python3 "$WA" verify --sidecar "$d/probe.http" --headers "$d/probe.reqhdr" \
        --req "$d/probe.req" --resp "$d/probe.json" --resphdr "$d/probe.resphdr" \
        --status "$d/probe.status" > "$d/out" 2> "$d/err" || r_rc=$?
    echo "$r_rc"
}

why() { head -2 "$d/err" | sed 's/^/       /'; }

echo "== S: the ABSENCE class -- every one of these MUST be caught =="

arm S0; judge S0 0 "$(run_full)" "positive control, untouched"

arm S1; rm -f "$d/probe.http"
judge S1 2 "$(run_full)" "the sidecar is DELETED"; why

arm S2; : > "$d/probe.http"
judge S2 2 "$(run_full)" "the sidecar is EMPTY"; why

arm S3; head -1 "$GOLD/probe.http" > "$d/probe.http"
# PREDICTED 1, MEASURED 2, and the measurement is right: a sidecar reduced to its
# provenance line has no `attestation-schema: 2`, so it is schema 1, and a schema 1
# sidecar presented WITH response artefacts refuses.  The wrong prediction is kept
# here rather than deleted -- it is the same shape T274 kept for its own arm 7a.
judge S3 2 "$(run_full)" "sidecar = the provenance line ONLY"; why

arm S4
# valid syntax, correct head, and ZERO assertions: everything after the wire
# block removed.  "Nothing asserted" must not mean "nothing wrong".
n=$(/usr/bin/grep -n '^request-headers-artefact:' "$GOLD/probe.http" | cut -d: -f1)
head -$((n - 1)) "$GOLD/probe.http" > "$d/probe.http"
judge S4 1 "$(run_full)" "valid syntax, ZERO assertions"; why

arm S5; /usr/bin/grep -v '^body-sha256:' "$GOLD/probe.http" > "$d/probe.http"
judge S5 1 "$(run_full)" "one assertion deleted (T261 F-4)"; why

arm S6; awk '{print} /^body-sha256:/{print}' "$GOLD/probe.http" > "$d/probe.http"
judge S6 1 "$(run_full)" "one assertion DUPLICATED"; why

arm S7; head -c 200 "$GOLD/probe.http" > "$d/probe.http"
judge S7 1 "$(run_full)" "sidecar TRUNCATED mid-line"; why

arm S8; /usr/bin/grep -v '^captured-at-utc:' "$GOLD/probe.http" > "$d/probe.http"
judge S8 1 "$(run_full)" "the un-derivable assertion removed"; why

arm S9; awk '{print} /^captured-at-utc:/{print}' "$GOLD/probe.http" > "$d/probe.http"
judge S9 1 "$(run_full)" "TWO captured-at-utc lines"; why

arm S10; { head -2 "$GOLD/probe.http"; printf 'invented-assertion: nothing derives this\n'; \
           tail -n +3 "$GOLD/probe.http"; } > "$d/probe.http"
judge S10 1 "$(run_full)" "an UNKNOWN key invented"; why

arm S11
# The exemption-list question, asked directly: is `content-length-crosscheck`
# still a key that can be asserted with a fictional value?  (T261's F-7.)
sed 's/^content-length-crosscheck: .*/content-length-crosscheck: MATCH (99999 bytes)/' \
    "$GOLD/probe.http" > "$d/probe.http"
judge S11 1 "$(run_full)" "a RECOGNISED key made false"; why

echo
echo "== E: the verifier's own error paths -- a nonzero is an ERROR, never a pass =="

arm E1; chmod 000 "$d/probe.http"
rc=$(run_full); chmod 644 "$d/probe.http"
judge E1 "$E_E1" "$rc" "sidecar exists but is UNREADABLE"; why

arm E2; rm -f "$d/probe.reqhdr"; mkdir "$d/probe.reqhdr"
judge E2 2 "$(run_full)" "the wire record is a DIRECTORY"; why

arm E3; sed -i '' 's/^Content-Length: .*/Content-Length: forty-six/' "$d/probe.reqhdr"
judge E3 2 "$(run_full)" "non-integer Content-Length [T274 UNVERIFIED]"; why

arm E4; awk '{print} /^Content-Length:/{print}' "$GOLD/probe.reqhdr" > "$d/probe.reqhdr"
judge E4 2 "$(run_full)" "TWO Content-Length headers [T274 UNVERIFIED]"; why

arm E5; : > "$d/probe.reqhdr"
judge E5 2 "$(run_full)" "the wire record is EMPTY"; why

arm E6; /usr/bin/grep -v '^HTTP/' "$GOLD/probe.resphdr" > "$d/probe.resphdr"
judge E6 2 "$(run_full)" "response record has NO status line"; why

arm E7; printf '\xff\xfe not utf-8 \xc3\x28\n' >> "$d/probe.reqhdr"
judge E7 1 "$(run_full)" "invalid UTF-8 in the wire record"; why

arm E8; rm -f "$d/probe.status"
judge E8 2 "$(run_full)" "the status file is DELETED"; why

echo
echo "SCORE: $pass as expected, $fail unexpected"
[ "$fail" -eq 0 ] || { echo "INSTRUMENT VERDICT: FAIL -- at least one arm did not behave as predicted."; exit 1; }
echo "INSTRUMENT VERDICT: PASS"
exit 0
