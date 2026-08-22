# lib-worktree-prune.zsh — T213
#
# Decides whether a linked git worktree is safe to PRUNE. Sourced by
# fire-program.sh's exit guard, and independently sourced by the T213 fixture
# harness so the exact same decision code is what gets fixture-tested, not a
# reimplementation that could drift from what actually runs on a live fire.
#
# A worktree is prunable ONLY IF, both:
#   1. its branch is MERGED into the target branch (default: main), AND
#   2. `git -C <worktree> status --porcelain -- :(top)` both SUCCEEDS (exit 0)
#      AND returns EMPTY.
# ...subject to two more fail-closed guards found by testing this function
# against the LIVE gerege-nbfi worktree list (T213 handoff, live-repo section):
#   3. a worktree `git worktree list --porcelain` reports as `locked` is never
#      prunable, full stop, regardless of merge/clean status.
#   4. a worktree still sitting on the harness's own auto-created default
#      per-worktree branch (named exactly `worktree-<basename of the worktree
#      dir>`, e.g. `worktree-agent-a341e70251b2e0209`) is never prunable
#      either — see "the default-branch trap" below.
#
# POLARITY IS THE WHOLE POINT OF THIS FILE. This is the same class of defect
# T190 and T202 closed in fire-program.sh's rescue sweep (fire-program.sh:224,
# :262 in the annotated history) — a FAILING git command must never be read as
# "clean" or "merged". Every git invocation below has its exit status captured
# into its own variable, checked BEFORE the output is inspected, and a
# non-zero/unexpected exit status resolves to KEEP, never to PRUNE. An
# unreadable gitdir is therefore NOT-prunable by construction, not by a
# special case bolted on afterward.
#
# THE DEFAULT-BRANCH TRAP [VERIFIED against the live repo, 43 linked
# worktrees, 2026-08-22]: `git merge-base --is-ancestor B main` is TRUE both
# when B's work is done and fast-forward-merged, AND when B has simply never
# diverged from main yet (a worktree just created, before its agent has made
# a single commit) — the two are topologically identical, tip(B) is an
# ancestor of main either way. Live-repo evidence: MY OWN currently-running
# worktree's own branch, `worktree-agent-a341e70251b2e0209`, evaluated
# "MERGED" by rule 1 alone — trivially, because it has made zero commits
# beyond main, not because its work is finished. Only this worktree's
# uncommitted edits (rule 2, the clean check) kept it from a false PRUNE
# verdict at the moment it was measured — a matter of timing, not of the
# merge rule being correct. 7 of 43 live worktrees carried this exact
# default-branch pattern; all 7 happened to also be `locked` at measurement
# time (rule 3 would have caught them too), but nothing before this fix
# guaranteed a not-yet-assigned or not-yet-relocked worktree would be. Rule 4
# closes the gap at its source instead of depending on timing or on rule 3
# alone. A REAL completed task's branch is never named this way in this repo
# — every merged task branch observed lives under `softhouse/...` — so this
# rule costs nothing against genuine cleanup candidates.
#
# This file performs NO destructive action. `wt_prune_check` only classifies
# and prints its reasoning; the caller decides whether to act on a PRUNE
# verdict (fire-program.sh's exit guard does; the T213 fixture harness does
# not, when run in demonstration mode against the live repo).
#
# Usage:
#   wt_prune_check <worktree-path> <branch-name-or-""-or-"(detached)"> \
#                   [<target-branch>] [<locked-marker-or-empty>]
#     stdout: "PRUNE" or "KEEP: <reason>"
#     exit:   0 = PRUNE, 1 = KEEP (also: 1 on any git failure — fail-closed)
#   <locked-marker-or-empty>: pass whatever the caller parsed from the
#     `locked ...` porcelain line for this worktree (any non-empty string);
#     pass "" if the worktree was not reported locked.

wt_prune_check() {
  local W="$1" BR="$2" TARGET="${3:-main}" LOCKED="${4:-}"

  if [[ -z "$W" ]]; then
    print -r -- "KEEP: no worktree path given"
    return 1
  fi
  if [[ ! -d "$W" ]]; then
    print -r -- "KEEP: worktree path $W does not exist (already gone, or unreadable)"
    return 1
  fi
  if [[ -n "$LOCKED" ]]; then
    print -r -- "KEEP: worktree is locked ($LOCKED) — never prune a locked worktree"
    return 1
  fi
  if [[ -z "$BR" || "$BR" == "(detached)" ]]; then
    print -r -- "KEEP: no resolvable branch (detached HEAD, or worktree list did not report one) — cannot establish merged status"
    return 1
  fi
  if [[ "$BR" == "$TARGET" ]]; then
    print -r -- "KEEP: branch IS $TARGET — never prune the target branch's own worktree"
    return 1
  fi
  if [[ "$BR" == "worktree-$(basename -- "$W")" ]]; then
    print -r -- "KEEP: branch $BR is this worktree's own never-repurposed default branch — 'merged' would be trivial (zero divergence from $TARGET), not evidence the work is done. See 'THE DEFAULT-BRANCH TRAP' in this file's header."
    return 1
  fi

  # --- MERGED check -----------------------------------------------------
  # `git merge-base --is-ancestor <branch> <target>` is read by EXIT STATUS
  # alone, never by scraping `git branch --merged` text. rc 0 = ancestor
  # (merged); rc 1 = definitively NOT an ancestor (not merged); any OTHER rc
  # (bad revision, corrupt object, unknown ref) is an ERROR and is NOT folded
  # into "not merged" — it is its own branch, logged distinctly, and still
  # resolves to KEEP. Silently mapping "git broke" onto "not merged" would
  # happen to be safe here (both KEEP), but the branches are kept apart so a
  # reader auditing this function can tell "the branch is behind" from "git
  # could not answer" without re-deriving it from a shared exit code.
  git merge-base --is-ancestor "$BR" "$TARGET" >/dev/null 2>&1
  local MB_RC=$?
  if (( MB_RC == 1 )); then
    print -r -- "KEEP: branch $BR is not merged into $TARGET"
    return 1
  elif (( MB_RC != 0 )); then
    print -r -- "KEEP: could not determine merge status of $BR into $TARGET (git merge-base --is-ancestor rc=$MB_RC) — treated as NOT merged"
    return 1
  fi

  # --- CLEAN check --------------------------------------------------------
  # Same discipline as fire-program.sh's own T190/T202 exit guard: the exit
  # status is captured into its OWN variable on the line directly after the
  # command substitution, so it cannot be swallowed by `set -o pipefail`
  # reporting some other stage, and cannot be defaulted away by `wc -l`
  # printing "0" on empty/failed input. `:(top)` anchors the pathspec at the
  # worktree root regardless of the caller's cwd, matching the pathspec the
  # rest of this program's exit guard uses.
  local CS CS_RC
  CS=$(git -C "$W" status --porcelain -- ':(top)' 2>/dev/null)
  CS_RC=$?
  if (( CS_RC != 0 )); then
    print -r -- "KEEP: git status failed inside $W (rc=$CS_RC) — unreadable gitdir or broken worktree; refusing to treat as clean"
    return 1
  fi
  if [[ -n "$CS" ]]; then
    print -r -- "KEEP: $W has uncommitted changes"
    return 1
  fi

  print -r -- "PRUNE"
  return 0
}
