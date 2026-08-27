#!/bin/bash
# T184: the GREEN half (P-50) -- same probe rig, money as an integer.
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
cat > "$W/.softhouse/capture/t184-probe/req/probe-body.json" <<'EOF'
{
  "locale": "en",
  "dateFormat": "dd MMMM yyyy",
  "principal": 1200000,
  "numberOfRepayments": 12
}
EOF
echo "=== GREEN run: same rig, integer minor units ==="
bash .softhouse/conformance.sh > /tmp/t184-green-float.txt 2>&1
echo "EXIT=$?"
grep -n 'CENSUS\|REFUSED\|t184-probe\|HARD guard\|probe =\|VERDICT' /tmp/t184-green-float.txt
