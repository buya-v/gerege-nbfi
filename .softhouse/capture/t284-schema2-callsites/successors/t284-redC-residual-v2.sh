#!/usr/bin/env bash
# T284 SITE 3 SUCCESSOR -- the RESIDUAL legs of T261's RED-DRIVE C, TAUGHT SCHEMA 2.
#
# THE SITE THIS SUPERSEDES, AND WHY THE ANSWER IS A SPLIT
#   .softhouse/reviews/t261-tenant-attestation/instruments/t261-redC-wrap.sh
#   Three REQUEST_ONLY `verify` calls (L54, L104, L168).  Measured on this
#   branch (../evidence/RED-site3.txt) it is the WORST of the three broken
#   sites, and not because it is loudest -- because it is quietest:
#
#     * all 17 verify calls in the wrap sweep print `verify FAILED`, and the
#       script still ends `exit 0`.  Its exit status is UNCONDITIONAL.  A caller
#       reading the status -- which is what a caller reads -- sees success.
#     * the `dupid` leg gets rc=2 (the SCHEMA refusal, nothing to do with header
#       multiplicity) and PRINTS `verify rc=2 DETECTED`.  A refusal is scored as
#       a security win.
#     * the `mbtrunc` leg does the same with rc=2.
#   That is the fail-open shape wearing a detection's clothes.  A refusal is the
#   absence of a verdict; it is never a detection.
#
#   The original is FROZEN and is NOT edited (T114's standing ruling: anything
#   that produced committed evidence is superseded by a scratch copy, never
#   edited in place).
#
#   RETIRED, NOT REPRODUCED: the 17-length wrap sweep.  The identical experiment
#   -- lengths 1 10 60 61 62 63 64 65 66 127 128 129 200 300 1000 4000 plus a
#   360-byte colon-and-space-laden value, ground truth the exact bytes handed to
#   curl's -H -- is run schema-2-natively, every run, by
#   .softhouse/capture/t274-attestation-failopen/instruments/
#   20-wrap-boundary-and-derivation-unchanged.sh, which additionally proves the
#   `.reqhdr` wire record is byte-identical to the T250 rig's.  Re-capturing 17
#   more times would buy nothing.
#   THAT RETIREMENT IS ASSERTED HERE, NOT CITED.  Coverage claimed by citation is
#   coverage that evaporates the day the cited file changes.  Leg 0 below reads
#   T274's instrument and FAILS if it is gone or if its length list has moved.
#
#   TAUGHT SCHEMA 2, because nothing else in the tree carries them:
#     leg 1  duplicated IDENTICAL header, one copy dropped from the sidecar
#            -- multiplicity, which T250's redC measured as a GAP
#     leg 2  CRLF injected into a header value
#     leg 3  a multibyte body: Content-Length byte-exactness, and a body
#            truncated MID-CHARACTER with every sidecar assertion left intact
#
# THE DISCRIMINATION THIS INSTRUMENT INSISTS ON
#   For legs 1 and 3, rc=1 (a verdict of NO) is a DETECTION and rc=2 (REFUSED) is
#   NOT.  Both are non-zero; only one is a measurement.  Scoring them together is
#   exactly what the frozen original does, and it is why its transcript reads as
#   though the attacks were caught when the verifier never looked at them.
#
# CAPTURES GO TO A SCRATCH DIRECTORY OUTSIDE THE REPOSITORY; only this transcript
# is committed.  Same reason as the site 2 successor: committed `*.req` artefacts
# are parsed by the harness's wire-float guard and counted by the sidecar ratchet
# whose pin lives outside this task's scope.
#
# THE BODY IS DELIBERATELY INVALID JSON.  The oracle refuses it at validation and
# creates nothing; a red-drive must not mutate the reference oracle.
#
# ENGINE (P-33/P-53): no grep, no rg, no git grep.  `git rev-parse` locates the
# root and its failure is fatal; line selection is `sed -n '/re/p'` under LC_ALL=C.
#
# CALIBRATION (P-72): every leg carries an untouched POSITIVE CONTROL that must
# verify rc=0 before its attack is scored.
#
# EXIT: 0 all legs as expected; 1 a leg moved; 2 REFUSED (no oracle, capture
# failed, wrong schema, or the retired coverage is missing).
set -euo pipefail

