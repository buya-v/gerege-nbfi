#!/usr/bin/env bash
set -u
W=/tmp/t446
SRC=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3c527271d46c1b56
TIP=softhouse/T445-case-route
while pgrep -f 'queue\.sh' >/dev/null 2>&1; do sleep 15; done

echo "### v5 (member names itself, as every real checker does) — CASE, RED on main"
bash "$W/drive-t446-v5.sh" "$W/red5" "$SRC" main CASE
echo "### v5 — CASE, GREEN on the T445 tip"
bash "$W/drive-t446-v5.sh" "$W/green5" "$SRC" "$TIP" CASE
echo "### RWB3 — the decisive-lines pin evaded by one substitution, on the T445 TIP"
bash "$W/drive-rwb3.sh" "$W/rwb3" "$SRC" "$TIP" RWB3
echo "### QUEUE2 COMPLETE"
