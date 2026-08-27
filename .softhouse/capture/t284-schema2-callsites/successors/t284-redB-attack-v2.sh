#!/usr/bin/env bash
# T284 SITE 2 SUCCESSOR -- T261's RED-DRIVE B attack set, TAUGHT SCHEMA 2.
#
# THE SITE THIS SUPERSEDES
#   .softhouse/reviews/t261-tenant-attestation/instruments/t261-redB-attack.sh
#   Two REQUEST_ONLY `verify` calls (L47, L49).  Since T274 every capture it
#   takes is schema 2, so its own CALIBRATION refuses and the script ABORTS at
#   exit 4 with ZERO of its eleven attacks scored.  Measured on this branch:
#   ../evidence/RED-site2.txt.  The abort is honest -- it does not score against
#   a broken baseline -- but the instrument is completely dead.
#
#   The original is FROZEN and is NOT edited (T114's standing ruling: anything
#   that produced committed evidence is superseded by a scratch copy, never
#   edited in place).  It wrote 265 committed files under
#   .softhouse/reviews/t261-tenant-attestation/evidence/, including the per-arm
#   `.vout` / `.verr` files that ARE the output of those two calls.
#
# WHY (a) TAUGHT, NOT (c) RETIRED
#   Six of its eleven attack shapes appear in NO other instrument in the tree:
#     A3  body truncated + all three body assertions deleted
#     A5  a wire header whose NAME COLLIDES with a sidecar assertion key, value
#         tampered in the sidecar
#     A7  a colon-bearing header value tampered after the colon
#     A8  a sidecar header NAME case-folded
#     A9  the header record swapped for a DIFFERENT real request's record
#     A11 `request-headers-sha256:` deleted outright
#   T274's own arms cover A1 (its R2b), A2 (R1), A4 (R2a), A6 (R3a) and A10 (R4).
#   Retiring this site would therefore drop six live attack shapes.  It is taught.
#
# WHAT CHANGED, AND WHAT DELIBERATELY DID NOT
#   * Every `verify` call now presents the whole artefact set:
#     --sidecar --headers --req --resp --resphdr --status.  A schema 2 sidecar
#     with an artefact withheld REFUSES, and a refusal is not a measurement.
#   * A12 is NEW and could not be written before T274: the RESPONSE HEADER
#     RECORD swapped for another capture's.  The response leg exists now, so it
#     is attacked.
#   * SCOPE GATE, the mirror of the site 1 successor's: every captured sidecar
#     must BE schema 2.  One that is not -> REFUSE (exit 2), grade nothing.  A
#     site scoped to a schema states that scope and enforces it in both
#     directions; silently proceeding on the wrong schema is how a frozen
#     instrument becomes a fail-open (P-45: a test-only guard is not a guard --
#     verify the path that actually executes calls it).
#   * THE BODY IS DELIBERATELY INVALID JSON that the oracle refuses at
#     validation.  T261's original POSTed a VALID office and created one (it is
#     still there: id 2, "T261 probe").  A red-drive must not mutate the
#     reference oracle to make its point; every attack here tampers ARTEFACTS
#     after capture, so the oracle's answer being a 4xx costs the experiment
#     nothing.
#   * EXPECTATIONS ARE NOT TUNED TO THE MEASUREMENT.  The stated expectation is
#     the CONTRACT: after T274's default-deny rewrite every one of these tamper
#     shapes must be caught -- rc=1 (a verdict of NO) or rc=2 (refused).  rc=0 is
#     a GAP and fails this instrument.  If a gap is real it is reported, never
#     absorbed by rewriting the expectation.
#
# CAPTURES GO TO A SCRATCH DIRECTORY OUTSIDE THE REPOSITORY, and only this
# transcript is committed.  Reason, stated rather than left to be discovered:
# committed capture artefacts under `.softhouse/capture/` are parsed by the
# harness's wire-float round-trip guard (every `*.req`) and counted by
# `attest_population.py`'s sidecar ratchet, whose pin lives in
# `.softhouse/capture/lib/` -- outside this task's scope.  Committing eleven
# deliberately-tampered artefact sets would require editing that pin.  The cost
# is real and is named in the handoff: this instrument's evidence is its
# transcript, and reproducing it needs the oracle.
#
# ENGINE (P-33/P-53): no grep, no rg, no git grep.  `git rev-parse` locates the
# root and its failure is fatal; line selection is `sed -n '/re/p'` under
# LC_ALL=C; tampering is done in python3 from a heredoc.
#
# CALIBRATION (P-72): A0 is an untouched POSITIVE CONTROL that must verify rc=0.
# If it does not, NOTHING is scored -- a guard graded against a broken baseline
# reports the baseline, not the guard.
#
# EXIT: 0 every attack caught and the control clean; 1 a GAP (an attack accepted)
# or the control failed; 2 REFUSED (no oracle, capture failed, wrong schema).
set -euo pipefail

