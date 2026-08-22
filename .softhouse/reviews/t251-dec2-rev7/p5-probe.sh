#!/usr/bin/env bash
# T251: verify T247's claim "P-5 is named nowhere in the ledger package".
#
# P-66/P-70: a non-existence is a statement about the SEARCH. So this states the
# population searched, and CALIBRATES on the sibling preconditions P-1..P-10 —
# if the probe cannot find P-4 either, its silence on P-5 proves nothing.
#
# P-75: git grep -P (PCRE), never bare grep, never rg, never git grep -E.
# Discrimination: \b anchors so that P-5 does not match P-50/P-51 and vice
# versa. The negative control below proves that anchoring actually bites.
#
# NOTE ON set -e: git grep exits 1 on "no match", which is the EXPECTED result
# for the very row this probe exists to establish. Every git grep here is
# therefore wrapped in `{ ...; } || true` so that a true negative is reported
# as 0 rather than killing the script and looking like a crash.
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

PKG=nexus/internal/apps/ledger

count() {  # count(pattern, pathspec) -> number of word-anchored occurrences
  { git grep -h -o -P "$1" -- "$2" 2>/dev/null || true; } | wc -l | tr -d ' '
}

echo "COMMIT: $(git rev-parse HEAD)"
echo
echo "POPULATION SEARCHED:"
git ls-files -- "$PKG" | sed 's/^/  /'
echo "  ---- $(git ls-files -- "$PKG" | wc -l | tr -d ' ') tracked files"
echo

echo "PER-PRECONDITION HIT COUNTS in $PKG (word-anchored PCRE):"
for p in P-1 P-2 P-3 P-4 P-5 P-6 P-7 P-8 P-9 P-10; do
  printf '  %-5s %s\n' "$p" "$(count "\\b${p}\\b" "$PKG")"
done
echo

echo "NEGATIVE CONTROL — does \\b actually discriminate P-5 from P-50?"
echo "  (an unanchored substring probe matches P-5, P-50 and P-51 alike; if the"
echo "   anchored and unanchored counts agree, the anchoring is not biting and"
echo "   the P-5 result would be void)"
echo "  anchored    \\bP-5\\b  = $(count '\bP-5\b'  "$PKG")"
echo "  anchored    \\bP-50\\b = $(count '\bP-50\b' "$PKG")"
echo "  UNanchored  P-5      = $(count 'P-5'      "$PKG")"
echo

echo "WIDER POPULATION — is P-5 named anywhere under nexus/ at all?"
{ git grep -n -P '\bP-5\b' -- nexus || echo "  (none under nexus/)"; }
echo

echo "AND where IS P-5 defined? (so 'not found' is anchored to a real referent)"
{ git grep -n -P '\bP-5\b' -- docs/adr/DEC-2-gl-accounting-adapter.md || true; } | head -8
