#!/bin/bash
# T302 attempt 2 — F5 REPRODUCTION, read-only, against the REAL repo history.
#
# CLAIM UNDER TEST (T309, ready-tasks.py:dispatches_predating_this_fire):
#   "The wrapper commits tasks.json as it stood the moment it took the lock ...
#    At that instant this fire has dispatched NOTHING -- so every task claiming
#    in_progress in THAT blob is a claim inherited from an earlier fire"
#
# COUNTER-CLAIM: a fire that INHERITS in_progress claims and then RE-DISPATCHES
# those same task ids has live workers whose ids are in the lock blob. The
# discriminator calls every one of them a corpse.
#
# Subject: fire 20260823-140001, the exact incident T309 was written for.
set -u
R=/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8
G="git -C $R"

echo "=== 1. fire 20260823-140001's lock commit and the blob the discriminator reads ==="
$G log -1 --format='%H %ad%n    %s' --date=iso --fixed-strings \
   --grep 'softhouse: local fire lock (20260823-140001)'
echo
python3 "$R/.softhouse/reviews/T302/a2/cmp-lockset.py" 5428c0a4 5964ab54
echo
echo "=== 2. the NEXT tasks.json commit of that same fire ==="
$G log -1 --format='%H %ad%n    %s' --date=iso 5964ab54
echo
echo "=== 3. GROUND TRUTH: did fire 20260823-140001 put LIVE workers on those ids? ==="
echo "--- commits authored during fire 20260823-140001 on the branches of tasks"
echo "--- that were ALREADY in_progress at that fire's own lock commit:"
for B in softhouse/T302-review-t288 softhouse/T298-review-t256 \
         softhouse/T297-review-t295 softhouse/T306-adjudicate-admit-widening \
         softhouse/T308-review-t292; do
  N=$($G rev-list --count "main..$B" 2>/dev/null || echo "?")
  D=$($G log -1 --format='%ad' --date=iso "$B" 2>/dev/null || echo "?")
  echo "  $B  commits-ahead=$N  head-date=$D"
done
echo
echo "=== 4. VERDICT ==="
echo "If (3) shows commits dated 2026-08-23 AFTER the lock commit's timestamp on"
echo "branches whose task ids appear in (1)'s 'DEMOTABLE' list, then the"
echo "discriminator classifies LIVE workers of the lock-holding fire as corpses."