fail_hard() { printf 'redB-v2 REFUSING: %s\n' "$*" >&2; exit 2; }

ROOT=$(git rev-parse --show-toplevel) || fail_hard "not inside a git repository."
[ -d "$ROOT/.softhouse" ] || fail_hard "$ROOT does not contain .softhouse."

LIB="$ROOT/.softhouse/capture/lib"
WA="$LIB/wire_attestation.py"
FROZEN="$ROOT/.softhouse/reviews/t261-tenant-attestation/instruments/t261-redB-attack.sh"
BASE="https://localhost:8443/fineract-provider/api/v1"
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
CT='Content-Type: application/json'

[ -f "$WA" ] || fail_hard "the verifier does not exist: $WA"
[ -f "$LIB/oracle_send.sh" ] || fail_hard "the capture library does not exist: $LIB/oracle_send.sh"
[ -f "$FROZEN" ] || fail_hard "the frozen original this supersedes is GONE: $FROZEN.
  A successor whose predecessor has vanished is not a supersession, it is an
  unexplained new instrument. Refusing rather than reporting a clean run."

EV=$(mktemp -d "${TMPDIR:-/tmp}/t284redB.XXXXXX") || fail_hard "mktemp -d failed"
# NOTE: no EXIT trap. `oracle_send` sets its own EXIT trap and clears it with
# `trap - EXIT`, which would silently drop ours (T283 FU-T283-1). Cleanup is
# explicit at the end; on an abort the scratch tree is left under TMPDIR, which
# is the diagnosable outcome rather than the tidy one.
mkdir -p "$EV/src" "$EV/req"
printf '{"invalid":"deliberately-not-a-valid-office"}\n' > "$EV/req/bad-office.json"

echo "T284 SITE 2 -- T261's RED-DRIVE B, taught schema 2"
echo "  supersedes : .softhouse/reviews/t261-tenant-attestation/instruments/t261-redB-attack.sh"
echo "               (FROZEN, sha256 $(shasum -a 256 "$FROZEN" | cut -d' ' -f1))"
echo "  verifier   : $(shasum -a 256 "$WA" | cut -d' ' -f1)"
echo "  oracle     : $BASE"
echo "  curl       : $(curl --version | head -1 | cut -d' ' -f1-2)"
echo "  scratch    : $EV"
echo

capture() {   # capture NAME METHOD PATH [BODY] [EXTRA_HEADER...]
    c_name=$1; c_method=$2; c_path=$3; c_body=${4:-}
    shift 4 2>/dev/null || shift $#
    mkdir -p "$EV/src/$c_name"
    OS_BASE="$BASE"; OS_OUTDIR="$EV/src/$c_name"; OS_LIB_DIR="$LIB"
    OS_HEADERS="$AUTH
Fineract-Platform-TenantId: default
$CT"
    for c_h in "$@"; do OS_HEADERS="$OS_HEADERS
$c_h"; done
    export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
    # shellcheck source=/dev/null
    . "$LIB/oracle_send.sh"
    oracle_send "$c_name" "$c_method" "$c_path" ${c_body:+"$c_body"}
}

echo "-- capturing base artefacts from the LIVE oracle --"
capture post  POST /offices "$EV/req/bad-office.json"      || fail_hard "the POST capture failed; no artefacts, no verdict."
capture dup   GET  /offices "" "Fineract-Platform-TenantId: gerege" || fail_hard "the duplicate-header capture failed."
capture colon GET  /offices "" 'X-T284-Note: alpha: beta; gamma'    || fail_hard "the colon-header capture failed."
capture kcoll GET  /offices "" 'body-bytes: 999999'                 || fail_hard "the key-collision capture failed."
echo

# ------------------------------------------------------------------ scope gate
echo "-- scope gate: every captured sidecar must BE schema 2 --"
gate_bad=0
for s in post dup colon kcoll; do
    side="$EV/src/$s/$s.http"
    if [ ! -f "$side" ]; then
        printf '  %-6s sidecar MISSING: %s\n' "$s" "$side"; gate_bad=1; continue
    fi
    line=$(LC_ALL=C sed -n '/^attestation-schema:/p' "$side" | LC_ALL=C sed -n '1p')
    if [ "$line" != "attestation-schema: 2" ]; then
        printf '  %-6s OUT OF SCOPE -- declares `%s`\n' "$s" "${line:-<no schema line: this is a SCHEMA 1 sidecar>}"
        gate_bad=1
    else
        printf '  %-6s schema 2\n' "$s"
    fi
