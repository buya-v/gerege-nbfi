#!/usr/bin/env bash
# T244 — DRIVER CORRECTION RESPONSE.
#
# The driver told me `git grep -E` is unsound in BOTH directions (it FABRICATES as well
# as loses) and instructed me to re-run the sweep under a sound engine and say which.
# My engine 2 WAS `git grep -E`, so its results are re-verified here under engines the
# driver's table and my own re-derivation BOTH mark sound:
#
#   git grep -P        <- SOUND, available in git here (the driver's find; lore missed it)
#   /usr/bin/grep -E   <- SOUND (BSD grep; this was already my PRIMARY engine)
#   python3 re         <- SOUND (this was already my multi-line engine)
#
# AND, per the driver's point 1, this calibrates on a KNOWN NEGATIVE as well as a known
# positive — because an engine that fabricates cannot be caught by a positive alone.
set -uo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 9
ROOT="$(cd "$SELF_DIR/../../.." && pwd)" || exit 9
cd "$ROOT" || exit 9
[ -f docs/adr/DEC-2-gl-accounting-adapter.md ] || { echo "FATAL: wrong tree"; exit 9; }

echo "root     : $ROOT"
echo "HEAD     : $(git rev-parse HEAD)"
echo "measured : $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC"
echo

echo "################ CALIBRATION — POSITIVE **AND** NEGATIVE ################"
echo "-- known POSITIVE: 'corpus contains no reversal' (DEC-2:823). Must be >= 1 everywhere."
printf '  git grep -P      : %s\n' "$(git grep -c -P 'corpus contains no reversal' -- . 2>/dev/null | wc -l | tr -d ' ') file(s)"
printf '  BSD grep -E      : %s\n' "$(/usr/bin/grep -rlE 'corpus contains no reversal' --exclude-dir=.git . 2>/dev/null | wc -l | tr -d ' ') file(s)"
echo
echo "-- known NEGATIVE (driver point 1): a token that is NOWHERE in the tree."
echo "   Chosen so it cannot self-match: it is built at runtime and never written to disk."
NEG="zzq$(printf '%s' T244)NEVERPRESENT$(printf '%s' XQ)"
printf '  token            : %s\n' "$NEG"
printf '  git grep -P      : %s hit(s)  [expect 0]\n' "$(git grep -c -P "$NEG" -- . 2>/dev/null | wc -l | tr -d ' ')"
printf '  BSD grep -E      : %s hit(s)  [expect 0]\n' "$(/usr/bin/grep -rlE "$NEG" --exclude-dir=.git . 2>/dev/null | wc -l | tr -d ' ')"
echo
echo "-- FABRICATION PROBE: the \\b trap, run against the REAL tree, both engines."
echo "   If an engine fabricates, these two counts will DISAGREE."
printf '  git grep -P  \\brevers\\b   : %s hit line(s)\n' "$(git grep -n -P '\brevers\b' -- . 2>/dev/null | wc -l | tr -d ' ')"
printf '  BSD grep -E  \\brevers\\b   : %s hit line(s)\n' "$(/usr/bin/grep -rnE '\brevers\b' --exclude-dir=.git . 2>/dev/null | wc -l | tr -d ' ')"
printf '  git grep -E  \\brevers\\b   : %s hit line(s)  <-- UNSOUND ENGINE, shown for contrast\n' "$(git grep -n -E '\brevers\b' -- . 2>/dev/null | wc -l | tr -d ' ')"
echo

echo "################ THE LOAD-BEARING RESULT, UNDER SOUND ENGINES ################"
echo "The claim: the stale reason survives at exactly TWO live sites, both in DEC-2."
echo
for p in 'corpus contains no revers' 'contains no revers' 'no reversal appears' 'retired by one capture'; do
  echo "--- PATTERN: $p"
  echo "  [git grep -P]"
  git grep -n -P "$p" -- . 2>/dev/null | /usr/bin/grep -v 't244-dec2-rev6' | cut -c1-150 | sed 's/^/    /'
  echo "  [BSD grep -E]"
  /usr/bin/grep -rnE "$p" --exclude-dir=.git . 2>/dev/null | /usr/bin/grep -v 't244-dec2-rev6' | cut -c1-150 | sed 's/^/    /'
  echo
done

echo "################ DO THE TWO SOUND ENGINES AGREE? ################"
A=$(git grep -n -P 'contains no revers|no reversal appears' -- . 2>/dev/null | /usr/bin/grep -v 't244-dec2-rev6' | wc -l | tr -d ' ')
B=$(/usr/bin/grep -rnE 'contains no revers|no reversal appears' --exclude-dir=.git . 2>/dev/null | /usr/bin/grep -v 't244-dec2-rev6' | wc -l | tr -d ' ')
echo "  git grep -P    : $A hit line(s)"
echo "  BSD grep -E    : $B hit line(s)"
echo "  (BSD searches the tree on disk incl. untracked; git grep searches TRACKED files."
echo "   A difference is explained by that, not by unsoundness — the file LIST is printed below.)"
echo
echo "  git grep -P files:"
git grep -l -P 'contains no revers|no reversal appears' -- . 2>/dev/null | sed 's/^/    /'
echo "  BSD grep -E files:"
/usr/bin/grep -rlE 'contains no revers|no reversal appears' --exclude-dir=.git . 2>/dev/null | sed 's/^/    /'
