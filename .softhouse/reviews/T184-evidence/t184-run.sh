#!/bin/bash
# T184 review harness driver
. /Users/buv/gerege-nbfi/.softhouse/bin/go-env.sh
cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-ae0f13a1bbf7c82f8
bash .softhouse/conformance.sh > /tmp/t184-run1.txt 2>&1
echo "EXIT=$?"
wc -l /tmp/t184-run1.txt
