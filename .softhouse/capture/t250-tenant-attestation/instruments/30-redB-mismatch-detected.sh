#!/usr/bin/env bash
# T250 RED-DRIVE B -- is a MISMATCH between sent and recorded DETECTED?
#
# Red-drive A shows the sidecar tracks the send WHEN THE RIG IS USED CORRECTLY.
# That is not enough: "it works when used correctly" is the same fail-open shape
# T250 exists to remove.  This drive attacks the artefacts AFTER capture and
# asks whether the disagreement is CAUGHT.
#
# Every arm below starts from a REAL exchange with the live reference oracle at
# https://localhost:8443.  Nothing is synthesised; the tampering is applied to
# genuine captured bytes.
#
# ARMS (each states the expected exit status of `wire_attestation.py verify`):
#   0  POSITIVE CONTROL      untouched artefacts                       -> 0 VERIFIED
#   1  sidecar tenant edited to a tenant that was NOT sent             -> 1 MISMATCH
#   2  header record edited, sidecar left alone                        -> 1 MISMATCH
#   3  header record DELETED                                           -> 2 REFUSED
#   4  legacy-shaped sidecar, no derivation provenance at all          -> 2 REFUSED
#   5  body artefact swapped under a sidecar that hashed the original  -> 1 MISMATCH
#   6  Content-Length sent disagrees with the committed body artefact  -> 1 MISMATCH
#   7  HONEST NEGATIVE: sidecar AND record AND digest all forged
#      consistently                                                    -> 0 (NOT caught)
#
# Arm 7 is included deliberately.  This module does not claim unforgeability and
# must not appear to: a consistent forgery of the whole artefact set is caught by
# the outer `MANIFEST.sha256` and the vectors' `capture_sha256` pins, not here.
# An evidence file that only shows its wins is the decoration this task removes.
#
# A calibration that never fails is not a calibration (P-72): arm 0 is the known
# POSITIVE and arms 1-6 are known NEGATIVES; if arm 0 fails or any of 1-6 passes,
# this script exits non-zero.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
EV="$HERE/../evidence/redB"
# --- T304 FAIL-CLOSED GUARD (FU-T284-3) ---------------------------------------------
# This instrument rebuilds its evidence directory from scratch on every run, and that
# directory holds 70 TRACKED files. T114 binds: committed evidence is named and
# SUPERSEDED by a scratch copy, never rewritten in place. Documenting the hazard in a
# handoff enforces nothing (P-45: "A test-only guard is not a guard ... verify the path
# that actually executes ... calls it, not merely that a test does") -- so the refusal
# is here, on the executing path, ahead of the destruction.
#   run for a NEW answer:  T304_EVIDENCE_SCRATCH="$(mktemp -d)" bash "$0"
#   read the OLD answer :  do not run it; the corpus is at the path above.
. "$(git rev-parse --show-toplevel)/.softhouse/capture/t304-evidence-destruction/instruments/refuse-if-tracked.sh"
EV="$(t304_evidence_root "$EV")" || exit 2
# --- end T304 guard -----------------------------------------------------------------
LIB=$(cd "$HERE/../../lib" && pwd)
WA="$LIB/wire_attestation.py"
rm -rf "$EV"
mkdir -p "$EV/out" "$EV/req"

B='https://localhost:8443/fineract-provider/api/v1'
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='

# shellcheck source=/dev/null
. "$LIB/oracle_send.sh"

# A body-bearing capture, so the body cross-checks are exercised too.  The body
# is deliberately invalid and carries NO monetary value: the oracle refuses it at
# validation, nothing is created, and the refusal is the observation.
printf '{"invalid":"deliberately-not-a-valid-office"}\n' > "$EV/req/bad-office.json"

OS_BASE="$B"
OS_OUTDIR="$EV/out"
OS_LIB_DIR="$LIB"
OS_HEADERS="$A
Fineract-Platform-TenantId: default
Content-Type: application/json"
export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS

echo "== capturing a REAL exchange from the live oracle (tenant SENT = default) =="
oracle_send probe POST /offices "$EV/req/bad-office.json"
echo "oracle status: $(cat "$EV/out/probe.status")"
echo
echo "--- the sidecar as derived ---"
cat "$EV/out/probe.http"
echo

pass=0
fail=0
run_arm() {                       # run_arm N EXPECTED_RC DESCRIPTION dir
  local n=$1 expected=$2 desc=$3 dir=$4
  local rc=0
  set +e
  python3 "$WA" verify --sidecar "$dir/probe.http" --headers "$dir/probe.reqhdr" \
          --req "$dir/probe.req" > "$dir/verify.out" 2> "$dir/verify.err"
  rc=$?
  set -e
  local ok="FAIL"
  if [ "$rc" -eq "$expected" ]; then ok="ok"; pass=$((pass + 1)); else fail=$((fail + 1)); fi
  printf 'ARM %s  expected rc=%s  got rc=%s  [%s]  %s\n' "$n" "$expected" "$rc" "$ok" "$desc"
  sed 's/^/        /' "$dir/verify.err" | head -6
  sed 's/^/        /' "$dir/verify.out" | head -3
}

mkarm() {                          # mkarm NAME -> fresh copy of the real capture
  local d="$EV/arm-$1"
  rm -rf "$d"; mkdir -p "$d"
  cp "$EV/out/probe.http" "$EV/out/probe.reqhdr" "$EV/out/probe.req" \
     "$EV/out/probe.req.sha256" "$EV/out/probe.json" "$EV/out/probe.status" "$d/"
  echo "$d"
}

