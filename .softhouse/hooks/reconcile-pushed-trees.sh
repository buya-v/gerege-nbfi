#!/usr/bin/env bash
# =============================================================================================
# FU-T412-4 -- POST-HOC RECONCILIATION OF PUSHED TREES AGAINST THE ATTESTATION LEDGER.  [T453]
#     bash .softhouse/hooks/reconcile-pushed-trees.sh [--ref <remote-tracking ref>] [--max <n>]
#
# WHY THIS EXISTS: `pre-push` IS CLIENT-SIDE AND `--no-verify` TURNS IT OFF.
# ---------------------------------------------------------------------------------------------
# T450 drove a GITLINK -- the one check the gate declares unbypassable, the tree entry this
# repository has carried exactly once, as the defect -- onto `refs/heads/main` with `git push
# --no-verify`, and the gate printed ZERO lines. That is not a hole in the gate; it is what a
# client-side hook IS. C1's "THERE IS NO BYPASS" is true about the gate and false about git.
#
# The honest answer to a bypassable pre-push check is not a louder pre-push check. It is a SECOND
# READING, taken AFTERWARDS, from evidence the bypasser did not get to choose: **what actually
# landed on the ref.** A push cannot both happen and leave no trace in the remote-tracking
# reflog, so every push -- gated, bypassed, or made from a machine with no hook at all -- is
# visible here. THIS PROGRAM CANNOT PREVENT ANYTHING. It makes the bypass COUNTABLE, which is the
# difference between an escape hatch and a hole.
#
# AND IT GIVES `bypass.log` ITS FIRST READER. T412 built a bypass ledger that nothing ever read,
# which is P-45 in miniature: a record nobody consults is a record that does not exist. Every row
# is printed here, every fire.
#
# WHAT IT CHECKS, per distinct tip in the reflog window:
#   R1  ATTESTED   the tip's TREE carries a FULL or CHEAP row in the ledger. A tip that landed
#                  with no row is a push this host's gate never graded.
#   R2  GITLINK    no mode 160000 anywhere in the tip's tree. This is C1 taken POST HOC, and it
#                  is the arm `--no-verify` cannot evade -- the entry is in the tree that landed.
#
# THE WINDOW IS DERIVED FROM THE LEDGER, NOT TYPED. Commits that predate the gate cannot be
# attested and counting them would make this instrument cry wolf on its first run, which is how a
# census gets pinned away (T299). The window is exactly the reflog tips that are DESCENDANTS of
# the OLDEST commit the ledger names. Everything older is reported as PRE-GATE and is not a
# finding.
#
# EXIT CODES -- three different facts, three different codes (T238's rule):
#   0   the window was READ and every tip in it is attested and gitlink-free -- a MEASUREMENT
#   1   at least one tip in the window is UNATTESTED or carries a GITLINK
#   2   the ledger is absent or empty, the ref has no reflog, or the window could not be built.
#       NEVER conflated with 0: an unreadable ledger would clear every push it was asked about.
#
# ENGINE (P-33/P-53): bash, git, POSIX grep/sed/awk. Declared, not assumed. No `git grep` runs
# here, so P-53's backslash-class trap cannot apply.
# =============================================================================================
set -u

ME='reconcile-pushed-trees'
say() { printf '%s: %s\n' "$ME" "$*"; }
die() { printf '%s: ABORT(%s) -- %s\n' "$ME" "$1" "$2" >&2; exit "$1"; }

REF='refs/remotes/origin/main'
MAX=80
while [ $# -gt 0 ]; do
  case "$1" in
    --ref) shift; REF="${1:-}"; [ -n "$REF" ] || die 2 "--ref needs a value" ;;
    --max) shift; MAX="${1:-}"; case "$MAX" in ''|*[!0-9]*) die 2 "--max needs a number" ;; esac ;;
    *) die 2 "unknown argument '$1'. Use --ref <ref> and --max <n>." ;;
  esac
  shift
done

TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die 2 "\`git rev-parse --show-toplevel\` failed. Not inside a work tree."
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" \
  || die 2 "\`git rev-parse --git-common-dir\` failed."
case "$COMMON" in /*) : ;; *) COMMON="$TOPLEVEL/$COMMON" ;; esac

GATE_DIR="$COMMON/softhouse-driver-gate"
ATTEST="$GATE_DIR/attest.tsv"
BYPASS_LOG="$GATE_DIR/bypass.log"

say "ref     $REF"
say "ledger  $ATTEST"

[ -f "$ATTEST" ] \
  || die 2 "the attestation ledger does not exist. There is nothing to reconcile against, and an absent ledger must never read as 'every push was graded'."
LROWS="$(LC_ALL=C grep -ac '' "$ATTEST" || true)"
case "${LROWS:-}" in ''|*[!0-9]*) LROWS=0 ;; esac
[ "$LROWS" -ge 1 ] \
  || die 2 "the attestation ledger is EMPTY. A reconciliation against zero rows would clear every push it was asked about (P-35)."
say "ledger rows: $LROWS"

# --- THE WINDOW.  Derived from the ledger's OLDEST named commit. ------------------------------
# A FILE, not a pipe: `set -u` is on and every reader below is an awk/grep over a file, so there
# is no early-exiting consumer to invert a status (P-57).
LTMP="$(mktemp "${TMPDIR:-/tmp}/$ME-ledger.XXXXXXXXXX")" || die 2 "could not create a scratch file"
trap '[ -n "${LTMP:-}" ] && rm -f "$LTMP" "$LTMP.tips" "$LTMP.trees"' EXIT
LC_ALL=C awk -F'\t' 'NF>=3 {print $3}' "$ATTEST" >"$LTMP" \
  || die 2 "could not read the commit column of the ledger."
ANCHOR=''
while IFS= read -r c; do
  [ -n "$c" ] || continue
  git rev-parse --verify --quiet "$c^{commit}" >/dev/null 2>&1 || continue
  if [ -z "$ANCHOR" ]; then ANCHOR="$c"; continue; fi
  # The OLDEST is the one that is an ancestor of the other.
  if git merge-base --is-ancestor "$c" "$ANCHOR" 2>/dev/null; then ANCHOR="$c"; fi
done <"$LTMP"
[ -n "$ANCHOR" ] \
  || die 2 "no commit named in the ledger resolves in this repository. The window cannot be built, and a window of everything would report every commit in history as ungated."
say "window  tips that DESCEND FROM $(git rev-parse --short "$ANCHOR") (the oldest commit the ledger names)"

# --- THE REFLOG OF THE REMOTE-TRACKING REF ----------------------------------------------------
# This is the evidence a bypasser does not get to choose. `--format=%H` prints the tip each entry
# recorded; duplicates are collapsed because one tree needs grading once, not once per fetch.
REFLOG="$(git reflog show --no-abbrev --format='%H' --max-count="$MAX" "$REF" 2>/dev/null)" || REFLOG=''
if [ -z "$REFLOG" ]; then
  say "the ref '$REF' has NO REFLOG ENTRIES on this host."
  say "  That is not 'no bad pushes'. It is 'this host has no record of any push to that ref' --"
  say "  a fresh clone, a different remote name, or a reflog that has expired. REFUSING to report"
  say "  a clean reconciliation from an empty window (P-35)."
  exit 2
fi
printf '%s\n' "$REFLOG" | LC_ALL=C sort -u >"$LTMP.tips"
NTIPS="$(LC_ALL=C grep -ac '' "$LTMP.tips" || true)"
case "${NTIPS:-}" in ''|*[!0-9]*) NTIPS=0 ;; esac
say "reflog  $NTIPS distinct tip(s) in the last $MAX entries of $REF"

LC_ALL=C awk -F'\t' 'NF>=2 {print $2}' "$ATTEST" | LC_ALL=C sort -u >"$LTMP.trees" \
  || die 2 "could not read the tree column of the ledger."

IN=0; PRE=0; UNATT=0; GLK=0
FINDINGS=''
while IFS= read -r tip; do
  [ -n "$tip" ] || continue
  git rev-parse --verify --quiet "$tip^{commit}" >/dev/null 2>&1 || continue
  if ! git merge-base --is-ancestor "$ANCHOR" "$tip" 2>/dev/null; then
    PRE=$((PRE + 1)); continue
  fi
  IN=$((IN + 1))
  t="$(git rev-parse --verify --quiet "$tip^{tree}")" \
    || die 2 "could not resolve the tree of $tip. An error is never an unattested tree."

  # R1 -- ATTESTED?
  if ! LC_ALL=C grep -aqx "$t" "$LTMP.trees"; then
    UNATT=$((UNATT + 1))
    FINDINGS="${FINDINGS}UNATTESTED  $(git rev-parse --short "$tip")  tree $t  $(git log -1 --format=%s "$tip" | LC_ALL=C cut -c1-60)
"
  fi

  # R2 -- GITLINK?  C1, taken post hoc. `--no-verify` cannot evade this arm: the mode is in the
  # tree that landed. P-57: git writes to a file and awk reads the file, so a git failure cannot
  # be laundered into "no gitlinks".
  LS="$(mktemp "${TMPDIR:-/tmp}/$ME-ls.XXXXXXXXXX")" || die 2 "could not create a scratch file"
  git ls-tree -r "$tip" >"$LS" \
    || { rm -f "$LS"; die 2 "git ls-tree failed on $tip. An error is never an empty tree."; }
  if ! LC_ALL=C grep -aq . "$LS"; then
    rm -f "$LS"; die 2 "git ls-tree listed ZERO entries for $tip. An empty listing would read as a tree with no gitlinks in it."
  fi
  G="$(LC_ALL=C awk '$1=="160000" {print $4}' "$LS")" || { rm -f "$LS"; die 2 "could not scan $tip for gitlinks."; }
  rm -f "$LS"
  if [ -n "$G" ]; then
    GLK=$((GLK + 1))
    FINDINGS="${FINDINGS}GITLINK     $(git rev-parse --short "$tip")  $(printf '%s' "$G" | LC_ALL=C tr '\n' ' ')
"
  fi
done <"$LTMP.tips"

# --- THE BYPASS LEDGER GETS ITS READER  [m-3] -------------------------------------------------
NBY=0
if [ -f "$BYPASS_LOG" ]; then
  NBY="$(LC_ALL=C grep -ac '' "$BYPASS_LOG" || true)"
  case "${NBY:-}" in ''|*[!0-9]*) NBY=0 ;; esac
  say "bypass  $NBY recorded bypass(es) at $BYPASS_LOG:"
  LC_ALL=C sed -n '1,40p' "$BYPASS_LOG" | while IFS= read -r l; do say "          $l"; done
else
  # A MEASURED absence, and the measurement is stated: the gate CREATES its directory on every
  # run, so "the file is not there" means "no bypass has been recorded here", not "nobody looked".
  say "bypass  none recorded on this host (the gate creates $GATE_DIR on every run, so the"
  say "          absence of $BYPASS_LOG is a measured zero and not an unread file)."
fi

say ""
say "T453-RECONCILE: ref=$REF window=$IN pre-gate=$PRE unattested=$UNATT gitlinks=$GLK bypasses=$NBY"
if [ -n "$FINDINGS" ]; then
  say ""
  # NO BACKTICKS INSIDE A DOUBLE-QUOTED say ARGUMENT. In bash a backtick pair inside "" is
  # COMMAND SUBSTITUTION, so the first draft of these three lines tried to EXECUTE --no-verify.
  # It is worth a comment because the failure would have appeared only on the refusal path, i.e.
  # only when this instrument is finally telling somebody something important.
  say "FINDINGS -- a tip landed on $REF that this host's gate never graded, or that carries a"
  say "  gitlink. A --no-verify push, a push from an ungated machine, and a hook that was never"
  say "  installed all present here identically, and all three are the same problem."
  printf '%s' "$FINDINGS" | while IFS= read -r l; do [ -n "$l" ] && say "  $l"; done
  exit 1
fi
if [ "$IN" -lt 1 ]; then
  say "NO TIP IN THE WINDOW. Every reflog entry predates the ledger's oldest commit, so nothing"
  say "  was reconciled. That is not a clean result -- it is an empty one. REFUSING (P-35)."
  exit 2
fi
say "RECONCILED CLEAN -- $IN tip(s) in the window, every one attested and gitlink-free."
exit 0
