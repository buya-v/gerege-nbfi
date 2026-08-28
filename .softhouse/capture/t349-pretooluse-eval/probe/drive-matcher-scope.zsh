#!/bin/zsh
# T349 -- COST MITIGATION: can the matcher be scoped so the hook process is not spawned
# on every tool call of every worker? Expect: with matcher "Agent|Task|Bash" the probe
# logs the Agent call and Bash calls but NOT the subagent's Write.
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
CAP=${T349_CAP:?capture dir}
cp "$CAP/probe/pretooluse-probe.py" "$ROOT/repo/.claude/pretooluse-probe.py"
cat > "$ROOT/repo/.claude/settings.json" <<'JSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent|Task|Bash",
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
print -r -- 'matcher scoped to "Agent|Task|Bash"; a subagent Write must NOT appear below'
zsh "$CAP/probe/drive-run.zsh" M1-matcher-scoped log "$CAP/probe/prompt-spawn.txt"
