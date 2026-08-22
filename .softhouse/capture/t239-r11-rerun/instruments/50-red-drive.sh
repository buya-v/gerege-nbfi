#!/usr/bin/env bash
# T239 — DRIVE IT RED (P-22). r11 §2 is a GUARD: it exists to catch a baseline computed from the
# moving ref `main`. So plant exactly that violation and show the guard does not fire.
#
# The plant is chosen so that ONLY the fifth alternative could catch it:
#     BASE=$(git rev-list -1 main)
# It contains no 'merge-base', no 'main:', no 'origin/main', no 'rev-parse main'. It is a bare
# word `main` used as a baseline — the literal P-24 trap the fifth term was written for.
#
# The tree is built with PLUMBING into a TEMPORARY INDEX (GIT_INDEX_FILE), so nothing is added to
# my branch, my working tree, or any path outside my scope. The scratch commit is an unreachable
# object; it is named in the transcript so the result can be reproduced.
set -u
cd "${1:?repo}" || { echo "FATAL: cd failed — INSTRUMENT IS VOID"; exit 2; }
T115=bd59187cf83c7c7161db23668e91d45bd46be2a8
P1=.softhouse/capture/t91/
P2=.softhouse/capture/charges/bin/preconditions.sh
P3=.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh
FIVE='merge-base|main:|origin/main|rev-parse main|\bmain\b'

echo "PWD=$(pwd)  HEAD=$(git rev-parse HEAD)"
echo

PLANT='#!/bin/sh
# planted by T239 to drive r11 s2 RED
BASE=$(git rev-list -1 main)
git archive "$BASE" > /tmp/x.tar
'
BLOB=$(printf '%s' "$PLANT" | git hash-object -w --stdin)
echo "planted blob: $BLOB"
echo "planted content:"
printf '%s' "$PLANT" | sed 's/^/    /'
echo

export GIT_INDEX_FILE=/tmp/t239-red-index
rm -f "$GIT_INDEX_FILE"
git read-tree "$T115"
git update-index --add --cacheinfo 100644,"$BLOB",.softhouse/capture/t91/t239-planted-baseline.sh
TREE=$(git write-tree)
SCRATCH=$(git commit-tree "$TREE" -p "$T115" -m "T239 scratch: T115 + one planted P-24 violation")
unset GIT_INDEX_FILE
rm -f /tmp/t239-red-index
echo "scratch commit (unreachable, not on any branch): $SCRATCH"
echo "  parent: $T115"
echo -n "  planted file present in scratch tree? -> "
git ls-tree -r --name-only "$SCRATCH" -- "$P1" | /usr/bin/grep -q 't239-planted-baseline.sh' && echo YES || echo "NO — PLANT FAILED, RESULTS VOID"
echo

echo "=================================================================="
echo "RED DRIVE — the ORIGINAL instrument (git grep -E) against the plant"
echo "=================================================================="
git grep -n -a -E "$FIVE" "$SCRATCH" -- "$P1" "$P2" "$P3" > /tmp/t239-red-E.txt 2>&1; rc=$?
echo "exit code: $rc"
echo "hit lines: $(wc -l < /tmp/t239-red-E.txt | tr -d ' ')"
cat /tmp/t239-red-E.txt | sed 's/^/    /'
echo "    ^^^ the planted violation is NOT here. The guard passes a tree that contains"
echo "        a baseline computed from main. THE GUARD IS RED-BLIND."
echo

echo "=================================================================="
echo "GREEN CONTROL — the SOUND instrument (git grep -P) against the same tree"
echo "=================================================================="
git grep -n -a -P "$FIVE" "$SCRATCH" -- "$P1" "$P2" "$P3" > /tmp/t239-red-P.txt 2>&1; rc=$?
echo "exit code: $rc"
echo "hit lines: $(wc -l < /tmp/t239-red-P.txt | tr -d ' ')"
echo "    the planted line, as the sound instrument reports it:"
/usr/bin/grep -a 't239-planted-baseline' /tmp/t239-red-P.txt | sed 's/^/    /'
echo
echo "=================================================================="
echo "SUMMARY OF THE RED DRIVE"
echo "=================================================================="
e=$(wc -l < /tmp/t239-red-E.txt | tr -d ' ')
p=$(wc -l < /tmp/t239-red-P.txt | tr -d ' ')
pe=$(/usr/bin/grep -c -a 't239-planted-baseline' /tmp/t239-red-E.txt || true)
pp=$(/usr/bin/grep -c -a 't239-planted-baseline' /tmp/t239-red-P.txt || true)
printf '    %-34s %s\n' "original -E, total hit lines"      "$e"
printf '    %-34s %s\n' "original -E, PLANT detected"       "${pe:-0}"
printf '    %-34s %s\n' "sound -P, total hit lines"         "$p"
printf '    %-34s %s\n' "sound -P, PLANT detected"          "${pp:-0}"
if [ "${pe:-0}" = "0" ] && [ "${pp:-0}" != "0" ]; then
  echo "    RESULT: RED DRIVE SUCCEEDED — guard blind, sound instrument sees it."
else
  echo "    RESULT: *** unexpected, investigate ***"
fi
