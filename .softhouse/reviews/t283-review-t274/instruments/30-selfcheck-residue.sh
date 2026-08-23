#!/usr/bin/env bash
# T283 -- WHAT THE ONLY REAL CALLER DOES WHEN THE VERIFIER SAYS NO.
#
# T274's handoff says: "the verifier's automatic caller already exists and is the
# capture-time self-check inside `oracle_send`, which is HARD and VOIDS the
# capture."  That is the load-bearing sentence for the whole design -- the
# verifier has no other caller (T250's attestation is a declared orphan and T274
# gave it none), so if the self-check does not void the capture, nothing does.
#
# This measures it by FAULT INJECTION rather than by reading: a shim library
# whose `wire_attestation.py` delegates `derive` to the real module and makes
# `verify` fail.  Both failure modes are driven, because they are different
# code paths in `oracle_send`:
#
#   A  derive FAILS   -- oracle_send's own comment says the response is not
#                        committed; expect NO artefacts left behind.
#   B  verify FAILS   -- "Treat every artefact for NAME as void."  Expect: ???
#   C  verify ERRORS  (exit 127, the missing-tool shape, not a verdict)
#   D  the library is ABSENT altogether -- expect a refusal before any request
#
# EXPECTED, STATED BEFORE THE RUN (P-76): A leaves nothing; D leaves nothing and
# never reaches the oracle; B and C return nonzero.  My PREDICTION for B and C
# is that the artefacts ARE LEFT ON DISK and that the only thing that voids them
# is the English sentence on stderr -- which is P-89: prose does not fire.
set -euo pipefail

TREE=${T274_TREE:?set T274_TREE to a checkout of softhouse/t274-attestation-failopen}
LIB="$TREE/.softhouse/capture/lib"
BASE_URL='https://localhost:8443/fineract-provider/api/v1'
AUTH='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
HDRS="$AUTH
Fineract-Platform-TenantId: default
Content-Type: application/json"

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t283self.XXXXXX")
trap 'rm -rf "$WORK"' EXIT HUP INT TERM QUIT

REAL="$LIB/wire_attestation.py"
shimlib() {  # shimlib DIR MODE RC -- a lib whose verify/derive fails
    mkdir -p "$1"
    cp "$LIB/oracle_send.sh" "$1/"
    cat > "$1/wire_attestation.py" <<SHIM
#!/usr/bin/env python3
"""T283 fault-injection shim: delegates to the real module except for $2."""
import subprocess, sys
if len(sys.argv) > 1 and sys.argv[1] == "$2":
    sys.stderr.write("T283 SHIM: forced failure of \`$2\` (rc=$3)\n")
    sys.exit($3)
sys.exit(subprocess.call([sys.executable, "$REAL"] + sys.argv[1:]))
SHIM
}

echo "T283 -- oracle_send's behaviour when the self-check says NO"
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
shasum -a 256 "$LIB/oracle_send.sh" | sed 's/^/  /'
echo

pass=0; fail=0
note() { printf '  %-3s %s\n' "$1" "$2"; }

run_arm() {  # run_arm NAME LIBDIR
    d="$WORK/$1"; mkdir -p "$d"
    rc=0
    (
        OS_BASE="$BASE_URL"; OS_OUTDIR="$d"; OS_LIB_DIR="$2"; OS_HEADERS="$HDRS"
        export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
        # shellcheck source=/dev/null
        . "$2/oracle_send.sh"
        oracle_send probe POST /offices "$WORK/body.json"
    ) > "$d/log" 2>&1 || rc=$?
    echo "$rc"
}

residue() {  # residue DIR -> the capture artefacts left behind
    ls "$1" | /usr/bin/grep -c '^probe\.' || true
}

printf '{"invalid":"deliberately-not-a-valid-office"}\n' > "$WORK/body.json"

# ---- A: derive fails -------------------------------------------------------
shimlib "$WORK/libA" derive 1
rc=$(run_arm A "$WORK/libA"); n=$(residue "$WORK/A")
note A "derive FAILS   -> oracle_send rc=$rc, capture artefacts left behind: $n"
sed -n '1,3p' "$WORK/A/log" | sed 's/^/       /'
if [ "$n" -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "       *** artefacts survived a failed derivation ***"; fi

# ---- B: verify fails (a verdict of NO) -------------------------------------
shimlib "$WORK/libB" verify 1
rc=$(run_arm B "$WORK/libB"); n=$(residue "$WORK/B")
note B "verify FAILS   -> oracle_send rc=$rc, capture artefacts left behind: $n"
ls "$WORK/B" | tr '\n' ' ' | sed 's/^/       /'; echo
sed -n '1,3p' "$WORK/B/log" | sed 's/^/       /'

# ---- C: verify errors (exit 127, the missing-tool shape) -------------------
shimlib "$WORK/libC" verify 127
rc=$(run_arm C "$WORK/libC"); n=$(residue "$WORK/C")
note C "verify ERRORS  -> oracle_send rc=$rc, capture artefacts left behind: $n"
sed -n '1,3p' "$WORK/C/log" | sed 's/^/       /'

# ---- D: the library is absent ----------------------------------------------
mkdir -p "$WORK/libD"; cp "$LIB/oracle_send.sh" "$WORK/libD/"
rc=$(run_arm D "$WORK/libD"); n=$(residue "$WORK/D")
note D "lib ABSENT     -> oracle_send rc=$rc, capture artefacts left behind: $n"
sed -n '1,2p' "$WORK/D/log" | sed 's/^/       /'
if [ "$n" -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); fi

echo
echo "READ THIS AS: arms B and C are the finding if the residue count is nonzero --"
echo "the capture is 'void' only in an English sentence on stderr.  A and D are the"
echo "controls that show oracle_send CAN and DOES clean up on the path it handles."
echo "controls as expected: $pass, unexpected: $fail"
exit 0
