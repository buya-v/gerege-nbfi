#!/usr/bin/env bash
cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-a71e695cfa5bea70b || exit 9
. .softhouse/bin/go-env.sh
bash .softhouse/conformance.sh --prove
echo "PROVE_EXIT=$?"