done
if [ "$gate_bad" -ne 0 ]; then
    fail_hard "at least one capture is not schema 2 (above). This instrument's call
  shape presents the response leg, which a schema 1 sidecar does not attest, so
  no verdict is available. REFUSED, and NOTHING was graded."
fi
echo

# --------------------------------------------------------------------- verify
# The three response flags are written out LITERALLY on both branches rather than
# assembled into "$@". They must be readable by
# ../instruments/10-callsite-registry.py, which classifies a call site by the
# flags it can SEE; a helper that hides them behind `$@` classifies as INDIRECT
# and would have to be granted a declared exception in the pin. Writing an
# exception for one's own file is how a default-deny register stops being one.
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

echo "-- CALIBRATION: the untouched positive control must VERIFY --"
rc=$(verify_full "$EV/src/post" post)
if [ "$rc" != "0" ]; then
    LC_ALL=C sed 's/^/    /' "$EV/src/post/post.verr"
    fail_hard "the positive control did not verify (rc=$rc). Nothing may be scored
  against a broken baseline; a guard that fails everything detects nothing."
fi
echo "  A0 positive control VERIFIED rc=0"
echo

PASS=0; GAP=0; N=0
mk() { rm -rf "$EV/$1"; cp -R "$EV/src/$2" "$EV/$1"; }
score() {   # score LABEL GOT_RC DIR NAME
    s_label=$1; s_got=$2; s_dir=$3; s_name=$4
    N=$((N + 1))
    if [ "$s_got" = "0" ]; then
        printf '  [%-8s] %-58s rc=%s  <-- GAP\n' "ACCEPTED" "$s_label" "$s_got"
        GAP=$((GAP + 1))
    else
        printf '  [%-8s] %-58s rc=%s\n' "CAUGHT" "$s_label" "$s_got"
        PASS=$((PASS + 1))
    fi
    LC_ALL=C sed -n '1,2p' "$s_dir/$s_name.verr" | LC_ALL=C sed 's/^/            /'
}

echo "-- ATTACKS (rc=1 verdict-NO or rc=2 refused is CAUGHT; rc=0 is a GAP) --"

# A1 -- duplicated header on the wire, one copy DELETED from the sidecar.
mk a1 dup
python3 - "$EV/a1/dup.http" <<'PY'
import sys
p = sys.argv[1]
out, seen = [], False
for l in open(p).read().split("\n"):
    if l.startswith("Fineract-Platform-TenantId:") and not seen:
        seen = True
        continue
    out.append(l)
open(p, "w").write("\n".join(out))
PY
score "A1  duplicated header: one copy removed from sidecar" "$(verify_full "$EV/a1" dup)" "$EV/a1" dup

# A2 -- body-sha256 deleted, body swapped for DIFFERENT bytes of the SAME length.
# The swap is `swapcase`, not a run of one character: a run of X bytes is not
# valid JSON and the harness's wire-float guard parses every committed .req
# (T274 met this). Same length, different bytes, still JSON, attack unchanged.
mk a2 post
python3 - "$EV/a2/post.http" "$EV/a2/post.req" <<'PY'
import sys
sc, rq = sys.argv[1], sys.argv[2]
b = open(rq, "rb").read()
open(rq, "wb").write(b.swapcase())
ls = [l for l in open(sc).read().split("\n") if not l.startswith("body-sha256: ")]
open(sc, "w").write("\n".join(ls))
PY
score "A2  body swapped (same length) + body-sha256 line deleted" "$(verify_full "$EV/a2" post)" "$EV/a2" post

