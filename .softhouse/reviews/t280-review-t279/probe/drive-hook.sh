#!/bin/sh
# T280 — drive T279's post-checkout hook RED myself, in a scratch repo.
set -u
HOOK="$1"        # absolute path to the hook file under test
T=$(mktemp -d /tmp/t280-hook.XXXXXX)
export GIT_CONFIG_NOSYSTEM=1
export HOME="$T/home"; mkdir -p "$HOME"
printf '[user]\n\tname = T280\n\temail = t280@local\n[init]\n\tdefaultBranch = main\n' > "$HOME/.gitconfig"

git init -q --bare "$T/origin.git"
git init -q "$T/wt"
cd "$T/wt" || exit 9
mkdir -p .softhouse
echo seed > .softhouse/seed.txt
git add -A >/dev/null; git commit -qm seed
git remote add origin "$T/origin.git"
git push -q origin main
git branch --set-upstream-to=origin/main main >/dev/null 2>&1

echo "### git version: $(git --version)"
echo

# --- CLEAN CASE: everything pushed. Hook must be silent and must not block.
mkdir -p "$T/wt/.git/hooks"
cp "$HOOK" "$T/wt/.git/hooks/post-checkout"; chmod +x "$T/wt/.git/hooks/post-checkout"
echo "=== CASE 1: clean (all pushed), SOFTHOUSE_PUSH_GATE=enforce ==="
git worktree add -q -b w1 "$T/w1" main 2>&1 | sed 's/^/  /'
echo "  worktree add rc=$?  ; dir exists: $([ -d "$T/w1" ] && echo YES || echo NO)"
echo

# --- RED CASE: an UNPUSHED .softhouse commit == the P-85 shape.
echo "dispatch record" > .softhouse/tasks.json
git add -A >/dev/null; git commit -qm "softhouse: DISPATCH RECORD (deliberately unpushed)"
echo "  unpushed .softhouse commits: $(git rev-list --count origin/main..HEAD -- .softhouse/)"
echo

echo "=== CASE 2: unpushed dispatch record, DEFAULT gate (unset -> warn) ==="
git worktree add -b w2 "$T/w2" main > "$T/c2.out" 2>&1; rc2=$?
echo "  worktree add rc=$rc2 ; new worktree dir exists: $([ -d "$T/w2" ] && echo YES || echo NO)"
echo "  branch w2 created: $(git rev-parse --verify --quiet refs/heads/w2 >/dev/null && echo YES || echo NO)"
echo "  hook output seen: $(grep -c 'PUSH-BEFORE-SPAWN VIOLATION' "$T/c2.out")"
sed 's/^/    | /' "$T/c2.out"
echo

echo "=== CASE 3: unpushed dispatch record, SOFTHOUSE_PUSH_GATE=enforce ==="
SOFTHOUSE_PUSH_GATE=enforce git worktree add -b w3 "$T/w3" main > "$T/c3.out" 2>&1; rc3=$?
echo "  worktree add rc=$rc3 ; new worktree dir exists: $([ -d "$T/w3" ] && echo YES || echo NO)"
echo "  branch w3 created: $(git rev-parse --verify --quiet refs/heads/w3 >/dev/null && echo YES || echo NO)"
echo "  files checked out in w3: $(ls -A "$T/w3" 2>/dev/null | wc -l | tr -d ' ')"
echo "  hook fired: $(grep -c 'PUSH-BEFORE-SPAWN VIOLATION' "$T/c3.out")"
sed 's/^/    | /' "$T/c3.out"
echo
echo "  => worktree list after enforce:"
git worktree list | sed 's/^/    /'
echo

echo "=== CASE 4: enforce, but violation is UNCOMMITTED only (dirty .softhouse) ==="
git push -q origin main
echo scratch > .softhouse/dirty.txt
SOFTHOUSE_PUSH_GATE=enforce git worktree add -b w4 "$T/w4" main > "$T/c4.out" 2>&1; rc4=$?
echo "  worktree add rc=$rc4 ; hook fired: $(grep -c 'PUSH-BEFORE-SPAWN VIOLATION' "$T/c4.out")"
echo

echo "=== CASE 5: does the hook fire when spawning FROM a linked worktree? ==="
git -C "$T/w1" checkout -q -b w1b 2>/dev/null
echo more > "$T/wt/.softhouse/late.txt"; git -C "$T/wt" add -A >/dev/null; git -C "$T/wt" commit -qm "unpushed again" >/dev/null
SOFTHOUSE_PUSH_GATE=enforce git -C "$T/w1" worktree add -b w5 "$T/w5" main > "$T/c5.out" 2>&1; rc5=$?
echo "  spawned from linked worktree: rc=$rc5 ; hook fired: $(grep -c 'PUSH-BEFORE-SPAWN VIOLATION' "$T/c5.out")"
echo "  (hook installed at common dir? $(ls "$T/wt/.git/hooks/post-checkout" >/dev/null 2>&1 && echo YES || echo NO))"
sed 's/^/    | /' "$T/c5.out" | head -20
echo
echo "scratch repo: $T"
