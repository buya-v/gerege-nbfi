#!/bin/sh
# T347 — independent re-derivation of T336's git-behaviour claims, in a THROWAWAY repo.
# Zero blast radius: nothing here touches /Users/buv/gerege-nbfi.
#
# Cases:
#   A  `git worktree add -b`  WITH checkout  -> does post-checkout fire? what signature?
#   B  `git worktree add --no-checkout`      -> hook must NOT fire; signature must DIFFER
#   C  `git reset --hard` inside B           -> hook must NOT fire
#   D  `git worktree add -b`                 -> does reference-transaction fire?
#   E  post-checkout that exits 1            -> T280's F-C: does the worktree survive?
#
# A vs B is the discriminator that closes the one alternative explanation T336 left open:
# if the harness used `--no-checkout` + populate, post-checkout would legitimately not run
# and nothing would be "suppressed".  B leaves a ONE-LINE logs/HEAD and an EMPTY tree; the
# harness worktree has A's TWO-LINE logs/HEAD and a populated tree.  So B is refuted.
set -u
S=${1:-/tmp/t347-scratch}
rm -rf "$S"; mkdir -p "$S"
git --version
git init -q "$S/origin-src"
git -C "$S/origin-src" config user.email t347@local
git -C "$S/origin-src" config user.name T347
echo one > "$S/origin-src/a.txt"
git -C "$S/origin-src" add a.txt
git -C "$S/origin-src" commit -qm c1
git clone -q "$S/origin-src" "$S/repo"
R="$S/repo"
git -C "$R" config user.email t347@local
git -C "$R" config user.name T347

cat > "$R/.git/hooks/post-checkout" <<HOOK
#!/bin/sh
echo "POSTCHECKOUT-FIRED pwd=\$(pwd) old=\$1 new=\$2 isbranch=\$3" >> $S/hook.log
: > "\$(pwd)/.t347-scratch-marker"
exit 0
HOOK
chmod +x "$R/.git/hooks/post-checkout"
: > "$S/hook.log"

echo "===== A. git worktree add -b brA (WITH checkout) ====="
git -C "$R" worktree add -q -b brA "$S/wtA" HEAD; echo "rc=$?"
echo "--- hook.log (expect ONE fire, old=null-sha) ---"; cat "$S/hook.log"
echo "--- marker dropped in wtA? ---"; ls -1 "$S/wtA/.t347-scratch-marker" 2>&1
echo "--- wtA logs/HEAD ---"; cat "$R/.git/worktrees/wtA/logs/HEAD"
echo "--- branch reflog ---"; cat "$R/.git/logs/refs/heads/brA"

echo; echo "===== B. git worktree add --no-checkout -b brB ====="
: > "$S/hook.log"
git -C "$R" worktree add -q --no-checkout -b brB "$S/wtB" HEAD; echo "rc=$?"
echo "--- hook.log (expect EMPTY) ---"; cat "$S/hook.log"; echo "[end]"
echo "--- wtB contents (expect .git only) ---"; ls -a "$S/wtB"
echo "--- wtB logs/HEAD (expect ONE line, no 'reset: moving to HEAD') ---"
cat "$R/.git/worktrees/wtB/logs/HEAD"

echo; echo "===== C. git reset --hard inside wtB ====="
: > "$S/hook.log"
git -C "$S/wtB" reset -q --hard HEAD
echo "--- hook.log (expect EMPTY) ---"; cat "$S/hook.log"; echo "[end]"
echo "--- wtB logs/HEAD after reset ---"; cat "$R/.git/worktrees/wtB/logs/HEAD"

echo; echo "===== D. does git worktree add fire reference-transaction? ====="
cat > "$R/.git/hooks/reference-transaction" <<HOOK
#!/bin/sh
echo "REFTXN state=\$1 pwd=\$(pwd)" >> $S/reftxn.log
cat >> $S/reftxn.log
exit 0
HOOK
chmod +x "$R/.git/hooks/reference-transaction"
: > "$S/reftxn.log"; : > "$S/hook.log"
git -C "$R" worktree add -q -b brD "$S/wtD" HEAD; echo "rc=$?"
echo "--- reftxn.log (expect refs/heads/brD created from null-sha) ---"; cat "$S/reftxn.log"
echo "--- post-checkout log ---"; cat "$S/hook.log"

echo; echo "===== E. T280's F-C core: post-checkout exits 1 ====="
rm -f "$R/.git/hooks/reference-transaction"
cat > "$R/.git/hooks/post-checkout" <<'HOOK'
#!/bin/sh
echo "REFUSING (post-checkout, exit 1) pwd=$(pwd)" >&2
exit 1
HOOK
chmod +x "$R/.git/hooks/post-checkout"
git -C "$R" worktree add -b brFC "$S/wtFC" HEAD; echo "rc=$?  <-- F-C says 1"
echo "--- branch created anyway? ---"; git -C "$R" rev-parse --verify refs/heads/brFC 2>&1
echo "--- tree populated anyway? ---"; ls -a "$S/wtFC"
echo "--- admin dir registered anyway? ---"; ls -d "$R/.git/worktrees/wtFC" 2>&1
echo "--- can a worker commit in the REFUSED worktree? ---"
echo hello > "$S/wtFC/newfile.txt"
git -C "$S/wtFC" add newfile.txt
git -C "$S/wtFC" commit -qm "committed inside the REFUSED worktree" && echo "COMMIT SUCCEEDED"
git -C "$R" log --oneline -1 brFC
echo; echo "scratch: $S"
