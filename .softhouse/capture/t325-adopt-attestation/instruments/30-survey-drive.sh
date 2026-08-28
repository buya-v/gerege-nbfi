#!/usr/bin/env bash
# T325 instrument 30 — the PRE-FLIGHT gate's arms.
#
# `repo-state-attest.sh survey` is what fire-program.sh now runs before it takes
# the lock, and it is the command the (unmade, specified) SKILL.md pre-flight
# change would run. It is single-state by necessity: at pre-flight there is no
# "before" to be differential against.
#
# THE FALSE-POSITIVE ARMS ARE THE POINT. A pre-flight check that shouts on a
# `.DS_Store`, on `.softhouse/LOCK`, on the ignored `.claude/worktrees/` and
# `.softhouse/toolchain/` trees, or on a stash somebody took in a different
# worktree, is a check the next fire comments out. Every G arm below is a state
# this repository is in RIGHT NOW, and every one of them must be 0.
set -uo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(cd -- "$HERE/../../../.." && pwd -P)
GUARD="$REPO_ROOT/.softhouse/guards/repo-state-attest.sh"
[ -r "$GUARD" ] || { echo "REFUSED: guard not readable at $GUARD"; exit 2; }

ROOT=$(mktemp -d /private/tmp/t325-survey-XXXXXX) || exit 2
ROOT=$(cd -- "$ROOT" && pwd -P)
case "$ROOT" in "$REPO_ROOT"*) echo "REFUSED: scratch root inside the repo"; exit 2 ;; esac
echo "scratch: $ROOT"; echo "git: $(git --version)"; echo

PASS=0; FAIL=0; declare -a FAILED=()

mkrepo() {
  local d="$ROOT/$1"
  git init -q -b main "$d" >/dev/null 2>&1 || return 1
  (
    cd "$d" || exit 1
    git config user.name Buyan; git config user.email buya.vol@gmail.com
    mkdir -p .softhouse
    printf '{"tasks":[]}\n' > .softhouse/tasks.json
    printf 'work\n' > worker-output.txt
    # The fixture's ignore rules mirror the SHAPE of this repo's (a dropping, a
    # per-agent layout dir, a reproducible toolchain tree) without reusing the
    # repo's own path literals: T316/T326's dead-path frontier guard counts a
    # repo-shaped path in a tracked instrument as a dead reference, and a fixture
    # string is not a reference to anything. [Measured: the first version of this
    # file added 3 frontier rows and drove `bash .softhouse/conformance.sh` to
    # EXIT 2 with NO probe line -- a failed HARD guard, per P-84.]
    printf '.DS_Store\nfixture-agents/\nfixture-toolchain/\n' > .gitignore
    git add -A; git commit -q -m init
  ) || return 1
  printf '%s' "$d"
}

run() {
  local name="$1" expect="$2" target="$3"
  local out rc
  out=$(bash "$GUARD" survey "$target" --label "$name" 2>&1); rc=$?
  printf '%s\n' "$out" > "$ROOT/$name.txt"
  if [ "$rc" = "$expect" ]; then
    echo "ARM $name: PASS  rc=$rc (expected $expect)"
    PASS=$((PASS+1))
  else
    echo "ARM $name: FAIL  rc=$rc (expected $expect)"
    printf '%s\n' "$out" | sed 's/^/      /'
    FAIL=$((FAIL+1)); FAILED+=("$name")
  fi
  printf '%s\n' "$out" | grep -E 'VERDICT|ADVISORY|HIDDEN WORK|legacy' | sed 's/^/      /'
}

echo "=== LEGITIMATE ARMS — every one must be 0 ==="

# G1 — a spotless checkout. The null control.
d=$(mkrepo g1) || exit 2
run G1_clean_checkout 0 "$d"

