#!/bin/bash
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
echo "### does THIS worktree contain .claude/worktrees?"
ls -d .claude/worktrees 2>&1 | head -1
echo "### is the pinned Fineract checkout inside the repo?"
find . -maxdepth 3 -type d -name 'fineract*' -not -path './.git/*' 2>/dev/null | head
echo "### probe line present on the two RED (guard-failure) runs?"
for f in /tmp/t184-red-float.txt /tmp/t184-red-catch.txt; do
  printf '%-30s probe lines: %s   exit-2 text: %s\n' "$f" \
    "$(grep -c 'probe = ' "$f")" "$(grep -c 'HARD guard failed' "$f")"
done
echo "### exit-2 from a GENUINE oracle outage — probe line MUST be present"
CONFORMANCE_ORACLE_HEALTH_URL=https://127.0.0.1:1/health bash .softhouse/conformance.sh > /tmp/t184-outage.txt 2>&1
echo "EXIT=$?"
grep -n 'probe = \|UNREACHABLE\|HARD guard\|VERDICT' /tmp/t184-outage.txt | head
echo "### go build / go test"
cd "$W/nexus" && go build ./... && echo "build rc=0"
go test ./... 2>&1 | tail -8
