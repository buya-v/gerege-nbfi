#!/usr/bin/env bash
#
# T46 negative leg N9 -- prove the M-5 identity check is FAILABLE.
#
# `analysis/t46_m5_identity.py` is what licenses publishing the re-emission
# `out/t46-mathcontext3.json`.  An assertion that has never failed has not been tested
# (`.softhouse/patterns.md`), so this leg runs it against a re-emission in which exactly ONE
# money cell has been perturbed by one minor unit, and requires it to exit 1 naming that cell.
#
# It also re-runs the check on the real pair, which must still exit 0 -- otherwise the leg is
# not discriminating, it is just broken.
#
# No container, no oracle contact, no committed observation altered: the perturbed payload is a
# throwaway written to out/negative/ and labelled corrupt in its own `task` field.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SET="$(cd "$HERE/.." && pwd)"
CHECK="$SET/analysis/t46_m5_identity.py"
COMMITTED="$SET/out/t42-mathcontext.json"
REEMIT="$SET/out/t46-mathcontext3.json"
BAD="$SET/out/negative/t46-perturbed-reemission.json"
TRANSCRIPT="$SET/out/negative/t46-n9-identity-check-failable.txt"

mkdir -p "$SET/out/negative"
verdict=0

{
  echo "== T46 negative leg N9 -- the M-5 identity check, exercised negatively"
  echo "== captured: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo

  [ -f "$REEMIT" ] || { echo "FAIL: $REEMIT does not exist; run src/run-mathcontext3.sh first."; exit 1; }

  echo "---- perturbing exactly one money cell by one minor unit ----"
  python3 - "$REEMIT" "$BAD" <<'PYPERTURB'
import json, sys
from decimal import Decimal
src, dst = sys.argv[1], sys.argv[2]
doc = json.load(open(src), parse_float=Decimal)   # no float() anywhere
doc["task"] = "T46-NEGATIVE-N9 (DELIBERATELY PERTURBED -- NOT AN OBSERVATION)"
hit = None
for c in doc["captures"]:
    o = c.get("observed")
    if not o:
        continue
    for p in o.get("periods", []):
        if p.get("periodNumber") == 1 and "interest" in p:
            old = p["interest"]
            new = str(Decimal(old) + Decimal("0.01"))   # exact decimal, one minor unit
            p["interest"] = new
            hit = (c["id"], old, new)
            break
    if hit:
        break
if not hit:
    raise SystemExit("could not find a cell to perturb -- the leg would be vacuous")
json.dump(doc, open(dst, "w"), indent=2, default=str)
print("  perturbed %s period[1].interest: %s -> %s" % hit)
PYPERTURB
  echo

  echo "---- NEGATIVE leg: the check against the perturbed re-emission (must exit 1) ----"
  set +e
  python3 "$CHECK" "$COMMITTED" "$BAD" | tail -20
  rc_neg="${PIPESTATUS[0]}"
  set -e
  echo "-- exit: $rc_neg --"
  if [ "$rc_neg" -eq 0 ]; then
    echo "N9 FAIL: the identity check PASSED a payload with a moved money cell."
    verdict=1
  else
    echo "N9 OK: the identity check FAILED the perturbed payload."
  fi
  echo

  echo "---- CONTROL leg: the check against the real re-emission (must exit 0) ----"
  set +e
  python3 "$CHECK" "$COMMITTED" "$REEMIT" | tail -8
  rc_pos="${PIPESTATUS[0]}"
  set -e
  echo "-- exit: $rc_pos --"
  if [ "$rc_pos" -ne 0 ]; then
    echo "N9 FAIL: the identity check also fails the real pair -- it is not discriminating."
    verdict=1
  fi
  echo
  echo "verdict: $([ "$verdict" -eq 0 ] && echo PASS || echo FAIL)"
} 2>&1 | tee "$TRANSCRIPT"

exit "$verdict"
