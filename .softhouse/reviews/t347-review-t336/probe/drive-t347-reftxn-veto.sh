#!/bin/sh
# T347 — re-derive T336's ONE positive-capability claim, in a THROWAWAY repo:
# `reference-transaction` in state `prepared` GENUINELY VETOES `git worktree add`.
# This is the claim T336 rejected option (b) on ("found one that can, and it is useless
# here"), so it is worth an independent drive.  Zero blast radius.
#
# ARM 1 (RED)     hook exits 1 in `prepared` for worktree-agent-* refs -> spawn must ABORT
#                 with NOTHING created: no branch, no directory, no admin dir.
# ARM 2 (CONTROL) same hook, exits 0 -> spawn must SUCCEED.  Without this arm, arm 1's
#                 failure could be caused by anything at all (P-22).
set -u
S=${1:-/tmp/t347-reftxn}
rm -rf "$S"; mkdir -p "$S"
git init -q "$S/repo"
R="$S/repo"
git -C "$R" config user.email t347@local
git -C "$R" config user.name T347
echo one > "$R/a.txt"; git -C "$R" add a.txt; git -C "$R" commit -qm c1

mk_hook () {   # $1 = exit code for the prepared state on a worktree-agent-* ref
cat > "$R/.git/hooks/reference-transaction" <<HOOK
#!/bin/sh
IN=\$(cat)
if [ "\$1" = "prepared" ] && printf '%s' "\$IN" | grep -q 'refs/heads/worktree-agent-'; then
  echo "T347 reftxn: refusing \$IN" >&2
  exit $1
fi
exit 0
HOOK
chmod +x "$R/.git/hooks/reference-transaction"
}

report () {  # $1 = label, $2 = branch, $3 = path
  echo "  rc=$RC"
  echo "  branch $2 : $(git -C "$R" rev-parse --verify "refs/heads/$2" 2>/dev/null || echo ABSENT)"
  echo "  directory $3 : $([ -d "$3" ] && echo PRESENT || echo ABSENT)"
  echo "  admin dir : $([ -d "$R/.git/worktrees/$(basename "$3")" ] && echo PRESENT || echo ABSENT)"
}

echo "===== ARM 1 (RED): reference-transaction exits 1 in 'prepared' ====="
mk_hook 1
git -C "$R" worktree add -b worktree-agent-RED "$S/wtRED" HEAD; RC=$?
report RED worktree-agent-RED "$S/wtRED"

echo
echo "===== ARM 2 (CONTROL): the SAME hook, exiting 0 ====="
mk_hook 0
git -C "$R" worktree add -b worktree-agent-OK "$S/wtOK" HEAD; RC=$?
report OK worktree-agent-OK "$S/wtOK"
echo
echo "scratch: $S"
