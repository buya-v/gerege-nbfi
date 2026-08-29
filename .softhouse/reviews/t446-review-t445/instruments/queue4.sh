#!/usr/bin/env bash
set -u
W=/tmp/t446
SRC=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3c527271d46c1b56
TIP=softhouse/T445-case-route
while pgrep -f 'queue3\.sh' >/dev/null 2>&1; do sleep 15; done
echo "### RWB3 CONTROL — the same M-1 fixture on the UNMUTATED T445 tip (must refuse)"
bash "$W/drive-rwb3-v2.sh" "$W/rwb3" "$SRC" "$TIP" RWB3CONTROL
echo "### RWB3 — the decisive-lines pin evaded by ONE substitution, on the T445 TIP"
bash "$W/drive-rwb3-v2.sh" "$W/rwb3" "$SRC" "$TIP" RWB3
echo "### QUEUE4 COMPLETE"
