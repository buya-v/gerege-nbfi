#!/bin/bash
# T382 — F-2: establish, BY RUNNING (P-83) and never by arithmetic, which rows leave the
# dead-path census between main and the T374 merge result, and what the T326 regenerator
# would produce on the merge result.
set -u
# HOST STATE IS A PARAMETER, NOT A LITERAL (guard_no_host_state_in_lint_corpus).
# A /tmp path assigned to a name in a tracked instrument is shared across worktrees,
# absent from every commit and deleted on reboot. Supply them:
#   T382_CLONE=<throwaway clone> T382_OUT=<scratch dir> bash <this script>
# The committed transcripts were produced with T382_OUT=/tmp/t382-out and the clone
# named in each transcript's first line.
SC="${T382_CLONE:?set T382_CLONE to a throwaway clone of this repo}"
O="${T382_OUT:?set T382_OUT to a scratch output directory}"
CENSUS=".softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
REGEN=".softhouse/capture/t326-frontier-host-state/instruments/10-regen-pin.py"
PIN=".softhouse/guards/dead-path-frontier.pin"
mkdir -p "$O"

rows() { grep -v '^#' "$1" | grep -c '|'; }

echo "### 0. what main is RIGHT NOW"
git -C "$SC" fetch -q origin
git -C "$SC" checkout -q -B pinmain origin/main
git -C "$SC" log --oneline -1
echo "pin rows committed on main: $(rows "$SC/$PIN")"

echo
echo "### 1. census RUN at main"
( cd "$SC" && python3 "$CENSUS" --json "$O/census-main.json" ) > "$O/census-main.txt" 2>&1
echo "census rc=$?"
grep -iE 'dead|rows|total' "$O/census-main.txt" | tail -8

echo
echo "### 2. regenerator --check at main (does main's own pin reproduce?)"
( cd "$SC" && python3 "$REGEN" --census "$O/census-main.json" --check ) > "$O/regen-main-check.txt" 2>&1
echo "regen --check rc=$?"
tail -5 "$O/regen-main-check.txt"

echo
echo "### 3. T374 branch ALONE — census RUN"
git -C "$SC" checkout -q -B pinT374 origin/softhouse/T374-t362-conditions
git -C "$SC" log --oneline -1
echo "pin rows committed on T374: $(rows "$SC/$PIN")"
( cd "$SC" && python3 "$CENSUS" --json "$O/census-t374.json" ) > "$O/census-t374.txt" 2>&1
echo "census rc=$?"
( cd "$SC" && python3 "$REGEN" --census "$O/census-t374.json" --check ) > "$O/regen-t374-check.txt" 2>&1
echo "regen --check rc=$?  (0 = the committed pin IS what the regenerator produces here)"
tail -5 "$O/regen-t374-check.txt"

echo
echo "### 4. THE MERGE RESULT — census RUN, and what the regenerator would produce"
git -C "$SC" checkout -q -B pinmerge origin/main
git -C "$SC" merge -q --no-edit origin/softhouse/T374-t362-conditions
git -C "$SC" log --oneline -1
echo "pin rows in the MERGE RESULT as committed: $(rows "$SC/$PIN")"
( cd "$SC" && python3 "$CENSUS" --json "$O/census-merge.json" ) > "$O/census-merge.txt" 2>&1
echo "census rc=$?"
( cd "$SC" && python3 "$REGEN" --census "$O/census-merge.json" --check ) > "$O/regen-merge-check.txt" 2>&1
echo "regen --check rc=$?"
tail -20 "$O/regen-merge-check.txt"

echo
echo "### 5. the ROW DELTA main -> merge result, named (this is the F-2 question)"
git -C "$SC" show origin/main:"$PIN" | grep -v '^#' | grep '|' | sort > "$O/pinrows-main.txt"
git -C "$SC" show origin/softhouse/T374-t362-conditions:"$PIN" | grep -v '^#' | grep '|' | sort > "$O/pinrows-t374.txt"
echo "--- rows on main but NOT on T374 (REMOVED) ---"
comm -23 "$O/pinrows-main.txt" "$O/pinrows-t374.txt"
echo "--- rows on T374 but NOT on main (ADDED) ---"
comm -13 "$O/pinrows-main.txt" "$O/pinrows-t374.txt"

echo
echo "### 6. does the REMOVED literal still occur anywhere tracked on the merge result?"
git -C "$SC" grep -n 'A2-7-capture-mandatory-accounts' -- '.softhouse/*.py' '.softhouse/*.sh' || echo "  (no tracked .py/.sh occurrence — the census corpus is exactly those two globs)"
