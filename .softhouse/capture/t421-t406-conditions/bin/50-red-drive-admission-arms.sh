#!/bin/sh
# T421 / F-T406-2, THE RED HALF (P-45).
#
# Eleven arms passing tells you the branches fire TODAY. It does not tell you the
# arms are LOAD-BEARING -- an arm that would pass with its branch deleted is
# decoration, which is the exact defect this finding is about. So: neuter the
# eleven `add(...)` calls in admit.go's accounting-path block IN A SCRATCH COPY,
# re-run, and require ALL ELEVEN to go RED. The control sub-test must still pass,
# because a neutered admitter admits.
#
# THE SCRATCH COPY IS RESTORED unconditionally by the trap, and the script
# verifies byte-for-byte at the end that admit.go is exactly as it was. T416 is
# concurrently editing admit.go on another branch; nothing here is committed.
set -e
ROOT=$(dirname "$0")/../../../..
ADMIT="$ROOT/nexus/internal/apps/ledger/conformance/admit.go"
BACKUP=$(mktemp)
cp "$ADMIT" "$BACKUP"
BEFORE=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
restore() {
  cp "$BACKUP" "$ADMIT"
  AFTER=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
  if [ "$BEFORE" != "$AFTER" ]; then
    echo "*** RESTORE FAILED: admit.go digest $AFTER != original $BEFORE" >&2
    exit 9
  fi
  echo "admit.go RESTORED byte-for-byte ($AFTER)"
  rm -f "$BACKUP"
}
trap restore EXIT

echo "T421 ADMISSION-ARM RED DRIVE -- $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "admit.go original sha256: $BEFORE"
echo

# Neuter the eleven reasons by mangling their message text, so `add` still runs
# (control flow unchanged) but no arm's needle can match. Line-anchored on the
# distinctive first words of each message.
python3 - "$ADMIT" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
NEEDLES = [
    'carries BOTH gl_account_id',
    'carries NEITHER a gl_account_id',
    'A placeholder code is a positive',
    'request.product_mappings is EMPTY',
    'AND request.legs carry per-leg slot codes',
    'request.product_id is 0',
    'NO leg resolves through any of them',
    'a placeholder code is positive',
    'twice. The oracle',
    'which is NOT in',
    'gl_account_id is %d',
]
n = 0
for s in NEEDLES:
    c = t.count(s)
    if c == 0:
        raise SystemExit("NEEDLE NOT FOUND IN admit.go, so the drive would be vacuous: %r" % s)
    t = t.replace(s, "T421NEUTERED")
    n += c
open(p, "w").write(t)
print("neutered %d reason fragment(s) across %d branches" % (n, len(NEEDLES)))
PY

echo
set +e
go test -C "$ROOT/nexus" -count=1 -run TestSlotAdmissionInputsAreDefaultDeny -v \
  ./internal/apps/ledger/conformance/ > /tmp/t421-red.txt 2>&1
RC=$?
set -e
echo "go test exit: $RC (wanted NON-ZERO)"
grep -E '^ *--- (PASS|FAIL): TestSlotAdmission' /tmp/t421-red.txt || true
echo
FAILS=$(grep -c '^    --- FAIL: TestSlotAdmissionInputsAreDefaultDeny/' /tmp/t421-red.txt || true)
PASSES=$(grep -c '^    --- PASS: TestSlotAdmissionInputsAreDefaultDeny/' /tmp/t421-red.txt || true)
echo "sub-tests FAILED with the branches neutered: $FAILS  (wanted 11 -- the eleven arms)"
echo "sub-tests PASSED with the branches neutered:  $PASSES  (wanted 1  -- the ADMITTED control)"
if [ "$FAILS" -eq 11 ] && [ "$PASSES" -eq 1 ] && [ "$RC" -ne 0 ]; then
  echo "RED DRIVE: every arm is LOAD-BEARING. None of them passes without its branch."
else
  echo "*** RED DRIVE FAILED -- at least one arm passes with its branch neutered, i.e. it is decoration."
  cat /tmp/t421-red.txt
  exit 1
fi
