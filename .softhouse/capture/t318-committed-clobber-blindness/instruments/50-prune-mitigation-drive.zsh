#!/bin/zsh
# T318 instrument 50 — P-94 obligation: DRIVE THE MITIGATION I INTEND TO CITE.
#
# P-94's rule, verbatim (patterns.md:3043):
#   "A SEVERITY DOWNGRADE THAT CITES A MITIGATION MUST DRIVE THAT MITIGATION
#    RED IN THE SAME PASS. ... a mitigation cited to lower a severity is a
#    CLAIM, not a reason. Drive it red in the same pass or do not lower the
#    severity."
#
# Instrument 20 scored `.softhouse/bin/lib-worktree-prune.zsh:121` as COVERED
# rather than BLIND, because a `git merge-base --is-ancestor` sits inside the
# +/-40-line window. That is a mitigation claim, and P-94 forbids me from
# resting a severity on it without driving it. So:
#
#   P1  the mitigation WORKING  — a worktree branch carrying a COMMITTED
#       clobber is no longer an ancestor of main, so rule 1 answers KEEP even
#       though rule 2 (`git status --porcelain`) sees a spotless tree.
#   P2  the mitigation FAILING  — the same prune check on a worktree that IS
#       merged and whose tree only LOOKS clean because
#       `git update-index --assume-unchanged` was set. rc 0 = PRUNE. The
#       modified content is destroyed on removal and no term in that file
#       could have seen it.
#
# P2 is the red arm. Without it, "worktree prune is covered" would be exactly
# the un-driven downgrade P-94 names.

set -uo pipefail

HERE=${0:A:h}
REPO=${HERE:h:h:h:h}
LIB="$REPO/.softhouse/bin/lib-worktree-prune.zsh"
GUARD="$REPO/.softhouse/guards/repo-state-attest.sh"
[[ -r "$LIB" ]]   || { print -u2 "lib not readable: $LIB"; exit 2 }
[[ -r "$GUARD" ]] || { print -u2 "guard not readable: $GUARD"; exit 2 }