fail_hard() { printf 'redC-v2 REFUSING: %s\n' "$*" >&2; exit 2; }

ROOT=$(git rev-parse --show-toplevel) || fail_hard "not inside a git repository."
[ -d "$ROOT/.softhouse" ] || fail_hard "$ROOT does not contain .softhouse."

LIB="$ROOT/.softhouse/capture/lib"
WA="$LIB/wire_attestation.py"
FROZEN="$ROOT/.softhouse/reviews/t261-tenant-attestation/instruments/t261-redC-wrap.sh"
WRAP_OWNER="$ROOT/.softhouse/capture/t274-attestation-failopen/instruments/20-wrap-boundary-and-derivation-unchanged.sh"
WRAP_LENGTHS="for n in 1 10 60 61 62 63 64 65 66 127 128 129 200 300 1000 4000; do"
BASE="https://localhost:8443/fineract-provider/api/v1"
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
CT='Content-Type: application/json'

[ -f "$WA" ] || fail_hard "the verifier does not exist: $WA"
[ -f "$LIB/oracle_send.sh" ] || fail_hard "the capture library does not exist: $LIB/oracle_send.sh"
[ -f "$FROZEN" ] || fail_hard "the frozen original this supersedes is GONE: $FROZEN."

echo "T284 SITE 3 -- T261's RED-DRIVE C residual legs, taught schema 2"
echo "  supersedes : .softhouse/reviews/t261-tenant-attestation/instruments/t261-redC-wrap.sh"
echo "               (FROZEN, sha256 $(shasum -a 256 "$FROZEN" | cut -d' ' -f1))"
echo "  verifier   : $(shasum -a 256 "$WA" | cut -d' ' -f1)"
echo "  oracle     : $BASE"
echo "  curl       : $(curl --version | head -1 | cut -d' ' -f1-2)"
echo

fail=0

