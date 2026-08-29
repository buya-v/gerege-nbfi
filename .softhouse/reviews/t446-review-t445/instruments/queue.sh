#!/usr/bin/env bash
# T446: run the remaining arms STRICTLY SEQUENTIALLY. Parallel bar runs starved the
# reference-oracle container into a SIGTERM once already; that outage is recorded in
# the review rather than hidden, and this runner exists so it does not recur.
set -u
W=/tmp/t446
SRC=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3c527271d46c1b56
TIP=softhouse/T445-case-route

# wait for anything still in flight
while pgrep -f 'drive-t446-v3.sh' >/dev/null 2>&1; do sleep 10; done

echo "### RED (unmutated main) — CASE and MCASE, re-driven with the v4 plant"
bash "$W/drive-t446-v4.sh" "$W/red2" "$SRC" main CASE MCASE

echo "### RED (unmutated main) — LEGDIRTY and WDIRTY re-driven with the oracle back up"
bash "$W/drive-t446-v4.sh" "$W/red3" "$SRC" main LEGDIRTY WDIRTY

echo "### GREEN (the T445 tip)"
bash "$W/drive-t446-v4.sh" "$W/green" "$SRC" "$TIP" Z LEGA CASE MCASE LEGDIRTY WDIRTY CDIRTY WGONE

echo "### SIXTH ROUTE — control, then the long-s harness substitution, on the T445 TIP"
bash "$W/drive-longs.sh" "$W/longs" "$SRC" "$TIP" CONTROL
bash "$W/drive-longs.sh" "$W/longs" "$SRC" "$TIP" LONGS
echo "### QUEUE COMPLETE"
