#!/bin/bash
# T189 — provenance: WHICH program does the token `grep` name, in each context that matters?
# And what exactly does the BSD "third mode" print?
set -u
PROBE_DIR="$(cd "$(dirname "$0")" && pwd)"
FIX="$PROBE_DIR/fixtures"

echo "===== 1. inside a bash script launched from the Claude Code Bash tool ====="
type -a grep 2>&1 | sed -e 's/^/    /'
echo "    command -v grep -> $(command -v grep)"
echo "    bare-grep --version -> $(grep --version 2>&1 | head -1)"

echo
echo "===== 2. inside zsh -lc (how launchd starts the real fire) ====="
/bin/zsh -lc 'echo "    whence -a grep:"; whence -a grep 2>&1 | sed -e "s/^/      /"; echo "    grep --version -> $(grep --version 2>&1 | head -1)"'

echo
echo "===== 3. inside zsh -c (non-login) ====="
/bin/zsh -c 'echo "    grep --version -> $(grep --version 2>&1 | head -1)"'

echo
echo "===== 4. env -i /bin/zsh -lc (no inherited env at all) ====="
env -i HOME="$HOME" /bin/zsh -lc 'echo "    grep --version -> $(grep --version 2>&1 | head -1)"'

echo
echo "===== 5. is the wrapper exported to children? ====="
echo "    bash -c: $(bash -c 'type -t grep' 2>&1)"
echo "    zsh  -c: $(/bin/zsh -c 'whence -w grep' 2>&1)"

echo
echo "===== 6. the claude binary run as ugrep — what does it report? ====="
CLAUDE_BIN="${CLAUDE_CODE_EXECPATH:-/Users/buv/.local/bin/claude}"
echo "    CLAUDE_BIN=$CLAUDE_BIN"
( exec -a ugrep "$CLAUDE_BIN" --version 2>&1 ) | head -3 | sed -e 's/^/    /'

echo
echo "===== 7. the BSD 'third mode' — exact stdout bytes, NUL fixture, no -a ====="
for shape in file redir pipe; do
  echo "--- shape=$shape ---"
  case $shape in
    file)  LC_ALL=C /usr/bin/grep -v '^?? \.softhouse/LOCK$' "$FIX/b-nul.txt" > "$PROBE_DIR/.o" 2>"$PROBE_DIR/.e"; rc=$? ;;
    redir) LC_ALL=C /usr/bin/grep -v '^?? \.softhouse/LOCK$' < "$FIX/b-nul.txt" > "$PROBE_DIR/.o" 2>"$PROBE_DIR/.e"; rc=$? ;;
    pipe)  cat "$FIX/b-nul.txt" | LC_ALL=C /usr/bin/grep -v '^?? \.softhouse/LOCK$' > "$PROBE_DIR/.o" 2>"$PROBE_DIR/.e"; rc=$? ;;
  esac
  echo "  exit=$rc"
  echo "  stdout od -c:"; od -c "$PROBE_DIR/.o" | sed -e 's/^/    /'
  echo "  stderr:"; sed -e 's/^/    ! /' "$PROBE_DIR/.e"
done

echo
echo "===== 8. same NUL fixture WITH -a (the live flags) ====="
for shape in file redir pipe; do
  case $shape in
    file)  LC_ALL=C /usr/bin/grep -av '^?? \.softhouse/LOCK$' "$FIX/b-nul.txt" > "$PROBE_DIR/.o" 2>"$PROBE_DIR/.e"; rc=$? ;;
    redir) LC_ALL=C /usr/bin/grep -av '^?? \.softhouse/LOCK$' < "$FIX/b-nul.txt" > "$PROBE_DIR/.o" 2>"$PROBE_DIR/.e"; rc=$? ;;
    pipe)  cat "$FIX/b-nul.txt" | LC_ALL=C /usr/bin/grep -av '^?? \.softhouse/LOCK$' > "$PROBE_DIR/.o" 2>"$PROBE_DIR/.e"; rc=$? ;;
  esac
  echo "--- shape=$shape exit=$rc ---"
  od -c "$PROBE_DIR/.o" | sed -e 's/^/    /'
done

rm -f "$PROBE_DIR/.o" "$PROBE_DIR/.e"
echo "===== DONE ====="
