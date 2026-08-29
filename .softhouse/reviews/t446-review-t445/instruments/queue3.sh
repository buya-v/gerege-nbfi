#!/usr/bin/env bash
set -u
W=/tmp/t446
SRC=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3c527271d46c1b56
TIP=softhouse/T445-case-route
while pgrep -f 'queue2\.sh' >/dev/null 2>&1; do sleep 15; done
echo "### SIXTH ROUTE re-driven with the reference oracle back up"
bash "$W/drive-longs.sh" "$W/longs2" "$SRC" "$TIP" CONTROL
bash "$W/drive-longs.sh" "$W/longs2" "$SRC" "$TIP" LONGS
echo "### QUEUE3 COMPLETE"