echo "== arms =="

d=$(mkarm 0)
run_arm 0 0 "POSITIVE CONTROL: nothing touched" "$d"

# ARM 1 -- the exact attack T245 F-2 warns about: the sidecar claims a tenant
# that was never sent.  This is what a hand-edited or retro-stamped sidecar
# would look like.
d=$(mkarm 1)
python3 - "$d/probe.http" <<'PY'
import sys
p = sys.argv[1]
with open(p, "rb") as fh:
    t = fh.read().decode("utf-8")
t = t.replace("Fineract-Platform-TenantId: default",
              "Fineract-Platform-TenantId: gerege")
with open(p, "w") as fh:
    fh.write(t)
PY
run_arm 1 1 "sidecar edited to claim tenant 'gerege' when 'default' was sent" "$d"

# ARM 2 -- the record tampered instead of the sidecar.
d=$(mkarm 2)
python3 - "$d/probe.reqhdr" <<'PY'
import sys
p = sys.argv[1]
with open(p, "rb") as fh:
    t = fh.read().decode("utf-8")
t = t.replace("Fineract-Platform-TenantId: default",
              "Fineract-Platform-TenantId: gerege")
with open(p, "w") as fh:
    fh.write(t)
PY
run_arm 2 1 "header record edited, sidecar untouched" "$d"

# ARM 3 -- the record is gone; verification must REFUSE, not shrug.
d=$(mkarm 3)
rm -f "$d/probe.reqhdr"
run_arm 3 2 "header record DELETED -- must refuse, not pass" "$d"

# ARM 4 -- a legacy cap10.sh-shaped sidecar.  It may well be true; nothing here
# can tell.  Default-deny.
d=$(mkarm 4)
cat > "$d/probe.http" <<'EOF'
POST /offices
Fineract-Platform-TenantId: gerege
Authorization: Basic <mifos:password>
Content-Type: application/json
body-file: req/bad-office.json
captured-at-utc: 2026-08-22T00:00:00Z
EOF
run_arm 4 2 "legacy literal sidecar, no derivation provenance" "$d"

# ARM 5 -- the body artefact swapped after the fact.
d=$(mkarm 5)
printf '{"invalid":"a-DIFFERENT-body-substituted-later"}\n' > "$d/probe.req"
run_arm 5 1 "body artefact swapped under a sidecar that hashed the original" "$d"

# ARM 6 -- Content-Length as sent no longer matches the committed body.  This is
# the shape where the body file changed BETWEEN snapshot and send.
d=$(mkarm 6)
python3 - "$d/probe.reqhdr" "$d/probe.http" <<'PY'
import sys, hashlib, re
hdr, side = sys.argv[1], sys.argv[2]
with open(hdr, "rb") as fh:
    t = fh.read().decode("utf-8")
t = re.sub(r"Content-Length: \d+", "Content-Length: 9999", t)
with open(hdr, "w") as fh:
    fh.write(t)
# restamp the sidecar's digest so ONLY the length disagreement remains under test
h = hashlib.sha256(open(hdr, "rb").read()).hexdigest()
with open(side, "rb") as fh:
    s = fh.read().decode("utf-8")
s = re.sub(r"request-headers-sha256: [0-9a-f]+", "request-headers-sha256: " + h, s)
s = s.replace("Content-Length: ", "Content-Length: ")
s = re.sub(r"^Content-Length: \d+$", "Content-Length: 9999", s, flags=re.M)
with open(side, "w") as fh:
    fh.write(s)
PY
run_arm 6 1 "Content-Length sent != committed body artefact byte count" "$d"

# ARM 7 -- the honest negative.  Forge everything, consistently.
d=$(mkarm 7)
python3 - "$d/probe.reqhdr" "$d/probe.http" <<'PY'
import sys, hashlib, re
hdr, side = sys.argv[1], sys.argv[2]
for p in (hdr, side):
    with open(p, "rb") as fh:
        t = fh.read().decode("utf-8")
    t = t.replace("Fineract-Platform-TenantId: default",
                  "Fineract-Platform-TenantId: gerege")
    with open(p, "w") as fh:
        fh.write(t)
h = hashlib.sha256(open(hdr, "rb").read()).hexdigest()
with open(side, "rb") as fh:
    s = fh.read().decode("utf-8")
s = re.sub(r"request-headers-sha256: [0-9a-f]+", "request-headers-sha256: " + h, s)
with open(side, "w") as fh:
    fh.write(s)
PY
run_arm 7 0 "HONEST NEGATIVE: whole artefact set forged consistently -- NOT caught here" "$d"

echo
echo "arms as expected: $pass    arms NOT as expected: $fail"
if [ "$fail" -ne 0 ]; then
  echo "RED-DRIVE B: FAIL" >&2
  exit 1
fi
cat <<'EOF'
RED-DRIVE B: PASS
  A disagreement between what was SENT and what is RECORDED is DETECTED in every
  single-artefact tampering shape tested (arms 1, 2, 5, 6), and a missing or
  underived record is REFUSED rather than passed (arms 3, 4).
  WHAT IS NOT CLAIMED (arm 7): a consistent forgery of the entire artefact set
  is NOT caught by this module. It is caught, if at all, by MANIFEST.sha256 and
  the vectors' capture_sha256 pins. Stated, not hidden.
EOF
