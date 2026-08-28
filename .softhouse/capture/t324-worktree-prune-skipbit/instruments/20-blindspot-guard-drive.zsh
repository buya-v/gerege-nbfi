#!/bin/zsh
# T324 instrument 20 — THE RED/GREEN DRIVE OF THE ACTUAL PRUNE DECISION CHAIN.
#
# WHAT IT DRIVES, AND WHY IT IS NOT A COPY.
# ---------------------------------------------------------------------------
# It reconstructs the decision the wrapper's exit guard really makes:
#
#     wt_prune_check(W, BR, main, locked) == PRUNE
#       AND  wt_prune_blindspot_check(W) == ok        <- T324's addition
#       THEN git worktree remove W
#
# ...from THE SHIPPED BYTES of both halves:
#   * `wt_prune_check`            — sourced from .softhouse/bin/lib-worktree-prune.zsh
#     (unchanged by T324; T324's edit set does not include that file).
#   * `wt_prune_blindspot_check`  — EXTRACTED from a fire-program.sh given as
#     $1, between the literal markers `T324-PRUNE-BLINDSPOT-GUARD BEGIN` and
#     `... END`, and eval'd. If the markers are absent the guard is treated as
#     ABSENT — which is exactly the pre-fix world, and is how the RED arm is
#     produced: by pointing this instrument at the PRE-FIX bytes, not by
#     commenting anything out.
#
# So the same file, run twice against two versions of fire-program.sh, is the
# red run and the green run. Nothing is reimplemented; if the guard's shipped
# text stops parsing, this instrument stops running.
#
# USAGE
#   20-blindspot-guard-drive.zsh <path-to-fire-program.sh> [scratch-root]
#
#   RED   : extract main's pre-fix copy first, e.g.
#             git show main:.softhouse/bin/fire-program.sh > /tmp/prefix.sh
#             20-blindspot-guard-drive.zsh /tmp/prefix.sh /private/tmp/t324-red
#   GREEN : 20-blindspot-guard-drive.zsh .softhouse/bin/fire-program.sh /private/tmp/t324-green
#
# EXIT: 0 when every row behaved as its POLARITY declares, 1 otherwise, 2 on a
# refusal (cannot read an input, scratch root inside the real checkout).
# Fail-closed: an instrument that cannot measure prints why and exits 2 rather
# than scoring a green.
#
# SAFETY: synthetic scratch repo only. Refuses to operate inside the real
# checkout. `git worktree remove` is called ONLY on worktrees this instrument
# created, under the scratch root.

set -uo pipefail

HERE=${0:A:h}
REPO=${HERE:h:h:h:h}

TARGET=${1:-}
[[ -n "$TARGET" && -r "$TARGET" ]] || { print -u2 "usage: $0 <path-to-fire-program.sh> [scratch-root]"; exit 2 }
TARGET=${TARGET:A}

LIB="$REPO/.softhouse/bin/lib-worktree-prune.zsh"
[[ -r "$LIB" ]] || { print -u2 "REFUSE: lib not readable: $LIB"; exit 2 }

