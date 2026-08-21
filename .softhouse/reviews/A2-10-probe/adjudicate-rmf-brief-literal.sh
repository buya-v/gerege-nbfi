#!/bin/bash
# A2-10: variant 2 of the brief's prescription - handler made reachable CORRECTLY
# (drop the trailing `rc=$?` that clobbers it) and `rm -f "$OUT"` RETAINED.
# This is the strongest form of "just restore the rm -f" and it is the one to judge.
set -u
STALE_TS="2000-01-01T00:00:00Z"
STALE_BODY='{"stale":"BODY FROM AN EARLIER FIRE - MUST NOT BE RE-DATED"}'

python3 - <<'PY'
src = open('/tmp/poison/cap-prefix.sh').read()
src = src.replace('NAME=$1; METHOD=$2; RPATH=$3; BODY=$4',
                  'NAME=${1-}; METHOD=${2-}; RPATH=${3-}; BODY=${4-}\nrc=0')
src = src.replace("-w '%{http_code}')\nfi", "-w '%{http_code}') || rc=$?\nfi")
src = src.replace("-d @\"$DIR/$BODY\" -o \"$OUT\" -w '%{http_code}')",
                  "-d @\"$DIR/$BODY\" -o \"$OUT\" -w '%{http_code}') || rc=$?")
src = src.replace("\nrc=$?\nif [ $rc -ne 0 ]", "\nif [ $rc -ne 0 ]")
open('/tmp/poison/cap-brief-literal.sh','w').write(src)
PY
chmod +x /tmp/poison/cap-brief-literal.sh
echo "--- brief-literal variant (reachable handler done right + rm -f kept) ---"
sed -n '30,48p' /tmp/poison/cap-brief-literal.sh

d=$(mktemp -d /tmp/poison/bl.XXXXXX); mkdir -p "$d/out" "$d/req"
cp /tmp/poison/cap-brief-literal.sh "$d/cap.sh"; chmod +x "$d/cap.sh"
{ echo "B=https://127.0.0.1:1/api/v1"; echo "A='Authorization: Basic x'"
  echo "T='Fineract-Platform-TenantId: gerege'"; echo "CT='Content-Type: application/json'"
  echo "export B A T CT"; } > "$d/env.sh"
printf '%s' "$STALE_BODY" > "$d/out/POISON.json"
printf '200\n' > "$d/out/POISON.status"
{ echo "POST /glaccounts"; echo "captured-at-utc: $STALE_TS"; } > "$d/out/POISON.http"
printf '{"x":1}' > "$d/req/b.json"

echo
echo "manifest-relevant sha256 of the earlier fire's body BEFORE:"
shasum -a 256 "$d/out/POISON.json"
/bin/sh "$d/cap.sh" POISON POST /glaccounts req/b.json; echo "  exit=$?"
echo "  out/ now contains: $(ls "$d/out" | tr '\n' ' ')"
echo "  out/POISON.http captured-at-utc: $(sed -n 's/^captured-at-utc: //p' "$d/out/POISON.http")"
if [ -f "$d/out/POISON.json" ]; then
  echo "  out/POISON.json survives:"; shasum -a 256 "$d/out/POISON.json"
else
  echo "  out/POISON.json: *** DELETED by rm -f -- an EARLIER FIRE'S EVIDENCE, covered by MANIFEST.sha256 ***"
fi
echo "  out/POISON.status: $(cat "$d/out/POISON.status" 2>/dev/null || echo ABSENT)"
rm -rf "$d"
