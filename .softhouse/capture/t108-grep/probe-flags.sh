#!/usr/bin/env bash
# T108 — supplementary probes the main matrix does not cover.
#
#  A. raw stdout/exit of every tool on the two decisive shapes, verbatim
#  B. the -q / -qF / -l forms the rigs actually use
#  C. does the Claude Code `grep` SHELL FUNCTION reach inside a script?
#     (this is the whole reason T80 and T91 disagreed)
#
# No arithmetic; no floating point (P-25).
#
# Usage: bash probe-flags.sh
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
CORPUS="$HERE/corpus"
CC_BIN="${CLAUDE_CODE_EXECPATH:-}"
if [ ! -x "$CC_BIN" ]; then CC_BIN="$HOME/.local/bin/claude"; fi

ccfn() {
  ARGV0=ugrep "$CC_BIN" -G --ignore-files --hidden -I \
    --exclude-dir=.git --exclude-dir=.svn --exclude-dir=.hg \
    --exclude-dir=.bzr --exclude-dir=.jj --exclude-dir=.sl "$@"
}

hr() { echo "------------------------------------------------------------"; }

echo "T108 supplementary probes"
echo "run at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "host   $(uname -srm)"
echo "bsd    $(/usr/bin/grep --version 2>&1 | head -1)"
echo "ccfn   $(ccfn --version 2>&1 | head -1)"
echo "CC_BIN $CC_BIN"
hr

echo "== A. verbatim stdout + exit status, decisive shapes =="
for f in "$CORPUS/t80-exact-repro.txt" "$CORPUS/s06-e2-same-line-before.txt"; do
  echo
  echo "FILE $(basename "$f")"
  case "$(basename "$f")" in
    t80-exact-repro.txt)       PAT='unbound variable' ;;
    s06-e2-same-line-before.txt) PAT='TARGET' ;;
  esac
  echo "PATTERN [$PAT]   true count on this file: 1"
  for cmd in "bsd -c" "bsd -ac" "ccfn -c" "ccfn -ac"; do
    tool="${cmd%% *}"; fl="${cmd##* }"
    for loc in "utf8" "posixC"; do
      if [ "$loc" = "utf8" ]; then
        out=$(env -u LC_ALL LANG=C.UTF-8 LC_CTYPE=C.UTF-8 bash -c \
          "$(declare -f ccfn); CC_BIN=$CC_BIN; if [ $tool = bsd ]; then /usr/bin/grep $fl \"\$1\" \"\$2\"; else ccfn $fl \"\$1\" \"\$2\"; fi" _ "$PAT" "$f" 2>&1)
      else
        out=$(env LC_ALL=C LANG=C bash -c \
          "$(declare -f ccfn); CC_BIN=$CC_BIN; if [ $tool = bsd ]; then /usr/bin/grep $fl \"\$1\" \"\$2\"; else ccfn $fl \"\$1\" \"\$2\"; fi" _ "$PAT" "$f" 2>&1)
      fi
      st=$?
      printf '  %-10s %-4s %-7s -> stdout=[%s] exit=%s\n' "$tool" "$fl" "$loc" "$out" "$st"
    done
  done
done
hr

echo "== B. the -q / -qF / -l forms the rigs actually use =="
F="$CORPUS/t80-exact-repro.txt"
P='unbound variable'
echo "FILE t80-exact-repro.txt  PATTERN [$P]  (PRESENT: true answer is 'found')"
for spec in "bsd -q" "bsd -qa" "bsd -qF" "bsd -qaF" "ccfn -q" "ccfn -qa" "ccfn -qF" "ccfn -qaF" "bsd -l" "bsd -al" "ccfn -l" "ccfn -al"; do
  tool="${spec%% *}"; fl="${spec##* }"
  for loc in utf8 posixC; do
    if [ "$loc" = utf8 ]; then ENVP=(env -u LC_ALL LANG=C.UTF-8 LC_CTYPE=C.UTF-8)
    else ENVP=(env LC_ALL=C LANG=C); fi
    if [ "$tool" = bsd ]; then
      out=$("${ENVP[@]}" /usr/bin/grep "$fl" "$P" "$F" 2>&1); st=$?
    else
      out=$("${ENVP[@]}" env ARGV0=ugrep "$CC_BIN" -G --ignore-files --hidden -I "$fl" "$P" "$F" 2>&1); st=$?
    fi
    if [ "$st" -eq 0 ]; then w="FOUND(correct)"; else w="ABSENT(WRONG)"; fi
    printf '  %-6s %-5s %-7s -> exit=%s %-14s stdout=[%s]\n' "$tool" "$fl" "$loc" "$st" "$w" "$out"
  done
done
hr

echo "== C. does the Claude Code \`grep\` shell function reach inside a script? =="
echo "The function is defined in the Bash-tool's OWN interactive shell, from the"
echo "session snapshot.  Shell functions are not exported to child processes, so a"
echo "script invoked as \`sh x.sh\` / \`bash x.sh\` gets /usr/bin/grep instead."
echo
cat > /tmp/t108-inner.sh <<'INNER'
echo "  inside script: type -a grep ->"
type -a grep 2>&1 | sed 's/^/    /'
echo "  inside script: grep --version -> $(grep --version 2>&1 | head -1)"
INNER
echo "-- bash /tmp/t108-inner.sh"
bash /tmp/t108-inner.sh
echo "-- sh /tmp/t108-inner.sh"
sh /tmp/t108-inner.sh
rm -f /tmp/t108-inner.sh
hr
echo "done"
