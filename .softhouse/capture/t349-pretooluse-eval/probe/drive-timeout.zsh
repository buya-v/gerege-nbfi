#!/bin/zsh
# T349 -- Q3 sub-question: when the PreToolUse hook exceeds its configured `timeout`,
# does the harness fail OPEN (the spawn proceeds) or CLOSED (the spawn is refused)?
# This decides whether a 4-second network call inside the hook is safe.
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
CAP=${T349_CAP:?capture dir}
cp "$CAP/probe/pretooluse-probe.py" "$ROOT/repo/.claude/pretooluse-probe.py"

cat > "$ROOT/repo/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"$CLAUDE_PROJECT_DIR/.claude/pretooluse-probe.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
JSON
print -r -- "settings hook timeout set to 5 s; hook will sleep 20 s then try to deny"
T349_HANG=20 zsh "$CAP/probe/drive-run.zsh" H1-hook-timeout-5s-hang20s hang "$CAP/probe/prompt-spawn.txt"

# restore the 30 s settings so later runs are unaffected
cat > "$ROOT/repo/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/usr/bin/python3 \"$CLAUDE_PROJECT_DIR/.claude/pretooluse-probe.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
JSON
print -r -- "settings restored to timeout 30"
