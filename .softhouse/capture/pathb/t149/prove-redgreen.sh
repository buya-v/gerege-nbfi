#!/bin/bash
# T149 — drive the new vector RED against HALF_EVEN and GREEN against HALF_UP.
#
# The discriminating power of a vector that is only CLAIMED is the "guard that cannot
# fail" class (P-22). So it is driven, twice, against the REAL harness:
#
#   arm 1  the 42-vector store as it stood BEFORE this vector, mutated to HALF_EVEN.
#          Expected: parity FAIL 3, exactly T61-HE-A/B/C. This is the arm that REFUTES
#          the commissioning brief's premise that nothing in the corpus would notice.
#   arm 2  the 43-vector store, mutated to HALF_EVEN.
#          Expected: parity FAIL 4 — the three above PLUS T149-PATHB-TIE (RED).
#   arm 3  the 43-vector store, unmutated.
#          Expected: parity PASS 43, exit 0 (GREEN).
#
# The mutation is not this task's invention: it is the already-named M7
# MONEY-QUANTIZATION-HALF-EVEN of .softhouse/handoff/T61-mutations.py, which applies one
# literal substitution to nexus/internal/apps/loanschedule/rounding.go and reverts it
# unconditionally. T61-mutations.py runs an unmutated BASELINE first and refuses to
# attribute anything to a mutation unless that baseline is green.
#
#     bash prove-redgreen.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
OUT="$HERE/redgreen"
VEC="$REPO/.softhouse/vectors/loanschedule/T149-PATHB-TIE-1M162502pt50-12x21pt6pct.json"
PARK="$HERE/.parked-vector.json"
mkdir -p "$OUT"

fail() { echo "PROOF FAILED: $*" >&2; exit 1; }

# --- arm 1: the 42-vector store, mutated ------------------------------------------
[ -f "$VEC" ] || fail "the vector is not in the store: $VEC"
mv "$VEC" "$PARK" || fail "could not park the vector"
python3 "$REPO/.softhouse/handoff/T61-mutations.py" M7 > "$OUT/premise-refuted-42-vector-store.txt" 2>&1
rc1=$?
mv "$PARK" "$VEC" || fail "could not restore the vector — DO NOT COMMIT until it is back"
[ "$rc1" = 0 ] || fail "arm 1 driver exited $rc1"

# --- arm 2: the 43-vector store, mutated ------------------------------------------
python3 "$REPO/.softhouse/handoff/T61-mutations.py" M7 > "$OUT/red-M7-43-vector-store.txt" 2>&1 \
    || fail "arm 2 driver failed"

# --- arm 3: the 43-vector store, unmutated ----------------------------------------
bash "$REPO/.softhouse/conformance.sh" > "$OUT/green-conformance-43-vectors.txt" 2>&1
rc3=$?

echo "=== arm 1 — 42-vector store + M7 (the premise) ==="
LC_ALL=C grep -a 'MONEY-QUANTIZATION-HALF-EVEN' "$OUT/premise-refuted-42-vector-store.txt" | tail -1
echo "=== arm 2 — 43-vector store + M7 (RED) ==="
LC_ALL=C grep -a 'MONEY-QUANTIZATION-HALF-EVEN' "$OUT/red-M7-43-vector-store.txt" | tail -1
echo "=== arm 3 — 43-vector store, unmutated (GREEN) ==="
LC_ALL=C grep -aE 'VERDICT|parity vectors' "$OUT/green-conformance-43-vectors.txt"
echo "conformance exit=$rc3"

# --- the assertions. A proof that prints numbers and compares none is the defect ---
a1=$(LC_ALL=C grep -ac 'T61-HE-A, T61-HE-B, T61-HE-C |' "$OUT/premise-refuted-42-vector-store.txt")
[ "$a1" = 1 ] || fail "arm 1: expected the killed-by list to be exactly T61-HE-A, T61-HE-B, T61-HE-C"
a1p=$(LC_ALL=C grep -ac '| 39 | 3 |' "$OUT/premise-refuted-42-vector-store.txt")
[ "$a1p" = 1 ] || fail "arm 1: expected parity PASS 39 FAIL 3 on the 42-vector store"

a2=$(LC_ALL=C grep -ac 'T149-PATHB-TIE' "$OUT/red-M7-43-vector-store.txt")
[ "$a2" -ge 1 ] || fail "arm 2: T149-PATHB-TIE did NOT go red under M7 — the vector does not discriminate"
a2p=$(LC_ALL=C grep -ac '| 39 | 4 |' "$OUT/red-M7-43-vector-store.txt")
[ "$a2p" = 1 ] || fail "arm 2: expected parity PASS 39 FAIL 4 on the 43-vector store"

[ "$rc3" = 0 ] || fail "arm 3: conformance exit $rc3, expected 0"
a3=$(LC_ALL=C grep -ac 'parity vectors          PASS 43   FAIL 0' "$OUT/green-conformance-43-vectors.txt")
[ "$a3" = 1 ] || fail "arm 3: expected parity PASS 43 FAIL 0"

echo
echo "PROOF HOLDS: RED under HALF_EVEN, GREEN under HALF_UP, and the 42-vector store was"
echo "             ALREADY red under HALF_EVEN — so this vector deepens that coverage, it"
echo "             does not create it."