ROOT=${2:-$(mktemp -d "${TMPDIR:-/tmp}/t324-drive.XXXXXX")}
mkdir -p "$ROOT" || exit 2
ROOT=${ROOT:A}
case "$ROOT" in
  "$REPO"|"$REPO"/*) print -u2 "REFUSE: scratch root inside the real checkout"; exit 2 ;;
esac

source "$LIB" || { print -u2 "REFUSE: cannot source $LIB"; exit 2 }
whence -w wt_prune_check >/dev/null || { print -u2 "REFUSE: wt_prune_check not defined after sourcing $LIB"; exit 2 }

# --- extract the guard from the target's SHIPPED BYTES ----------------------
# awk, no pipeline into the eval, and the extraction is scored: an empty
# extraction is reported as ABSENT rather than silently eval'ing nothing and
# looking like a guard that never fires.
GUARD_SRC=$(LC_ALL=C awk '
  /T324-PRUNE-BLINDSPOT-GUARD BEGIN/ { on=1; next }
  /T324-PRUNE-BLINDSPOT-GUARD END/   { on=0 }
  on { print }
' "$TARGET")
GUARD_PRESENT=0
if [[ -n "$GUARD_SRC" ]] && print -r -- "$GUARD_SRC" | LC_ALL=C grep -q 'wt_prune_blindspot_check()'; then
  eval "$GUARD_SRC" || { print -u2 "REFUSE: the extracted guard did not parse"; exit 2 }
  whence -w wt_prune_blindspot_check >/dev/null || { print -u2 "REFUSE: wt_prune_blindspot_check not defined after eval"; exit 2 }
  GUARD_PRESENT=1
fi

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); print -r -- "  PASS  $*" }
bad() { FAIL=$((FAIL+1)); print -r -- "  FAIL  $*" }

print -r -- "T324 INSTRUMENT 20 — RED/GREEN DRIVE OF THE PRUNE DECISION CHAIN"
print -r -- "target fire-program.sh : $TARGET"
print -r -- "  sha256               : $(/usr/bin/shasum -a 256 "$TARGET" | cut -d' ' -f1)"
print -r -- "  bytes                : $(/usr/bin/stat -f %z "$TARGET")"
print -r -- "  blind-spot guard     : $( (( GUARD_PRESENT )) && print -n 'PRESENT (extracted between the markers and eval-ed)' || print -n 'ABSENT — no T324 markers in these bytes; this is the PRE-FIX chain' )"
print -r -- "  guard source lines   : $( (( GUARD_PRESENT )) && print -n ${#${(f)GUARD_SRC}} || print -n 0 )"
print -r -- "lib-worktree-prune.zsh : $LIB"
print -r -- "  sha256               : $(/usr/bin/shasum -a 256 "$LIB" | cut -d' ' -f1)"
print -r -- "root                   : $ROOT"
print -r -- "date                   : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
print -r -- "git                    : $(git --version)"
print -r -- ""

# --- synthetic host repo ----------------------------------------------------
HOST="$ROOT/host"
rm -rf "$HOST"; mkdir -p "$HOST"
git -C "$HOST" init -q -b main
git -C "$HOST" config user.name  SoftFactory
git -C "$HOST" config user.email buya.vol@gmail.com
mkdir -p "$HOST/.softhouse"
print -r -- '{"tasks": []}'    > "$HOST/.softhouse/tasks.json"
print -r -- 'ignored-scratch/' > "$HOST/.gitignore"
git -C "$HOST" add -A >/dev/null 2>&1
git -C "$HOST" commit -q -m base

# wt_prune_check's MERGED rule is a BARE `git merge-base` with no -C, so it is
# answered about the CALLER'S cwd, not about $W (FU-T318-4, still open; T324's
# edit set does not include lib-worktree-prune.zsh so it is not fixed here).
# T318 instrument 50 lost its whole first run to this. Stand inside the host.
cd "$HOST" || { print -u2 "REFUSE: cannot cd into $HOST"; exit 2 }
print -r -- "cwd                    : $PWD   (wt_prune_check's MERGED rule is cwd-relative — FU-T318-4)"
print -r -- ""

mkwt() {
  local w br
  w=$(mktemp -d "$ROOT/wt.XXXXXX") || return 1
  br="probe/${w:t}"
  rm -rf "$w"
  git -C "$HOST" worktree add -q -b "$br" "$w" main >/dev/null 2>&1 || return 1
  print -r -- "$w"
}

# --- the decision chain, exactly as run_exit_guard() sequences it ------------
decide() {   # $1 worktree  $2 branch  -> prints verdict; rc 0 = REMOVE
  local W="$1" BR="$2" V RC B BRC
  V=$(wt_prune_check "$W" "$BR" main ""); RC=$?
  if (( RC != 0 )); then print -r -- "KEEP by wt_prune_check: $V"; return 1; fi
  if (( GUARD_PRESENT )); then
    B=$(wt_prune_blindspot_check "$W"); BRC=$?
    if (( BRC != 0 )); then print -r -- "KEEP by T324 blind-spot check: $B"; return 1; fi
  fi
  print -r -- "REMOVE"
  return 0
}

# $1 label  $2 witness  $3 setup fn  $4 POLARITY: PRESERVE|PRUNE
#   PRESERVE = unrecoverable content is on disk; a correct chain must NOT remove
#   PRUNE    = nothing unrecoverable is at risk; a correct chain SHOULD remove,
#              and a chain that refuses here is INERT (T319's counter-consideration)
#
# CROSS-ROW CONTAMINATION, AND THE INSTRUMENT CAUGHT IT, NOT THE AUTHOR.
# The first run scored R5 ("plain untracked file", which the pre-fix chain is
# supposed to survive because `git worktree remove` refuses on untracked files)
# as CONTENT DESTROYED — contradicting instrument 10 shape F, which measured
# rc=128 and the content surviving on the same git. The rows had not disagreed;
# R4 had poisoned R5, R6 and R7.
#
# THE CAUSE IS A REAL PROPERTY OF GIT AND IT MAKES THE UNDERLYING FINDING WORSE.
# `git -C <linked-worktree> config status.showUntrackedFiles no` does NOT write a
# per-worktree setting. Without `extensions.worktreeConfig` it writes the SHARED
# `.git/config` [VERIFIED: the contaminated run left `showUntrackedFiles = no` at
# `$HOST/.git/config:12`, and no `.git/worktrees/*/config.worktree` existed —
# transcript evidence/20-drive-CONTAMINATED-RUN.txt]. So that one setting, made
# anywhere, silences untracked reporting for EVERY worktree of the repository at
# once, which is exactly the shape of blindness this task is about.
# The teardown below clears it between rows so each row measures its own shape.
reset_shared_config() { git -C "$HOST" config --unset-all status.showUntrackedFiles >/dev/null 2>&1; return 0 }

row() {
  local LABEL="$1" WITNESS="$2" SETUP="$3" POLARITY="$4"
  reset_shared_config
  local W; W=$(mkwt) || { bad "$LABEL: could not create worktree"; reset_shared_config; return }
  local BR="probe/${W:t}"
  "$SETUP" "$W"
  local BYTES; BYTES=$(wc -c < "$W/$WITNESS" 2>/dev/null | tr -d ' '); : ${BYTES:=0}
  local V RC; V=$(decide "$W" "$BR"); RC=$?
  local ACTED="not removed" RM_RC="-" AFTER
  if (( RC == 0 )); then
    local RM_OUT; RM_OUT=$(git -C "$HOST" worktree remove "$W" 2>&1); RM_RC=$?
    (( RM_RC == 0 )) && ACTED="REMOVED" || ACTED="remove refused: $RM_OUT"
  fi
  if [[ -e "$W/$WITNESS" ]]; then AFTER="SURVIVED ($(wc -c < "$W/$WITNESS" | tr -d ' ') bytes)"
  elif [[ -d "$W" ]];            then AFTER="dir survives, WITNESS GONE"
  else                                AFTER="WORKTREE DESTROYED, WITNESS GONE"
  fi
  print -r -- "--- $LABEL"
  print -r -- "    polarity   : $POLARITY"
  print -r -- "    witness    : $WITNESS ($BYTES bytes before the decision)"
  print -r -- "    decision   : rc=$RC  $V"
  print -r -- "    action     : $ACTED (git worktree remove rc=$RM_RC)"
  print -r -- "    outcome    : $AFTER"
  case "$POLARITY" in
    PRESERVE)
      if [[ "$AFTER" == SURVIVED* ]]; then
        ok "$LABEL  content PRESERVED"
      else
        bad "$LABEL  CONTENT DESTROYED ($BYTES bytes) — the chain pruned a worktree holding unrecoverable work"
      fi
      ;;
    PRUNE)
      if [[ "$ACTED" == REMOVED ]]; then
        ok "$LABEL  pruned, as it should be — the chain is NOT inert"
      else
        bad "$LABEL  REFUSED to prune a disposable worktree ($V) — INERTNESS: a prune check that never prunes has traded a rare catastrophe for a permanent one (T319)"
      fi
      ;;
  esac
  reset_shared_config
  print -r -- ""
}

s_clean()     { : }
s_assume()    { git -C "$1" update-index --assume-unchanged .softhouse/tasks.json >/dev/null 2>&1
                print -r -- 'IRREPLACEABLE WORKER OUTPUT HIDDEN BY assume-unchanged' > "$1/.softhouse/tasks.json" }
s_skipwt()    { git -C "$1" update-index --skip-worktree .softhouse/tasks.json >/dev/null 2>&1
                print -r -- 'IRREPLACEABLE WORKER OUTPUT HIDDEN BY skip-worktree' > "$1/.softhouse/tasks.json" }
s_both()      { git -C "$1" update-index --assume-unchanged --skip-worktree .softhouse/tasks.json >/dev/null 2>&1
                print -r -- 'IRREPLACEABLE WORKER OUTPUT HIDDEN BY BOTH BITS' > "$1/.softhouse/tasks.json" }
s_showuntr()  { git -C "$1" config status.showUntrackedFiles no >/dev/null 2>&1
                print -r -- 'UNTRACKED OUTPUT HIDDEN BY status.showUntrackedFiles=no' > "$1/.softhouse/handoff-draft.md" }
s_untracked() { print -r -- 'PLAIN UNTRACKED WORKER OUTPUT' > "$1/.softhouse/handoff-draft.md" }
s_ignored()   { mkdir -p "$1/ignored-scratch"
                print -r -- 'WORKER OUTPUT IN A GITIGNORED PATH' > "$1/ignored-scratch/notes.md" }

print -r -- "=== rows ==="
print -r -- ""
row "R1 --assume-unchanged hides a live modification" ".softhouse/tasks.json"       s_assume    PRESERVE
row "R2 --skip-worktree hides a live modification"    ".softhouse/tasks.json"       s_skipwt    PRESERVE
row "R3 both index bits at once"                      ".softhouse/tasks.json"       s_both      PRESERVE
row "R4 status.showUntrackedFiles=no hides untracked" ".softhouse/handoff-draft.md" s_showuntr  PRESERVE
row "R5 plain untracked file (no hiding)"             ".softhouse/handoff-draft.md" s_untracked PRESERVE
row "R6 CONTROL: genuinely clean, disposable worktree" ".softhouse/tasks.json"      s_clean     PRUNE

# R7 is declared as a KNOWN-UNCLOSED shape and is scored as such: it is listed
# with polarity PRUNE because the chain DOES remove it, in both the red and the
# green run, and the row exists so nobody can read this transcript as a claim
# that every kill shape is closed. See FU-T324-1 in the handoff, and the
# argument in fire-program.sh's guard comment for why gating on ignored files
# would buy this shape at the cost of permanent inertness in THIS repo.
row "R7 KNOWN-UNCLOSED: gitignored content (FU-T324-1)" "ignored-scratch/notes.md"  s_ignored   PRUNE

print -r -- "PASS=$PASS  FAIL=$FAIL"
print -r -- "scratch kept at: $ROOT"
(( FAIL == 0 )) || exit 1
exit 0
