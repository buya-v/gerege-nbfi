#!/bin/bash
# T184: drive the wire-float guard RED through the REAL harness (not the selftest).
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
W=/Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
cd "$W"
mkdir -p "$W/.softhouse/capture/t184-probe/req"
cat > "$W/.softhouse/capture/t184-probe/req/probe-body.json" <<'EOF'
{
  "locale": "en",
  "dateFormat": "dd MMMM yyyy",
  "principal": 1200000.00,
  "numberOfRepayments": 12
}
EOF
echo "=== RED run: probe body carries 1200000.00 ==="
bash .softhouse/conformance.sh > /tmp/t184-red-float.txt 2>&1
echo "EXIT=$?"
grep -n 'CENSUS\|REFUSED\|t184-probe\|HARD guard\|probe =\|VERDICT' /tmp/t184-red-float.txt
