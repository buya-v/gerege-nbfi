#!/usr/bin/env bash
# T46 negative leg N7 -- EXERCISE THE VACUITY GUARD.
#
# Audit finding M-8 (T44 section 3): `NEGATIVE-TESTS.md` says leg N4 fires the "the ambient-absence
# probe is VACUOUS" guard.  It does not.  N4 sets `T42_EXPECT_CANARY_THROWS=0`, which makes
# `must_throw` False and fires the OPPOSITE branch of the same `if`
# (`run-mathcontext.sh:161-162`, "negative run: the canary DID throw ...").
# The vacuity guard itself -- `run-mathcontext.sh:157-160`, the branch that makes the whole
# absence experiment falsifiable -- had never been exercised.
#
# This leg exercises it, by the same technique leg N6 already uses for `controls.py`: run the
# SHIPPED assertion code against a deliberately corrupted payload.  It does not re-run the
# capture, does not start a container, and does not touch the running oracle.
#
# "The SHIPPED assertion code" is meant literally: the Python block is EXTRACTED from
# `src/run-mathcontext.sh` at run time (the heredoc between `<<'PY'` and the closing `PY`), so
# what is exercised is the committed guard, not a copy of it that could drift.
#
# The corruption: `ambientCanary` is rewritten from
#     "THREW java.lang.IllegalStateException: Rounding mode is not initialized for tenant: ..."
# to
#     "precision=19 roundingMode=HALF_UP"
# i.e. exactly the failure mode the guard exists to catch -- a MoneyHelper that RETURNED a context
# on an uninitialised tenant instead of throwing, which would make every ABSENCE case meaningless.
# `T42_EXPECT_CANARY_THROWS` is left at its default 1, so `must_throw` is True.
#
# EXPECTED RESULT: exit 1, with `BREACH: the ambient-absence probe is VACUOUS: ...` on stderr.
# The leg FAILS (exit 1 from this script) if the guard does NOT fire.
#
# No money value is created, altered or re-published by this script.  The corrupted payload is
# written to out/negative/ and is labelled corrupt in its own `task` field.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SET="$(cd "$HERE/.." && pwd)"
RUNNER="$SET/src/run-mathcontext.sh"
SRC_PAYLOAD="$SET/out/t42-mathcontext.json"
BAD_PAYLOAD="$SET/out/negative/t46-corrupted-canary-payload.json"
TRANSCRIPT="$SET/out/negative/t46-n7-vacuity-guard.txt"
BLOCK="$(mktemp -t t46-vacuity-block)"
trap 'rm -f "$BLOCK"' EXIT

mkdir -p "$SET/out/negative"

{
  echo "== T46 negative leg N7 -- the vacuity guard, exercised for the first time"
  echo "runner under test : $RUNNER"
  echo "source payload    : $SRC_PAYLOAD"
  echo "corrupted payload : $BAD_PAYLOAD"
  echo

  # 1. extract the SHIPPED assertion block, so the guard exercised is the committed one.
  awk "/<<'PY'/{flag=1;next} /^PY\$/{flag=0} flag" "$RUNNER" > "$BLOCK"
  echo "assertion block extracted from the runner: $(wc -l < "$BLOCK" | tr -d ' ') lines"
  echo "the guard under test, as extracted:"
  grep -n 'VACUOUS' -A 2 -B 2 "$BLOCK" | sed 's/^/    /'
  echo

  # 2. corrupt ONLY the canary field.  Never touch an observed money cell.
  python3 - "$SRC_PAYLOAD" "$BAD_PAYLOAD" <<'PYCORRUPT'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
doc = json.load(open(src))          # no float() anywhere: money leaves are JSON strings and are
                                    # copied through untouched.
before = doc["ambientCanary"]
doc["task"] = "T46-NEGATIVE-N7 (DELIBERATELY CORRUPTED PAYLOAD -- NOT AN OBSERVATION)"
doc["ambientCanary"] = "precision=19 roundingMode=HALF_UP"
doc["t46NegativeLegNote"] = ("ambientCanary rewritten from a THREW string to a returned context, to "
                             "exercise run-mathcontext.sh's VACUOUS guard.  No observed cell altered.")
json.dump(doc, open(dst, "w"), indent=2)
print("  ambientCanary BEFORE: " + before)
print("  ambientCanary AFTER : " + doc["ambientCanary"])
PYCORRUPT
  echo

  # 3. prove no observed cell moved between the two payloads.
  python3 - "$SRC_PAYLOAD" "$BAD_PAYLOAD" <<'PYIDENT'
import json, sys
from decimal import Decimal
a = json.load(open(sys.argv[1]), parse_float=Decimal)
b = json.load(open(sys.argv[2]), parse_float=Decimal)
def cells(node, p=""):
    out = []
    if isinstance(node, dict):
        for k in sorted(node):
            out += cells(node[k], p + "/" + k)
    elif isinstance(node, list):
        for i, x in enumerate(node):
            out += cells(x, p + "[%d]" % i)
    else:
        if isinstance(node, float):
            raise SystemExit("FLOAT LEAF at " + p)
        out.append((p, format(node, "f") if isinstance(node, Decimal) else str(node)))
    return out
ca = {("%s|%s" % (c["id"], k)): v for c in a["captures"] for k, v in cells(c.get("observed"), "")}
cb = {("%s|%s" % (c["id"], k)): v for c in b["captures"] for k, v in cells(c.get("observed"), "")}
moved = [k for k in sorted(set(ca) | set(cb)) if ca.get(k) != cb.get(k)]
print("  observed cells in source payload   : %d" % len(ca))
print("  observed cells in corrupted payload: %d" % len(cb))
print("  observed cells that MOVED          : %d" % len(moved))
if moved:
    for k in moved[:20]:
        print("    " + k)
    raise SystemExit("the corruption touched an observation -- aborting")
PYIDENT
  echo

  # 4. run the SHIPPED guard against the corrupted payload, with must_throw left at 1.
  echo "-- running the shipped assertion block, T42_EXPECT_CANARY_THROWS unset (default 1) --"
  set +e
  EXPECT_CANARY_THROWS="1" python3 "$BLOCK" "$BAD_PAYLOAD"
  rc=$?
  set -e
  echo "-- exit code: $rc --"
  echo

  if [ "$rc" -ne 0 ]; then
    echo "N7 PASS: the vacuity guard FIRED (exit $rc).  The absence experiment is falsifiable."
    verdict=0
  else
    echo "N7 FAIL: the vacuity guard did NOT fire.  Every ABSENCE case in T42 would be unfalsifiable."
    verdict=1
  fi
  echo
  echo "control leg (sanity): the SAME guard against the UNCORRUPTED payload must exit 0"
  set +e
  EXPECT_CANARY_THROWS="1" python3 "$BLOCK" "$SRC_PAYLOAD"
  rc_clean=$?
  set -e
  echo "-- exit code on the uncorrupted payload: $rc_clean --"
  if [ "$rc_clean" -ne 0 ]; then
    echo "N7 FAIL: the guard fires on the CLEAN payload too -- it is not discriminating."
    verdict=1
  fi
  echo
  echo "verdict: $([ "${verdict:-1}" -eq 0 ] && echo PASS || echo FAIL)"
  exit "${verdict:-1}"
} 2>&1 | tee "$TRANSCRIPT"

exit "${PIPESTATUS[0]}"
