#!/bin/zsh
# T324 instrument 10 — DOES `git ls-files -v` ACTUALLY COVER THE HOLE?
#
# T318's FU-T318-2 prescribes the fix as "one `git -C "$W" ls-files -v` call:
# a worktree with any tag other than `H` is never prunable". The T324 brief
# forbids me from taking that on trust:
#
#   "VERIFY THAT IS SUFFICIENT rather than taking it -- T318's own guard was
#    wrong twice and its drive, not its author, caught both. In particular:
#    does `--skip-worktree` behave the same as `--assume-unchanged` here, and
#    does `ls-files -v` see both? Answer both by experiment, not by reading
#    the man page."
#
# So this instrument answers, PER SHAPE, three questions with three
# measurements and no reading:
#   S  `git status --porcelain` -- the term every existing gate uses
#   L  `git ls-files -v`        -- the proposed replacement term
#   R  `git worktree remove` (no --force) -- does the content SURVIVE?
#
# A shape is a KILL SHAPE when S=CLEAN and R=DESTROYED. The proposed fix is
# SUFFICIENT only if L flags every kill shape, and it is NOT INERT only if L
# stays quiet on the benign shapes. Both halves are scored, because T319
# recorded the counter-consideration that a permanent fail-CLOSED is its own
# defect: "replacing a fail-OPEN with a permanent fail-CLOSED, which is the
# failure T288 exists to remove" (T319 handoff, F3a).
#
# POLARITY: rows are declared with an EXPECTATION derived from the T318
# finding, and a row that stops behaving as declared FAILS LOUDLY rather than
# passing quietly -- the same discipline as T318 instrument 50's P3 arm. If
# git ever starts refusing these removals, this instrument must go red so the
# handoff citing it is known to be stale.
#
# SAFETY: builds a SYNTHETIC repo under a scratch root and refuses to run
# anywhere inside the real checkout. Nothing here touches gerege-nbfi.

set -uo pipefail

HERE=${0:A:h}
REPO=${HERE:h:h:h:h}

