#!/usr/bin/env bash
# T523 item 7 — WHAT DOES balanceSynonymRe = `(?i)outstanding` ACTUALLY COST?
#
# isBalanceName (main.go:340) is `balanceNameRe || balanceSynonymRe`, and it is the SINGLE
# predicate behind every balance decision in the guard — Go identifier (:888, :993, :1212),
# SQL column (:501, :519, :555) and, since T509, SQL TABLE name (:477). So the synonym widens
# all six surfaces at once.
#
# Measured differentially: the shipped guard vs a byte-identical build with the synonym regex
# replaced by one that cannot match. The delta is exactly the set of findings the synonym is
# responsible for, and the whole-tree name census says how much surface it now covers.
#
# Usage: synonym-cost.sh <shipped-binary> <synonym-disabled-binary> <nexus-dir> <scratch-dir>
set -u -o pipefail
BIN="$1"; NOSYN="$2"; NEXUS="$3"; SCR="$4"; mkdir -p "$SCR"

findings() { "$1" --root "$2" 2>&1 | LC_ALL=C grep -a -E '^  \[' | LC_ALL=C sed 's/^  //' | LC_ALL=C sort; }

findings "$BIN"   "$NEXUS" > "$SCR/withsyn.txt"
findings "$NOSYN" "$NEXUS" > "$SCR/nosyn.txt"

printf 'shipped guard findings:            %s\n' "$(LC_ALL=C grep -ac . "$SCR/withsyn.txt")"
printf 'same guard, synonym disabled:      %s\n' "$(LC_ALL=C grep -ac . "$SCR/nosyn.txt")"
printf 'attributable to (?i)outstanding:   %s\n\n' \
  "$(LC_ALL=C comm -23 "$SCR/withsyn.txt" "$SCR/nosyn.txt" | LC_ALL=C grep -ac . || true)"

echo '--- findings that exist ONLY because of (?i)outstanding ---'
LC_ALL=C comm -23 "$SCR/withsyn.txt" "$SCR/nosyn.txt"

echo ''
echo '--- every identifier in nexus/ that (?i)outstanding matches but (?i)balance does not ---'
echo '    (the surface the synonym newly rules on; a name here is refused wherever it is WRITTEN)'
LC_ALL=C grep -rhoaE '[A-Za-z_][A-Za-z0-9_]*' --include='*.go' "$NEXUS" \
  | LC_ALL=C grep -aiE 'outstanding' \
  | LC_ALL=C grep -aivE 'balance' \
  | LC_ALL=C sort | LC_ALL=C uniq -c | LC_ALL=C sort -rn

echo ''
echo '--- SQL column/table-shaped tokens with "outstanding" and no "balance", in string literals ---'
LC_ALL=C grep -rhoaE '[a-z_][a-z0-9_]*outstanding[a-z0-9_]*' --include='*.go' "$NEXUS" \
  | LC_ALL=C grep -aivE 'balance' | LC_ALL=C sort -u
