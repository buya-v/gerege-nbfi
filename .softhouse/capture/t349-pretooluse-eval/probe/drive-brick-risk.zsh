#!/bin/zsh
# T349 -- THE QUESTION THE DRIVER GATED T336 ON: if the hook itself is broken, does the
# repo become unusable? Two failure shapes, driven through the real route.
#   B1  the hook script CRASHES (traceback, exit 1)
#   B2  the hook script is MISSING (command not found)
# Expect (to be measured, not assumed): a crashing PreToolUse hook fails OPEN, so a broken
# gate degrades to "no gate" rather than to "no repo".
set -u
ROOT=${T349_ROOT:-/tmp/t349-scratch}
CAP=${T349_CAP:?capture dir}

settings() {
  cat > "$ROOT/repo/.claude/settings.json" <<JSON
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "*", "hooks": [ { "type": "command", "command": "$1", "timeout": 20 } ] }
    ]
  }
}
JSON
}

print -r -- '########## B1 -- the hook CRASHES (exit 1 with a traceback)'
cat > "$ROOT/repo/.claude/broken-hook.py" <<'PY'
import sys
raise RuntimeError("T349 BRICK DRIVE: this hook is deliberately broken")
PY
settings '/usr/bin/python3 "$CLAUDE_PROJECT_DIR/.claude/broken-hook.py"'
zsh "$CAP/probe/drive-run.zsh" B1-hook-crashes unused "$CAP/probe/prompt-spawn.txt"

print -r -- ''
print -r -- '########## B2 -- the hook script is MISSING entirely'
settings '/usr/bin/python3 "$CLAUDE_PROJECT_DIR/.claude/does-not-exist.py"'
zsh "$CAP/probe/drive-run.zsh" B2-hook-missing unused "$CAP/probe/prompt-spawn.txt"
