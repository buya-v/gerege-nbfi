#!/bin/zsh
# T215 -- per-site RED demonstration, SITE 2 (STAGE) ONLY.
#
# This is the exact scenario the T215 driver measurement described:
# mutating ONLY the `git add -A` pathspec (the STAGE site) while leaving
# the `git status --porcelain` DETECT site untouched. T210's original
# probe was proven blind to this (both checks passed, VERDICT PASS, exit
# 0). This demo proves the T215-extended check-lock-exclusion-anchor.sh:
#   (a) still finds BOTH sites by population scan,
#   (b) fails specifically on site 2 (STAGE), naming it,
#   (c) still reports site 1 (DETECT) clean.
#
# Targeting is by CONTENT, not by line number: the mutation is applied to
# "the line containing 'git add -A'", wherever that line currently sits in
# the file -- never to a hardcoded line index.
set -uo pipefail
HERE="${0:A:h}"
LIVE="${HERE}/../../bin/fire-program.sh"
LIVE="${LIVE:A}"
MUTANT="${HERE}/fire-program.sh.RED-site2-scratch-copy.sh"

if [[ ! -f "$LIVE" ]]; then
  print -u2 -- "ERROR: live file not found at $LIVE -- cannot build RED mutant"
  exit 2
fi

NEEDLE=":(top,exclude).softhouse/LOCK'"
REPLACEMENT=":(top,exclude).softhouse/LOCK*'"

# Rebuild the file line by line so only the line matching the STAGE
# command ('git add -A') is mutated; every other line (including the
# DETECT site, which shares the identical NEEDLE substring) passes through
# untouched. This is the driver's ORIGINAL measurement, reproduced by
# construction: it mutated ONLY the `git add -A` pathspec.
/usr/bin/python3 - "$LIVE" "$MUTANT" "$NEEDLE" "$REPLACEMENT" <<'PYEOF'
import sys
live, mutant, needle, replacement = sys.argv[1:5]
with open(live, "r") as f:
    lines = f.readlines()
out = []
mutated_any = False
for line in lines:
    if "git add -A" in line and needle in line:
        line = line.replace(needle, replacement)
        mutated_any = True
    out.append(line)
if not mutated_any:
    sys.stderr.write("ERROR: no STAGE-site line ('git add -A' + needle) found -- cannot construct a faithful site-2 mutant\n")
    sys.exit(2)
with open(mutant, "w") as f:
    f.writelines(out)
PYEOF
PY_RC=$?
if (( PY_RC != 0 )); then
  exit $PY_RC
fi

echo "=== DETECT-site line, confirmed UNCHANGED ==="
LC_ALL=C /usr/bin/grep -n 'git status --porcelain' "$MUTANT"
echo "=== mutated STAGE-site line (scratch copy only, live file untouched) ==="
LC_ALL=C /usr/bin/grep -n 'git add -A' "$MUTANT"
echo

echo "=== running check-lock-exclusion-anchor.sh against the SITE-2 MUTANT (expect FAIL naming site 2/STAGE, and site 1/DETECT still PASS) ==="
zsh "${HERE}/check-lock-exclusion-anchor.sh" "$MUTANT"
RC=$?
echo
echo "exit code: $RC"

# --- prove the arm RAN (P-64): the transcript above must show BOTH sites
# were found and classified, not just a bare nonzero exit. Re-run and
# capture output to check this mechanically rather than eyeballing it.
OUT=$(zsh "${HERE}/check-lock-exclusion-anchor.sh" "$MUTANT" 2>&1)
RAN_SITE1=0; RAN_SITE2=0; SITE2_FAILED=0; SITE1_PASSED=0
[[ "$OUT" == *"classified: DETECT"* ]] && RAN_SITE1=1
[[ "$OUT" == *"classified: STAGE"* ]] && RAN_SITE2=1
# match generically on the STAGE-tagged malformed-pathspec message -- do
# NOT hardcode "site 2": which numeric SITE_INDEX the STAGE line gets is
# an artifact of where it happens to sit in the file today, not a property
# this demo should assume.
[[ "$OUT" == *", STAGE) matched the LOCK-exclusion census but the pathspec argument is not the exact expected token"* ]] && SITE2_FAILED=1
[[ "$OUT" == *"CHECK 1 PASS"* && "$OUT" == *"CHECK 2 PASS"* ]] && SITE1_PASSED=1

rm -f "$MUTANT"

if (( ! RAN_SITE1 )) || (( ! RAN_SITE2 )); then
  echo "PRECONDITION FAILED (P-64): the probe did not visibly classify both sites -- an inconclusive run, not a red one. RAN_SITE1=$RAN_SITE1 RAN_SITE2=$RAN_SITE2"
  exit 2
fi

if (( RC == 0 )); then
  echo "SITE-2 RED DEMONSTRATION FAILED: probe PASSED against a known-bad site-2 mutant -- it cannot detect this regression. This is the EXACT gap T215 was raised to close (T210's probe passed against this same mutation shape)."
  exit 1
fi

if (( ! SITE2_FAILED )); then
  echo "SITE-2 RED DEMONSTRATION AMBIGUOUS: probe failed (exit $RC) but did not print the specific site-2 (STAGE) failure line -- cannot confirm it named the right site."
  exit 1
fi

if (( ! SITE1_PASSED )); then
  echo "SITE-2 RED DEMONSTRATION WEAKENED: probe failed overall, but site 1 (DETECT) did NOT report clean -- this run cannot show the failure is site-2-specific."
  exit 1
fi

echo "SITE-2 RED DEMONSTRATION CONFIRMED: probe failed (exit $RC), named site 2 (STAGE) as broken, AND reported site 1 (DETECT) clean -- the failure is attributed to the correct site, not a blanket red. This closes the gap T215 was raised to fix."
exit 0