# ------------------------------------------------- LEG 0: the retirement, asserted
echo "-- LEG 0: the wrap sweep is RETIRED onto T274 instrument 20. Assert it, do not cite it. --"
if [ ! -f "$WRAP_OWNER" ]; then
    fail_hard "the wrap sweep was retired onto
    ${WRAP_OWNER#"$ROOT/"}
  and that file does not exist. The coverage is GONE, not elsewhere. This
  instrument deliberately does not duplicate it, so it refuses rather than
  reporting a clean run over coverage nobody holds."
fi
got_lengths=$(LC_ALL=C sed -n '/^for n in 1 10 60 /p' "$WRAP_OWNER" | LC_ALL=C sed -n '1p' | LC_ALL=C sed 's/^[[:space:]]*//')
if [ "$got_lengths" != "$WRAP_LENGTHS" ]; then
    fail_hard "T274 instrument 20 no longer sweeps the length list this retirement
  relies on.
    expected: $WRAP_LENGTHS
    found   : ${got_lengths:-<no matching line at all>}
  A retirement onto a moving target is a coverage drop with a citation on top."
fi
echo "  ${WRAP_OWNER#"$ROOT/"}"
echo "  carries the pinned length list -- 16 lengths + a 360-byte colon-laden value."
echo "  sha256 $(shasum -a 256 "$WRAP_OWNER" | cut -d' ' -f1)"
echo

EV=$(mktemp -d "${TMPDIR:-/tmp}/t284redC.XXXXXX") || fail_hard "mktemp -d failed"
# No EXIT trap: `oracle_send` clears EXIT traps (T283 FU-T283-1). Explicit cleanup.
mkdir -p "$EV"

send() {    # send NAME METHOD PATH [BODY] [EXTRA_HEADER...]
    s_name=$1; s_method=$2; s_path=$3; s_body=${4:-}
    shift 4 2>/dev/null || shift $#
    mkdir -p "$EV/$s_name"
    OS_BASE="$BASE"; OS_OUTDIR="$EV/$s_name"; OS_LIB_DIR="$LIB"
    OS_HEADERS="$AUTH
Fineract-Platform-TenantId: default
$CT"
    for s_h in "$@"; do OS_HEADERS="$OS_HEADERS
$s_h"; done
    export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
    # shellcheck source=/dev/null
    . "$LIB/oracle_send.sh"
    oracle_send "$s_name" "$s_method" "$s_path" ${s_body:+"$s_body"}
}

# The three response flags are written out LITERALLY on both branches so that
# ../instruments/10-callsite-registry.py can CLASSIFY this site by reading it.
# A helper that hides its flags behind `$@` classifies as INDIRECT and would need
# a declared exception in the pin -- and an author who writes an exception for
# their own file has stopped operating a default-deny register.
verify_full() {   # verify_full DIR NAME -> prints rc
    v_d=$1; v_n=$2; v_rc=0
    if [ -f "$v_d/$v_n.req" ]; then
        python3 "$WA" verify --sidecar "$v_d/$v_n.http" --headers "$v_d/$v_n.reqhdr" \
            --req "$v_d/$v_n.req" --resp "$v_d/$v_n.json" \
            --resphdr "$v_d/$v_n.resphdr" --status "$v_d/$v_n.status" \
            > "$v_d/$v_n.vout" 2> "$v_d/$v_n.verr" || v_rc=$?
    else
        python3 "$WA" verify --sidecar "$v_d/$v_n.http" --headers "$v_d/$v_n.reqhdr" \
            --resp "$v_d/$v_n.json" --resphdr "$v_d/$v_n.resphdr" \
            --status "$v_d/$v_n.status" \
            > "$v_d/$v_n.vout" 2> "$v_d/$v_n.verr" || v_rc=$?
    fi
    echo "$v_rc"
}

require_schema2() {   # require_schema2 DIR NAME
    r_side="$1/$2.http"
    r_line=$(LC_ALL=C sed -n '/^attestation-schema:/p' "$r_side" | LC_ALL=C sed -n '1p')
    if [ "$r_line" != "attestation-schema: 2" ]; then
        fail_hard "capture $2 is not schema 2 (declares '${r_line:-<nothing>}'). This
  instrument presents the response leg, so it can say nothing about a schema 1
  sidecar. REFUSED; nothing graded."
    fi
}

judge() {   # judge LABEL WANT_RC GOT_RC DIR NAME
    j_l=$1; j_w=$2; j_g=$3; j_d=$4; j_n=$5
    if [ "$j_g" = "$j_w" ]; then j_v='ok'; else j_v='*** UNEXPECTED ***'; fail=$((fail + 1)); fi
    printf '  %-52s want rc=%s got rc=%s  %s\n' "$j_l" "$j_w" "$j_g" "$j_v"
    if [ "$j_g" = "2" ] && [ "$j_w" = "1" ]; then
        printf '      rc=2 is a REFUSAL, not a detection. The verifier never reached the\n'
        printf '      shape under test, so this arm measured NOTHING.\n'
    fi
    LC_ALL=C sed -n '1,2p' "$j_d/$j_n.verr" | LC_ALL=C sed 's/^/      /'
}

# --------------------------------------------- LEG 1: duplicated IDENTICAL header
echo "-- LEG 1: duplicated IDENTICAL header, one copy dropped from the sidecar --"
send dupid GET /offices "" "Fineract-Platform-TenantId: default" || fail_hard "the dupid capture failed."
require_schema2 "$EV/dupid" dupid
judge "L1a positive control: untouched set must verify" 0 "$(verify_full "$EV/dupid" dupid)" "$EV/dupid" dupid
cp -R "$EV/dupid" "$EV/dupid-cut"
python3 - "$EV/dupid-cut/dupid.http" "$EV/dupid-cut/dupid.reqhdr" <<'PY'
import sys
sc, rec = sys.argv[1], sys.argv[2]
tag = "Fineract-Platform-TenantId: default"
nrec = open(rec).read().count(tag)
t = open(sc).read()                       # read fully BEFORE opening for write
nsc = t.count(tag)
print("      wire record carries the header %d time(s); sidecar carries it %d time(s)"
      % (nrec, nsc))
out, dropped = [], False
for l in t.split("\n"):
    if l == tag and not dropped:
        dropped = True
        continue
    out.append(l)
open(sc, "w").write("\n".join(out))
print("      dropped ONE of the %d identical copies from the sidecar" % nsc)
PY
judge "L1b one of two IDENTICAL copies dropped -> multiplicity" 1 "$(verify_full "$EV/dupid-cut" dupid)" "$EV/dupid-cut" dupid
echo

# ------------------------------------------------------- LEG 2: CRLF in a value
echo "-- LEG 2: CRLF injected into a header value --"
crlf_rc=0
send crlf GET /offices "" "X-T284-Inj: safe$(printf '\r\n')X-T284-Evil: injected" || crlf_rc=$?
if [ "$crlf_rc" -ne 0 ]; then
    echo "  the capture itself was REFUSED (rc=$crlf_rc) -- that is an acceptable outcome"
    echo "  and is recorded as such; nothing further is claimed about this leg."
else
    require_schema2 "$EV/crlf" crlf
    echo "  record lines mentioning X-T284:"
    LC_ALL=C sed -n '/^X-T284/p' "$EV/crlf/crlf.reqhdr" | LC_ALL=C sed 's/^/      /'
    echo "  sidecar lines mentioning X-T284:"
    LC_ALL=C sed -n '/^X-T284/p' "$EV/crlf/crlf.http" | LC_ALL=C sed 's/^/      /'
    # T261 only OBSERVED this. Observation is not a check: assert that whatever
    # curl put on the wire, the sidecar reproduces it and the set verifies.
    judge "L2 whatever went out, the sidecar must re-derive it" 0 "$(verify_full "$EV/crlf" crlf)" "$EV/crlf" crlf
fi
echo

# ---------------------------------------------------------- LEG 3: multibyte body
echo "-- LEG 3: multibyte body -- is the Content-Length crosscheck BYTE-exact? --"
mkdir -p "$EV/mbsrc"
python3 - "$EV/mbsrc/body.json" <<'PY'
import sys
s = '{"invalid":"Улаанбаатар ᠮᠣᠩᠭᠣᠯ","x":1}'
b = s.encode("utf-8")
open(sys.argv[1], "wb").write(b)
print("      body bytes on disk: %d (characters %d)" % (len(b), len(s)))
PY
send mb POST /offices "$EV/mbsrc/body.json" || fail_hard "the multibyte capture failed."
require_schema2 "$EV/mb" mb
echo "  Content-Length on the wire : $(LC_ALL=C sed -n '/^Content-Length:/p' "$EV/mb/mb.http" | LC_ALL=C sed -n '1p')"
echo "  crosscheck line            : $(LC_ALL=C sed -n '/^content-length-crosscheck:/p' "$EV/mb/mb.http")"
echo "  committed .req size        : $(wc -c < "$EV/mb/mb.req" | tr -d ' ') bytes"
judge "L3a positive control: untouched multibyte set verifies" 0 "$(verify_full "$EV/mb" mb)" "$EV/mb" mb
cp -R "$EV/mb" "$EV/mbtrunc"
python3 - "$EV/mbtrunc/mb.req" <<'PY'
import sys
p = sys.argv[1]
b = open(p, "rb").read()
open(p, "wb").write(b[:len(b) - 1])   # cut one byte off a multibyte character
PY
judge "L3b body truncated MID-CHARACTER, assertions intact" 1 "$(verify_full "$EV/mbtrunc" mb)" "$EV/mbtrunc" mb
echo

rm -rf "$EV"
if [ "$fail" -ne 0 ]; then
    echo "SITE 3 SUCCESSOR: FAIL -- $fail leg(s) did not behave as required." >&2
    exit 1
fi
cat <<'EOF'
SITE 3 SUCCESSOR: PASS
  Header MULTIPLICITY is now a DETECTION (rc=1), not a refusal and not a gap --
  T250's redC recorded it as a GAP and the frozen original scores the schema
  refusal as though it were the catch.
  A multibyte body truncated MID-CHARACTER, with every sidecar assertion left
  intact, is DETECTED.
  The 17-length wrap sweep is NOT measured here: it is retired onto T274
  instrument 20, whose presence and length list are ASSERTED in LEG 0 above.
EOF
