#!/bin/zsh
# T302 attempt 2 -- F8: RE-MEASURE THE BUDGET, AND MEASURE THE SCALING T309 DID NOT.
#
# T309 measured the reconcile at ~1.25s for 8 in_progress tasks and concluded the
# handler now fits launchd's grace with ~11s of headroom. 8 is the size of ONE incident.
# reconcile() calls branch_wip() ONCE PER DEMOTED TASK and branch_wip makes TWO git
# subprocess calls (`rev-parse --verify` + `rev-list --count main..B`), so the cost is
# LINEAR IN THE NUMBER OF CORPSES, and in `wrapper` mode -- the signal path -- every
# in_progress task is a corpse. The two calls T309 counts as "not per task"
# (dispatches_predating_this_fire) are the in_session-only ones; the signal path never
# makes them and never pays that saving.
#
# The signal-path budget is  SIGNAL_GRACE_SECS - elapsed - GIT_PUSH_TIMEOUT_SECS - 2
# = 20 - ~1 - 10 - 2 = ~7s with the shipped defaults.
#
# Measure wall clock for N = 4, 8, 16, 32, 40, 64 and report where 7s is crossed.
# Wrapper mode is obtained with NO LOCK on disk (see F7) -- which is itself the finding,
# and is the only way a process running under `claude` can reach wrapper mode at all.
#
# Nothing outside $TMP is written. --dry-run. The real repo is only READ.
set -u
zmodload zsh/datetime
WT=${WT:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8}
POST=$WT/.softhouse/bin/ready-tasks.py
TRIALS=${TRIALS:-3}

print "POST (main, post-T309): sha256 $(/usr/bin/shasum -a 256 $POST | cut -c1-16)"
print "python3: $(/usr/bin/python3 -V 2>&1)   git: $(git --version)"
print "trials per N: $TRIALS   (median reported)"
print ""
print "N   median_s   min_s   max_s   git_calls(=2N)   verdict_vs_7s_signal_budget"

for N in 4 8 16 32 40 64; do
  TMP=$(mktemp -d /tmp/t302f8.XXXXXX); R=$TMP/repo
  mkdir -p $R/.softhouse/bin
  # tasks.json: take the REAL file (792 KB, 198 tasks) so JSON parse cost is real,
  # then force exactly N tasks to in_progress with a branch that EXISTS in this repo.
  git -C $WT show HEAD:.softhouse/tasks.json > $TMP/tasks.json
  /usr/bin/python3 - "$TMP/tasks.json" "$R/.softhouse/tasks.json" "$N" <<'PY'
import json, sys
src, dst, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
doc = json.load(open(src))
k = 0
for t in doc["tasks"]:
    if k < n:
        t["status"] = "in_progress"
        t["branch"] = "softhouse/costbench-%03d" % k
        k += 1
    elif t.get("status") == "in_progress":
        t["status"] = "done"
json.dump(doc, open(dst, "w"), indent=2, ensure_ascii=False)
PY
  ( cd $R
    git init -q -b main .
    git config user.email t302@local
    git config user.name T302
    git add -A; git commit -q -m "base"
    for i in {0..$((N-1))}; do
      B=$(printf 'softhouse/costbench-%03d' $i)
      git branch -q "$B" main
      git checkout -q "$B"
      print "wip $i" > wip.txt
      git add -A; git commit -q -m "wip $i"
      git checkout -q main
    done
  ) >/dev/null 2>&1
  cp $POST $R/.softhouse/bin/ready-tasks.py
  # NO .softhouse/LOCK -> wrapper mode -> all N demoted -> branch_wip runs N times.
  local -a times; times=()
  for trial in {1..$TRIALS}; do
    S=$EPOCHREALTIME
    /usr/bin/python3 $R/.softhouse/bin/ready-tasks.py --reconcile --fire COST \
        --dry-run --repo "$R" > $TMP/out.$trial 2>&1
    E=$EPOCHREALTIME
    times+=( $(printf '%.3f' $((E-S))) )
  done
  D=$(grep -c "in_progress -> needs_retry" $TMP/out.1)
  SORTED=($(print -l $times | sort -n))
  MED=${SORTED[$(( (TRIALS+1)/2 ))]}
  MIN=${SORTED[1]}; MAX=${SORTED[-1]}
  if (( MED > 7 )); then V="OVER the ~7s signal budget"; else V="fits"; fi
  printf '%-3s %-10s %-7s %-7s %-16s %s\n' "$N" "$MED" "$MIN" "$MAX" "$((2*N))" "$V"
  [[ "$D" == "$N" ]] || print "    !! demoted $D, expected $N -- cell is not measuring what it claims"
  rm -rf $TMP
done

print ""
print "=== control: the same N=8 run with the WIP evidence suppressed (no branches) ==="
print "    (isolates the per-task git cost from the 792 KB JSON parse)"
TMP=$(mktemp -d /tmp/t302f8b.XXXXXX); R=$TMP/repo
mkdir -p $R/.softhouse/bin
git -C $WT show HEAD:.softhouse/tasks.json > $TMP/tasks.json
/usr/bin/python3 - "$TMP/tasks.json" "$R/.softhouse/tasks.json" 0 <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
for t in doc["tasks"]:
    if t.get("status") == "in_progress":
        t["status"] = "done"
json.dump(doc, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
PY
( cd $R; git init -q -b main .; git config user.email t@l; git config user.name T
  git add -A; git commit -q -m base ) >/dev/null 2>&1
cp $POST $R/.softhouse/bin/ready-tasks.py
S=$EPOCHREALTIME
/usr/bin/python3 $R/.softhouse/bin/ready-tasks.py --reconcile --fire COST --dry-run --repo "$R" >/dev/null 2>&1
E=$EPOCHREALTIME
printf '    N=0 (parse + startup only): %.3fs\n' $((E-S))
rm -rf $TMP
