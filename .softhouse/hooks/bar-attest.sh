#!/usr/bin/env bash
# =============================================================================================
# BAR ATTESTATION.  [T412]   `bash .softhouse/hooks/bar-attest.sh [<commit-ish>]`
#
# Runs `bash .softhouse/conformance.sh` against a NAMED COMMIT'S TREE, materialised in scratch,
# and records the result in the attestation ledger keyed BY THAT TREE'S SHA.
#
# THIS IS THE ONLY WAY TO SATISFY THE DRIVER PUSH GATE'S C3, AND THAT IS DELIBERATE.
# The alternative -- letting the driver hand the gate an existing bar transcript -- was rejected:
# a transcript is bytes, and nothing in it binds it to the tree it claims to have graded. That is
# T314's witness-path forgery in a new costume. Here the tool checks the tree out ITSELF, so the
# tree it records is unforgeably the tree it graded.
#
# IT ALSO CLOSES INSTANCE 2 MECHANICALLY. On 2026-08-28 the driver ran the bar in a scratch merge
# directory, then pushed a merge commit whose tree had moved underneath it, and noticed only
# because it happened to compare two tree hashes by hand. This tool cannot make that mistake: it
# is given a commit, it resolves that commit's tree, it grades THAT, and the ledger row is the
# tree -- there is no path through it that grades one thing and records another.
#
# ACCEPTANCE, and every clause is checked in this order for a reason:
#   1. `grep -c 'probe = '` >= 1                  -- PRESENCE BEFORE VALUE. Four exit-2 paths in
#      conformance.sh run BEFORE the probe prints, including a failed HARD guard, so an ABSENT
#      probe line is not `down` -- it is "no verdict is available" (P-84).
#   2. every probe line reads `up`                -- an oracle outage is not a pass.
#   3. a `VERDICT: PASS` line is present.
#   4. the bar's exit status is 0 -- OR, under DEC-2 §4.4.2, the exit is 2 AND the refusal is
#      the RECORDED DECISION: the ledger finding set matched its pinned baseline EXACTLY (re-run
#      here, never read from the banner), and the transcript says the exit was that recorded
#      decision. Any other non-zero exit is refused.
# All four (with the one named exception), or no attestation is written. A partial pass is not
# an attestation of anything.
#
# ENGINE (P-33/P-53): bash, git, POSIX grep/sed. Declared, not assumed.
# =============================================================================================
set -u

say() { printf 'bar-attest: %s\n' "$*"; }
die() { printf 'bar-attest: %s\n' "$*"; exit 3; }

REF="${1:-HEAD}"

TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || die "ABORT(3) -- \`git rev-parse --show-toplevel\` failed. Not inside a work tree."
[ -n "$TOPLEVEL" ] || die "ABORT(3) -- empty repository root."
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" \
  || die "ABORT(3) -- \`git rev-parse --git-common-dir\` failed."
case "$COMMON" in /*) : ;; *) COMMON="$TOPLEVEL/$COMMON" ;; esac

COMMIT="$(git rev-parse --verify --quiet "$REF^{commit}")" \
  || die "ABORT(3) -- '$REF' does not resolve to a commit."
TREE="$(git rev-parse --verify --quiet "$COMMIT^{tree}")" \
  || die "ABORT(3) -- could not resolve the tree of $COMMIT."

GATE_DIR="$COMMON/softhouse-driver-gate"
ATTEST="$GATE_DIR/attest.tsv"
mkdir -p "$GATE_DIR" || die "ABORT(3) -- could not create $GATE_DIR"

D="$(mktemp -d "${TMPDIR:-/tmp}/t412-attest.XXXXXXXXXX")" \
  || die "ABORT(3) -- could not create a scratch directory."
WT="$D/wt"

cleanup() {
  # The worktree registry entry is removed before the directory, and both are best-effort at
  # EXIT because a failed prune must not overwrite the exit status of the grading run itself.
  if [ -d "$WT" ]; then
    git worktree remove --force "$WT" >/dev/null 2>&1
  fi
  git worktree prune >/dev/null 2>&1
  if [ -n "${D:-}" ] && [ -d "$D" ]; then
    rm -rf "$D"
  fi
}
trap cleanup EXIT

say "commit $COMMIT"
say "tree   $TREE"
say "scratch worktree $WT"

# The FULL bar needs a real work tree with a real .git link -- guard_graded_root_is_this_tree and
# several guards call `git rev-parse --show-toplevel` and `git ls-files` from $REPO_ROOT. A bare
# checkout-index directory would not satisfy them, so this one uses `git worktree add --detach`,
# which is the shape every other task in this program already uses for merge-result grading, and
# it is pruned on exit.
git worktree add --detach "$WT" "$COMMIT" >"$D/wt-add.log" 2>&1 \
  || { LC_ALL=C sed -n '1,20p' "$D/wt-add.log"; die "ABORT(3) -- \`git worktree add\` failed for $COMMIT."; }

WTTREE="$(git -C "$WT" rev-parse --verify --quiet 'HEAD^{tree}')" \
  || die "ABORT(3) -- could not read the scratch worktree's HEAD tree."
if [ "$WTTREE" != "$TREE" ]; then
  die "ABORT(3) -- the scratch worktree checked out tree $WTTREE, not $TREE. REFUSING: grading one tree and recording another is the defect this tool exists to close."
fi

BAR="$WT/.softhouse/conformance.sh"
[ -f "$BAR" ] || die "ABORT(3) -- .softhouse/conformance.sh is absent from tree $TREE. It is the bar; its absence is a refusal and never a pass."

LOG="$D/bar.log"
say "running the bar (this takes minutes) ..."
( cd "$WT" || exit 9; bash .softhouse/conformance.sh ) >"$LOG" 2>&1
BARRC=$?
say "bar exit: $BARRC"

if [ "$BARRC" -eq 9 ]; then
  die "ABORT(3) -- could not enter the scratch worktree. 9 is this tool's own code for that, and it is never a bar verdict."
fi

# 1. PRESENCE BEFORE VALUE.
PROBE_N="$(LC_ALL=C grep -ac 'probe = ' "$LOG")"
case "${PROBE_N:-}" in ''|*[!0-9]*) PROBE_N=0 ;; esac
say "probe lines PRINTED: $PROBE_N"
if [ "$PROBE_N" -lt 1 ]; then
  say "REFUSED -- the probe line was NEVER PRINTED. Four exit-2 paths run before it, including a"
  say "  failed HARD guard. ABSENCE IS NOT \`down\`; it is 'no verdict is available' (P-84)."
  LC_ALL=C grep -aE '^conformance: (EXIT|.*REFUSED|.*FAILED)' "$LOG" | LC_ALL=C sed -n '1,20p'
  LC_ALL=C sed -n '$p' "$LOG"
  cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
  say "  transcript kept at ${GATE_DIR}/last-refused-bar.log"
  exit 1
fi

# 2. VALUE.
NOT_UP="$(LC_ALL=C grep -a 'probe = ' "$LOG" | LC_ALL=C grep -av 'probe = up')"
if [ -n "$NOT_UP" ]; then
  say "REFUSED -- a probe line does not read \`up\`:"
  printf '%s\n' "$NOT_UP" | LC_ALL=C sed -n '1,5p'
  cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
  exit 1
fi

# 3. VERDICT.
if ! LC_ALL=C grep -aq 'VERDICT: PASS' "$LOG"; then
  say "REFUSED -- no \`VERDICT: PASS\` line in the transcript."
  LC_ALL=C grep -a 'VERDICT' "$LOG" | LC_ALL=C sed -n '1,10p'
  cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
  exit 1
fi

# 4. EXIT STATUS -- with the ONE exception DEC-2 §4.4.2 ratifies.
#    Exit 0 is a green attestation, exactly as before. Exit 2 is attestable ONLY as the
#    RECORDED DECISION: the graded tree's ledger finding set must match its pinned baseline
#    EXACTLY (the comparison is RE-RUN here against the graded tree -- a banner in the
#    transcript is not evidence), AND the transcript must say the exit was that recorded
#    decision and not some other post-grading refusal. Any other non-zero exit is refused.
case "$BARRC" in
  0) ATTEST_MODE="green" ;;
  2)
    CMP_LOG="$D/compare.log"
    ( cd "$WT" || exit 9; bash .softhouse/guards/ledger-invariants-compare.sh ) >"$CMP_LOG" 2>&1
    CMPRC=$?
    if [ "$CMPRC" -eq 9 ]; then
      die "ABORT(3) -- could not enter the scratch worktree to re-run the §4.4.2 comparison."
    fi
    say "§4.4.2 comparison exit: $CMPRC"
    RECORDED_EXIT=0
    if LC_ALL=C grep -aq '§4.4.2-RECORDED-DECISION-EXIT' "$LOG"; then
      RECORDED_EXIT=1
    fi
    if [ "$CMPRC" -eq 0 ] && [ "$RECORDED_EXIT" -eq 1 ]; then
      ATTEST_MODE="recorded"
    else
      say "REFUSED -- the bar exited 2, but this is not the recorded-decision state:"
      if [ "$CMPRC" -ne 0 ]; then
        say "  the ledger finding set did NOT match the pinned baseline (comparison exit $CMPRC):"
        LC_ALL=C sed -n '1,20p' "$CMP_LOG"
      fi
      if [ "$RECORDED_EXIT" -ne 1 ]; then
        say "  the transcript does not record a §4.4.2 recorded-decision exit, so the non-zero exit"
        say "  was caused by something else and must not be attested."
      fi
      cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
      exit 1
    fi
    ;;
  *)
    say "REFUSED -- the bar exited $BARRC. A probe line and a verdict do not outrank a non-zero exit."
    cp "$LOG" "$GATE_DIR/last-refused-bar.log" 2>/dev/null
    exit 1
    ;;
esac

# ---- GRADER IDENTITY ON THE ROW.  [T465 / C-T461-2] -----------------------------------------
# The CHEAP rows the push gate writes have carried `gate=`/`headblob=` since T453; the FULL rows
# written here carried NO grader identity at all, so a post-hoc reader could not tell a tree
# graded by the reviewed bytes from one graded by an uncommitted edit -- for exactly the half of
# the ledger that claims the most. T465 decided that asymmetry the way m-3 decided `bypass.log`:
# the field is READ (reconcile-pushed-trees.sh grades it, R3) and therefore it is WRITTEN by
# BOTH writers. Three shas, and they answer three different questions:
#     bar=          the conformance.sh that actually ran. It comes OUT OF THE GRADED TREE
#                   (line ~89), so this row records WHAT the tree used to grade itself -- the
#                   self-grading T412 named, made legible instead of implicit.
#     gate=         the bytes of THIS file as they ran. SPELT `gate=`, not `attester=`, on
#                   purpose: it is the same field name the CHEAP rows use, so ONE reader grades
#                   BOTH kinds of row. Two names for one fact is how a reader ends up checking
#                   half the ledger.
#     headblob=     this file as HEAD has it. gate != headblob means the attestation was
#                   produced by an edit nobody has reviewed.
# UNRESOLVABLE IS SPELT, NEVER BLANK: `<unknown>` and `<not-in-HEAD>` are values a reader can
# act on; an empty field would be indistinguishable from a row written before this change.
BAR_SHA="$(shasum -a 256 "$BAR" 2>/dev/null | LC_ALL=C cut -c1-16)" || BAR_SHA=''
[ -n "$BAR_SHA" ] || BAR_SHA='<unknown>'
ATTESTER_SELF="$0"
ATTESTER_SHA="$(shasum -a 256 "$ATTESTER_SELF" 2>/dev/null | LC_ALL=C cut -c1-16)" || ATTESTER_SHA=''
[ -n "$ATTESTER_SHA" ] || ATTESTER_SHA='<unknown>'
ATTESTER_BLOB='<not-in-HEAD>'
ATTESTER_REL="$(git -C "$TOPLEVEL" ls-files --full-name -- "$ATTESTER_SELF" 2>/dev/null | LC_ALL=C sed -n '1p')" || ATTESTER_REL=''
if [ -n "$ATTESTER_REL" ]; then
  BLOBTMP="$(mktemp "${TMPDIR:-/tmp}/t412-attester-blob.XXXXXXXXXX")" || BLOBTMP=''
  if [ -n "$BLOBTMP" ]; then
    if git -C "$TOPLEVEL" show "HEAD:$ATTESTER_REL" >"$BLOBTMP" 2>/dev/null; then
      ATTESTER_BLOB="$(shasum -a 256 "$BLOBTMP" 2>/dev/null | LC_ALL=C cut -c1-16)" || ATTESTER_BLOB='<unreadable>'
    fi
    rm -f "$BLOBTMP"
  fi
fi
say "grader bytes: bar=$BAR_SHA attester=$ATTESTER_SHA HEAD blob=$ATTESTER_BLOB"
if [ "$ATTESTER_BLOB" != '<not-in-HEAD>' ] && [ "$ATTESTER_SHA" != "$ATTESTER_BLOB" ]; then
  say "  NOTE: this attester's running bytes DIFFER from the blob HEAD carries. The row below"
  say "  records both, so the difference survives this log and can be read post hoc (R3)."
fi

VERDICT="$(LC_ALL=C grep -a 'VERDICT: PASS' "$LOG" | LC_ALL=C sed -n '1p' | LC_ALL=C tr '\t' ' ')"
case "$ATTEST_MODE" in
  recorded) EXIT_TAG="exit2-DEC-2-4.4.2-recorded" ;;
  *)        EXIT_TAG="exit0" ;;
esac
printf 'FULL\t%s\t%s\t%s\t%s\n' "$TREE" "$COMMIT" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  "$EXIT_TAG probe=${PROBE_N}xup bar=$BAR_SHA gate=$ATTESTER_SHA headblob=$ATTESTER_BLOB ${VERDICT}" >>"$ATTEST" \
  || die "ABORT(3) -- could not append the attestation. An attestation that was not recorded is not an attestation."

cp "$LOG" "$GATE_DIR/attested-${TREE}.log" 2>/dev/null

say ""
say "ATTESTED FULL -- tree $TREE"
if [ "$ATTEST_MODE" = "recorded" ]; then
  say "  exit 2 BY RECORDED DECISION (DEC-2 §4.4.2): ledger findings == baseline, probe PRESENT x$PROBE_N all reading \`up\`, $VERDICT"
else
  say "  exit 0, probe PRESENT x$PROBE_N all reading \`up\`, $VERDICT"
fi
say "  ledger:     $ATTEST"
say "  transcript: ${GATE_DIR}/attested-${TREE}.log"
exit 0
