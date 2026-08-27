#!/bin/bash
# A2-10 adjudication of A2-5's refusal to restore `rm -f "$OUT"`.
# Build the COUNTERFACTUAL the brief prescribed: pre-fix cap.sh + reachable handler
# + the `rm -f "$OUT"` retained. Then ask the only question that matters:
#   does a STALE ARTEFACT UNDER A FRESH captured-at-utc still land under out/ ?
set -u
STALE_TS="2000-01-01T00:00:00Z"
STALE_BODY='{"stale":"BODY FROM AN EARLIER FIRE - MUST NOT BE RE-DATED"}'

# --- build the counterfactual: pre-fix bytes, handler made reachable, rm -f kept ----
sed -e 's/^set -e$/set -e/' \
    -e "s/^              -d @\"\$DIR\/\$BODY\" -o \"\$OUT\" -w '%{http_code}')$/              -d @\"\$DIR\/\$BODY\" -o \"\$OUT\" -w '%{http_code}') || rc=\$?/" \
    -e "s/^  code=\$(curl -sk -X \"\$METHOD\" \"\$B\$RPATH\" -H \"\$A\" -H \"\$T\" -o \"\$OUT\" -w '%{http_code}')$/  code=\$(curl -sk -X \"\$METHOD\" \"\$B\$RPATH\" -H \"\$A\" -H \"\$T\" -o \"\$OUT\" -w '%{http_code}') || rc=\$?/" \
    -e 's/^NAME=\$1; METHOD=\$2; RPATH=\$3; BODY=\$4$/NAME=${1-}; METHOD=${2-}; RPATH=${3-}; BODY=${4-}\nrc=0/' \
    /tmp/poison/cap-prefix.sh > /tmp/poison/cap-counterfactual.sh
chmod +x /tmp/poison/cap-counterfactual.sh
echo "--- counterfactual: the brief's fix (reachable handler + rm -f retained) ---"
grep -n 'rc=\$?\|rc=0\|rm -f\|TRANSPORT' /tmp/poison/cap-counterfactual.sh

seed() {
  d=$(mktemp -d /tmp/poison/cf.XXXXXX)
  mkdir -p "$d/out" "$d/req"
  cp "$1" "$d/cap.sh"; chmod +x "$d/cap.sh"
  {
    echo "B=https://127.0.0.1:1/api/v1"
    echo "A='Authorization: Basic x'"
    echo "T='Fineract-Platform-TenantId: gerege'"
    echo "CT='Content-Type: application/json'"
    echo "export B A T CT"
  } > "$d/env.sh"
  printf '%s' "$STALE_BODY" > "$d/out/POISON.json"
  printf '200\n' > "$d/out/POISON.status"
  {
    echo "POST /glaccounts"; echo "Fineract-Platform-TenantId: gerege"
    echo "Authorization: Basic <mifos:password>"; echo "captured-at-utc: $STALE_TS"
  } > "$d/out/POISON.http"
  printf '{"x":1}' > "$d/req/b.json"
  echo "$d"
}

report() {
  echo "  exit=$2"
  echo "  out/ now contains: $(ls "$1/out" | tr '\n' ' ')"
  if [ -f "$1/out/POISON.http" ]; then
    echo "  out/POISON.http captured-at-utc: $(sed -n 's/^captured-at-utc: //p' "$1/out/POISON.http")"
  else
    echo "  out/POISON.http: ABSENT"
  fi
  if [ -f "$1/out/POISON.json" ]; then
    echo "  out/POISON.json: $(cat "$1/out/POISON.json")"
  else
    echo "  out/POISON.json: *** DELETED - EARLIER FIRE'S EVIDENCE DESTROYED ***"
  fi
  echo "  out/POISON.status: $(cat "$1/out/POISON.status" 2>/dev/null || echo ABSENT)"
}

echo
echo "=== COUNTERFACTUAL (the brief's prescribed fix), seeded with an earlier fire ==="
d=$(seed /tmp/poison/cap-counterfactual.sh)
/bin/sh "$d/cap.sh" POISON POST /glaccounts req/b.json; ec=$?
report "$d" "$ec"; rm -rf "$d"

echo
echo "=== COUNTERFACTUAL, clean slate ==="
d=$(seed /tmp/poison/cap-counterfactual.sh); rm -f "$d"/out/*
/bin/sh "$d/cap.sh" POISON POST /glaccounts req/b.json; ec=$?
report "$d" "$ec"; rm -rf "$d"

echo
echo "=== A2-5's SHIPPED FIX, same seeded sandbox ==="
d=$(seed /tmp/poison/cap-postfix.sh)
/bin/sh "$d/cap.sh" POISON POST /glaccounts req/b.json; ec=$?
report "$d" "$ec"; rm -rf "$d"
