#!/usr/bin/env bash
# T239 — ENUMERATE THE POPULATION r11-hygiene.sh:35 actually searched.
#
# The line under audit:
#   git grep -n -a -E 'merge-base|main:|origin/main|rev-parse main|\bmain\b' "$T115" -- \
#     .softhouse/capture/t91/ \
#     .softhouse/capture/charges/bin/preconditions.sh \
#     .softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh
#
# The COMMIT ARGUMENT "$T115" is load-bearing: the population is the T115 TREE restricted to those
# three pathspecs — NOT the working tree. T234's instruments/21-r11-recall-loss.sh omits the commit
# argument, so it enumerated a different population. This script measures BOTH so the gap is visible.
set -u
cd "${1:?repo}" || { echo "FATAL: cd failed — INSTRUMENT IS VOID"; exit 2; }
T91=ccf3c14171dea52bd044d81d5ca67aba8054b74c
T115=bd59187cf83c7c7161db23668e91d45bd46be2a8
P1=.softhouse/capture/t91/
P2=.softhouse/capture/charges/bin/preconditions.sh
P3=.softhouse/capture/audit-t44/charges/bin/preconditions-COPY.sh

echo "PWD=$(pwd)"
echo "HEAD=$(git rev-parse HEAD)"
echo "T115=$T115  type=$(git cat-file -t $T115 2>&1)"
echo "T115 is an ancestor of HEAD? -> $(git merge-base --is-ancestor $T115 HEAD && echo YES || echo NO)"
echo "T115 subject: $(git log -1 --format=%s $T115)"
echo "T115 date   : $(git log -1 --format=%cI $T115)"
echo

echo "=================================================================="
echo "POPULATION A — the tree r11 ACTUALLY searched: T115, 3 pathspecs"
echo "=================================================================="
git ls-tree -r --name-only "$T115" -- "$P1" "$P2" "$P3" > /tmp/t239-pop-T115.txt 2>/dev/null
echo "files          : $(wc -l < /tmp/t239-pop-T115.txt | tr -d ' ')"
echo "  under $P1 : $(/usr/bin/grep -c "^${P1//\//\\/}" /tmp/t239-pop-T115.txt || true)"
echo "  $P2 present? : $(/usr/bin/grep -qx "$P2" /tmp/t239-pop-T115.txt && echo YES || echo NO)"
echo "  $P3 present? : $(/usr/bin/grep -qx "$P3" /tmp/t239-pop-T115.txt && echo YES || echo NO)"
tot=0
while read -r f; do
  n=$(git show "$T115:$f" 2>/dev/null | wc -l | tr -d ' ')
  tot=$((tot+n))
done < /tmp/t239-pop-T115.txt
echo "TOTAL LINES in population A: $tot"
echo
echo "--- the file list (population A) ---"
cat -n /tmp/t239-pop-T115.txt
echo

echo "=================================================================="
echo "POPULATION B — what T234's instrument 21 searched: WORKING TREE"
echo "=================================================================="
git ls-files -- "$P1" "$P2" "$P3" > /tmp/t239-pop-HEAD.txt 2>/dev/null
echo "files          : $(wc -l < /tmp/t239-pop-HEAD.txt | tr -d ' ')"
tot2=0
while read -r f; do
  n=$(wc -l < "$f" 2>/dev/null | tr -d ' '); n=${n:-0}
  tot2=$((tot2+n))
done < /tmp/t239-pop-HEAD.txt
echo "TOTAL LINES in population B: $tot2"
echo

echo "=================================================================="
echo "A vs B — are they the same population?"
echo "=================================================================="
echo "files only in A (T115) : $(comm -23 /tmp/t239-pop-T115.txt /tmp/t239-pop-HEAD.txt | wc -l | tr -d ' ')"
echo "files only in B (HEAD) : $(comm -13 /tmp/t239-pop-T115.txt /tmp/t239-pop-HEAD.txt | wc -l | tr -d ' ')"
echo "files in both          : $(comm -12 /tmp/t239-pop-T115.txt /tmp/t239-pop-HEAD.txt | wc -l | tr -d ' ')"
echo
echo "--- only in A ---"; comm -23 /tmp/t239-pop-T115.txt /tmp/t239-pop-HEAD.txt | sed 's/^/    /'
echo "--- only in B ---"; comm -13 /tmp/t239-pop-T115.txt /tmp/t239-pop-HEAD.txt | sed 's/^/    /'
echo
echo "--- of the files in BOTH, how many differ in content between T115 and HEAD? ---"
d=0; s=0
while read -r f; do
  a=$(git rev-parse "$T115:$f" 2>/dev/null)
  b=$(git hash-object "$f" 2>/dev/null)
  if [ "$a" = "$b" ]; then s=$((s+1)); else d=$((d+1)); fi
done < <(comm -12 /tmp/t239-pop-T115.txt /tmp/t239-pop-HEAD.txt)
echo "    identical: $s    differing: $d"