ROOT=${1:-$(mktemp -d "${TMPDIR:-/tmp}/t324-taxonomy.XXXXXX")}
mkdir -p "$ROOT" || exit 2
ROOT=${ROOT:A}
case "$ROOT" in
  "$REPO"|"$REPO"/*) print -u2 "REFUSING: scratch root inside the real checkout"; exit 2 ;;
esac

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); print -r -- "  PASS  $*" }
bad() { FAIL=$((FAIL+1)); print -r -- "  FAIL  $*" }

print -r -- "T324 INSTRUMENT 10 — SKIP-BIT / BLIND-SPOT TAXONOMY"
print -r -- "root       : $ROOT"
print -r -- "date       : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
print -r -- "git        : $(git --version)"
print -r -- "uname      : $(uname -sr)"
print -r -- ""

# ---- a synthetic host repo, so the measurement is about GIT, not this repo --
HOST="$ROOT/host"
rm -rf "$HOST"; mkdir -p "$HOST"
git -C "$HOST" init -q -b main
git -C "$HOST" config user.name  SoftFactory
git -C "$HOST" config user.email buya.vol@gmail.com
mkdir -p "$HOST/.softhouse"
print -r -- '{"tasks": []}'    > "$HOST/.softhouse/tasks.json"
print -r -- '# resume'         > "$HOST/.softhouse/RESUME.md"
print -r -- 'ignored-scratch/' > "$HOST/.gitignore"
git -C "$HOST" add -A >/dev/null 2>&1
git -C "$HOST" commit -q -m "base"

# FIRST RUN FAILED HERE, AND THE INSTRUMENT — NOT ITS AUTHOR — CAUGHT IT.
# `mkwt` is always called as `W=$(mkwt)`, i.e. IN A SUBSHELL, so a counter
# incremented inside it is discarded the moment the subshell exits. Row A got
# `wt1`; every later row also asked for `wt1`, whose branch already existed,
# and `git worktree add -b` failed 7 times in a row. Transcript:
# evidence/10-taxonomy-FAILED-FIRST-RUN.txt. The name now comes from `mktemp`,
# which is subshell-safe because the uniqueness lives in the filesystem rather
# than in a shell variable.
mkwt() {   # -> prints worktree path; branch is created at main's tip (so MERGED is trivially true)
  local w br
  w=$(mktemp -d "$ROOT/wt.XXXXXX") || return 1
  br="probe/${w:t}"
  rm -rf "$w"
  git -C "$HOST" worktree add -q -b "$br" "$w" main >/dev/null 2>&1 || return 1
  git -C "$w" config user.name  SoftFactory        >/dev/null 2>&1
  git -C "$w" config user.email buya.vol@gmail.com >/dev/null 2>&1
  print -r -- "$w"
}

# ---- the three measurements ------------------------------------------------
m_status() {   # CLEAN | DIRTY | ERR<rc>
  local out rc
  out=$(git -C "$1" status --porcelain -- ':(top)' 2>/dev/null); rc=$?
  (( rc != 0 )) && { print -r -- "ERR$rc"; return }
  [[ -z "$out" ]] && print -r -- CLEAN || print -r -- DIRTY
}
m_lsfiles() {  # the distinct NON-'H' tag letters actually observed, or H-only
  local out rc tags
  out=$(git -C "$1" ls-files -v -- ':(top)' 2>/dev/null); rc=$?
  (( rc != 0 )) && { print -r -- "ERR$rc"; return }
  tags=$(printf '%s\n' "$out" | LC_ALL=C awk 'length($0)>0 && substr($0,1,1)!="H" {print substr($0,1,1)}' \
           | LC_ALL=C sort -u | tr -d '\n')
  [[ -z "$tags" ]] && print -r -- "H-only" || print -r -- "NON-H:[$tags]"
}

# ---- one row ---------------------------------------------------------------
# $1 label  $2 expectation  $3 witness path (relative)  $4 setup fn  $5 recoverable?
#   KILL           = status CLEAN and remove DESTROYS UNRECOVERABLE content; the fix MUST flag it
#   BENIGN         = nothing unrecoverable is lost; the fix must NOT flag it
#   KILL-UNCOVERED = a kill shape the ls-files term is DECLARED not to cover
#   BENIGN-FLAG-BY-DESIGN = flagged on purpose; see the case body for the race argument
#
# $5 RECOVERABLE=yes|no IS THE SECOND THING THE FIRST RUN GOT WRONG, and it is
# the more interesting of the two. The first draft scored a kill as "status
# said CLEAN and the directory is gone", and row A — a GENUINELY CLEAN
# worktree — duly failed as an "UNEXPECTED KILL SHAPE". It is not one.
# `git worktree remove` deleting a directory whose every byte is reachable
# from the branch tip destroys NOTHING; that is the operation working. WORK
# DESTRUCTION is the removal of bytes that exist ONLY on disk. Conflating the
# two would have made this instrument condemn the very cleanup the wrapper is
# supposed to perform — which is precisely the inertness T319 warns about,
# reached through a measurement error rather than a policy choice.
row() {
  local LABEL="$1" EXPECT="$2" WITNESS="$3" SETUP="$4" RECOVERABLE="$5"
  local W; W=$(mkwt) || { bad "$LABEL: could not create worktree"; return }
  "$SETUP" "$W"
  local S L BYTES RM_OUT RM_RC AFTER
  S=$(m_status "$W")
  L=$(m_lsfiles "$W")
  BYTES=$(wc -c < "$W/$WITNESS" 2>/dev/null | tr -d ' '); : ${BYTES:=0}
  RM_OUT=$(git -C "$HOST" worktree remove "$W" 2>&1); RM_RC=$?
  if [[ -e "$W/$WITNESS" ]]; then AFTER="SURVIVED ($(wc -c < "$W/$WITNESS" | tr -d ' ') bytes)"
  elif [[ -d "$W" ]];            then AFTER="dir survives, WITNESS GONE"
  else                                AFTER="WORKTREE DESTROYED"
  fi
  print -r -- "--- $LABEL"
  print -r -- "    expectation                  : $EXPECT"
  print -r -- "    witness                      : $WITNESS ($BYTES bytes on disk before removal)"
  print -r -- "    witness recoverable from git : $RECOVERABLE"
  print -r -- "    S  git status --porcelain    : $S"
  print -r -- "    L  git ls-files -v           : $L"
  print -r -- "    R  git worktree remove       : rc=$RM_RC  ${RM_OUT:-<no output>}"
  print -r -- "    R  content after             : $AFTER"

  local IS_KILL=0
  [[ "$S" == CLEAN && "$AFTER" != SURVIVED* && "$RECOVERABLE" == no ]] && IS_KILL=1
  local FLAGGED=0
  [[ "$L" == NON-H:* || "$L" == ERR* ]] && FLAGGED=1

  case "$EXPECT" in
    KILL)
      if (( IS_KILL )); then
        ok "$LABEL  KILL SHAPE REPRODUCES (status CLEAN, remove rc=$RM_RC, content gone)"
      else
        bad "$LABEL  KILL SHAPE DID NOT REPRODUCE (S=$S after=$AFTER) — the finding this task rests on may be stale on this git"
      fi
      if (( FLAGGED )); then
        ok "$LABEL  ls-files -v COVERS it ($L)"
      else
        bad "$LABEL  ls-files -v is BLIND to it ($L) — the prescribed one-call fix is NOT sufficient for this shape"
      fi
      ;;
    BENIGN)
      if (( IS_KILL )); then
        bad "$LABEL  UNEXPECTED KILL SHAPE (S=$S after=$AFTER) — a second hole, not covered by this task's brief"
      else
        ok "$LABEL  not a kill shape (S=$S, after=$AFTER)"
      fi
      if (( FLAGGED )); then
        bad "$LABEL  ls-files -v FLAGS a benign worktree ($L) — this is the INERTNESS cost T319 warns about"
      else
        ok "$LABEL  ls-files -v stays quiet ($L) — no inertness cost"
      fi
      ;;
    BENIGN-FLAG-BY-DESIGN)
      # Shape E: the skip bit is set but the content still matches, so nothing
      # unrecoverable is at risk RIGHT NOW and TERM 1 refuses anyway. The first
      # draft scored that as a false positive and this row stood permanently red.
      # It is not a false positive, and the reason is a RACE.
      #
      # TERM 1 deliberately keys on THE BIT, not on whether a difference happens
      # to exist at the instant it looks. Once the bit is set, git has been told
      # to stop comparing that path — so between this check and the
      # `git worktree remove` that follows it, a write can land and NOTHING in
      # git will report it. A version of TERM 1 that asked "is it modified yet?"
      # would have to ask the very oracle the bit has switched off, which is the
      # whole defect restated one layer down. Refusing on the bit is the only
      # answer that does not depend on timing.
      #
      # So this row PASSES when flagged, and FAILS if the flag ever goes away —
      # that would mean TERM 1 had become content-dependent and racy.
      if (( IS_KILL )); then
        bad "$LABEL  UNEXPECTED KILL SHAPE (S=$S after=$AFTER)"
      else
        ok "$LABEL  nothing unrecoverable at risk at this instant (S=$S, after=$AFTER)"
      fi
      if (( FLAGGED )); then
        ok "$LABEL  ls-files -v flags it BY DESIGN ($L) — TERM 1 keys on the BIT, not on a difference that a write could create after the check and before the removal. Measured cost on the live checkout: 0 of 55 worktrees (evidence/30-live-worktree-census.txt)"
      else
        bad "$LABEL  ls-files -v did NOT flag a worktree carrying a skip bit ($L) — TERM 1 has become content-dependent, and therefore racy"
      fi
      ;;
    KILL-UNCOVERED)
      if (( IS_KILL )); then
        ok "$LABEL  KILL SHAPE REPRODUCES (status CLEAN, remove rc=$RM_RC, content gone)"
      else
        bad "$LABEL  declared a kill shape and is not one (S=$S after=$AFTER) — update the declaration"
      fi
      if (( FLAGGED )); then
        bad "$LABEL  declared UNCOVERED but ls-files -v flagged it ($L) — the taxonomy is wrong, re-read"
      else
        ok "$LABEL  ls-files -v is BLIND to it, AS DECLARED ($L) — a SECOND blind spot, reported not fixed"
      fi
      ;;
  esac
  print -r -- ""
}

# ============================ the shapes ====================================
s_control_clean() { : }
s_assume()    { git -C "$1" update-index --assume-unchanged .softhouse/tasks.json >/dev/null 2>&1
                print -r -- 'IRREPLACEABLE WORKER OUTPUT HIDDEN BY assume-unchanged' > "$1/.softhouse/tasks.json" }
s_skipwt()    { git -C "$1" update-index --skip-worktree .softhouse/tasks.json >/dev/null 2>&1
                print -r -- 'IRREPLACEABLE WORKER OUTPUT HIDDEN BY skip-worktree' > "$1/.softhouse/tasks.json" }
s_both()      { git -C "$1" update-index --assume-unchanged --skip-worktree .softhouse/tasks.json >/dev/null 2>&1
                print -r -- 'IRREPLACEABLE WORKER OUTPUT HIDDEN BY BOTH BITS' > "$1/.softhouse/tasks.json" }
s_bit_no_mod(){ git -C "$1" update-index --assume-unchanged .softhouse/tasks.json >/dev/null 2>&1 }
s_untracked() { print -r -- 'PLAIN UNTRACKED WORKER OUTPUT' > "$1/.softhouse/handoff-draft.md" }
s_ignored()   { mkdir -p "$1/ignored-scratch"
                print -r -- 'WORKER OUTPUT IN A GITIGNORED PATH' > "$1/ignored-scratch/notes.md" }
s_showuntr()  { git -C "$1" config status.showUntrackedFiles no >/dev/null 2>&1
                print -r -- 'UNTRACKED OUTPUT HIDDEN BY status.showUntrackedFiles=no' > "$1/.softhouse/handoff-draft.md" }

print -r -- "=== shapes (S = status, L = ls-files -v, R = worktree remove) ==="
print -r -- ""
row "A control: genuinely clean worktree"        BENIGN         ".softhouse/tasks.json"       s_control_clean yes
row "B --assume-unchanged + modification"        KILL           ".softhouse/tasks.json"       s_assume        no
row "C --skip-worktree + modification"           KILL           ".softhouse/tasks.json"       s_skipwt        no
row "D both bits + modification"                 KILL           ".softhouse/tasks.json"       s_both          no
row "E skip bit set, content UNMODIFIED"         BENIGN-FLAG-BY-DESIGN ".softhouse/tasks.json" s_bit_no_mod yes
row "F plain untracked file (no bits)"           BENIGN         ".softhouse/handoff-draft.md" s_untracked     no
row "G gitignored file with content"             KILL-UNCOVERED "ignored-scratch/notes.md"    s_ignored       no
row "H status.showUntrackedFiles=no + untracked" KILL-UNCOVERED ".softhouse/handoff-draft.md" s_showuntr      no

print -r -- "PASS=$PASS  FAIL=$FAIL"
print -r -- "scratch kept at: $ROOT"
(( FAIL == 0 )) || exit 1
exit 0
