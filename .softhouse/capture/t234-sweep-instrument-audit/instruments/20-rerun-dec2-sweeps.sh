#!/usr/bin/env bash
# T234 — REPRODUCIBILITY of the three sweeps behind DEC-2's "the population is closed".
# Each one hard-`cd`s into the author's own worktree. Do those worktrees still exist,
# and what does the script DO today?  This is run VERBATIM, unmodified, as committed.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a71e695cfa5bea70b

echo "### worktrees each sweep depends on"
for d in agent-a3fcb4c7f1ea451ee agent-a356a016636abdd7e agent-a5244bad2b6814a39; do
  p=/Users/buv/gerege-nbfi/.claude/worktrees/$d
  if [ -d "$p" ]; then echo "  EXISTS  $d"; else echo "  GONE    $d"; fi
done
echo "  (owner: a3fc=A2-31 probe-sweep.sh, a356=A2-32 sweep.sh, a524=A2-33 sweep.sh)"
echo

echo "### A2-31 probe-sweep.sh, run verbatim TODAY"
bash "$R/.softhouse/reviews/a2-31-dec2-rev4/probe-sweep.sh" > /tmp/t234_a231.out 2>&1
echo "  exit=$?  output lines=$(wc -l < /tmp/t234_a231.out | tr -d ' ')"
echo "  --- first 6 lines ---"; head -6 /tmp/t234_a231.out | sed 's/^/      /'
echo

echo "### A2-32 sweep.sh, run verbatim TODAY"
bash "$R/.softhouse/handoff/2026-08-21-run2-tierA-gl-accounting-A2/A2-32-evidence/sweep.sh" > /tmp/t234_a232.out 2>&1
echo "  exit=$?  output lines=$(wc -l < /tmp/t234_a232.out | tr -d ' ')"
echo "  --- first 6 lines ---"; head -6 /tmp/t234_a232.out | sed 's/^/      /'
echo

echo "### A2-33 sweep.sh, run verbatim TODAY (the sweep behind the rev-5 RATIFICATION)"
bash "$R/.softhouse/reviews/a2-33-dec2-rev5/sweep.sh" REPO > /tmp/t234_a233.out 2>&1
echo "  exit=$?  output lines=$(wc -l < /tmp/t234_a233.out | tr -d ' ')"
echo "  patterns declared : $(grep -c '^run ' "$R/.softhouse/reviews/a2-33-dec2-rev5/sweep.sh")"
echo "  patterns reporting '(no hits)' : $(grep -c '(no hits)' /tmp/t234_a233.out)"
echo "  actual match lines emitted     : $(grep -cv -e '^##########' -e '(no hits)' -e '^$' /tmp/t234_a233.out)"
echo "  --- first 12 lines ---"; head -12 /tmp/t234_a233.out | sed 's/^/      /'
