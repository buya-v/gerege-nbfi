#!/usr/bin/env bash
# T239 — cross-checks. Two jobs:
#   (1) CALIBRATE THE POPULATION before reporting the 0. 20-rerun.sh §A returned 0 hit lines for the
#       original five-alternative pattern. A zero is a negative, and P-72 forbids reporting a
#       negative without a known positive through the SAME route. So: substring 'main' over the same
#       tree, same pathspecs, same engine, must be non-zero.
#   (2) EXPLAIN the disagreement with T234, which reported four-alternative=3. Break the four
#       literal alternatives out one at a time, at T115 AND at HEAD, so the population effect is
#       visible rather than asserted.
#   (3) THIRD ENGINE: BSD /usr/bin/grep -E cannot take a commit argument, so pipe `git show` of each
#       file through it. An independent engine reaching the same 38 is worth more than one engine.
set -u
cd "${1:?repo}" || { echo "FATAL: cd failed — INSTRUMENT IS VOID"; exit 2; }
T115=bd59187cf83c7c7161db23668e91d45bd46be2a8
P1=.softhouse/capture/t91/
P2=.softhouse/capture/charges/bin/preconditions.sh
P3=.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh

echo "PWD=$(pwd)  HEAD=$(git rev-parse HEAD)"
echo
echo "=== (1) POSITIVE CONTROL on the POPULATION — substring 'main', engine -E, tree T115 ==="
echo -n "   hit lines: "
git grep -c -a -E -- 'main' "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo "   ^ non-zero here means the route WORKS and the zeros below are real findings, not a dead rig."
echo -n "   files touched by that control: "
git grep -l -a -E -- 'main' "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | wc -l | tr -d ' '
echo

echo "=== (2) THE FOUR LITERAL ALTERNATIVES, ONE AT A TIME, engine -E ==="
printf '   %-18s %8s %8s\n' "alternative" "@T115" "@HEAD"
for t in 'merge-base' 'main:' 'origin/main' 'rev-parse main'; do
  a=$(git grep -c -a -E -- "$t" "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  b=$(git grep -c -a -E -- "$t"          -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
  printf '   %-18s %8s %8s\n' "$t" "$a" "$b"
done
echo
echo "   and the 5th term:"
a=$(git grep -c -a -P -- '\bmain\b' "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
b=$(git grep -c -a -P -- '\bmain\b'          -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}')
printf '   %-18s %8s %8s   (engine -P, sound)\n' '\bmain\b' "$a" "$b"
echo
echo "   WHICH FILES supply the @HEAD-only literal hits (the ones T234 saw and r11 could not):"
for t in 'merge-base' 'origin/main'; do
  echo "     -- $t @HEAD:"
  git grep -n -a -E -- "$t" -- "$P1" "$P2" "$P3" 2>/dev/null | sed 's/^/        /'
done
echo

echo "=== (3) INDEPENDENT ENGINE — BSD /usr/bin/grep -E over git show of every population file ==="
echo "    (BSD grep honours \\b per transcripts/00-engines.txt; it cannot take a commit arg, so the"
echo "     tree content is streamed to it file by file.)"
n=0; files=0
git ls-tree -r --name-only "$T115" -- "$P1" "$P2" "$P3" > /tmp/t239-pop.txt
while read -r f; do
  c=$(git show "$T115:$f" 2>/dev/null | /usr/bin/grep -c -a -E -- '\bmain\b' 2>/dev/null || true)
  c=${c:-0}
  if [ "$c" -gt 0 ]; then n=$((n+c)); files=$((files+1)); fi
done < /tmp/t239-pop.txt
echo "    BSD grep -E '\\bmain\\b' : $n hit lines across $files files"
echo "    git grep -P  '\\bmain\\b' : $a hit lines   <-- must agree"
if [ "$n" = "$a" ]; then echo "    AGREE — two independent sound engines, same count."; else echo "    *** DISAGREE — investigate ***"; fi