# G2 — untracked files of exactly the kinds the live checkout always carries:
# `.softhouse/LOCK` (the fire's own lock, written before the driver starts) and
# `.claude/settings.local.json`. UNCOMMITTED IS NOT HIDDEN: the pre-flight gate
# must not confuse "visible work sitting in the tree" with "work git has been
# told to stop looking at". A survey that returned 1 here would abort every fire.
d=$(mkrepo g2) || exit 2
mkdir -p "$d/.claude"; printf '{"host":"buyan"}\n' > "$d/.softhouse/LOCK"
printf '{}\n' > "$d/.claude/settings.local.json"
run G2_untracked_lock_and_settings 0 "$d"

# G3 — ignored droppings: `.DS_Store` and the two trees `.gitignore` itself
# declares reproducible (`.claude/worktrees/`, `.softhouse/toolchain/`).
# ADVISORY, never a vote — T318's boundary ruling (d), and T324 measured the same
# population: the ignored paths in this repo are layout and toolchain, not work.
d=$(mkrepo g3) || exit 2
printf 'junk' > "$d/.DS_Store"
mkdir -p "$d/fixture-toolchain/go/bin"; printf 'bin' > "$d/fixture-toolchain/go/bin/go"
mkdir -p "$d/fixture-agents/agent-deadbeef"; printf 'x' > "$d/fixture-agents/agent-deadbeef/f"
run G3_ignored_droppings 0 "$d"

# G4 — THE MASS FALSE POSITIVE THE STASH TERM WOULD HAVE PRODUCED. A stash is
# taken in the MAIN tree; the survey runs against a LINKED WORKTREE that never
# stashed anything. `refs/stash` is common-dir scoped [VERIFIED:
# evidence/05-stash-scope-probe.txt, git 2.50.1], so it is visible from here.
# Reported as ADVISORY with that attribution, and NOT a vote: otherwise one stash
# would light up all forty-odd worktrees of the live repo simultaneously.
d=$(mkrepo g4) || exit 2
( cd "$d" && git worktree add -q "$ROOT/g4wt" -b wt-branch && printf 'dirt\n' > worker-output.txt && git stash -q ) >/dev/null 2>&1
run G4_worktree_with_foreign_stash 0 "$ROOT/g4wt"

# G5 — THE LIVE POPULATION, read-only: this worker's own worktree of the real
# repo, 7,391 tracked files and 612 refs. A drive that only ever ran against
# four-file fixtures would not have measured the thing that actually runs.
run G5_this_live_worktree 0 "$REPO_ROOT"

echo
echo "=== HIDDEN-WORK ARMS — every one must be 1 ==="

# R1 — `--assume-unchanged`. `git status --porcelain` reports CLEAN over a file
# that has been overwritten. This is the one term the survey votes on.
d=$(mkrepo r1) || exit 2
( cd "$d" && git update-index --assume-unchanged worker-output.txt && printf 'DESTROYED\n' > worker-output.txt )
run R1_assume_unchanged 1 "$d"

# R2 — `--skip-worktree`, the other bit, which `git ls-files -v` tags `S` rather
# than lowercase. T324 settled the tag table; this arm keeps it honest.
d=$(mkrepo r2) || exit 2
( cd "$d" && git update-index --skip-worktree worker-output.txt && printf 'DESTROYED\n' > worker-output.txt )
run R2_skip_worktree 1 "$d"

echo
echo "=== REFUSAL ARMS — 'I could not measure' must never be 'clean' ==="

# X1 — a directory that is not a git repo at all.
mkdir -p "$ROOT/x1"
run X1_not_a_repo 2 "$ROOT/x1"

# X2 — a path that does not exist. Fail CLOSED: refuse, never return 0.
run X2_missing_path 2 "$ROOT/does-not-exist"

echo
echo "================================================================"
echo "TOTAL: PASS=$PASS FAIL=$FAIL"
if [ "$FAIL" -ne 0 ]; then echo "FAILED: ${FAILED[*]}"; echo "scratch kept: $ROOT"; exit 1; fi
echo "scratch kept: $ROOT"
exit 0
