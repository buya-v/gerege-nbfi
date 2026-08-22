#!/bin/zsh
# T215 -- per-site RED demonstration, SITE 1 (DETECT) ONLY.
#
# Mutates a SCRATCH COPY of the live file so that ONLY the DETECT site
# (the `git status --porcelain ...` line that computes $DIRTY) is broken --
# the STAGE site (`git add -A ...`) is left byte-identical. This proves the
# extended check-lock-exclusion-anchor.sh can (a) still find BOTH sites by
# population scan, (b) fail specifically on site 1, and (c) still PASS site
# 2, i.e. it names which site is broken rather than reporting an
# undifferentiated "something is wrong somewhere".
#
# Targeting is by CONTENT, not by line number: the mutation is applied to
# "the line containing 'git status --porcelain'", wherever that line
# currently sits in the file -- never to a hardcoded line index.
set -uo pipefail
HERE="${0:A:h}"
LIVE="${HERE}/../../bin/fire-program.sh"
LIVE="${LIVE:A}"
MUTANT="${HERE}/fire-program.sh.RED-site1-scratch-copy.sh"

if [[ ! -f "$LIVE" ]]; then
  print -u2 -- "ERROR: live file not found at $LIVE -- cannot build RED mutant"
  exit 2
fi

NEEDLE=":(top,exclude).softhouse/LOCK'"
REPLACEMENT=":(top,exclude).softhouse/LOCK*'"

# Rebuild the file line by line so only the line matching the DETECT
# command ('git status --porcelain') is mutated; every other line
# (including the STAGE site, which shares the identical NEEDLE substring)
# passes through untouched.
/usr/bin/python3 - "$LIVE" "$MUTANT" "$NEEDLE" "$REPLACEMENT" <<'PYEOF'
import sys
live, mutant, needle, replacement = sys.argv[1:5]
with open(live, "r") as f:
    lines = f.readlines()
out = []
mutated_any = False
for line in lines:
    if "git status --porcelain" in line and needle in line:
        line = line.replace(needle, replacement)
        mutated_any = True
    out.append(line)
if not mutated_any:
    sys.stderr.write("ERROR: no DETECT-site line ('git status --porcelain' + needle) found -- cannot construct a faithful site-1 mutant\n")
    sys.exit(2)
with open(mutant, "w") as f:
    f.writelines(out)
PYEOF
PY_RC=$?
if (( PY_RC != 0 )); then
  exit $PY_RC
fi

echo "=== mutated DETECT-site line (scratch copy only, live file untouched) ==="
LC_ALL=C /usr/bin/grep -n 'git status --porcelain' "$MUTANT"
echo "=== STAGE-site line, confirmed UNCHANGED ==="
LC_ALL=C /usr/bin/grep -n 'git add -A' "$MUTANT"
echo

echo "=== running check-lock-exclusion-anchor.sh against the SITE-1 MUTANT (expect FAIL naming site 1/DETECT, and site 2/STAGE still PASS) ==="
zsh "${HERE}/check-lock-exclusion-anchor.sh" "$MUTANT"
RC=$?
echo
echo "exit code: $RC"

# --- prove the arm RAN (P-64): the transcript above must show BOTH sites
# were found and classified, not just a bare nonzero exit. Re-run and
# capture output to check this mechanically rather than eyeballing it.
OUT=$(zsh "${HERE}/check-lock-exclusion-anchor.sh" "$MUTANT" 2>&1)
RAN_SITE1=0; RAN_SITE2=0; SITE1_FAILED=0; SITE2_PASSED=0
[[ "$OUT" == *"classified: DETECT"* ]] && RAN_SITE1=1
[[ "$OUT" == *"classified: STAGE"* ]] && RAN_SITE2=1
# match generically on the DETECT-tagged malformed-pathspec message -- do
# NOT hardcode "site 1": which numeric SITE_INDEX the DETECT line gets is
# an artifact of where it happens to sit in the file today, not a property
# this demo should assume.
[[ "$OUT" == *", DETECT) matched the LOCK-exclusion census but the pathspec argument is not the exact expected token"* ]] && SITE1_FAILED=1
[[ "$OUT" == *"CHECK 1S PASS"* && "$OUT" == *"CHECK 2S PASS"* ]] && SITE2_PASSED=1

rm -f "$MUTANT"

if (( ! RAN_SITE1 )) || (( ! RAN_SITE2 )); then
  echo "PRECONDITION FAILED (P-64): the probe did not visibly classify both sites -- an inconclusive run, not a red one. RAN_SITE1=$RAN_SITE1 RAN_SITE2=$RAN_SITE2"
  exit 2
fi

if (( RC == 0 )); then
  echo "SITE-1 RED DEMONSTRATION FAILED: probe PASSED against a known-bad site-1 mutant -- it cannot detect this regression."
  exit 1
fi

if (( ! SITE1_FAILED )); then
  echo "SITE-1 RED DEMONSTRATION AMBIGUOUS: probe failed (exit $RC) but did not print the specific site-1 (\$DIRTY) failure line -- cannot confirm it named the right site."
  exit 1
fi

if (( ! SITE2_PASSED )); then
  echo "SITE-1 RED DEMONSTRATION WEAKENED: probe failed overall, but site 2 (STAGE) did NOT report clean -- this run cannot show the failure is site-1-specific."
  exit 1
fi

echo "SITE-1 RED DEMONSTRATION CONFIRMED: probe failed (exit $RC), named site 1 (DETECT, \$DIRTY) as broken, AND reported site 2 (STAGE) clean -- the failure is attributed to the correct site, not a blanket red."
exit 0
