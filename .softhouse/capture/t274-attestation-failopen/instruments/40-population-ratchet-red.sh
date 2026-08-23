#!/usr/bin/env bash
# T274 -- the RATCHET (`attest_population.py`) driven RED four ways, plus its
# positive control on the real tree.
#
# The ratchet is what T269 can actually wire.  A pin that has never been seen to
# FAIL is not a pin, so every failure mode is driven here, in a THROWAWAY GIT
# REPOSITORY built for the purpose -- the real tree is never tampered with, and
# nothing here can leave a stray file or a stray index entry behind.
#
# ARMS (expected exit status in brackets):
#   C0 [0] the REAL repository against the REAL pin -- the positive control.
#          A guard that cannot pass is as useless as one that cannot fail.
#   R1 [1] a NEW sidecar with no derivation line is committed  -> legacy ROSE
#   R2 [1] a legacy sidecar is removed without moving the pin  -> legacy FELL
#   R3 [1] a directory declares itself tampered evidence but is NOT in the pin
#   R4 [1] a PINNED tampered-evidence directory disappears
#   F1 [2] `git ls-files` matches no sidecar at all            -> REFUSE, never
#          "clean" (not found is a statement about the search)
#   F2 [2] the pin file is missing                             -> REFUSE
#
# F1 is the arm that matters most to this program: an empty search result read as
# a clean tree is the fail-open this repository has recorded again and again.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TASK=$(cd "$HERE/.." && pwd)
ROOT=$(cd "$TASK/../../.." && pwd)
GUARD="$ROOT/.softhouse/capture/lib/attest_population.py"
REALPIN="$ROOT/.softhouse/capture/lib/attest_population_pin.json"
EV="$TASK/evidence"
TAG='attestation-derivation: curl --trace-ascii; request headers AS SENT'

if [ ! -f "$GUARD" ] || [ ! -f "$REALPIN" ]; then
    echo "REFUSING: missing $GUARD or $REALPIN" >&2
    exit 2
fi

pass=0
fail=0
judge() {  # judge ARM EXPECTED ACTUAL DESC
    if [ "$3" -eq "$2" ]; then j='ok'; pass=$((pass + 1));
    else j='*** UNEXPECTED ***'; fail=$((fail + 1)); fi
    printf '  %-3s expected rc=%s  got rc=%s  %-20s %s\n' "$1" "$2" "$3" "$j" "$4"
}

echo "T274 -- the sidecar-population ratchet, driven red"
shasum -a 256 "$GUARD" "$REALPIN" | sed 's/^/  /'
echo

# ---- C0: the positive control, on the real tree and the real pin ------------
rc=0
python3 "$GUARD" > "$EV/40-population-real-tree.txt" 2>&1 || rc=$?
judge C0 0 "$rc" "REAL tree vs REAL pin"
sed 's/^/    /' "$EV/40-population-real-tree.txt"
echo

# ---- a throwaway repository, so no arm can touch the real one ---------------
SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t274ratchet.XXXXXX")
trap 'rm -rf "$SCRATCH"' EXIT HUP INT TERM QUIT

build() {   # build  -> a fresh mini-repo: 2 legacy, 1 derived, 1 tampered dir
    rm -rf "$SCRATCH/repo"
    mkdir -p "$SCRATCH/repo/caps" "$SCRATCH/repo/tampered"
    git -C "$SCRATCH/repo" init -q
    git -C "$SCRATCH/repo" config user.email t274@example.invalid
    git -C "$SCRATCH/repo" config user.name T274
    printf 'POST /x HTTP/1.1\nFineract-Platform-TenantId: gerege\n' > "$SCRATCH/repo/caps/old1.http"
    printf 'POST /y HTTP/1.1\nFineract-Platform-TenantId: gerege\n' > "$SCRATCH/repo/caps/old2.http"
    printf '%s\nsend-header-block 1 of 1\nGET /z HTTP/1.1\n' "$TAG" > "$SCRATCH/repo/caps/new1.http"
    printf 'POST /t HTTP/1.1\n' > "$SCRATCH/repo/tampered/forged.http"
    printf 'declared\n' > "$SCRATCH/repo/tampered/ATTEST-TAMPERED-EVIDENCE"
    cat > "$SCRATCH/pin.json" <<'JSON'
{ "legacy_sidecars": 2, "tampered_evidence_dirs": ["tampered"] }
JSON
    git -C "$SCRATCH/repo" add -A
}

run() {   # run DESC -> echoes rc
    r=0
    python3 "$GUARD" --root "$SCRATCH/repo" --pin "$SCRATCH/pin.json" \
        > "$SCRATCH/out" 2> "$SCRATCH/err" || r=$?
    echo "$r"
}

build
judge S0 0 "$(run)" "scratch baseline: 2 legacy == pin 2, 1 exclusion pinned"

build
printf 'POST /new HTTP/1.1\nFineract-Platform-TenantId: gerege\n' > "$SCRATCH/repo/caps/added.http"
git -C "$SCRATCH/repo" add -A
judge R1 1 "$(run)" "a NEW sidecar with no derivation line -> legacy ROSE"
sed 's/^/    /' "$SCRATCH/err"

build
git -C "$SCRATCH/repo" rm -q -f caps/old2.http
judge R2 1 "$(run)" "a legacy sidecar removed without moving the pin -> legacy FELL"
sed 's/^/    /' "$SCRATCH/err"

build
mkdir -p "$SCRATCH/repo/sneaky"
printf 'POST /s HTTP/1.1\n' > "$SCRATCH/repo/sneaky/x.http"
printf 'declared\n' > "$SCRATCH/repo/sneaky/ATTEST-TAMPERED-EVIDENCE"
git -C "$SCRATCH/repo" add -A
judge R3 1 "$(run)" "an UNPINNED directory excludes itself"
sed 's/^/    /' "$SCRATCH/err"

build
git -C "$SCRATCH/repo" rm -q -r -f tampered
judge R4 1 "$(run)" "a PINNED exclusion disappears without a pin change"
sed 's/^/    /' "$SCRATCH/err"

build
git -C "$SCRATCH/repo" rm -q -f caps/old1.http caps/old2.http caps/new1.http
git -C "$SCRATCH/repo" rm -q -r -f tampered
judge F1 2 "$(run)" "NO sidecar matches at all -> REFUSE, not 'clean'"
sed 's/^/    /' "$SCRATCH/err"

build
rm -f "$SCRATCH/pin.json"
judge F2 2 "$(run)" "the pin file is missing -> REFUSE"
sed 's/^/    /' "$SCRATCH/err"

echo
echo "SCORE: $pass as expected, $fail unexpected"
if [ "$fail" -ne 0 ]; then
    echo "INSTRUMENT VERDICT: FAIL"
    exit 1
fi
echo "INSTRUMENT VERDICT: PASS -- the ratchet passes on the real tree and fails on"
echo "every route by which the population could rot."
exit 0
