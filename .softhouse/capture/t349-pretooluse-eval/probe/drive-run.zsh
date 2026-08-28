#!/bin/zsh
# T349 -- one measured nested `claude -p` run inside the THROWAWAY scratch repo.
#
# usage: drive-run.zsh <tag> <mode> <prompt-file> [extra-env=...]
#   <mode> is $T349_MODE for the probe hook.
#
# Records: hook log, claude stdout/stderr, rc, wall time, and the post-state of the
# scratch repo (worktrees, branches) so a "deny" can be distinguished from a
# "denied but the worktree was created anyway".
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
TAG=${1:?tag}
MODE=${2:?mode}
PROMPTF=${3:?prompt file}
OUT=$ROOT/out
mkdir -p "$OUT"

export T349_LOG="$OUT/$TAG.hook.jsonl"
export T349_MODE="$MODE"
rm -f "$T349_LOG"

# pre-state
git -C "$ROOT/repo" worktree list --porcelain > "$OUT/$TAG.worktrees.before" 2>&1
git -C "$ROOT/repo" branch -a > "$OUT/$TAG.branches.before" 2>&1

PROMPT=$(<"$PROMPTF")
T0=$(/usr/bin/python3 -c 'import time;print(time.time())')
cd "$ROOT/repo"
# macOS has no coreutils `timeout`; perl's alarm is always present.
TO=(/usr/bin/perl -e 'my $t=shift; $SIG{ALRM}=sub{ kill 9,-$$; exit 124 }; alarm $t; exec @ARGV;' ${T349_TIMEOUT:-420})
"${TO[@]}" claude -p "$PROMPT" \
  --permission-mode ${T349_PERM:-bypassPermissions} \
  --max-turns ${T349_TURNS:-12} \
  --output-format text \
  > "$OUT/$TAG.stdout.txt" 2> "$OUT/$TAG.stderr.txt"
RC=$?
T1=$(/usr/bin/python3 -c 'import time;print(time.time())')

git -C "$ROOT/repo" worktree list --porcelain > "$OUT/$TAG.worktrees.after" 2>&1
git -C "$ROOT/repo" branch -a > "$OUT/$TAG.branches.after" 2>&1

{
  print -r -- "=== T349 run $TAG"
  print -r -- "mode=$MODE perm=${T349_PERM:-bypassPermissions} rc=$RC"
  print -r -- "wall_s=$(/usr/bin/python3 -c "print(round($T1-$T0,2))")"
  print -r -- "--- hook invocations (tool_name : decision)"
  if [[ -s "$T349_LOG" ]]; then
    /usr/bin/python3 -c '
import json,sys
for l in open(sys.argv[1]):
    r=json.loads(l)
    print("   %-14s %-22s %s" % (r.get("tool_name"), r.get("decision"), (r.get("tool_input") or "")[:110]))
' "$T349_LOG"
  else
    print -r -- "   (NO HOOK LOG FILE -- the hook never ran)"
  fi
  print -r -- "--- branches created during the run"
  diff "$OUT/$TAG.branches.before" "$OUT/$TAG.branches.after" || true
  print -r -- "--- worktrees created during the run"
  diff "$OUT/$TAG.worktrees.before" "$OUT/$TAG.worktrees.after" || true
  print -r -- "--- claude stdout"
  cat "$OUT/$TAG.stdout.txt"
  print -r -- "--- claude stderr (tail)"
  tail -20 "$OUT/$TAG.stderr.txt"
} > "$OUT/$TAG.report.txt" 2>&1

cat "$OUT/$TAG.report.txt"
