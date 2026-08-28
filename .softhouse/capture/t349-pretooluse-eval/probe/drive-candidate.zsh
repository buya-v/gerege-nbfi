#!/bin/zsh
# T349 -- drive the CANDIDATE gate RED and GREEN through a real Agent-tool worktree spawn
# in the throwaway repo, plus unit drives for the clauses a live spawn cannot exercise.
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
CAP=${T349_CAP:?capture dir}
OUT=$ROOT/out
mkdir -p "$OUT"
cp "$CAP/probe/spawn-gate-candidate.py" "$ROOT/repo/.claude/spawn-gate-candidate.py"

cat > "$ROOT/repo/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"$CLAUDE_PROJECT_DIR/.claude/spawn-gate-candidate.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
JSON

cat > "$CAP/probe/prompt-spawn-t900.txt" <<'TXT'
Your only job is to spawn one subagent. Do not use any other tool first, and do not do the work yourself.

Call the Agent tool exactly once with: subagent_type "general-purpose", isolation "worktree", run_in_background false, description "T900", prompt "=== TASK T900 === Create a file HELLO900.txt containing hi. Commit to branch softhouse/T900-probe. Write your handoff to .softhouse/handoff/run-t349/T900.md and commit it."

If the Agent tool call is refused, do NOT retry, do NOT use any other tool, and do NOT do the work yourself. Report in one line the exact refusal text.
TXT

cd "$ROOT/repo"
git checkout -q main 2>/dev/null || true

print -r -- "########## seed: a fire in flight, dispatch record committed but NOT pushed"
print -r -- "host=scratch pid=1 started_at=2026-08-28T00:00:00Z" > .softhouse/LOCK
print -r -- "# in-flight" > .softhouse/RESUME.md
print -r -- '{"tasks":[{"id":"T900","status":"pending","branch":null}]}' > .softhouse/tasks.json
git add -A >/dev/null 2>&1; git commit -q -m "LOCK + RESUME + tasks (T900 pending)"; git push -q origin main
print -r -- '{"tasks":[{"id":"T900","status":"in_progress","branch":"softhouse/T900-probe"}]}' > .softhouse/tasks.json
git add -A >/dev/null 2>&1; git commit -q -m "DISPATCH RECORD T900 -- deliberately NOT pushed"
print -r -- "origin says: $(git show origin/main:.softhouse/tasks.json)"
print -r -- "local  says: $(cat .softhouse/tasks.json)"

export SOFTHOUSE_SPAWN_GATE_LOG="$OUT/candidate.gate.jsonl"
rm -f "$SOFTHOUSE_SPAWN_GATE_LOG"
zsh "$CAP/probe/drive-run.zsh" C1-candidate-RED-unpushed unused "$CAP/probe/prompt-spawn-t900.txt"

print -r -- ""
print -r -- "########## GREEN: push the same dispatch record, spawn again"
cd "$ROOT/repo"
git push -q origin main
print -r -- "origin says: $(git show origin/main:.softhouse/tasks.json)"
zsh "$CAP/probe/drive-run.zsh" C2-candidate-GREEN-pushed unused "$CAP/probe/prompt-spawn-t900.txt"

print -r -- ""
print -r -- "########## gate decision log"
cat "$OUT/candidate.gate.jsonl"
