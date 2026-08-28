#!/bin/bash
# T382 — re-run T374's OWN prover on the merge result, independently, to check that its
# claimed 28/28 reproduces outside the author's worktree. Runs in the throwaway clone
# /tmp/t382-scratch, which is at the T374 merge result and has been reset to pristine.
set -u
SC=/tmp/t382-scratch
O=/tmp/t382-out
mkdir -p "$O"
git -C "$SC" reset --hard --quiet t382-pristine
git -C "$SC" clean -fdq
echo "at: $(git -C "$SC" log --oneline -1)"
( cd "$SC" && bash .softhouse/capture/t374-t362-conditions/prove-t374-fixes-can-fail.sh ) > "$O/prover-rerun.txt" 2>&1
echo "prover EXIT=$?"
tail -20 "$O/prover-rerun.txt"
echo "--- working tree after the prover (T374 discloses it rewrites tracked evidence) ---"
git -C "$SC" status --porcelain | head -20
