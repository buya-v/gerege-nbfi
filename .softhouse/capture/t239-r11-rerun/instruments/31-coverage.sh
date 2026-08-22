#!/usr/bin/env bash
# T239 — TWO coverage questions the \b defect hid behind itself.
#
# (a) r11 §2's alternation set is 'merge-base|main:|origin/main|rev-parse main|\bmain\b'.
#     It contains NO term for HEAD. HEAD is a moving ref too, and 30-classify.py found 7
#     invocations resolving it. So even a SOUND version of :35 could not have reported them.
#     This is a PATTERN-DESIGN gap, independent of the engine defect — a second mechanism.
#
# (b) r11's OTHER sub-check (lines 43-47) DOES enumerate revision-resolving invocations, and it
#     has no \b in it, so it worked. But it iterates a HARD-CODED list of 5 filenames. How many
#     .sh files are in the population it was supposed to cover?
set -u
cd "${1:?repo}" || { echo "FATAL: cd failed — INSTRUMENT IS VOID"; exit 2; }
T115=bd59187cf83c7c7161db23668e91d45bd46be2a8
P1=.softhouse/capture/t91/
P2=.softhouse/capture/charges/bin/preconditions.sh
P3=.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh

echo "PWD=$(pwd)  HEAD=$(git rev-parse HEAD)"
echo
echo "=== (a) does r11 §2's pattern contain any HEAD term? ==="
echo "    pattern: merge-base|main:|origin/main|rev-parse main|\\bmain\\b"
echo -n "    contains 'HEAD'? -> "
echo 'merge-base|main:|origin/main|rev-parse main|\bmain\b' | /usr/bin/grep -q 'HEAD' && echo YES || echo "NO — HEAD is not in the alternation at all"
echo -n "    \\bHEAD\\b hit lines in the population (engine -P, sound): "
git grep -c -a -P -- '\bHEAD\b' "$T115" -- "$P1" "$P2" "$P3" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}'
echo "    ^ a sound engine + the SAME pattern still reports none of these."
echo

echo "=== (b) sub-check at r11:43-47 — hard-coded file list vs actual population ==="
NAMED="t115-drive-mf1.sh t115-drive-mf2.sh t115-drive-mf3-mf4.sh t115-rerun-attacks.sh prove-guards.sh"
echo "    files the sub-check names: $(echo $NAMED | wc -w | tr -d ' ')"
git ls-tree -r --name-only "$T115" -- "$P1" "$P2" "$P3" | /usr/bin/grep -E '\.sh$' > /tmp/t239-sh.txt
echo "    .sh files actually in the population: $(wc -l < /tmp/t239-sh.txt | tr -d ' ')"
echo
echo "    --- .sh files in the population NOT named by the sub-check ---"
miss=0
while read -r f; do
  b=$(basename "$f")
  hit=0
  for n in $NAMED; do [ "$b" = "$n" ] && hit=1; done
  if [ "$hit" = 0 ]; then
    r=$(git show "$T115:$f" 2>/dev/null | /usr/bin/grep -c -a -E 'git (archive|show|cat-file|rev-parse|merge-base)' || true)
    echo "        $f   (revision-resolving invocations inside: ${r:-0})"
    miss=$((miss+1))
  fi
done < /tmp/t239-sh.txt
echo "    UNCOVERED: $miss of $(wc -l < /tmp/t239-sh.txt | tr -d ' ') .sh files"
echo

echo "=== (c) do the 7 HEAD-resolving sites fall inside or outside the named 5? ==="
for f in $(cat /tmp/t239-sh.txt); do
  b=$(basename "$f")
  n=$(git show "$T115:$f" 2>/dev/null | /usr/bin/grep -c -a -E 'git [a-z-]*[[:space:]]*(--short[[:space:]]*)?HEAD' || true)
  n=${n:-0}
  if [ "$n" -gt 0 ]; then
    covered=NO
    for x in $NAMED; do [ "$b" = "$x" ] && covered=YES; done
    printf '    %-58s HEAD-sites=%-3s named-by-subcheck=%s\n' "$f" "$n" "$covered"
  fi
done
