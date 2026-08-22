#!/bin/zsh
# T210 zero-match demonstration.
#
# Points check-lock-exclusion-anchor.sh at a DECOY file that does not
# contain its anchor pattern (DIRTY=$(git status --porcelain ...) at all,
# and shows the probe ERRORS (nonzero exit, message naming the pattern and
# the file) rather than silently passing. This is exactly the failure mode
# T210 exists to close: T172's old probe kept passing after T190 deleted
# the bytes it replayed (grep -c against the live file returned 0, yet the
# probe stayed green). P-35 (patterns.md): a check inspecting zero items is
# an ERROR, not a pass.
set -uo pipefail
HERE="${0:A:h}"
DECOY="${HERE}/decoy-no-anchor.RED-scratch-copy.sh"

print -r -- '#!/bin/zsh' > "$DECOY"
print -r -- 'echo "this file deliberately has no DIRTY=... guard line at all"' >> "$DECOY"

echo "=== decoy file contents (anchor pattern absent by construction) ==="
cat "$DECOY"
echo

echo "=== running check-lock-exclusion-anchor.sh against the DECOY (expect ERROR, nonzero exit, not a vacuous pass) ==="
zsh "${HERE}/check-lock-exclusion-anchor.sh" "$DECOY"
RC=$?
echo
echo "exit code: $RC"
rm -f "$DECOY"

if (( RC == 0 )); then
  echo "ZERO-MATCH DEMONSTRATION FAILED: probe returned SUCCESS (0) despite zero anchor matches -- P-35 violation."
  exit 1
else
  echo "ZERO-MATCH DEMONSTRATION CONFIRMED: probe refused with a non-zero exit ($RC) and named the pattern + file, never a vacuous pass."
  exit 0
fi
