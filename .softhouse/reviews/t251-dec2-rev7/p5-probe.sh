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
# ---------------------------------------------------------------------------
# REPAIRED BY THE DRIVER, local fire 20260822-140002, after this script tripped
# conformance.sh's fail-open guard as a NEW TIER2 instrument (frontier 10 -> 11)
# on the merge of T251 at 6694a34.
#
# THE DEFECT, and it is the one this program keeps re-finding: `git grep` exits
# 1 on NO MATCH and >1 on ERROR. The original wrapped every search in
# `|| echo "  (none under nexus/)"` and `|| true`, so a bad pathspec, a broken
# PCRE, or running outside a repo printed the SAME reassuring negative as a
# genuine no-match — a negative the probe DID NOT MEASURE. That is the exact
# shape the guard exists to catch, and it appeared in a script written to
# enforce P-66 ("state where you looked"). Repaired, NOT suppressed: the
# `# lint-failopen: ok` escape hatch would have silenced the detector while
# leaving the script able to lie.
#
# Now every search classifies its own exit status: 0 = matched, 1 = a REAL
# measured negative, >1 = an error that ABORTS rather than printing an absence.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd) || {
  echo "FATAL: cannot resolve repo root from ${BASH_SOURCE[0]}" >&2; exit 2; }
cd "$ROOT" || { echo "FATAL: cannot cd to $ROOT" >&2; exit 2; }

PKG=nexus/internal/apps/ledger

# search(pattern, pathspec, extra-git-grep-args...) -> prints matches, or the
# words NO MATCH, and NEVER conflates the two with an error.
search() {
  local pat="$1" path="$2"; shift 2
  local out rc
  set +e
  out=$(git grep "$@" -P "$pat" -- "$path" 2>&1)
  rc=$?
  set -e
  case "$rc" in
    0) printf '%s\n' "$out" ;;
    1) echo "NO MATCH [MEASURED: git grep exited 1 = no match, not an error]" ;;
    *) echo "FATAL: git grep exited $rc searching $path for $pat — this is an ERROR," >&2
       echo "       NOT an absence. Refusing to report a negative this probe did not measure." >&2
       printf '%s\n' "$out" >&2
       exit 2 ;;
  esac
}

# count(pattern, pathspec) -> number of word-anchored occurrences. An error
# aborts; it must never be rendered as the count 0.
count() {
  local pat="$1" path="$2" out rc
  set +e
  out=$(git grep -h -o -P "$pat" -- "$path" 2>&1)
  rc=$?
  set -e
  case "$rc" in
    0) printf '%s\n' "$out" | wc -l | tr -d ' ' ;;
    1) echo 0 ;;
    *) echo "FATAL: git grep exited $rc counting $pat in $path — an error is not a zero." >&2
       exit 2 ;;
  esac
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
search '\bP-5\b' nexus -n
echo

echo "AND where IS P-5 defined? (so 'not found' is anchored to a real referent)"
search '\bP-5\b' docs/adr/DEC-2-gl-accounting-adapter.md -n | head -8