ROOT=${1:-$(mktemp -d "${TMPDIR:-/tmp}/t318-prune.XXXXXX")}
mkdir -p "$ROOT" || exit 2
ROOT=${ROOT:A}
case "$ROOT" in
  "$REPO"|"$REPO"/*) print -u2 "REFUSING: scratch root inside the real checkout"; exit 2 ;;
esac

source "$LIB" || { print -u2 "cannot source $LIB"; exit 2 }
whence -w wt_prune_check >/dev/null || { print -u2 "wt_prune_check not defined after sourcing"; exit 2 }

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); print -r -- "  PASS  $*" }
bad() { FAIL=$((FAIL+1)); print -r -- "  FAIL  $*" }

print -r -- "T318 INSTRUMENT 50 — DRIVING THE lib-worktree-prune MITIGATION"
print -r -- "lib   : $LIB"
print -r -- "root  : $ROOT"
print -r -- "date  : $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- a scratch main repo with a linked worktree ---------------------------
MAIN="$ROOT/main"
rm -rf "$MAIN"
git clone -q --no-hardlinks "$REPO" "$MAIN" >/dev/null 2>&1 || { print -u2 "clone failed"; exit 2 }
git -C "$MAIN" config user.name SoftFactory        >/dev/null 2>&1
git -C "$MAIN" config user.email buya.vol@gmail.com >/dev/null 2>&1
git -C "$MAIN" checkout -q -B main                  >/dev/null 2>&1

# CWD MATTERS, AND FINDING OUT COST THIS INSTRUMENT ITS FIRST RUN.
# `wt_prune_check`'s CLEAN check is `git -C "$W" status ...` (line 121,
# worktree-anchored) but its MERGED check is a BARE `git merge-base
# --is-ancestor "$BR" "$TARGET"` (line 102, NO -C) — so the merged question is
# answered about whatever repo the CALLER is standing in, not about $W.
# Run from /tmp the first time, both arms returned rc=128 "could not determine
# merge status", and P1 scored a PASS that had nothing to do with the
# mitigation it claims to test. Transcript:
# evidence/50-prune-FAILED-FIRST-RUN.txt
# It fails CLOSED (rc!=0/1 -> KEEP), so this is a correctness asymmetry and a
# follow-up, not a fail-open. The instrument now stands inside $MAIN.
cd "$MAIN" || { print -u2 "cannot cd into $MAIN"; exit 2 }
print -r -- "cwd   : $PWD   (wt_prune_check's MERGED check is cwd-relative — see comment)"

mkwt() {   # $1 = worktree name, $2 = branch name
  local w="$ROOT/$1"
  rm -rf "$w"
  git -C "$MAIN" worktree add -q -b "$2" "$w" main >/dev/null 2>&1 || return 1
  git -C "$w" config user.name SoftFactory         >/dev/null 2>&1
  git -C "$w" config user.email buya.vol@gmail.com >/dev/null 2>&1
  print -r -- "$w"
}

# =========================================================================
print -r -- "\n=== P1 — mitigation WORKING: committed clobber on the worktree branch"
# =========================================================================
W1=$(mkwt wt1 softhouse/T318-fixture-a) || { bad "P1 could not create worktree"; }
if [[ -n "${W1:-}" ]]; then
  "$GUARD" snapshot "$W1" "$ROOT/p1.before" >/dev/null 2>&1
  (
    cd "$W1" || exit 9
    print -r -- '{"run_id": "t288-fixture", "tasks": []}' > .softhouse/tasks.json
    print -r -- '# fixture RESUME'                        > .softhouse/RESUME.md
    git add -A >/dev/null 2>&1
    git commit -q -m "fixture: committed clobber" >/dev/null 2>&1
  )
  "$GUARD" snapshot "$W1" "$ROOT/p1.after" >/dev/null 2>&1

  ST=$(git -C "$W1" status --porcelain); [[ -z "$ST" ]] && LG=CLEAN || LG=DIRTY
  OUT=$(wt_prune_check "$W1" softhouse/T318-fixture-a main "" 2>&1); RC=$?
  "$GUARD" compare "$ROOT/p1.before" "$ROOT/p1.after" --writ-branch softhouse/T318-fixture-a \
      >"$ROOT/p1.guard.log" 2>&1; GRC=$?

  print -r -- "    LEGACY (git status --porcelain) : $LG"
  print -r -- "    wt_prune_check                  : rc=$RC  $OUT"
  print -r -- "    repo-state-attest               : rc=$GRC"
  if (( RC == 1 )); then
    ok "P1  prune check answered KEEP — the merge-base rule DID cover this shape"
  else
    bad "P1  prune check answered PRUNE (rc=$RC) on a worktree carrying a committed clobber"
  fi
  (( GRC == 1 )) && ok "P1  repo-state-attest also flagged it (rc=1)" \
                 || bad "P1  repo-state-attest missed it (rc=$GRC)"
fi

# =========================================================================
print -r -- "\n=== P2 — mitigation FAILING: merged worktree, tree only LOOKS clean"
# =========================================================================
# The branch is created at main's tip and never commits, so
# `git merge-base --is-ancestor BR main` is TRUE — rule 1 says merged.
# `git update-index --assume-unchanged` then hides a real modification from
# rule 2. Both rules pass. Verdict: PRUNE. The content is destroyed on
# `git worktree remove` and NOTHING in that file could have seen it.
W2=$(mkwt wt2 softhouse/T318-fixture-b) || { bad "P2 could not create worktree"; }
if [[ -n "${W2:-}" ]]; then
  "$GUARD" snapshot "$W2" "$ROOT/p2.before" >/dev/null 2>&1
  (
    cd "$W2" || exit 9
    git update-index --assume-unchanged .softhouse/tasks.json >/dev/null 2>&1
    print -r -- 'IRREPLACEABLE WORKER OUTPUT THAT git status WILL NOT MENTION' \
      > .softhouse/tasks.json
  )
  "$GUARD" snapshot "$W2" "$ROOT/p2.after" >/dev/null 2>&1

  ST=$(git -C "$W2" status --porcelain); [[ -z "$ST" ]] && LG=CLEAN || LG=DIRTY
  BYTES=$(wc -c < "$W2/.softhouse/tasks.json" | tr -d ' ')
  OUT=$(wt_prune_check "$W2" softhouse/T318-fixture-b main "" 2>&1); RC=$?
  "$GUARD" compare "$ROOT/p2.before" "$ROOT/p2.after" --writ-branch softhouse/T318-fixture-b \
      >"$ROOT/p2.guard.log" 2>&1; GRC=$?

  print -r -- "    on-disk tasks.json              : $BYTES bytes of unrecoverable content"
  print -r -- "    LEGACY (git status --porcelain) : $LG"
  print -r -- "    wt_prune_check                  : rc=$RC  $OUT"
  print -r -- "    repo-state-attest               : rc=$GRC"
  print -r -- "    repo-state-attest findings:"
  LC_ALL=C grep -E '^  (DAMAGE|ADVISORY)' "$ROOT/p2.guard.log" | sed 's/^/      | /'

  if (( RC == 0 )); then
    ok "P2 (RED ARM) prune check answered PRUNE on a worktree hiding live content — the merge-base mitigation does NOT cover this shape"
  else
    bad "P2 (RED ARM) DID NOT REPRODUCE: prune check answered rc=$RC ($OUT). The mitigation is broader than claimed; re-read the handoff."
  fi
  (( GRC == 1 )) && ok "P2  repo-state-attest caught what the prune check could not (rc=1)" \
                 || bad "P2  repo-state-attest ALSO missed it (rc=$GRC) — my own guard is blind here"
fi

# =========================================================================
print -r -- "\n=== P3 — the THIRD mitigation: does \`git worktree remove\` catch it?"
# =========================================================================
# fire-program.sh:1364-1367 claims: "`git worktree remove` (no --force) is
# itself a THIRD, independent clean check — git refuses if it finds
# modifications we somehow missed". That is a mitigation cited in a comment,
# and P-94 forbids resting a severity on it undriven. So: actually call it on
# the P2 worktree and see whether the 61 bytes survive.
if [[ -n "${W2:-}" ]]; then
  BEFORE_BYTES=$(wc -c < "$W2/.softhouse/tasks.json" 2>/dev/null | tr -d ' ')
  RM_OUT=$(git worktree remove "$W2" 2>&1); RM_RC=$?
  if [[ -e "$W2/.softhouse/tasks.json" ]]; then
    AFTER_STATE="STILL PRESENT ($(wc -c < "$W2/.softhouse/tasks.json" | tr -d ' ') bytes)"
  elif [[ -d "$W2" ]]; then
    AFTER_STATE="worktree dir survives but the file is GONE"
  else
    AFTER_STATE="WORKTREE DIRECTORY DESTROYED"
  fi
  print -r -- "    content before                  : $BEFORE_BYTES bytes"
  print -r -- "    git worktree remove             : rc=$RM_RC  ${RM_OUT:-<no output>}"
  print -r -- "    content after                   : $AFTER_STATE"
  # POLARITY, same discipline as instrument 40's XFAIL rows: this arm PASSES
  # when the finding REPRODUCES. If `git worktree remove` ever starts
  # refusing, the finding has expired and the handoff citing it is stale —
  # which is a FAIL, loudly, rather than a quiet green.
  if (( RM_RC == 0 )) && [[ ! -e "$W2/.softhouse/tasks.json" ]]; then
    ok "P3 (RED ARM REPRODUCED) \`git worktree remove\` SUCCEEDED and the content is GONE — the 'third independent clean check' (fire-program.sh:1364) does NOT see an assume-unchanged modification. All THREE mitigations fail together."
  else
    bad "P3 RED DID NOT REPRODUCE: \`git worktree remove\` rc=$RM_RC, content $AFTER_STATE. The third mitigation is stronger than measured on 2026-08-27; re-read the handoff's claim."
  fi
fi

print -r -- "\nPASS=$PASS  FAIL=$FAIL"
print -r -- "scratch kept at: $ROOT"
(( FAIL == 0 )) || exit 1
exit 0
