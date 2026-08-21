#!/bin/bash
# T125 — drive the effective-rounding-mode canary RED against a JVM that is genuinely
# NOT running HALF_UP, and record whether the attestation completes anyway.
#
# THE JVM IS REAL AND THE MODE IS REAL.  The shared reference-oracle container serves TWO
# tenants from ONE process: `gerege` at HALF_UP (ratified) and `default` at HALF_EVEN
# (Fineract's stock default).  Both are logged by MoneyHelper at startup and both are
# observable behaviourally on the exact half-cent tie:
#     gerege  -> period-1 interest 20925.05   (HALF_UP)
#     default -> period-1 interest 20925.04   (HALF_EVEN)
# So no container is restarted, rebuilt, re-seeded or reconfigured to run this: the
# HALF_EVEN JVM was already there, addressed by tenant header.
#
# WHAT IS SIMULATED, STATED PLAINLY: exactly one thing — the OUTER precondition gate is
# disabled, because preconditions.sh is today the ONLY thing that refuses a wrong-mode
# tenant, and this script's whole question is what the INNER canary block does when it is
# reached.  Two one-line substitutions are applied to a scratch copy of attest.py and the
# resulting diff is printed and archived so a reviewer can see there is nothing else:
#   (1) `if pre.returncode != 0:` -> `if False:`        (the labelled bypass)
#   (2) canary request calc-pmode2-gerege.json -> calc-pmode2-default.json
#       (productId 11 exists only in `gerege`; the default tenant's twin of the SAME exact
#        tie is productId 10, so the canary actually observes the mode instead of 404ing.
#        Both files are committed; neither is edited.)
# The canary verdict block itself is UNTOUCHED, and every capture, every DB read and the
# canary POST are real requests to the real oracle.
#
# Usage: bash drive-canary-red.sh <out-dir-name-ending-in--default>
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
T36="$HERE/../t36"
OUTNAME=${1:?usage: drive-canary-red.sh <out-dir-name ending in -default>}
OUTDIR="$HERE/$OUTNAME"
SCRATCH="$T36/.t125-scratch-attest.py"

sed -e "s|^if pre.returncode != 0:|if False:  # T125 RED DEMO: OUTER precondition gate DISABLED|" \
    -e "s|'calc-pmode2-gerege.json'|'calc-pmode2-default.json'|" \
    "$T36/attest.py" > "$SCRATCH"

mkdir -p "$OUTDIR"
echo "== the ONLY changes made to attest.py for this run =="
diff "$T36/attest.py" "$SCRATCH" | tee "$OUTDIR/scratch.diff"
nchanged=$(diff "$T36/attest.py" "$SCRATCH" | grep -c '^[<>]')
echo "changed lines: $nchanged (expect 4 = 2 substitutions x <old + >new)"

echo
echo "== running: ATTEST_OUT=$OUTNAME python3 attest.py default pathb =="
ATTEST_OUT="$OUTDIR" ATTEST_TASK=T125-RED-DEMO ATTEST_BRANCH=softhouse/T125-attest-canary-gates \
  python3 "$SCRATCH" default pathb > "$OUTDIR/stdout.txt" 2> "$OUTDIR/stderr.txt"
rc=$?
rm -f "$SCRATCH"

echo "--- stdout ---"; cat "$OUTDIR/stdout.txt"
echo "--- stderr ---"; cat "$OUTDIR/stderr.txt"
echo "--- EXIT CODE: $rc ---"
if [ -f "$OUTDIR/attestation.json" ]; then
  echo "--- attestation.json WAS WRITTEN.  Its own record of the mode: ---"
  python3 - "$OUTDIR/attestation.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
c = d['effective_mode_canary']; e = d['effective_math_context']
print('  tenant                              :', d['tenant']['identifier'])
print('  JVM init logline (tail)             :', (d['tenant']['rounding_mode_in_force_logline'] or '')[-42:])
print('  rounding_mode_in_force              :', d['tenant']['rounding_mode_in_force'])
print('  effective MathContext               :', e['notation'])
print('  matches_ratified_production_setting :', e['matches_ratified_production_setting'])
print('  canary http_status                  :', c['http_status'])
print('  canary observed_period1_interest    :', c['observed_period1_interest'])
print('  canary VERDICT                      :', c['verdict'])
print('  captures                            :', len(d['captures']),
      'all HTTP', sorted({x['http_status'] for x in d['captures']}))
PY
else
  echo "--- attestation.json was NOT written ---"
fi
echo "T125 RED DEMO exit code was $rc"
exit $rc
