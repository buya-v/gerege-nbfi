#!/bin/zsh
# T302 attempt 2 -- F6: the discriminator's ANCHOR IS A SUBSTRING SEARCH OVER PROSE,
# and `git log -1` takes the NEWEST match.
#
# ready-tasks.py:dispatches_predating_this_fire() locates the lock instant with
#     git log -1 --format=%H --fixed-strings --grep "softhouse: local fire lock (<id>)"
# `--grep` matches ANYWHERE in the commit message -- subject OR body -- and `-1` returns
# the newest match. So ANY later commit whose message merely QUOTES that string becomes
# the anchor, and the blob read is that later commit's tasks.json, which contains this
# fire's OWN dispatches. Every one of them then reads as "already in_progress at the
# lock instant" = a corpse.
#
# The population that writes such messages is REVIEWERS AND HANDOFFS DESCRIBING THIS
# MECHANISM. T309's own merge commit quotes the subject with a `<id>` placeholder; a
# reviewer who quotes it with a REAL id arms this.
#
# Three cells:
#   1  BASELINE   only the real lock commit exists.               -> correct
#   2  BODY QUOTE a later commit whose BODY quotes the subject.   -> ?
#   3  --grep vs --grep on subject only                            (control)
#
# Nothing outside $TMP is written. The real repo is only READ. No signal is sent.
set -u
WT=${WT:-/Users/buv/gerege-nbfi/.claude/worktrees/agent-a3e635faba72121c8}
POST=$WT/.softhouse/bin/ready-tasks.py
FIRE=20260823-140001

print "POST (main, post-T309): sha256 $(/usr/bin/shasum -a 256 $POST | cut -c1-16)"
print ""

build() {   # build <repo-dir> <extra-commit-message-or-empty>
  local R=$1 EXTRA=$2
  mkdir -p $R/.softhouse/bin
  ( cd $R
    git init -q .
    git config user.email t302@local
    git config user.name T302
    # 1. the fire's REAL lock commit: 8 inherited corpses, nothing dispatched yet
    git -C $WT show 5428c0a4:.softhouse/tasks.json > .softhouse/tasks.json
    git add -A; git commit -q -m "softhouse: local fire lock ($FIRE)"
    # 2. the fire dispatches. tasks.json now records ITS OWN live workers.
    git -C $WT show 5964ab54:.softhouse/tasks.json > .softhouse/tasks.json
    git add -A; git commit -q -m "DISPATCH fire $FIRE batch 1"
    # 3. optionally, a reviewer commit that merely TALKS about the lock commit
    if [[ -n "$EXTRA" ]]; then
      mkdir -p .softhouse/reviews/TXXX
      print "a review" > .softhouse/reviews/TXXX/REVIEW.md
      git add -A; git commit -q -m "$EXTRA"
    fi
  )
  print '{ "holder":"local-launchd", "host":"'$(hostname -s)'", "pid":'$PPID', "fire":"'$FIRE'" }' \
    > $R/.softhouse/LOCK
  cp $POST $R/.softhouse/bin/ready-tasks.py
}

run() {   # run <name> <extra-msg> <correct>
  local name=$1 extra=$2 correct=$3
  local TMP R out n anchor
  TMP=$(mktemp -d /tmp/t302f6.XXXXXX); R=$TMP/repo
  build $R "$extra"
  print "############################################################"
  print "# $name"
  print "#   correct answer: demote $correct  (all 8 in_progress are this fire's LIVE workers)"
  print "############################################################"
  anchor=$(git -C $R log -1 --format='%h %s' --fixed-strings \
             --grep "softhouse: local fire lock ($FIRE)")
  print "    anchor commit the resolver will pick: $anchor"
  out=$(/usr/bin/python3 $R/.softhouse/bin/ready-tasks.py --reconcile \
          --fire "$FIRE" --dry-run --repo "$R" 2>&1)
  n=$(print -r -- "$out" | grep -c "in_progress -> needs_retry")
  print -r -- "$out" | grep -E "in-session evidence|IN-SESSION authority|RESULT:" | sed 's/^/    /'
  if ! print -r -- "$out" | grep -q "RESULT:"; then
    print "    >>> **VACUOUS** -- no RESULT line. Raw:"; print -r -- "$out" | sed 's/^/      | /'
  elif [[ "$n" == "$correct" ]]; then
    print "    >>> OK (demotions=$n)"
  else
    print "    >>> **WRONG** (demotions=$n, correct $correct)"
  fi
  rm -rf $TMP
  print ""
}

run "CELL 1 BASELINE -- only the real lock commit carries that string" \
    "" 0

run "CELL 2 BODY QUOTE -- a later REVIEW commit quotes the subject in its BODY" \
    "T302: review of the lock-commit discriminator

The anchor it looks for is the commit whose subject is
softhouse: local fire lock ($FIRE)
and I checked that it is unique in this repo." 0

run "CELL 3 SUBJECT REUSE -- a second lock commit for the same fire id (re-acquire)" \
    "softhouse: local fire lock ($FIRE)" 0
