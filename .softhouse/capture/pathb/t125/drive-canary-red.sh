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
# reached.  Two one-line substitutions are ATTEMPTED against a scratch copy of attest.py and
# the resulting diff is printed, archived AND ASSERTED (T147) so a reviewer can see there is
# nothing else:
#   (1) `if pre.returncode != 0:` -> `if False:`        (the labelled bypass)
#   (2) canary request calc-pmode2-gerege.json -> calc-pmode2-default.json
#       (productId 11 exists only in `gerege`; the default tenant's twin of the SAME exact
#        tie is productId 10, so the canary actually observes the mode instead of 404ing.
#        Both files are committed; neither is edited.)
#       Against post-T125 bytes (2) MATCHES NOTHING and is a no-op: attest.py now resolves the
#       canary by tenant through attest_gate.canary_request_for(), so `default` already gets
#       calc-pmode2-default.json without any edit.  It is kept so a re-introduced literal
#       would still be switched, and the assertion below DERIVES the expected diff size from
#       whether it matched instead of hard-coding "4" the way this script used to.
#       [Confounder ruled out by T136: `m_product_loan` 10@fineract_default and
#        11@fineract_gerege agree on 89 of 89 columns, differing only in `id` — so the
#        20925.05 / 20925.04 split observed below is the ROUNDING MODE and nothing else.]
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

# T147 (P-35), closing T136's F-2.  This line used to read
#     echo "changed lines: $nchanged (expect 4 = 2 substitutions x <old + >new)"
# with NOTHING comparing $nchanged to 4 — and on today's attest.py it printed
# "changed lines: 2 (expect 4 ...)", the script emitting its own contradiction and carrying
# on (`capture/pathb/t147/red-pre-fix/f3-drive-canary-red-prefix.txt`).  A value computed,
# printed against a prose expectation and compared to nothing is exactly the shape T125
# exists to close, and it was in T125's own driver.
#
# The honesty of this whole RED demo rests on that diff being the substitutions it claims and
# nothing else, so the count is now DERIVED from what each -e clause could actually match and
# ASSERTED.  Substitution (1) — the labelled bypass — MUST apply, or the demo is not testing
# what it says.  Substitution (2) is a NO-OP against post-T125 bytes, because attest.py now
# chooses the canary BY TENANT from attest_gate.PINNED_CANARY_BY_TENANT rather than carrying
# the literal; it is retained so that a re-introduced literal is still switched, and whether
# it matched is measured rather than assumed.  LC_ALL=C grep -a per P-33.
# NOTE the quotes in the needle: it must be the EXACT string the -e clause substitutes, not
# the bare filename.  T147's first attempt counted the bare filename and got 1 — a hit on a
# prose comment that sed cannot match — which would have made this assertion demand a diff
# size that can never occur.  A guard derived from the wrong operand is still a wrong guard.
n_literal=$(LC_ALL=C grep -ac "'calc-pmode2-gerege.json'" "$T36/attest.py" || true)
n_bypass=$(LC_ALL=C grep -ac 'T125 RED DEMO: OUTER precondition gate DISABLED' "$SCRATCH" || true)
expect_changed=$(( 2 + 2 * n_literal ))
nchanged=$(diff "$T36/attest.py" "$SCRATCH" | LC_ALL=C grep -ac '^[<>]' || true)
if [ "$n_bypass" -ne 1 ]; then
  echo "FAIL: the labelled precondition bypass did not apply to the scratch copy" \
       "(found $n_bypass occurrences, expected 1). This run would not be testing the INNER" \
       "canary gate at all." >&2
  rm -f "$SCRATCH"; exit 1
fi
if [ "$nchanged" -ne "$expect_changed" ]; then
  echo "FAIL: the scratch copy differs from attest.py on $nchanged lines, but the" \
       "substitutions this script makes account for exactly $expect_changed" \
       "(bypass 2 + canary-literal $(( 2 * n_literal ))). Refusing to present an" \
       "unexplained edit as 'the ONLY changes made'." >&2
  rm -f "$SCRATCH"; exit 1
fi
echo "ASSERTED: changed lines = $nchanged, and that is exactly what these substitutions" \
     "account for (labelled bypass 2 + canary literal $(( 2 * n_literal )) —" \
     "the literal occurs $n_literal times in attest.py)."

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