# A3 -- body truncated, all three body assertions deleted.
mk a3 post
python3 - "$EV/a3/post.http" "$EV/a3/post.req" <<'PY'
import sys
sc, rq = sys.argv[1], sys.argv[2]
b = open(rq, "rb").read()
open(rq, "wb").write(b[:len(b) // 2])
ls = [l for l in open(sc).read().split("\n")
      if not l.startswith("body-sha256: ")
      and not l.startswith("body-bytes: ")
      and not l.startswith("content-length-crosscheck: ")]
open(sc, "w").write("\n".join(ls))
PY
score "A3  body truncated + all three body assertions deleted" "$(verify_full "$EV/a3" post)" "$EV/a3" post

# A4 -- header lines REORDERED in the sidecar (membership vs sequence).
mk a4 post
python3 - "$EV/a4/post.http" <<'PY'
import sys
p = sys.argv[1]
ls = open(p).read().split("\n")
i = [n for n, l in enumerate(ls) if l.startswith("Fineract-Platform-TenantId:")]
j = [n for n, l in enumerate(ls) if l.startswith("Host:")]
if i and j:
    ls[i[0]], ls[j[0]] = ls[j[0]], ls[i[0]]
open(p, "w").write("\n".join(ls))
PY
score "A4  sidecar header lines REORDERED vs the wire" "$(verify_full "$EV/a4" post)" "$EV/a4" post

# A5 -- a wire header whose NAME collides with a sidecar assertion key, tampered.
mk a5 kcoll
python3 - "$EV/a5/kcoll.http" <<'PY'
import sys
p = sys.argv[1]
# READ FULLY FIRST. `open(p, "w").write(open(p).read())` TRUNCATES BEFORE IT
# READS -- the first draft of this instrument did exactly that, the sidecar came
# out empty, and all four affected arms scored CAUGHT rc=2 on "does not begin
# with attestation-derivation:" instead of on the attack. A green score read
# without its messages is not a measurement.
t = open(p).read()
open(p, "w").write(t.replace("body-bytes: 999999", "body-bytes: 1"))
PY
score "A5  wire header named 'body-bytes' tampered in sidecar" "$(verify_full "$EV/a5" kcoll)" "$EV/a5" kcoll

# A6 -- an INVENTED line under a key the verifier recognises.
mk a6 post
python3 - "$EV/a6/post.http" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()          # read fully BEFORE opening for write (see A5)
open(p, "w").write(t.rstrip("\n") + "\ncontent-length-crosscheck: MATCH (99999 bytes)\n")
PY
score "A6  invented 'content-length-crosscheck' line appended" "$(verify_full "$EV/a6" post)" "$EV/a6" post

# A7 -- a colon-bearing header value tampered AFTER the colon.
mk a7 colon
python3 - "$EV/a7/colon.http" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()          # read fully BEFORE opening for write (see A5)
open(p, "w").write(t.replace("alpha: beta; gamma", "alpha: DELTA; gamma"))
PY
score "A7  colon-bearing header value tampered in sidecar" "$(verify_full "$EV/a7" colon)" "$EV/a7" colon

# A8 -- a sidecar header NAME case-folded.
mk a8 post
python3 - "$EV/a8/post.http" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()          # read fully BEFORE opening for write (see A5)
open(p, "w").write(t.replace("Fineract-Platform-TenantId: ",
                             "fineract-platform-tenantid: "))
PY
score "A8  sidecar header name case-folded" "$(verify_full "$EV/a8" post)" "$EV/a8" post

# A9 -- the request header record swapped for a DIFFERENT real request's record.
mk a9 post
cp "$EV/src/dup/dup.reqhdr" "$EV/a9/post.reqhdr"
score "A9  request record swapped for another real request's" "$(verify_full "$EV/a9" post)" "$EV/a9" post

# A10 -- the RESPONSE BODY swapped for another real capture's.
mk a10 post
cp "$EV/src/dup/dup.json" "$EV/a10/post.json"
score "A10 RESPONSE body swapped for another capture's" "$(verify_full "$EV/a10" post)" "$EV/a10" post

# A11 -- request-headers-sha256 line DELETED entirely.
mk a11 post
python3 - "$EV/a11/post.http" <<'PY'
import sys
p = sys.argv[1]
ls = [l for l in open(p).read().split("\n")
      if not l.startswith("request-headers-sha256: ")]
open(p, "w").write("\n".join(ls))
PY
score "A11 request-headers-sha256 line deleted from sidecar" "$(verify_full "$EV/a11" post)" "$EV/a11" post

# A12 -- NEW, and only expressible since T274: the RESPONSE HEADER RECORD swapped.
mk a12 post
cp "$EV/src/dup/dup.resphdr" "$EV/a12/post.resphdr"
score "A12 RESPONSE HEADER record swapped for another capture's" "$(verify_full "$EV/a12" post)" "$EV/a12" post

echo
echo "SCORE: $PASS caught / $GAP accepted, of $N attacks"
rm -rf "$EV"
if [ "$GAP" -ne 0 ]; then
    echo "SITE 2 SUCCESSOR: FAIL -- $GAP attack(s) were ACCEPTED (rc=0)." >&2
    exit 1
fi
echo "SITE 2 SUCCESSOR: PASS -- all $N tamper shapes caught, positive control clean."
