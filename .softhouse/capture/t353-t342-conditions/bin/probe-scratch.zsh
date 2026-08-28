#!/bin/zsh
# T353 — run the REAL wrapper's `--probe` (full preflight, then exit before the lock) against
# a throwaway repo, so the two new preflight gates are exercised on the path that actually
# executes rather than reasoned about. $1 = wrapper, $2 = optional PATH override dir.
emulate -L zsh
set -uo pipefail
FP="${1:?usage: probe-scratch.zsh <fire-program.sh>}"
S="$(mktemp -d "${TMPDIR:-/tmp}/t353probe.XXXXXX")"
mkdir -p "$S/repo/.softhouse" "$S/logs"
REAL_HOME="$HOME"
export GIT_CONFIG_NOSYSTEM=1 HOME="$S/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T353\n\temail = t353@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"
git init -q "$S/repo"
print -r -- x > "$S/repo/.softhouse/x"
git -C "$S/repo" add -A >/dev/null 2>&1
git -C "$S/repo" commit -qm seed >/dev/null 2>&1
GEREGE_NBFI_REPO="$S/repo" LOG_DIR="$S/logs" CLAUDE_BIN="${CLAUDE_BIN:-$REAL_HOME/.local/bin/claude}" zsh "$FP" --probe 2>&1
rc=$?
print -r -- "PROBE_EXIT=$rc"
rm -rf "$S"
exit $rc
