#!/bin/bash
# T382 — re-run T374's OWN prover on the merge result, independently, to check that its
# claimed 28/28 reproduces outside the author's worktree. Runs in the throwaway clone
# /tmp/t382-scratch, which is at the T374 merge result and has been reset to pristine.
set -u
# HOST STATE IS A PARAMETER, NOT A LITERAL (guard_no_host_state_in_lint_corpus).
# A /tmp path assigned to a name in a tracked instrument is shared across worktrees,
# absent from every commit and deleted on reboot. Supply them:
#   T382_CLONE=<throwaway clone> T382_OUT=<scratch dir> bash <this script>
# The committed transcripts were produced with T382_OUT=/tmp/t382-out and the clone
# named in each transcript's first line.
SC="${T382_CLONE:?set T382_CLONE to a throwaway clone of this repo}"
O="${T382_OUT:?set T382_OUT to a scratch output directory}"
mkdir -p "$O"
git -C "$SC" reset --hard --quiet t382-pristine
git -C "$SC" clean -fdq
echo "at: $(git -C "$SC" log --oneline -1)"
( cd "$SC" && bash .softhouse/capture/t374-t362-conditions/prove-t374-fixes-can-fail.sh ) > "$O/prover-rerun.txt" 2>&1
echo "prover EXIT=$?"
tail -20 "$O/prover-rerun.txt"
echo "--- working tree after the prover (T374 discloses it rewrites tracked evidence) ---"
git -C "$SC" status --porcelain | head -20
