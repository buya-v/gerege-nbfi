#!/bin/zsh
# T279 — drive the F-7 push-before-spawn hook RED then GREEN, in SCRATCH CLONES ONLY.
#
# Reproduces the exact 101-second window T265 measured: LOCK and RESUME.md pushed on time,
# `tasks.json` (the machine-readable dispatch record) committed but NOT pushed, and the
# first `git worktree add` fired anyway. RED must catch it; GREEN must be silent after the
# push. Then the same again with SOFTHOUSE_PUSH_GATE=enforce, to MEASURE (not assume)
# whether git honours a non-zero post-checkout exit for `git worktree add`.
set -uo pipefail
HERE="${0:A:h}"
HOOK="$HERE/post-checkout"
SB="$(mktemp -d /tmp/t279-hook.XXXXXX)"
trap 'rm -rf "$SB"' EXIT

print -r -- "sandbox: $SB    (nothing outside it is touched)"
print -r -- "git: $(git --version)"
print -r -- ""

# ---- a bare 'origin' plus a working clone, standing in for the shared checkout -------
git init -q --bare "$SB/origin.git"
git clone -q "$SB/origin.git" "$SB/repo"
cd "$SB/repo"
git config user.email t279@local; git config user.name T279
mkdir -p .softhouse
print -r -- '{"tasks":[]}'                       > .softhouse/tasks.json
print -r -- '# RESUME'                           > .softhouse/RESUME.md
print -r -- '{"holder":"none"}'                  > .softhouse/LOCK
git add -A; git commit -q -m "base"; git push -q origin HEAD:refs/heads/main
git branch -q -M main; git branch -q --set-upstream-to=origin/main main 2>/dev/null

install -m 755 "$HOOK" "$SB/repo/.git/hooks/post-checkout"
print -r -- "hook installed at .git/hooks/post-checkout"
print -r -- ""

spawn() {  # $1 = label, $2 = branch
  print -r -- "--- git worktree add ($1) ---"
  local out rc
  out="$(git worktree add -q -b "$2" "$SB/wt-$2" 2>&1)"; rc=$?
  print -r -- "$out"
  print -r -- "  rc=$rc   worktree dir exists: $([[ -d $SB/wt-$2 ]] && print yes || print no)"
  print -r -- ""
}

# =========================================================== GREEN (baseline) =========
print -r -- "===== GREEN 0: everything published — the hook must be SILENT ====="
spawn "clean" wt-clean

# =========================================================== RED ======================
print -r -- "===== RED: the P-85 window, reproduced ====="
print -r -- "the driver refreshes its LOCK and its in-flight RESUME.md and pushes them,"
print -r -- "then flips tasks.json to in_progress and COMMITS IT WITHOUT PUSHING —"
print -r -- "which is exactly what happened at fe24419 on 2026-08-22, 101 s before the"
print -r -- "first worker spawned."
print -r -- ""
print -r -- '{"holder":"local-fire","pid":4242}' > .softhouse/LOCK
print -r -- '# RESUME — IN FLIGHT: T-a T-b'      > .softhouse/RESUME.md
git add -A; git commit -q -m "fire OPEN: lock + in-flight manifest"; git push -q origin main
print -r -- '{"tasks":[{"id":"T-a","status":"in_progress","branch":"softhouse/T-a"}]}' > .softhouse/tasks.json
git add -A; git commit -q -m "tasks.json: dispatch record"        # NOT pushed
print -r -- "unpushed commits touching .softhouse/: $(git rev-list --count origin/main..HEAD -- .softhouse/)"
print -r -- ""
spawn "unpushed dispatch record — MUST WARN" wt-red

print -r -- "===== RED 2: not even committed ====="
print -r -- '{"tasks":[{"id":"T-b"}]}' > .softhouse/tasks.json
spawn "dirty .softhouse — MUST WARN" wt-red2

# =========================================================== GREEN ====================
print -r -- "===== GREEN: push, then spawn — the hook must go SILENT again ====="
git add -A; git commit -q -m "tasks.json again"; git push -q origin main
print -r -- "unpushed commits touching .softhouse/: $(git rev-list --count origin/main..HEAD -- .softhouse/)"
spawn "published — MUST BE SILENT" wt-green

# ================================================= exit-code semantics, MEASURED ======
print -r -- "===== does git HONOUR a non-zero post-checkout exit for 'git worktree add'? ====="
print -r -- '{"tasks":[{"id":"T-c"}]}' > .softhouse/tasks.json
git add -A; git commit -q -m "unpushed again"
print -r -- "SOFTHOUSE_PUSH_GATE=enforce:"
SOFTHOUSE_PUSH_GATE=enforce spawn "enforce" wt-enforce

print -r -- "===== the escape hatch ====="
print -r -- "SOFTHOUSE_PUSH_GATE=off:"
SOFTHOUSE_PUSH_GATE=off spawn "off" wt-off

print -r -- "===== a FILE checkout (\$3==0) must never speak ====="
git checkout -q -- .softhouse/tasks.json 2>&1 | sed 's/^/  /'
print -r -- "  (silence above = correct)"
