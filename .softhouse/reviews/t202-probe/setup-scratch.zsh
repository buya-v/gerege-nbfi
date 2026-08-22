#!/bin/zsh
# T202 -- builds a scratch main repo with TWO linked worktrees, each holding
# genuinely stranded worker deliverables. Entirely under /tmp; never touches
# /Users/buv/gerege-nbfi or its live .softhouse/LOCK.
set -uo pipefail
S=/tmp/t202/scratch
rm -rf "$S"; mkdir -p "$S/main"
cd "$S/main" || exit 1
git init -q -b main
git -c user.name=t202 -c user.email=t202@example.com commit -q --allow-empty -m init
mkdir -p .softhouse/handoff docs
print -r -- baseline > .softhouse/tasks.json
print -r -- baseline > docs/baseline.md
git add .softhouse/tasks.json docs/baseline.md
git -c user.name=t202 -c user.email=t202@example.com commit -q -m baseline

# two linked worktrees, as a real fire has
git worktree add -q -b wk-healthy  "$S/wt-healthy"  >/dev/null 2>&1
git worktree add -q -b wk-broken   "$S/wt-broken"   >/dev/null 2>&1

# stranded worker deliverables inside each
print -r -- "4482 insertions of real work" > "$S/wt-healthy/handoff.md"
print -r -- "an entire DEC-1 retry"        > "$S/wt-broken/handoff.md"
print -r -- "vector capture"               > "$S/wt-broken/vector.json"
print -r -- "Scratch built at $S"
