#!/usr/bin/env bash
# T274 -- THE FOUR FAIL-OPEN ROUTES, EACH DRIVEN RED AND EACH SHOWN GREEN.
#
# T261 attacked T250's `wire_attestation.py verify` with shapes T250 did not
# design around and FOUR ROUTES got through.  This instrument runs every one of
# them TWICE, against artefact sets captured from the LIVE reference oracle:
#
#   RED  arm -- the T250 rig exactly as it shipped, byte-copied to
#               `../baseline/` before T274 touched anything.  Every route must
#               return rc=0: that is the fail-open, demonstrated rather than
#               quoted.
#   GREEN arm -- the T274 rig in `.softhouse/capture/lib/`.  Every route must
#               return rc NONZERO.
#
# The two arms differ in the verifier under test AND IN NOTHING ELSE: the same
# `tamper.py` modes, the same oracle, the same headers, the same bodies.
#
# ROUTES (T261's finding ids in brackets; note that tasks.json and REVIEW.md
# number the last two the other way round, so they are identified here by SHAPE):
#   R1  [F-4 HIGH] delete the `body-sha256:` assertion + swap the committed body
#                 for DIFFERENT BYTES OF THE SAME LENGTH
#   R2a [F-5]     reorder two wire header lines in the sidecar
#   R2b [F-5]     send an identical header TWICE, drop ONE copy from the sidecar
#   R3a [known_keys exemption] invent `content-length-crosscheck: MATCH (99999 bytes)`
#   R3b [known_keys exemption] ALTER the real crosscheck line to the same fiction
#   R4  [response leg unattested] swap the response `.json` for another capture's
#
# R2a/R2b are ONE route (set membership instead of sequence) shown through its two
# distinct shapes; R3a/R3b likewise (a recognised key was never validated).  Four
# routes, six demonstrations -- because "four claimed routes with three
# demonstrations is a rejection", and a route shown through only the shape the fix
# was designed around is not driven red.
#
# CONTROLS.  A guard that fails everything detects nothing (P-22/P-72), so:
#   P0  UNTOUCHED artefacts must verify rc=0 in BOTH arms.
#   P1  a SCHEMA 1 sidecar from T250's committed evidence, copied not edited,
#       must still verify rc=0 under the T274 verifier.
#   P2  the DOWNGRADE the T274 fix could have opened -- delete
#       `attestation-schema: 2` and present the response anyway -- must REFUSE
#       (rc=2), not pass.
#
# NOTHING under `.softhouse/capture/t250-tenant-attestation/` is written or
# edited (T114): its arm-0 artefacts are COPIED into this task's evidence tree.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TASK=$(cd "$HERE/.." && pwd)
ROOT=$(cd "$TASK/../../.." && pwd)
FIXED_LIB="$ROOT/.softhouse/capture/lib"
BASE_LIB="$TASK/baseline"
EV="$TASK/evidence"
TAMPER="$HERE/tamper.py"
MARKER_TEXT='This directory holds artefacts that were TAMPERED ON PURPOSE by the T274
red-drives. They are evidence of an attack, not captures. `attest_population.py`
excludes this directory from the sidecar census and PRINTS the exclusion; the
directory must appear in `.softhouse/capture/lib/attest_population_pin.json` or
the census FAILS. See ../../instruments/ and the T274 handoff.
'

BASE_URL='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='

for f in "$BASE_LIB/wire_attestation.py" "$BASE_LIB/oracle_send.sh" \
         "$FIXED_LIB/wire_attestation.py" "$FIXED_LIB/oracle_send.sh" "$TAMPER"; do
    if [ ! -f "$f" ]; then
        echo "REFUSING: missing $f" >&2
        exit 2
    fi
done

rm -rf "$EV/red" "$EV/green"
mkdir -p "$EV/red" "$EV/green"

# Every sidecar under these two trees is tampered on purpose.  The marker keeps
# them OUT of the committed-sidecar census and IN its printed output, and the
# census FAILS unless the directory is pinned -- an exclusion that cannot be
# created quietly.  It is rewritten here because the instrument deletes the
# trees on every run, and a marker that survives only by luck enforces nothing.
for d in "$EV/red" "$EV/green"; do
    printf '%s' "$MARKER_TEXT" > "$d/ATTEST-TAMPERED-EVIDENCE"
done

pass=0
fail=0

# capture LIBDIR OUTDIR NAME METHOD PATH BODYFILE HEADERS
capture() {
    cap_lib=$1; cap_out=$2; cap_name=$3; cap_method=$4; cap_path=$5
    cap_body=$6; cap_hdrs=$7
    mkdir -p "$cap_out"
    (
        OS_BASE="$BASE_URL"
        OS_OUTDIR="$cap_out"
        OS_LIB_DIR="$cap_lib"
        OS_HEADERS="$cap_hdrs"
        export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
        # shellcheck source=/dev/null
        . "$cap_lib/oracle_send.sh"
        oracle_send "$cap_name" "$cap_method" "$cap_path" "$cap_body"
    ) > "$cap_out/capture.log" 2>&1
}

