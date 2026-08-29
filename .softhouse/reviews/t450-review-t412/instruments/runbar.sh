#!/bin/bash
cd /Users/buv/gerege-nbfi/.claude/worktrees/agent-a62c36acdc958c697 || exit 9
date '+%H:%M:%S' > /tmp/t450/bar1-start.txt
S=$(date +%s)
bash .softhouse/conformance.sh > /tmp/t450/bar-run1.log 2>&1
RC=$?
E=$(date +%s)
echo "EXIT=$RC" >> /tmp/t450/bar-run1.log
echo "WALL_SECONDS=$((E-S))" >> /tmp/t450/bar-run1.log
echo "RC=$RC WALL=$((E-S))" > /tmp/t450/bar1-done.txt
