#!/usr/bin/env bash
#
# T50 -- PROVE THE ADMISSIBILITY CHECKERS ARE FAILABLE.
#
# `patterns.md`: "A precondition script is only worth what its negative run proves.  An assertion
# suite that has never failed has not been tested."  So this corrupts a committed payload one axis
# at a time and requires the checker to REJECT each corruption while ACCEPTING the clean original.
#
# Contacts no oracle, no container, no server, no database.  Writes only into out/negative/.
# Every path is derived from this script's own location.
set -uo pipefail

CAPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NEG="$CAPDIR/out/negative"
mkdir -p "$NEG"
TMP="$NEG/.t50-tmp.json"
FAILED=0

expect() {   # expect <wanted-exit> <label> <checker> <payload>
  local want="$1" label="$2" checker="$3" payload="$4"
  python3 "$CAPDIR/analysis/$checker" "$payload" > "$NEG/t50-neg-$label.txt" 2>&1
  local rc=$?
  if [ "$rc" = "$want" ]; then
    echo "  ok  $label -> exit $rc (wanted $want)"
  else
    echo "  FAIL $label -> exit $rc (wanted $want); transcript $NEG/t50-neg-$label.txt"
    FAILED=1
  fi
}

corrupt() {  # corrupt <src> <dst> <python-snippet operating on `d`>
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
src, dst, snippet = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src))
exec(snippet)
json.dump(d, open(dst, "w"), indent=1)
PY
}

echo "== T50 negative tests: is the admissibility checker failable? =="

T1="$CAPDIR/out/t50-tier1.json"
T2="$CAPDIR/out/t50-tier2.json"
[ -f "$T1" ] || { echo "BREACH: $T1 missing -- run run-t50-tier1.sh first"; exit 1; }
[ -f "$T2" ] || { echo "BREACH: $T2 missing -- run run-t50-tier2.sh first"; exit 1; }

# ---- the clean payloads must be ACCEPTED --------------------------------------------------
expect 0 "tier1-clean" t50_assert_tier1.py "$T1"
expect 0 "tier2-clean" t50_assert_tier2.py "$T2"

# ---- N1: a VACUOUS absence probe must be rejected -------------------------------------------
# If MoneyHelper had NOT thrown on an uninitialised tenant, every ABSENT case would be meaningless.
corrupt "$T1" "$TMP" 'd["ambientCanary"] = "NO THROW -- ambient read succeeded: precision=19 roundingMode=HALF_UP"'
expect 1 "N1-vacuous-canary" t50_assert_tier1.py "$TMP"

# ---- N2: an attestation that disagrees with the case id must be rejected ---------------------
corrupt "$T1" "$TMP" 'd["cases"][900]["attestation"]["ambientMathContextObject"] = "precision=19 roundingMode=UNNECESSARY"'
expect 1 "N2-attestation-drift" t50_assert_tier1.py "$TMP"

# ---- N3: a threaded MathContext echoed as something other than what the id declares ----------
corrupt "$T1" "$TMP" 'd["cases"][900]["attestation"]["threadedPrecisionObject"] = 12'
expect 1 "N3-threaded-precision-drift" t50_assert_tier1.py "$TMP"

# ---- N4: a moving NULL CONTROL must be rejected -----------------------------------------------
# The control exists to show the grid is not simply always-different.  If it moves, the harness is
# discriminating on something other than the rounding mode and nothing below it can be trusted.
corrupt "$T1" "$TMP" '
for c in d["cases"]:
    if c["value"] == "V3-noTie-scale2" and c["inputs"]["ambientRoundingModeIntent"] == "FLOOR":
        c["observed"] = "0.99"
        break
'
expect 1 "N4-null-control-moves" t50_assert_tier1.py "$TMP"

# ---- N5: a silently dropped case must be rejected ---------------------------------------------
corrupt "$T1" "$TMP" 'del d["cases"][17]'
expect 1 "N5-case-dropped" t50_assert_tier1.py "$TMP"

# ---- N6: an ABSENT case that quietly SUCCEEDED must be rejected --------------------------------
# This is the coverage detector.  If a site declared ambient-ABSENT returns a number instead of
# throwing, the ambient cache was populated behind the probe's back.
corrupt "$T1" "$TMP" '
for c in d["cases"]:
    if c["inputs"]["ambientRoundingModeOrdinal"] is None:
        c["attestation"]["ambientMathContextObject"] = "precision=19 roundingMode=HALF_UP"
        break
'
expect 1 "N6-absent-case-succeeded" t50_assert_tier1.py "$TMP"

# ---- N7: the ordinal proof must be rejected if it disagrees with the JDK ------------------------
corrupt "$T1" "$TMP" 'd["ordinalProof"][4]["moneyHelperRoundingMode"] = "HALF_EVEN"'
expect 1 "N7-ordinal-map-drift" t50_assert_tier1.py "$TMP"

# ---- N8: Tier 2 -- a leg whose null control moves must be rejected -------------------------------
corrupt "$T2" "$TMP" '
for c in d["cases"]:
    if c["value"] == "W5-noTie" and c["leg"].startswith("L1") and c["error"] is None:
        c["observed"] = "9.99"
        break
'
expect 1 "N8-tier2-null-control-moves" t50_assert_tier2.py "$TMP"

# ---- N9: Tier 2 -- a vacuous canary must be rejected ----------------------------------------------
corrupt "$T2" "$TMP" 'd["ambientCanary"] = "NO THROW"'
expect 1 "N9-tier2-vacuous-canary" t50_assert_tier2.py "$TMP"

rm -f "$TMP"
echo
if [ "$FAILED" = "0" ]; then
  echo "== PASS -- the checkers accept both clean payloads and reject all nine corruptions =="
  exit 0
fi
echo "== FAIL -- at least one corruption was NOT rejected; the checkers are not failable =="
exit 1
