#!/bin/zsh
# T202 -- END-TO-END run of the PATCHED fire-program.sh, invoked exactly as the
# launchd plist invokes it: `/bin/zsh -lc <path>`, WorkingDirectory = the repo.
# Everything is redirected into /tmp: a scratch REPO, a scratch LOG_DIR, and a
# fake `claude` that behaves like a driver committing a real handoff, stranding
# an uncommitted deliverable in the main tree, and stranding another inside a
# linked worktree whose git is then BROKEN.
set -uo pipefail
E=/tmp/t202/e2e
rm -rf "$E"; mkdir -p "$E/repo/.softhouse" "$E/logs" "$E/bin"
cd "$E/repo" || exit 1
git init -q -b main
print -r -- baseline > .softhouse/tasks.json
print -r -- '{"status":"running"}' > .softhouse/program.json
print -r -- '{"tasks":[]}' > .softhouse/tasks.json
print -r -- "resume" > .softhouse/RESUME.md
git add -A
git -c user.name=t202 -c user.email=t202@example.com commit -q -m baseline
git worktree add -q -b wk-good "$E/wt-good" >/dev/null 2>&1
git worktree add -q -b wk-bad  "$E/wt-bad"  >/dev/null 2>&1

cat > "$E/bin/claude" <<'FAKE'
#!/bin/zsh
# fake driver: commits one thing, strands another, strands a third in a worktree
cd /tmp/t202/e2e/repo
print -r -- "committed by the driver" > docs-committed.md
mkdir -p .softhouse
git add -A -- ':(top)' >/dev/null 2>&1
git -c user.name=d -c user.email=d@e.com commit -q -m "driver work" >/dev/null 2>&1
print -r -- "STRANDED in the main tree"    > T999-handoff.md
print -r -- "resumed" > .softhouse/RESUME.md
print -r -- "STRANDED inside a worktree"   > /tmp/t202/e2e/wt-good/handoff.md
print -r -- "STRANDED behind a broken git" > /tmp/t202/e2e/wt-bad/handoff.md
print -r -- GARBAGE > /tmp/t202/e2e/wt-bad/.git
print -r -- '{"type":"system","subtype":"init","session_id":"fake"}'
print -r -- '{"type":"result","subtype":"success","result":"fake driver done"}'
exit 0
FAKE
chmod +x "$E/bin/claude"

export GEREGE_NBFI_REPO="$E/repo"
export LOG_DIR="$E/logs"
export CLAUDE_BIN="$E/bin/claude"
export FINERACT_SRC=/tmp/t202/nonexistent-fineract
export CHAIN_MAX=1
export FINERACT_HEALTH_URL="https://127.0.0.1:1/none"
/bin/zsh -lc "$1"
print -r -- "===== wrapper rc=$? ====="
print -r -- "===== log ====="
cat "$E"/logs/fire-*.log
print -r -- "===== main-tree state ====="
git -C "$E/repo" log --oneline -4
print -r -- "-- still uncommitted:"; git -C "$E/repo" status --porcelain -- ':(top)'
print -r -- "===== rescue branches ====="
git -C "$E/repo" branch --list 'softhouse/rescued-*'
print -r -- "===== LOCK present? ====="
[[ -f "$E/repo/.softhouse/LOCK" ]] && print PRESENT || print absent
