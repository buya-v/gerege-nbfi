#!/bin/zsh
# T336 P2 — what reflog signature does a real `git worktree add` leave, and does the
# harness's worktree admin dir match it? If it does not, the harness may not be using
# `git worktree add` at all, and a post-checkout hook would never fire on the real route.
set -u
GIT=/usr/bin/git
T=$(mktemp -d /tmp/t336-sig.XXXXXX)
$GIT init -q --bare "$T/remote.git"
$GIT clone -q "$T/remote.git" "$T/repo" 2>/dev/null
R="$T/repo"
$GIT -C "$R" config user.email t336@local
$GIT -C "$R" config user.name T336
print hi > "$R/a.txt"
$GIT -C "$R" add -A >/dev/null
$GIT -C "$R" commit -qm base
$GIT -C "$R" push -q -u origin HEAD:main

print "===== A. plain: git worktree add -b worktree-agent-FAKE <path> origin/main ====="
cd "$R"
$GIT worktree add -b worktree-agent-FAKE "$T/wtA" origin/main >/dev/null 2>&1
print "  .git/worktrees/wtA/HEAD          : $(cat "$R/.git/worktrees/wtA/HEAD")"
print "  .git/worktrees/wtA/logs/HEAD     :"
sed 's/^/      /' "$R/.git/worktrees/wtA/logs/HEAD"
print "  .git/logs/refs/heads/worktree-agent-FAKE:"
sed 's/^/      /' "$R/.git/logs/refs/heads/worktree-agent-FAKE"
print "  admin dir contents: $(ls "$R/.git/worktrees/wtA" | tr '\n' ' ')"

print "\n===== B. plus a 'git reset --hard HEAD' inside it (what the harness seems to do next) ====="
cd "$T/wtA"
$GIT reset -q --hard HEAD
print "  logs/HEAD now:"
sed 's/^/      /' "$R/.git/worktrees/wtA/logs/HEAD"

print "\n===== C. the REAL harness worktree, for comparison ====="
W=/Users/buv/gerege-nbfi/.git/worktrees/agent-ac0beb58b1e2738ea
print "  HEAD       : $(cat $W/HEAD)"
print "  logs/HEAD  :"
sed 's/^/      /' "$W/logs/HEAD"
print "  branch reflog:"
sed 's/^/      /' /Users/buv/gerege-nbfi/.git/logs/refs/heads/worktree-agent-ac0beb58b1e2738ea
print "  admin dir contents: $(ls $W | tr '\n' ' ')"

print "\nscratch: $T"
