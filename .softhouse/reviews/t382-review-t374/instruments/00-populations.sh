#!/bin/bash
# T382 — enumerate the fork-sha vs HEAD observation populations in the scratch clone,
# so the attack targets are CHOSEN by measurement rather than guessed.
set -u
# HOST STATE IS A PARAMETER, NOT A LITERAL (guard_no_host_state_in_lint_corpus).
# A /tmp path assigned to a name in a tracked instrument is shared across worktrees,
# absent from every commit and deleted on reboot. Supply them:
#   T382_CLONE=<throwaway clone> T382_OUT=<scratch dir> bash <this script>
# The committed transcripts were produced with T382_OUT=/tmp/t382-out and the clone
# named in each transcript's first line.
SC="${T382_CLONE:?set T382_CLONE to a throwaway clone of this repo}"
O="${T382_OUT:?set T382_OUT to a scratch output directory}"
FORK=12a7f8d9a3af4665fd5281a9f9c001d4f1276a53
mkdir -p "$O"
git -C "$SC" ls-tree -r --name-only "$FORK" -- .softhouse/capture/tierA-a2/out .softhouse/capture/tierA-a2/req | sort > "$O/pop-fork.txt"
git -C "$SC" ls-tree -r --name-only HEAD  -- .softhouse/capture/tierA-a2/out .softhouse/capture/tierA-a2/req | sort > "$O/pop-head.txt"
comm -13 "$O/pop-fork.txt" "$O/pop-head.txt" > "$O/pop-postfork.txt"
echo "fork-sha observations : $(wc -l < "$O/pop-fork.txt" | tr -d ' ')"
echo "HEAD observations     : $(wc -l < "$O/pop-head.txt" | tr -d ' ')"
echo "post-fork (ARM A blind): $(wc -l < "$O/pop-postfork.txt" | tr -d ' ')"
echo
echo "--- first 5 post-fork observations ---"
head -5 "$O/pop-postfork.txt"
