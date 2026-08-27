#!/bin/zsh
# T302 attempt 2 -- F8b: calibrate the scratch-repo cost against the REAL repo.
#
# drive-f8-cost.zsh measures in a scratch repo with one commit of history and N tiny
# branches. The real repo has a large object store and ~100 refs, and `git rev-parse
# --verify` / `git rev-list --count main..B` both pay for that. So measure the two calls
# branch_wip() actually makes, on REAL branches, in THIS worktree, and report per-call
# cost -- then N * 2 * per-call is the honest extrapolation.
#
# Read-only. No writes anywhere.
set -u
zmodload zsh/datetime
WT=${WT:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8}

print "repo: $WT"
print "refs in this repo: $(git -C $WT for-each-ref --format='%(refname)' | wc -l | tr -d ' ')"
print "packed-refs size:  $(wc -c < $WT/../../../.git/packed-refs 2>/dev/null || print '?') bytes"
print ""

BR=(${(f)"$(git -C $WT for-each-ref --format='%(refname:short)' refs/heads/softhouse | head -40)"})
print "sampling ${#BR} real softhouse/* branches"
print ""

T0=$EPOCHREALTIME
for B in $BR; do
  git -C $WT rev-parse --verify --quiet "$B^{commit}" >/dev/null
done
T1=$EPOCHREALTIME
for B in $BR; do
  git -C $WT rev-list --count "main..$B" >/dev/null
done
T2=$EPOCHREALTIME

RP=$(( (T1-T0) / ${#BR} ))
RL=$(( (T2-T1) / ${#BR} ))
printf 'git rev-parse --verify  : %.4fs per call\n' $RP
printf 'git rev-list --count    : %.4fs per call\n' $RL
printf 'branch_wip() per task   : %.4fs  (both calls)\n' $((RP+RL))
print ""
for N in 8 40 64 100; do
  printf 'extrapolated N=%-4s      : %.2fs of git + ~0.11s startup/parse\n' $N $(( N*(RP+RL) ))
done
print ""
print "signal-path budget with shipped defaults:"
print "  SIGNAL_GRACE_SECS(20) - elapsed(~1) - GIT_PUSH_TIMEOUT_SECS(10) - 2 = ~7s"