# verify ARM DIR NAME  -> echoes rc; uses the verifier and the argument set
# belonging to that arm's rig.  The RED arm is invoked EXACTLY as T250's
# `oracle_send` invokes it, because that is the call site whose behaviour is
# under test; it has no response arguments to pass.
verify_arm() {
    va_arm=$1; va_dir=$2; va_name=$3
    va_rc=0
    if [ "$va_arm" = red ]; then
        set -- --sidecar "$va_dir/$va_name.http" --headers "$va_dir/$va_name.reqhdr"
        if [ -f "$va_dir/$va_name.req" ]; then
            set -- "$@" --req "$va_dir/$va_name.req"
        fi
        python3 "$BASE_LIB/wire_attestation.py" verify "$@" \
            > "$va_dir/verify.out" 2> "$va_dir/verify.err" || va_rc=$?
    else
        set -- --sidecar "$va_dir/$va_name.http" --headers "$va_dir/$va_name.reqhdr" \
               --resp "$va_dir/$va_name.json" --resphdr "$va_dir/$va_name.resphdr" \
               --status "$va_dir/$va_name.status"
        if [ -f "$va_dir/$va_name.req" ]; then
            set -- "$@" --req "$va_dir/$va_name.req"
        fi
        python3 "$FIXED_LIB/wire_attestation.py" verify "$@" \
            > "$va_dir/verify.out" 2> "$va_dir/verify.err" || va_rc=$?
    fi
    echo "$va_rc"
}

judge() {   # judge ARM ROUTE EXPECTED_RC ACTUAL_RC DESC
    j_arm=$1; j_route=$2; j_exp=$3; j_got=$4; j_desc=$5
    if [ "$j_got" -eq "$j_exp" ]; then
        j_ok='ok'
        pass=$((pass + 1))
    else
        j_ok='*** UNEXPECTED ***'
        fail=$((fail + 1))
    fi
    printf '  %-5s %-4s expected rc=%s  got rc=%s  %-20s %s\n' \
        "$j_arm" "$j_route" "$j_exp" "$j_got" "$j_ok" "$j_desc"
}

HDR_ONE="$AUTH
Fineract-Platform-TenantId: default
Content-Type: application/json"
HDR_DUP="$AUTH
Fineract-Platform-TenantId: default
Fineract-Platform-TenantId: default
Content-Type: application/json"

echo "T274 -- four fail-open routes, RED (T250 rig as shipped) vs GREEN (T274 rig)"
echo "curl: $(curl --version | head -1)"
echo "oracle: $BASE_URL"
echo "baseline rig sha256:"
shasum -a 256 "$BASE_LIB/wire_attestation.py" "$BASE_LIB/oracle_send.sh" | sed 's/^/  /'
echo "fixed rig sha256:"
shasum -a 256 "$FIXED_LIB/wire_attestation.py" "$FIXED_LIB/oracle_send.sh" | sed 's/^/  /'
echo

# The request body is deliberately invalid and carries NO monetary value: the
# oracle refuses it at validation, nothing is created, and the refusal is the
# observation.  Same body in both arms.
mkdir -p "$EV/req"
printf '{"invalid":"deliberately-not-a-valid-office"}\n' > "$EV/req/bad-office.json"
BODY="$EV/req/bad-office.json"

