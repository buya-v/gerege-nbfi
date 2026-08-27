#!/bin/zsh
# T302 attempt 2 -- F9: THE RECONCILER DRIVEN AGAINST THE REAL KILLED WORKERS' REAL REFS.
#
# The brief's central claim is that none of this has been driven against a REAL killed
# `claude` worker with a real worktree and a real dispatch. T309's matrix builds a fresh
# `git init` repo per cell and plants tasks.json blobs in it -- real BLOBS, but NO real
# REFS, so every branch_wip() call in those cells answers "absent" for a reason that has
# nothing to do with the corpse. The WIP evidence -- which is the whole content of the
# note T288 exists to write -- was never once graded against a real branch.
#
# This removes the substitution: a `--shared` clone of THIS repo with EVERY head fetched
# (528 refs), so the corpse branches are REAL refs with REAL objects, and tasks.json is
# the REAL blob committed at fire 20260823-140001's lock commit.
#
# Cell 1: in_session against the real corpses (LOCK carries `fire`).
# Cell 2: wrapper mode -- the SIGNAL path's mode -- against the same.
# Cell 3: ground truth for every WIP line cell 2 printed.
#
# Nothing outside $TMP is written. --dry-run throughout. The real repo's `.softhouse/LOCK`
# is never written or removed. No signal is sent to any process.
set -u
zmodload zsh/datetime
WT=${WT:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8}
POST=$WT/.softhouse/bin/ready-tasks.py
CORPSES=(T297 T298 T299 T302 T304 T305 T306 T308)

TMP=$(mktemp -d /tmp/t302f9.XXXXXX); R=$TMP/repo
T0=$EPOCHREALTIME
git clone -q --shared --no-checkout "$WT" "$R" || exit 1
git -C $R symbolic-ref HEAD refs/heads/t302-scratch
git -C $R fetch -q --no-tags "$WT" '+refs/heads/*:refs/heads/*' || exit 1
T1=$EPOCHREALTIME
printf 'clone + fetch: %.2fs   heads: %s\n' $((T1-T0)) \
    "$(git -C $R for-each-ref --format='%(refname)' refs/heads | wc -l | tr -d ' ')"
git -C $R symbolic-ref HEAD refs/heads/main
git -C $R read-tree --reset -u HEAD
# the state as fire 20260823-140001 FOUND it: 8 inherited in_progress claims
git -C $WT show 5428c0a4:.softhouse/tasks.json > $R/.softhouse/tasks.json
# and the lock commit the discriminator anchors on, on THIS clone's history
git -C $R log -1 --format='    anchor: %h %s' --fixed-strings \
    --grep 'softhouse: local fire lock (20260823-140001)'
cp $POST $R/.softhouse/bin/ready-tasks.py
print ""

run() {   # run <label> <lockjson-or-NONE>
  local label=$1 lockjson=$2
  print "############################################################"
  print "# $label"
  print "############################################################"
  if [[ "$lockjson" == NONE ]]; then rm -f $R/.softhouse/LOCK
  else print -r -- "$lockjson" > $R/.softhouse/LOCK; fi
  local T0=$EPOCHREALTIME
  /usr/bin/python3 $R/.softhouse/bin/ready-tasks.py --reconcile \
      --fire 20260823-140001 --dry-run --repo "$R" 2>&1 | sed 's/^/    /'
  local T1=$EPOCHREALTIME
  printf '\n    wall clock: %.3fs for 8 REAL corpses against 528 REAL refs\n\n' $((T1-T0))
}

run "CELL 1 -- in_session, LOCK carries fire 20260823-140001 (ancestor pid = this zsh)" \
    '{ "holder":"local-launchd", "host":"'$(hostname -s)'", "pid":'$$', "fire":"20260823-140001" }'

run "CELL 2 -- wrapper mode (the SIGNAL path's mode): NO LOCK on disk (F7)" NONE

print "############################################################"
print "# CELL 3 -- GROUND TRUTH for the WIP evidence printed above"
print "############################################################"
printf '    %-48s %-8s %-10s %s\n' BRANCH ahead merged verdict
for T in $CORPSES; do
  B=$(git -C $WT show 5428c0a4:.softhouse/tasks.json | /usr/bin/python3 -c \
      'import json,sys; d=json.load(sys.stdin); print(next((t.get("branch") or "" for t in d["tasks"] if t["id"]==sys.argv[1]), ""))' "$T")
  [[ -n "$B" ]] || { printf '    %-48s %s\n' "(none recorded for $T)" -; continue; }
  if ! git -C $R rev-parse --verify --quiet "$B^{commit}" >/dev/null; then
    printf '    %-48s %-8s %-10s %s\n' "$B" "-" "-" "REF ABSENT"
    continue
  fi
  N=$(git -C $R rev-list --count "main..$B")
  if git -C $R merge-base --is-ancestor "$B" main; then M=MERGED; else M=unmerged; fi
  if [[ "$N" == 0 && "$M" == MERGED ]]; then V="F1 CASE: note will say 'nothing was ever committed'"
  elif [[ "$N" == 0 ]]; then V="genuinely empty"
  else V="has WIP"; fi
  printf '    %-48s %-8s %-10s %s\n' "$B" "$N" "$M" "$V"
done

rm -rf $TMP
