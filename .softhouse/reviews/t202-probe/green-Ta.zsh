#!/bin/zsh
# T202 GREEN for T-a. Runs the SAME scenario matrix against
#   PRE   = the shipped pre-fix bytes  (sed -n '260,274p' of main's file)
#   POST  = the patched bytes          (sed -n '354,411p' of the branch file)
#   MUT-A = POST with the rc test INVERTED
#   MUT-B = POST with WS_RC captured from the WRONG command
#   MUT-C = POST that logs the rc but still silently `continue`s (no ERROR)
# P-50: the harness must FAIL the mutants, not merely pass the fix -- otherwise
# it is a demonstration, not a regression test.
set -uo pipefail
S=/tmp/t202/scratch
STAMP=GREEN-000000
LOGBUF=""
log() { LOGBUF="$LOGBUF$*"$'\n'; }

PASS=0; FAIL=0; CHECKED=0
ck() {  # ck <variant> <scenario> <what> <expected> <actual>
  (( CHECKED++ ))
  if [[ "$4" == "$5" ]]; then (( PASS++ )); print -r -- "    ok   [$1/$2] $3 = $5"
  else (( FAIL++ ));            print -r -- "    FAIL [$1/$2] $3: expected $4, got $5"; fi
}

build() {   # build <shape>
  rm -rf "$S"; mkdir -p "$S/main"
  cd "$S/main" || exit 1
  git init -q -b main
  git -c user.name=t202 -c user.email=t202@example.com commit -q --allow-empty -m init
  case "$1" in
    space) git worktree add -q -b wk-a "$S/wt with space" >/dev/null 2>&1 ;;
    *)     git worktree add -q -b wk-a "$S/wt-a" >/dev/null 2>&1
           git worktree add -q -b wk-b "$S/wt-b" >/dev/null 2>&1 ;;
  esac
  case "$1" in
    healthy)  print -r -- "4482 insertions" > "$S/wt-a/handoff.md"
              print -r -- "DEC-1 retry"     > "$S/wt-b/handoff.md" ;;
    corrupt)  print -r -- "4482 insertions" > "$S/wt-a/handoff.md"
              print -r -- "DEC-1 retry"     > "$S/wt-b/handoff.md"
              print -r -- GARBAGE > "$S/wt-b/.git" ;;
    badindex) print -r -- "4482 insertions" > "$S/wt-a/handoff.md"
              print -r -- "DEC-1 retry"     > "$S/wt-b/handoff.md"
              GD="$(git -C "$S/wt-b" rev-parse --absolute-git-dir)"
              print -r -- 'NOT-AN-INDEX-FILE-AT-ALL' > "$GD/index" ;;
    clean)    : ;;
    space)    print -r -- "work in a path with a space" > "$S/wt with space/handoff.md" ;;
  esac
}

run_variant() {   # run_variant <name> <blockfile> <shape> <cwd>
  local name=$1 block=$2 shape=$3 where=$4
  build "$shape"
  LOGBUF=""
  cd "$where" || { print -r -- "    (cwd $where missing)"; return; }
  run_block() { source "$block" }
  run_block
  cd "$S/main" 2>/dev/null || cd /tmp
}

has()   { [[ "$LOGBUF" == *"$1"* ]] && print yes || print no }
branches() { git -C "$S/main" branch --list 'softhouse/rescued-*' --format='%(refname:short)' 2>/dev/null }
nbranches() { local -a b; b=("${(@f)$(branches)}"); b=("${(@)b:#}"); print ${#b} }

for V in PRE POST MUT-A MUT-B MUT-C; do
  case $V in
    PRE)   B=/tmp/t202/prefix-sweep.zsh ;;
    POST)  B=/tmp/t202/postfix-sweep.zsh ;;
    *)     B=/tmp/t202/mut-${V#MUT-}.zsh ;;
  esac
  print -r -- "== variant $V ($B) =="

  # S1 healthy: both worktrees dirty, git fine -> both rescued, no ERROR
  run_variant $V $B healthy "$S/main"
  ck $V S1-healthy "rescue branches" 2 "$(nbranches)"
  ck $V S1-healthy "ERROR logged"    no "$(has 'ERROR')"

  # S2 corrupt gitdir pointer in wt-b -> wt-a rescued, wt-b LOUDLY unverified
  run_variant $V $B corrupt "$S/main"
  ck $V S2-corrupt "rescue branches"            1  "$(nbranches)"
  ck $V S2-corrupt "REFUSING logged for wt-b"   yes "$(has 'REFUSING to treat it as clean')"

  # S3 second failure shape: corrupt index inside the linked worktree's gitdir
  run_variant $V $B badindex "$S/main"
  ck $V S3-badindex "REFUSING logged"           yes "$(has 'REFUSING to treat it as clean')"

  # S4 both worktrees clean -> nothing rescued AND no false alarm (no crying wolf)
  run_variant $V $B clean "$S/main"
  ck $V S4-clean "rescue branches" 0  "$(nbranches)"
  ck $V S4-clean "ERROR logged"    no "$(has 'ERROR')"

  # S5 P-35: enumeration itself fails (cwd is not a repo) -> ERROR, not silence
  run_variant $V $B healthy /tmp
  ck $V S5-noenum "enumeration ERROR logged" yes "$(has 'could not enumerate worktrees')"

  # S6 worktree path containing a space -> rescued, not split into bogus paths
  run_variant $V $B space "$S/main"
  ck $V S6-space "rescue branches" 1 "$(nbranches)"
  print -r -- ""
done

print -r -- "CHECKS INSPECTED=$CHECKED  PASS=$PASS  FAIL=$FAIL"
(( CHECKED > 0 )) || { print -r -- "ERROR: zero checks inspected (P-35)"; exit 3 }