for arm in red green; do
    if [ "$arm" = red ]; then LIB="$BASE_LIB"; else LIB="$FIXED_LIB"; fi
    echo "=============== ARM: $arm  (lib: ${LIB#"$ROOT"/}) ==============="

    # ---- P0 positive control -------------------------------------------------
    d="$EV/$arm/P0"; capture "$LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
    judge "$arm" P0 0 "$(verify_arm "$arm" "$d" probe)" "UNTOUCHED artefacts must verify"

    # ---- R1 delete the body assertion, forge a same-length body --------------
    d="$EV/$arm/R1"; capture "$LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
    python3 "$TAMPER" del-body-sha "$d" probe
    if [ "$arm" = red ]; then e=0; else e=1; fi
    judge "$arm" R1 "$e" "$(verify_arm "$arm" "$d" probe)" \
        "body-sha256: deleted + same-length body forged"

    # ---- R2a reorder ---------------------------------------------------------
    d="$EV/$arm/R2a"; capture "$LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
    python3 "$TAMPER" swap-headers "$d" probe
    if [ "$arm" = red ]; then e=0; else e=1; fi
    judge "$arm" R2a "$e" "$(verify_arm "$arm" "$d" probe)" \
        "two wire header lines reordered in the sidecar"

    # ---- R2b duplicate dropped ----------------------------------------------
    d="$EV/$arm/R2b"; capture "$LIB" "$d" probe POST /offices "$BODY" "$HDR_DUP"
    python3 "$TAMPER" drop-dup "$d" probe 'Fineract-Platform-TenantId: default'
    if [ "$arm" = red ]; then e=0; else e=1; fi
    judge "$arm" R2b "$e" "$(verify_arm "$arm" "$d" probe)" \
        "one of TWO identical tenant headers dropped"

    # ---- R3a invented assertion under a known key ---------------------------
    d="$EV/$arm/R3a"; capture "$LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
    python3 "$TAMPER" append-crosscheck "$d" probe
    if [ "$arm" = red ]; then e=0; else e=1; fi
    judge "$arm" R3a "$e" "$(verify_arm "$arm" "$d" probe)" \
        "invented content-length-crosscheck (99999 bytes)"

    # ---- R3b the real assertion made to lie ---------------------------------
    d="$EV/$arm/R3b"; capture "$LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
    python3 "$TAMPER" alter-crosscheck "$d" probe
    if [ "$arm" = red ]; then e=0; else e=1; fi
    judge "$arm" R3b "$e" "$(verify_arm "$arm" "$d" probe)" \
        "real crosscheck ALTERED to a fictional byte count"

    # ---- R4 response swapped for another capture's --------------------------
    d="$EV/$arm/R4"; capture "$LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
    capture "$LIB" "$d" other GET /offices "" "$HDR_ONE"
    cp "$d/other.json" "$d/probe.json"
    echo "  tamper: probe.json replaced by other.json ($(wc -c < "$d/probe.json" | tr -d ' ') bytes, a DIFFERENT real oracle response)"
    if [ "$arm" = red ]; then e=0; else e=1; fi
    judge "$arm" R4 "$e" "$(verify_arm "$arm" "$d" probe)" \
        "response .json swapped for another capture's"
    echo
done

echo "=============== CONTROLS (T274 verifier only) ==============="

# P1 -- T250's committed schema 1 evidence, COPIED not edited, must still verify.
d="$EV/green/P1"; mkdir -p "$d"
SRC="$ROOT/.softhouse/capture/t250-tenant-attestation/evidence/redB/arm-0"
for f in probe.http probe.reqhdr probe.req probe.json probe.status; do
    cp "$SRC/$f" "$d/$f"
done
rc=0
python3 "$FIXED_LIB/wire_attestation.py" verify --sidecar "$d/probe.http" \
    --headers "$d/probe.reqhdr" --req "$d/probe.req" \
    > "$d/verify.out" 2> "$d/verify.err" || rc=$?
judge green P1 0 "$rc" "T250 schema 1 sidecar still verifies (no retro-edit)"

# P2 -- the downgrade this fix could have opened.
d="$EV/green/P2"; capture "$FIXED_LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
cp "$EV/green/R4/other.json" "$d/probe.json"
python3 "$TAMPER" drop-schema "$d" probe
rc=0
python3 "$FIXED_LIB/wire_attestation.py" verify --sidecar "$d/probe.http" \
    --headers "$d/probe.reqhdr" --req "$d/probe.req" --resp "$d/probe.json" \
    --resphdr "$d/probe.resphdr" --status "$d/probe.status" \
    > "$d/verify.out" 2> "$d/verify.err" || rc=$?
judge green P2 2 "$rc" "schema line deleted + response swapped -> REFUSE, not pass"

# P3 -- withhold an attested artefact from a schema 2 sidecar.
d="$EV/green/P3"; capture "$FIXED_LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
rc=0
python3 "$FIXED_LIB/wire_attestation.py" verify --sidecar "$d/probe.http" \
    --headers "$d/probe.reqhdr" --req "$d/probe.req" \
    > "$d/verify.out" 2> "$d/verify.err" || rc=$?
judge green P3 2 "$rc" "schema 2 sidecar, response artefacts withheld -> REFUSE"

# P4 -- withhold the BODY artefact from a capture whose wire shows Content-Length.
d="$EV/green/P4"; capture "$FIXED_LIB" "$d" probe POST /offices "$BODY" "$HDR_ONE"
rc=0
python3 "$FIXED_LIB/wire_attestation.py" verify --sidecar "$d/probe.http" \
    --headers "$d/probe.reqhdr" --resp "$d/probe.json" \
    --resphdr "$d/probe.resphdr" --status "$d/probe.status" \
    > "$d/verify.out" 2> "$d/verify.err" || rc=$?
judge green P4 2 "$rc" "body artefact withheld though the wire sent one -> REFUSE"

echo
echo "SCORE: $pass as expected, $fail unexpected"
if [ "$fail" -ne 0 ]; then
    echo "INSTRUMENT VERDICT: FAIL"
    exit 1
fi
echo "INSTRUMENT VERDICT: PASS -- every route fails open on the T250 rig and is"
echo "detected by the T274 rig, and the controls hold."
exit 0
