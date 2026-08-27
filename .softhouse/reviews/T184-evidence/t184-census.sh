#!/bin/bash
# T184: re-derive T173's census numbers under MY OWN rule, independent of the guard code.
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
CAP=.softhouse/capture

echo "=== RULE (mine): a request body is (a) *.json whose PARENT DIRECTORY is named 'req',"
echo "===              at any depth under .softhouse/capture, or (b) any *.req at any depth."
echo
echo "-- (a) *.json under a dir named req:"
find "$CAP" -type d -name req -not -path '*/.git/*' | wc -l | xargs echo "   req directories:"
find "$CAP" -type f -name '*.json' -path '*/req/*' | awk -F/ '{ if ($(NF-1)=="req") print }' | wc -l | xargs echo "   .json bodies:   "
echo "-- (b) *.req anywhere under capture:"
find "$CAP" -type f -name '*.req' | wc -l | xargs echo "   .req files:     "
echo "-- rigs (first path component under .softhouse/capture that contributes >=1 body):"
{ find "$CAP" -type f -name '*.json' -path '*/req/*' | awk -F/ '{ if ($(NF-1)=="req") print }'
  find "$CAP" -type f -name '*.req'; } | sed "s|^$CAP/||" | cut -d/ -f1 | sort -u | tee /tmp/t184-rigs.txt | wc -l | xargs echo "   rigs:           "
cat /tmp/t184-rigs.txt | tr '\n' ' '; echo
echo
echo "=== .java census, my rule: every *.java under the repo root, pruning"
echo "===   .git node_modules build .gradle AND .claude/worktrees"
find . -type f -name '*.java' \
  -not -path './.git/*' -not -path '*/node_modules/*' -not -path '*/build/*' \
  -not -path '*/.gradle/*' -not -path './.claude/worktrees/*' | tee /tmp/t184-java.txt | wc -l | xargs echo "   .java files:    "
sed 's|/[^/]*$||' /tmp/t184-java.txt | sort -u | wc -l | xargs echo "   directories:    "
echo
echo "=== independent numeric-token count with jq (a different JSON parser entirely)"
command -v jq >/dev/null 2>&1 && echo "jq present: $(jq --version)" || echo "jq ABSENT — cross-check not available"
