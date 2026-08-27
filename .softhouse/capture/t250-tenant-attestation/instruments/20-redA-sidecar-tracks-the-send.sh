#!/usr/bin/env bash
# T250 RED-DRIVE A -- does the sidecar TRACK what was actually sent?
#
# PROPERTY UNDER TEST: change the tenant, and the committed sidecar changes with
# it.  The T245 F-2 defect is precisely that this is FALSE today for
# `cap.sh` / `cap8.sh` / `cap9.sh` / `cap10.sh`.
#
# BOTH ARMS ARE RUN AGAINST THE LIVE REFERENCE ORACLE.  Nothing here is
# synthesised: every sidecar in this transcript is derived from a curl trace of a
# real exchange with https://localhost:8443.
#
# ARM 1 (RED)   -- the LEGACY shape, reproduced verbatim from cap10.sh's writer
#                  block into a scratch copy.  T114: the real cap*.sh files are
#                  NOT touched, NOT run, and NOT edited; this is a copy of their
#                  writer, which is what is under test.
#                  EXPECTED: tenant changes gerege -> default, sidecar does NOT.
# ARM 2 (GREEN) -- `.softhouse/capture/lib/oracle_send.sh`.
#                  EXPECTED: tenant changes gerege -> default, sidecar DOES.
#
# The test FAILS (exit 1) if arm 1 tracks the tenant (then there was no defect
# to fix and this whole task is vacuous -- P-22) or if arm 2 does not.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
EV="$HERE/../evidence/redA"
# --- T304 FAIL-CLOSED GUARD (FU-T284-3) ---------------------------------------------
# This instrument rebuilds its evidence directory from scratch on every run, and that
# directory holds 14 TRACKED files. T114 binds: committed evidence is named and
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
rm -rf "$EV"
mkdir -p "$EV/legacy" "$EV/derived"

B='https://localhost:8443/fineract-provider/api/v1'
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
RPATH='/offices'

# --- ARM 1: the legacy writer, reproduced ---------------------------------
# This is cap10.sh's `{ echo ... } > "$HTTP"` block, transcribed.  The tenant
# line is a hard-coded literal; the send uses "$T".
legacy_capture() {
  local name=$1 tenant=$2 outdir=$3
  local T="Fineract-Platform-TenantId: $tenant"
  local code
  code=$(curl -sk -X GET "$B$RPATH" -H "$A" -H "$T" \
              -o "$outdir/$name.json" -w '%{http_code}')
  {
    echo "GET $RPATH"
    echo "Fineract-Platform-TenantId: gerege"
    echo "Authorization: Basic <mifos:password>"
    echo "body: <none>"
    echo "captured-at-utc: <fixed-for-diff>"
  } > "$outdir/$name.http"
  echo "$code" > "$outdir/$name.status"
}

# --- ARM 2: the derived writer --------------------------------------------
# shellcheck source=/dev/null
. "$LIB/oracle_send.sh"

derived_capture() {
  local name=$1 tenant=$2 outdir=$3
  OS_BASE="$B"
  OS_OUTDIR="$outdir"
  OS_LIB_DIR="$LIB"
  OS_HEADERS="$A
Fineract-Platform-TenantId: $tenant"
  export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
  oracle_send "$name" GET "$RPATH"
}

echo "== ARM 1 (RED expected): legacy literal writer =="
legacy_capture t-gerege gerege "$EV/legacy"
legacy_capture t-default default "$EV/legacy"
echo "--- legacy sidecar, tenant SENT = gerege ---"
cat "$EV/legacy/t-gerege.http"
echo "--- legacy sidecar, tenant SENT = default ---"
cat "$EV/legacy/t-default.http"

legacy_differs=0
if ! cmp -s "$EV/legacy/t-gerege.http" "$EV/legacy/t-default.http"; then
  legacy_differs=1
fi
echo "legacy sidecars differ: $legacy_differs  (0 = the defect, sidecar is blind)"

echo
echo "== ARM 2 (GREEN expected): derived-from-wire writer =="
derived_capture t-gerege gerege "$EV/derived"
derived_capture t-default default "$EV/derived"
echo "--- derived sidecar, tenant SENT = gerege ---"
cat "$EV/derived/t-gerege.http"
echo "--- derived sidecar, tenant SENT = default ---"
cat "$EV/derived/t-default.http"

derived_differs=0
if ! cmp -s "$EV/derived/t-gerege.http" "$EV/derived/t-default.http"; then
  derived_differs=1
fi
echo "derived sidecars differ: $derived_differs  (1 = the sidecar tracks the send)"

echo
echo "== the tenant line each sidecar actually carries =="
python3 - "$EV" <<'PY'
import sys, os, re
ev = sys.argv[1]
pat = re.compile(r'^Fineract-Platform-TenantId:\s*(.*)$', re.M)
for arm in ("legacy", "derived"):
    for sent in ("gerege", "default"):
        p = os.path.join(ev, arm, "t-%s.http" % sent)
        with open(p, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
        m = pat.search(text)
        claimed = m.group(1) if m else "<no tenant line>"
        verdict = "TRUE " if claimed == sent else "FALSE"
        print("  %-7s arm: SENT %-8s  SIDECAR SAYS %-8s  -> %s"
              % (arm, sent, claimed, verdict))
PY

echo
rc=0
if [ "$legacy_differs" -ne 0 ]; then
  echo "UNEXPECTED: the legacy writer tracked the tenant. The premise of T250 does"
  echo "  not hold on this host and the fix would be vacuous (P-22)." >&2
  rc=1
fi
if [ "$derived_differs" -ne 1 ]; then
  echo "FAIL: the derived writer did NOT track the tenant." >&2
  rc=1
fi
if [ "$rc" -eq 0 ]; then
  echo "RED-DRIVE A: PASS"
  echo "  legacy  writer -- tenant changed, sidecar did NOT (RED reproduced)"
  echo "  derived writer -- tenant changed, sidecar DID    (GREEN)"
fi
exit "$rc"
