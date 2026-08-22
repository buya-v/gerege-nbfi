#!/usr/bin/env bash
# T261 RED-DRIVE A -- INDEPENDENT reproduction of the F-2 defect against the LIVE
# reference oracle (Fineract, https://localhost:8443).  This is NOT a re-run of
# T250's 20-redA script (P-76): the legacy writer below is reconstructed from the
# frozen `cap*.sh` source lines I read myself (cap10.sh:113/114/117), and the
# comparison is written here from scratch.
#
# CLAIM UNDER TEST (T250 handoff s.0):
#   send tenant `default`, and the legacy sidecar still says `gerege`.
#
# Engine: bash + curl + python3.  No grep/rg/git grep anywhere (P-75).
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../../.." && pwd)
EV="$ROOT/.softhouse/reviews/t261-tenant-attestation/evidence/redA"
LIB="$ROOT/.softhouse/capture/lib"   # the library under review, in place
BASE="https://localhost:8443/fineract-provider/api/v1"
A='Authorization: Basic bWlmb3M6cGFzc3dvcmQ='
CT='Content-Type: application/json'

mkdir -p "$EV/legacy" "$EV/derived"

# ---------------------------------------------------------------- legacy writer
# Reconstructed verbatim in SHAPE from cap10.sh:110-118 -- the sidecar's tenant
# and content-type lines are LITERALS while $T and $CT carry the sent values.
legacy_capture() {
  ln_name=$1; ln_tenant=$2
  T="Fineract-Platform-TenantId: $ln_tenant"
  code=$(curl -sk -X GET "$BASE/offices" -H "$A" -H "$T" -H "$CT" \
             -o "$EV/legacy/$ln_name.json" -w '%{http_code}')
  {
    echo "GET /offices"
    echo "Fineract-Platform-TenantId: gerege"
    echo "Authorization: Basic <mifos:password>"
    echo "Content-Type: application/json"
    echo "captured-at-utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$EV/legacy/$ln_name.http"
  echo "$code" > "$EV/legacy/$ln_name.status"
  printf '%s' "$code"
}

# --------------------------------------------------------------- derived writer
derived_capture() {
  dn_name=$1; dn_tenant=$2
  OS_BASE="$BASE"
  OS_OUTDIR="$EV/derived"
  OS_LIB_DIR="$LIB"
  OS_HEADERS="$A
Fineract-Platform-TenantId: $dn_tenant
$CT"
  export OS_BASE OS_OUTDIR OS_LIB_DIR OS_HEADERS
  # shellcheck disable=SC1091
  . "$LIB/oracle_send.sh"
  oracle_send "$dn_name" GET /offices >/dev/null
}

# reads the tenant a sidecar CLAIMS, without assuming where in the file it is
sidecar_says() {
  python3 - "$1" <<'PY'
import re, sys
t = open(sys.argv[1], "rb").read().decode("utf-8", "replace")
m = re.search(r"(?im)^Fineract-Platform-TenantId:\s*(\S+)\s*$", t)
print(m.group(1) if m else "<ABSENT>")
PY
}

fail=0
report() {
  w=$1; sent=$2; says=$3
  if [ "$sent" = "$says" ]; then verdict=TRUE; else verdict=FALSE; fi
  printf '  %-8s arm: SENT %-9s SIDECAR SAYS %-9s -> %s\n' "$w" "$sent" "$says" "$verdict"
  echo "$verdict"
}

echo "T261 RED-DRIVE A -- live oracle $BASE"
echo "curl: $(curl --version | head -1)"
echo ""

declare -a results
for ten in gerege default; do
  c=$(legacy_capture "t-$ten" "$ten")
  says=$(sidecar_says "$EV/legacy/t-$ten.http")
  v=$(report legacy "$ten" "$says" | tail -1)
  printf '  %-8s arm: SENT %-9s HTTP %s   SIDECAR SAYS %-9s -> %s\n' legacy "$ten" "$c" "$says" "$v"
  results+=("legacy:$ten:$says:$v")
done

for ten in gerege default; do
  derived_capture "t-$ten" "$ten"
  says=$(sidecar_says "$EV/derived/t-$ten.http")
  if [ "$ten" = "$says" ]; then v=TRUE; else v=FALSE; fi
  printf '  %-8s arm: SENT %-9s HTTP %s   SIDECAR SAYS %-9s -> %s\n' derived "$ten" \
      "$(cat "$EV/derived/t-$ten.status")" "$says" "$v"
  results+=("derived:$ten:$says:$v")
done

echo ""
# P-22: this script must FAIL if the legacy arm tracked the tenant, i.e. if the
# defect could not be reproduced.  A fix certified against a defect that would
# not reproduce certifies nothing.
legacy_default_says=$(sidecar_says "$EV/legacy/t-default.http")
if [ "$legacy_default_says" = "default" ]; then
  echo "REFUSING: the legacy arm TRACKED the tenant -- the F-2 defect did NOT"
  echo "  reproduce on this host, so nothing here may be certified.  (P-22)"
  exit 3
fi
echo "DEFECT REPRODUCED: legacy sidecar says '$legacy_default_says' for a request"
echo "  genuinely sent with Fineract-Platform-TenantId: default."

for ten in gerege default; do
  says=$(sidecar_says "$EV/derived/t-$ten.http")
  if [ "$says" != "$ten" ]; then
    echo "FAIL: derived arm did not track tenant $ten (said '$says')"
    fail=1
  fi
done
[ "$fail" -eq 0 ] && echo "DERIVED WRITER TRACKS THE SEND on both arms."
exit "$fail"
