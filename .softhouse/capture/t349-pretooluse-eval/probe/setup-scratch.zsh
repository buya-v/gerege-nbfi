#!/bin/zsh
# T349 -- build a THROWAWAY repo with its own .claude/settings.json carrying the probe
# PreToolUse hook. Nothing here touches /Users/buv/gerege-nbfi/.claude/settings.json.
#
# usage: setup-scratch.zsh <scratch-root> <probe-hook-path>
set -e
ROOT=${1:?scratch root}
HOOK=${2:?probe hook path}

rm -rf "$ROOT"
mkdir -p "$ROOT"
git init --bare -q "$ROOT/origin.git"
mkdir -p "$ROOT/repo/.claude"
cd "$ROOT/repo"
git init -q -b main
git config user.email t349@scratch.local
git config user.name T349
print -r -- "scratch" > README.md
mkdir -p .softhouse
print -r -- '{"tasks":[]}' > .softhouse/tasks.json
git add -A
git commit -q -m "scratch base"
git remote add origin "$ROOT/origin.git"
git push -q -u origin main

cp "$HOOK" "$ROOT/repo/.claude/pretooluse-probe.py"
chmod +x "$ROOT/repo/.claude/pretooluse-probe.py"

cat > "$ROOT/repo/.claude/settings.json" <<JSON
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"\$CLAUDE_PROJECT_DIR/.claude/pretooluse-probe.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
JSON

print -r -- "scratch ready: $ROOT/repo"
