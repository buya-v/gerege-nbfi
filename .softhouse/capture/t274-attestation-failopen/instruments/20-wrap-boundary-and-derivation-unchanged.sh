#!/usr/bin/env bash
# T274 -- the two things a verifier rewrite could QUIETLY BREAK, measured.
#
# T261 called the `--trace-ascii` 64-byte wrap reassembly "the strongest work in
# the diff" and swept the boundary live to prove it.  A rewrite of the same file
# that repaired four fail-opens and silently corrupted long-header reassembly
# would be a worse outcome than the fail-opens, so this re-runs that sweep
# against the T274 rig, and adds the check T261 did not need:
#
#   (A) WRAP BOUNDARY.  Ground truth is the exact bytes handed to curl's `-H`.
#       The sidecar must reproduce them character for character at 1, 10, 60-66,
#       127-129, 200, 300, 1000 and 4000 bytes, plus a 360-byte colon-laden
#       value.  Nothing is taken from any transcript.
#   (B) THE REQUEST DERIVATION IS UNCHANGED.  The same headers are captured by
#       the T250 baseline rig and by the T274 rig and the two `.reqhdr` wire
#       records are compared BYTE FOR BYTE.  If they differ, T274 changed what is
#       recorded rather than only what is checked, and every claim about
#       continuity with T250's evidence is void.
#
# A calibration that cannot fail is not a calibration (P-72): (A) fails loudly if
# any length is attested inexactly, and (B) fails if the records differ by one
# byte.  Both are checked against a value each run rather than asserted.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TASK=$(cd "$HERE/.." && pwd)
ROOT=$(cd "$TASK/../../.." && pwd)
FIXED_LIB="$ROOT/.softhouse/capture/lib"
BASE_LIB="$TASK/baseline"
EV="$TASK/evidence/wrap"
# --- T304 FAIL-CLOSED GUARD (FU-T284-3) ---------------------------------------------
# This instrument rebuilds its evidence directory from scratch on every run, and that
# directory holds 145 TRACKED files. T114 binds: committed evidence is named and
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
mkdir -p "$EV"
fail=0

send_fixed() {   # send_fixed NAME HEADERVALUE
    sf_name=$1; sf_val=$2
    mkdir -p "$EV/$sf_name"
    (
        OS_BASE="$BASE_URL"
        OS_OUTDIR="$EV/$sf_name"
        OS_LIB_DIR="$FIXED_LIB"
        OS_HEADERS="$AUTH
Fineract-Platform-TenantId: default
X-T274-Long: $sf_val"
        export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
        # shellcheck source=/dev/null
        . "$FIXED_LIB/oracle_send.sh"
        oracle_send "$sf_name" GET /offices ""
    ) > "$EV/$sf_name/capture.log" 2>&1
}

check_exact() { # check_exact NAME HEADERVALUE
    python3 - "$EV/$1/$1.http" "$2" "$1" <<'PY'
import re, sys
sidecar, expect, name = open(sys.argv[1]).read(), sys.argv[2], sys.argv[3]
m = re.search(r"(?m)^X-T274-Long: (.*)$", sidecar)
got = m.group(1) if m else "<ABSENT>"
ok = (got == expect)
print("  %-8s sent=%-5d attested=%-5s %s"
      % (name, len(expect), (len(got) if m else "-"), "EXACT" if ok else "*** CORRUPT ***"))
if not ok:
    print("      expected[:80] %r" % expect[:80])
    print("      attested[:80] %r" % got[:80])
    sys.exit(1)
PY
}

echo "T274 (A) -- trace-ascii wrap reassembly across the 64-byte boundary"
echo "curl: $(curl --version | head -1)"
echo "verifier under test: $FIXED_LIB/wire_attestation.py"
shasum -a 256 "$FIXED_LIB/wire_attestation.py" | sed 's/^/  /'
echo

for n in 1 10 60 61 62 63 64 65 66 127 128 129 200 300 1000 4000; do
    v=$(python3 -c "import sys; print('A'*int(sys.argv[1]))" "$n")
    send_fixed "L$n" "$v"
    rc=0
    check_exact "L$n" "$v" || rc=$?
    [ "$rc" -eq 0 ] || fail=$((fail + 1))
    # and the whole artefact set must verify under the T274 verifier
    vrc=0
    python3 "$FIXED_LIB/wire_attestation.py" verify \
        --sidecar "$EV/L$n/L$n.http" --headers "$EV/L$n/L$n.reqhdr" \
        --resp "$EV/L$n/L$n.json" --resphdr "$EV/L$n/L$n.resphdr" \
        --status "$EV/L$n/L$n.status" > "$EV/L$n/verify.out" 2> "$EV/L$n/verify.err" || vrc=$?
    if [ "$vrc" -ne 0 ]; then
        echo "      verify rc=$vrc for L$n  *** UNEXPECTED ***"
        fail=$((fail + 1))
    fi
done

echo
echo "  -- a long value CONTAINING colons and spaces (the shape that breaks naive parsers) --"
vmix=$(python3 -c "print('x: y; '*60)")
send_fixed Lmix "$vmix"
rc=0
check_exact Lmix "$vmix" || rc=$?
[ "$rc" -eq 0 ] || fail=$((fail + 1))

echo
echo "T274 (B) -- is the WIRE RECORD itself unchanged from the T250 rig?"
mkdir -p "$EV/cmp-red" "$EV/cmp-green"
CMP_HDRS="$AUTH
Fineract-Platform-TenantId: default
X-T274-Cmp: $(python3 -c "print('B'*200)")"
for arm in red green; do
    if [ "$arm" = red ]; then lib="$BASE_LIB"; else lib="$FIXED_LIB"; fi
    (
        OS_BASE="$BASE_URL"
        OS_OUTDIR="$EV/cmp-$arm"
        OS_LIB_DIR="$lib"
        OS_HEADERS="$CMP_HDRS"
        export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
        # shellcheck source=/dev/null
        . "$lib/oracle_send.sh"
        oracle_send cmp GET /offices ""
    ) > "$EV/cmp-$arm/capture.log" 2>&1
done
echo "  T250 rig  .reqhdr: $(shasum -a 256 "$EV/cmp-red/cmp.reqhdr" | cut -d' ' -f1)"
echo "  T274 rig  .reqhdr: $(shasum -a 256 "$EV/cmp-green/cmp.reqhdr" | cut -d' ' -f1)"
if cmp -s "$EV/cmp-red/cmp.reqhdr" "$EV/cmp-green/cmp.reqhdr"; then
    echo "  IDENTICAL -- T274 changed what is CHECKED, not what is RECORDED."
else
    echo "  *** DIFFER *** -- T274 changed the request record itself:"
    diff "$EV/cmp-red/cmp.reqhdr" "$EV/cmp-green/cmp.reqhdr" | sed 's/^/    /'
    fail=$((fail + 1))
fi

echo
if [ "$fail" -ne 0 ]; then
    echo "INSTRUMENT VERDICT: FAIL ($fail problem(s))"
    exit 1
fi
echo "INSTRUMENT VERDICT: PASS -- every length attested EXACT, every artefact set"
echo "verified, and the request wire record is byte-identical to the T250 rig's."
exit 0
