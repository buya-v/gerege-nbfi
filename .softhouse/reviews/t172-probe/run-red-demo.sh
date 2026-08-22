#!/bin/zsh
# T210 RED demonstration.
#
# Mutates a SCRATCH COPY of the live LOCK-exclusion guard line (never the
# live .softhouse/bin/fire-program.sh) to reintroduce, in today's shape,
# the prefix-collision bug T172 originally fixed: broadens the git
# pathspec exact-exclude to a trailing glob, so it also swallows
# .softhouse/LOCKED_STATE.md the way the pre-T172 unanchored grep did.
# Shows check-lock-exclusion-anchor.sh FAILS LOUDLY (nonzero exit) against
# the mutated copy.
#
# Sibling-file shape (T161's measured trap): fire-program.sh itself does
# NOT derive its repo root from $0/__file__ -- verified by grepping the
# live file for '0:A' and '__file__'/'BASH_SOURCE', zero matches; REPO is
# `${GEREGE_NBFI_REPO:-/Users/buv/gerege-nbfi}`, hardcoded. So copying the
# whole script elsewhere would not by itself reproduce a __file__-derived
# defect (there isn't one here) -- but check-lock-exclusion-anchor.sh's own
# DEFAULT target resolution IS $0-relative, and the mutated file must sit
# where a real drift would put it (next to the real file's directory
# structure) for a faithful test, so this script writes the mutant beside
# this directory's other probe scripts and passes it explicitly as
# TARGET_FILE rather than relying on default resolution.
set -uo pipefail
HERE="${0:A:h}"
LIVE="${HERE}/../../bin/fire-program.sh"
LIVE="${LIVE:A}"
MUTANT="${HERE}/fire-program.sh.RED-scratch-copy.sh"

if [[ ! -f "$LIVE" ]]; then
  print -u2 -- "ERROR: live file not found at $LIVE -- cannot build RED mutant"
  exit 2
fi

NEEDLE=":(top,exclude).softhouse/LOCK'"
REPLACEMENT=":(top,exclude).softhouse/LOCK*'"

content="$(<"$LIVE")"
if [[ "$content" != *"$NEEDLE"* ]]; then
  print -u2 -- "ERROR: expected substring not found in live file, cannot construct a faithful mutant:"
  print -u2 -- "  needle: $NEEDLE"
  print -u2 -- "  file:   $LIVE"
  exit 2
fi
mutated="${content//$NEEDLE/$REPLACEMENT}"
print -rn -- "$mutated" > "$MUTANT"

echo "=== mutated guard line (scratch copy only, live file untouched) ==="
LC_ALL=C /usr/bin/grep -n 'DIRTY=\$(git status --porcelain' "$MUTANT"
echo

echo "=== running check-lock-exclusion-anchor.sh against the MUTANT (expect FAIL, nonzero exit) ==="
zsh "${HERE}/check-lock-exclusion-anchor.sh" "$MUTANT"
RC=$?
echo
echo "exit code: $RC"
rm -f "$MUTANT"

if (( RC == 0 )); then
  echo "RED DEMONSTRATION FAILED: probe PASSED against a known-bad mutant -- it cannot detect this regression. This is itself a defect in the probe."
  exit 1
else
  echo "RED DEMONSTRATION CONFIRMED: probe correctly FAILED (exit $RC) against the mutant."
  exit 0
fi
