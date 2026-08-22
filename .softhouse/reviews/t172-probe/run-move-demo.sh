#!/bin/zsh
# T215 -- content-binding demonstration.
#
# T210's core property, which this T215 extension must NOT lose: the probe
# extracts its anchor(s) by PATTERN, never by line number, so a rewrite
# that relocates the guarded code (as T211 in fact did -- run_driver moved
# 237-291 -> 356-474, and the LOCK-exclusion sites drifted 313->496 and
# 334->517 alongside it) does not break the probe.
#
# This demo builds a SCRATCH COPY of the live fire-program.sh with a large
# block of padding lines inserted BEFORE the exit-protocol guard function,
# which shifts BOTH LOCK-exclusion sites to different line numbers than
# they hold in the live file today, and confirms
# check-lock-exclusion-anchor.sh still finds both sites, classifies them
# correctly, and PASSES -- proving the extended (population-rule) probe
# still binds by content, not by line number.
set -uo pipefail
HERE="${0:A:h}"
LIVE="${HERE}/../../bin/fire-program.sh"
LIVE="${LIVE:A}"
MUTANT="${HERE}/fire-program.sh.MOVE-scratch-copy.sh"

if [[ ! -f "$LIVE" ]]; then
  print -u2 -- "ERROR: live file not found at $LIVE -- cannot build MOVE mutant"
  exit 2
fi

ORIG_DETECT_LINE=$(LC_ALL=C /usr/bin/grep -n 'git status --porcelain' "$LIVE" | /usr/bin/grep -F ':(top,exclude).softhouse/LOCK' | /usr/bin/cut -d: -f1)
ORIG_STAGE_LINE=$(LC_ALL=C /usr/bin/grep -n 'git add -A' "$LIVE" | /usr/bin/grep -F ':(top,exclude).softhouse/LOCK' | /usr/bin/cut -d: -f1)

if [[ -z "$ORIG_DETECT_LINE" || -z "$ORIG_STAGE_LINE" ]]; then
  print -u2 -- "ERROR: could not locate original DETECT/STAGE line numbers in the live file -- cannot build a faithful move demo"
  exit 2
fi

echo "original (live file) line numbers: DETECT=$ORIG_DETECT_LINE STAGE=$ORIG_STAGE_LINE"

# Insert 300 padding comment lines right at the top of the file (after the
# shebang) -- this shifts EVERY subsequent line, including both guard
# sites, by a large constant offset, simulating "the file was rewritten
# and the guard moved" without changing the guard's own bytes at all.
/usr/bin/python3 - "$LIVE" "$MUTANT" <<'PYEOF'
import sys
live, mutant = sys.argv[1:3]
with open(live) as f:
    lines = f.readlines()
if not lines or not lines[0].startswith("#!"):
    sys.stderr.write("ERROR: expected file to start with a shebang line\n")
    sys.exit(2)
padding = ["# T215 move-demo padding line %d -- exists only to shift subsequent line numbers\n" % i for i in range(300)]
out = [lines[0]] + padding + lines[1:]
with open(mutant, "w") as f:
    f.writelines(out)
PYEOF
PY_RC=$?
if (( PY_RC != 0 )); then
  exit $PY_RC
fi

NEW_DETECT_LINE=$(LC_ALL=C /usr/bin/grep -n 'git status --porcelain' "$MUTANT" | /usr/bin/grep -F ':(top,exclude).softhouse/LOCK' | /usr/bin/cut -d: -f1)
NEW_STAGE_LINE=$(LC_ALL=C /usr/bin/grep -n 'git add -A' "$MUTANT" | /usr/bin/grep -F ':(top,exclude).softhouse/LOCK' | /usr/bin/cut -d: -f1)
echo "moved (scratch mutant) line numbers:  DETECT=$NEW_DETECT_LINE STAGE=$NEW_STAGE_LINE"

if [[ "$NEW_DETECT_LINE" == "$ORIG_DETECT_LINE" || "$NEW_STAGE_LINE" == "$ORIG_STAGE_LINE" ]]; then
  print -u2 -- "ERROR: line numbers did not actually shift -- this demo did not do what it claims"
  exit 2
fi
echo "confirmed: both sites moved to different line numbers in the mutant."
echo

echo "=== running check-lock-exclusion-anchor.sh against the MOVED mutant (expect PASS -- content-bound, not line-bound) ==="
OUT=$(zsh "${HERE}/check-lock-exclusion-anchor.sh" "$MUTANT" 2>&1)
RC=$?
print -r -- "$OUT"
echo
echo "exit code: $RC"

rm -f "$MUTANT"

FOUND_NEW_DETECT=0
FOUND_NEW_STAGE=0
[[ "$OUT" == *"line $NEW_DETECT_LINE"* && "$OUT" == *"classified: DETECT"* ]] && FOUND_NEW_DETECT=1
[[ "$OUT" == *"line $NEW_STAGE_LINE"* && "$OUT" == *"classified: STAGE"* ]] && FOUND_NEW_STAGE=1

if (( RC != 0 )); then
  echo "MOVE DEMONSTRATION FAILED: probe did not PASS against the moved-but-unmutated guard -- it is (at least partly) line-bound, which is the exact property T210 got right and T215 must not lose."
  exit 1
fi

if (( ! FOUND_NEW_DETECT )) || (( ! FOUND_NEW_STAGE )); then
  echo "MOVE DEMONSTRATION AMBIGUOUS: probe exited 0 but did not visibly report BOTH sites at their NEW (post-move) line numbers -- cannot confirm it re-extracted by content rather than, say, silently finding nothing and defaulting to pass. FOUND_NEW_DETECT=$FOUND_NEW_DETECT FOUND_NEW_STAGE=$FOUND_NEW_STAGE"
  exit 1
fi

echo "MOVE DEMONSTRATION CONFIRMED: both sites relocated by ~300 lines, and the probe found and classified BOTH at their NEW line numbers ($NEW_DETECT_LINE, $NEW_STAGE_LINE) and still PASSED -- content-binding holds, exactly as T210 established and as T211's real rewrite (313->496, 334->517) already proved for the DETECT-only probe."
exit 0
