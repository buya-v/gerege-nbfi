#!/bin/bash
# T444 — the reviewer's own bar, on this review branch, from the worktree itself.
set -u
R="$1"; O="$2"
[ -n "$R" ] && [ -n "$O" ] || { echo "usage: own-bar.sh <repo> <outfile>"; exit 9; }
cd "$R" || exit 2
echo "=== HEAD ==="; git log --oneline -1
echo "=== status BEFORE ==="; git status --porcelain | head
echo "=== BAR ==="
bash .softhouse/conformance.sh > "$O" 2>&1
echo "EXIT=$?"
echo "-- P-84: PRESENCE first --"; echo "   grep -c 'probe = ' = $(LC_ALL=C grep -c 'probe = ' "$O")"
echo "-- value --"; LC_ALL=C grep 'probe = ' "$O"
echo "-- VERDICT --"; LC_ALL=C grep -E '^VERDICT' "$O"
echo "-- wrong ledger impls --"; LC_ALL=C grep -E 'wrong ledger implementations' "$O"
echo "-- guards-dir census --"; LC_ALL=C grep 'GUARDS-DIR-REGISTRATION: population' "$O"
echo "-- dead-path --"; LC_ALL=C grep -E 'T316-DEADPATH-(CENSUS|FRONTIER)' "$O"
echo "-- host state --"; LC_ALL=C grep -A2 'CENSUS host state' "$O" | LC_ALL=C sed -n '1,4p'
echo "-- fail-open frontier --"; LC_ALL=C grep -E 'FAILOPEN|fail-open frontier' "$O" | LC_ALL=C sed -n '1,4p'
echo "-- namespace --"; LC_ALL=C grep -E 'namespace: ' "$O" | head -2
echo "=== status AFTER ==="; git status --porcelain | head
