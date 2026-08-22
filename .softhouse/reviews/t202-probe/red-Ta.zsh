#!/bin/zsh
# T202 RED for T-a: the shipped worktree sweep reads a FAILING git as a CLEAN
# worktree and silently `continue`s, abandoning stranded deliverables.
# Runs the SHIPPED BYTES (sed -n '260,274p' of fire-program.sh) verbatim.
set -uo pipefail
S=/tmp/t202/scratch
STAMP=RED0000-000000
log() { print -r -- "  [log] $*" }

/bin/zsh /tmp/t202/setup-scratch.zsh >/dev/null

print -r -- "=== A. baseline: what git says about each worktree (both healthy) ==="
for W in "$S/wt-healthy" "$S/wt-broken"; do
  print -r -- "  $(basename $W):"
  git -C "$W" status --porcelain | sed 's/^/    /'
done

print -r -- ""
print -r -- "=== B. CORRUPT wt-broken's gitdir pointer, then measure the shipped expression ==="
print -r -- "GARBAGE-NOT-A-GITDIR-POINTER" > "$S/wt-broken/.git"
print -r -- "  wt-broken/.git now: $(cat "$S/wt-broken/.git")"

git -C "$S/wt-broken" status --porcelain
RC_BARE=$?
print -r -- "  bare   git -C wt-broken status --porcelain          rc=$RC_BARE"

WD=$(git -C "$S/wt-broken" status --porcelain | wc -l | tr -d ' ')
RC_PIPE=$?
print -r -- "  shipped  ... | wc -l | tr -d ' '   WD=[$WD]  pipeline rc=$RC_PIPE  pipestatus=(${pipestatus[@]})"
if (( WD == 0 )); then
  print -r -- "  shipped guard verdict: WD==0 -> continue   *** WORKTREE TREATED AS CLEAN - FAIL-OPEN ***"
else
  print -r -- "  shipped guard verdict: would rescue"
fi

print -r -- ""
print -r -- "=== C. drive the SHIPPED loop end to end over the real worktree list ==="
cd "$S/main" || exit 1
source /tmp/t202/prefix-sweep.zsh
print -r -- ""
print -r -- "=== D. did the stranded work survive? ==="
print -r -- "  rescue branches created in the main repo:"
git -C "$S/main" branch --list 'softhouse/rescued-*' | sed 's/^/    /'
print -r -- "  (empty above == none)"
print -r -- "  wt-broken/handoff.md still uncommitted on disk: $([[ -f $S/wt-broken/handoff.md ]] && print YES || print no)"
