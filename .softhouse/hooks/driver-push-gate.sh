#!/usr/bin/env bash
# =============================================================================================
# THE DRIVER PUSH GATE.  [T412]
#
# THE DEFECT IT REFUSES, MEASURED FOUR TIMES IN THIS PROGRAM
# ---------------------------------------------------------------------------------------------
# Every worker must run `bash .softhouse/conformance.sh` from a clean tree before handing off.
# The `/softhouse-program` driver is required to do no such thing, and it is the only identity
# that writes to `main`. Four recorded instances, all on `main`, all pushed:
#
#   1. 2026-08-28  the driver wrote the token `P-100` into `.softhouse/RESUME.md` naming a
#      pattern that did not exist. RESUME.md is a DIRECTIVE file to the P-number citation
#      checker, so that is a FATAL UNDEFINED citation and `guard_pnumber_citations` is a HARD
#      guard: the bar went EXIT 2 with NO PROBE LINE AT ALL. `main` was red across three pushed
#      commits and nothing detected it. It surfaced only because an unrelated merge was graded.
#
#   2. same fire, merging T401: the driver graded a SCRATCH MERGE, then pushed a merge whose
#      tree differed from the graded one because `main` had moved underneath it. It pushed a
#      tree no bar had ever seen and came back green by luck.
#
#   3. same fire: a worker left a git worktree at `<repo>/main`; the driver's next `git add -A`
#      swept it in as a GITLINK -- `160000 af397c6b... main` -- committed at 8c08f7d8 and
#      PUSHED. A gitlink is a legal tree entry, so the push succeeded. A stray FILE would not
#      even have printed git's "embedded git repository" warning.
#
#   4. 2026-08-29 10:01:33, fire 20260829-080002, the fire that dispatched T412: the driver ran
#      the bar on `main` at 2a1dac46 (EXIT 0, probe up, VERDICT PASS 46/7884), then committed and
#      pushed b102875c WITHOUT re-running it. VERIFIED by tree identity, not by prose:
#          tree(2a1dac46, GRADED) = 617c9a853924c28a24d9fba59ca1f083acbd0a38
#          tree(b102875c, PUSHED) = 729cd8a07c986a0ebb3244ee2e6e3f47f8e18cb1
#      The commit message on b102875c itself says "graded on 2a1dac46 -- the tree that is
#      actually on main", which had stopped being true the moment that commit was written.
#
# The common shape is not "the driver forgot". It is P-45: a rule whose only enforcement is the
# reader remembering it enforces nothing. T392's handoff had REPORTED instance 1's near-miss and
# the driver reproduced it within minutes of reading that report.
#
# WHAT THIS IS
# ---------------------------------------------------------------------------------------------
# A `pre-push` gate. It engages ONLY for `refs/heads/main` and stands aside, loudly, for every
# other ref -- worker branches already run the full bar, and 35 `softhouse/*` heads exist on
# origin that must keep pushing.
#
#   C1  GITLINK REFUSAL          -- no mode 160000 entry anywhere in the pushed tree. NO BYPASS.
#   C2  DRIVER WRITE-PATH ALLOWLIST -- every path in every NON-MERGE commit of the pushed range
#       must be under `.softhouse/`, `docs/` or `.claude/`. Merge commits are exempt because they
#       lawfully carry a worker's whole branch, and that branch ran the bar.
#   C3  GRADE IDENTITY           -- the tree ACTUALLY BEING PUSHED must have been graded, or must
#       differ from a graded ancestor only inside the enumerated STATE set, in which case the
#       cheap subset is run on the pushed tree.
#
# The design decision, argued in .softhouse/handoff/T412-driver-selfgrading.md against numbers
# from fire 20260829-080002: the full bar on every push is unaffordable (15 pushes in 2h01m; the
# bar is ~4 min => ~60 of 121 minutes of the fire spent grading), and the citation checker alone
# is affordable (measured 24.98 s on the real 9,730-file tree, materialisation included) and is
# the one guard that actually reddened main.
#
# WHY THE LEDGER LIVES OUTSIDE EVERY TREE
# ---------------------------------------------------------------------------------------------
# An attestation says "tree T was graded". If the ledger were a tracked file, recording an
# attestation would change the tree, so the recorded tree would never be the tree that ships --
# instance 2 rebuilt as a data structure. The ledger is therefore written under the git COMMON
# DIR, which is in no commit. It is host state, deliberately: it is a record of what THIS host
# ran, and a fresh clone that has graded nothing must be told so rather than inheriting a claim.
#
# ENGINE (P-33/P-53): bash, git, /usr/bin/python3, POSIX grep/sed/awk. Declared, not assumed.
# =============================================================================================
set -u

GATE_NAME="driver-push-gate"

say()  { printf '%s: %s\n' "$GATE_NAME" "$*" >&2; }
die()  { printf '%s: %s\n' "$GATE_NAME" "$*" >&2; exit 1; }

# --- roots -----------------------------------------------------------------------------------
# Derived, never typed. An absolute path literal in a tracked instrument is host state and would
# also be a dead absolute path on any other machine.
TOPLEVEL="$(git rev-parse --show-toplevel 2>/dev/null)" || die "ABORT -- git rev-parse --show-toplevel failed. Not inside a work tree; refusing rather than passing."
[ -n "$TOPLEVEL" ] || die "ABORT -- empty repository root. Refusing rather than passing."
COMMON="$(git rev-parse --git-common-dir 2>/dev/null)" || die "ABORT -- git rev-parse --git-common-dir failed. Refusing rather than passing."
case "$COMMON" in
  /*) : ;;
  *)  COMMON="$TOPLEVEL/$COMMON" ;;
esac
[ -d "$COMMON" ] || die "ABORT -- the git common dir does not resolve to a directory: $COMMON"

GATE_DIR="$COMMON/softhouse-driver-gate"
ATTEST="$GATE_DIR/attest.tsv"
BYPASS_LOG="$GATE_DIR/bypass.log"
mkdir -p "$GATE_DIR" || die "ABORT -- could not create $GATE_DIR"
[ -f "$ATTEST" ] || : >"$ATTEST" || die "ABORT -- could not create the attestation ledger"

GUARDED_REF="refs/heads/main"
ZERO='0000000000000000000000000000000000000000'

# --- the driver write-path allowlist ---------------------------------------------------------
# DERIVED, not chosen: over the last 400 NON-MERGE first-parent commits on `main` the driver's
# write set is exactly `.softhouse/**` (231 tasks.json, 122 LOCK, 88 RESUME.md, 43 reviews, 31
# program.json, 27 capture, 21 patterns.md, 19 observations, 17 state, 15 gates.md, 4 bin, 3
# conformance.sh, 2 reference-oracle.md, 2 handoff), plus `docs/adr` x1 and `.claude/skills` x1.
# The ONLY other top-level entry in all 400 is the literal path `main` -- which is instance 3,
# the gitlink. So this allowlist refuses exactly the recorded defect and nothing else that has
# ever happened.
allowed_driver_path() {
  case "$1" in
    .softhouse/*|docs/*|.claude/*) return 0 ;;
    *) return 1 ;;
  esac
}

# --- the STATE set: what the cheap subset is licensed to re-grade -----------------------------
# A path is STATE only if the FOURTEEN guards the cheap subset does NOT run provably cannot read
# it. Each clause below names the guards it is there for; this is the whole fail-open surface of
# the cheap path and it is enumerated rather than hand-waved.
#
#   (a) `.softhouse/` only                  -- nexus/ Go source is guard_gofmt + the ledger
#                                              invariants + every parity vector.
#   (b) never .softhouse/vectors/**         -- guard_no_float_in_vectors, guard_accepting_side_gap.
#   (c) never .softhouse/guards/**          -- guard_guards_dir_registration, and the frontier pin.
#   (d) never .softhouse/bin/**             -- guard_reconciler_ownership reads ready-tasks.py.
#   (e) never .softhouse/toolchain/**       -- untracked build root; the frontier's known trap.
#   (f) never .softhouse/conformance.sh     -- changing the grader is never a state edit.
#   (g) extension in md|txt|json|log ONLY   -- guard_no_fail_open_instruments, guard_dead_path_
#                                              frontier and guard_no_host_state_in_lint_corpus all
#                                              select over tracked *.sh / *.py. Excluding those two
#                                              extensions removes all three corpora at once.
#   (h) no path segment named `req`         -- guard_no_float_in_capture_requests takes every *.json
#                                              whose DIRECT parent is `req`, plus every *.req.
#   (i) `.softhouse/LOCK` is admitted by name -- it has no extension.
#
# AND, orthogonally, clause (j) in the caller: the cheap path admits ADDED and MODIFIED paths
# only. A DELETION or RENAME can redden guards whose corpus it never appears in -- deleting a
# file that some tracked *.sh names by literal GROWS the dead-path frontier; deleting a `req/`
# json LOWERS a derived float floor; deleting one of the two calibration directories makes
# guard_capture_namespace's P-72 calibration lapse into a pass. Deletions take the full bar.
state_path() {
  local p="$1"
  case "$p" in
    .softhouse/vectors/*|.softhouse/guards/*|.softhouse/bin/*|.softhouse/toolchain/*) return 1 ;;
    .softhouse/conformance.sh) return 1 ;;
    */req/*) return 1 ;;
    .softhouse/LOCK) return 0 ;;
    .softhouse/*.md|.softhouse/*.txt|.softhouse/*.json|.softhouse/*.log) return 0 ;;
    .softhouse/*/*) : ;;
    *) return 1 ;;
  esac
  case "$p" in
    *.md|*.txt|*.json|*.log) return 0 ;;
    *) return 1 ;;
  esac
}

# --- bypass ----------------------------------------------------------------------------------
# C2 and C3 can be bypassed with a REASON; C1 cannot be bypassed at all. The split is argued:
# a gitlink has no legitimate use in this repository and has occurred exactly once, as the
# defect, so its false-positive cost is measured at zero. C2 and C3 have plausible legitimate
# exceptions (a driver repairing a Go merge conflict in place; a rescue push while the oracle is
# down), and a gate with no exit is a gate somebody deletes.
#
# The bypass is NOT silent, which is the difference between an exit and a hole: it demands a
# reason of at least 12 characters, prints a banner, and appends to a ledger, so "how often did
# the driver bypass this" is a countable fact for the next reviewer rather than an impression.
BYPASS="${SOFTHOUSE_DRIVER_GATE_BYPASS:-}"
bypass_ok() {
  [ -n "$BYPASS" ] || return 1
  [ "${#BYPASS}" -ge 12 ] || return 1
  return 0
}
record_bypass() {
  printf '%s\t%s\t%s\t%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$1" "$2" "$BYPASS" >>"$BYPASS_LOG" \
    || die "ABORT -- could not append to the bypass ledger. A bypass that leaves no record is a hole."
  say ""
  say "  ############################################################################"
  say "  # BYPASSED: $1"
  say "  # reason  : $BYPASS"
  say "  # recorded: ${BYPASS_LOG#"$TOPLEVEL"/}"
  say "  ############################################################################"
  say ""
}

# --- attestation ledger ----------------------------------------------------------------------
# Row: <kind>\t<tree>\t<commit>\t<iso8601>\t<detail>
attested_kind() {
  local tree="$1" k
  k="$(LC_ALL=C awk -F'\t' -v t="$tree" '$2==t {print $1}' "$ATTEST" | LC_ALL=C sort -u | LC_ALL=C tr '\n' ',')" \
    || return 1
  printf '%s' "$k"
  return 0
}

# =============================================================================================
# MAIN
# =============================================================================================
say "T412 driver push gate engaged. remote=${1:-<none>} url=${2:-<none>}"

pushes_main=0
rc_all=0

# stdin: <local ref> <local sha> <remote ref> <remote sha>, one line per ref being pushed.
while read -r LREF LSHA RREF RSHA; do
  [ -n "${RREF:-}" ] || continue

  if [ "$RREF" != "$GUARDED_REF" ]; then
    say "STANDS ASIDE for $RREF -- this gate guards $GUARDED_REF only. Worker branches run the"
    say "  full bar on their own tree before handoff; that obligation is unchanged and this gate"
    say "  neither adds to it nor substitutes for it."
    continue
  fi

  pushes_main=$((pushes_main + 1))

  if [ "$LSHA" = "$ZERO" ]; then
    say "REFUSED -- this push DELETES $GUARDED_REF."
    if bypass_ok; then record_bypass "DELETE $GUARDED_REF" "$LSHA"; continue; fi
    say "  Set SOFTHOUSE_DRIVER_GATE_BYPASS to a reason of 12+ characters if that is deliberate."
    rc_all=1; continue
  fi

  LTREE="$(git rev-parse --verify --quiet "$LSHA^{tree}")" \
    || die "ABORT -- could not resolve the tree of $LSHA. Refusing rather than passing."
  say "pushing $LSHA -> $RREF   tree=$LTREE"

  # -------------------------------------------------------------------------------------------
  # C1 -- GITLINK REFUSAL.  Instance 3.  NO BYPASS.
  # -------------------------------------------------------------------------------------------
  # P-57: no pipeline. `git ls-tree` writes to a file and awk reads the file, so a git failure
  # cannot be laundered into "the tree has no gitlinks" by a pipeline's last-command status.
  LSTREE="$(mktemp "${TMPDIR:-/tmp}/${GATE_NAME}-lstree.XXXXXXXXXX")" \
    || die "ABORT -- could not create a scratch file for the tree listing."
  git ls-tree -r "$LSHA" >"$LSTREE" \
    || { rm -f "$LSTREE"; die "ABORT -- git ls-tree failed on $LSHA. An error is never an empty tree."; }
  if ! LC_ALL=C grep -aq . "$LSTREE"; then
    rm -f "$LSTREE"
    die "ABORT -- git ls-tree listed ZERO entries for $LSHA. An empty listing here would read as a tree with no gitlinks in it."
  fi
  GL="$(LC_ALL=C awk '$1=="160000" {print $4}' "$LSTREE")" \
    || { rm -f "$LSTREE"; die "ABORT -- could not scan the tree listing for gitlinks."; }
  rm -f "$LSTREE"
  if [ -n "$GL" ]; then
    say ""
    say "C1 REFUSED -- THE PUSHED TREE CONTAINS A GITLINK (mode 160000):"
    printf '%s\n' "$GL" | while IFS= read -r g; do say "    $g"; done
    say ""
    say "  This is instance 3 exactly: a worker left a git worktree inside the repo, the driver's"
    say "  \`git add -A\` staged it as a submodule reference, git printed a warning nobody read,"
    say "  and the push succeeded because a gitlink is a legal tree entry (8c08f7d8, reverted at"
    say "  c31b0842). Remove the entry -- \`git rm --cached <path>\` -- and stage explicitly."
    say ""
    say "  THERE IS NO BYPASS FOR C1. No commit in this repository's history has ever legitimately"
    say "  carried a gitlink; the only occurrence is the defect."
    rc_all=1; continue
  fi
  say "  C1 gitlinks: none in the pushed tree."

  # -------------------------------------------------------------------------------------------
  # C2 -- DRIVER WRITE-PATH ALLOWLIST.  The quiet version of instance 3.
  # -------------------------------------------------------------------------------------------
  if [ "$RSHA" = "$ZERO" ] || ! git rev-parse --verify --quiet "$RSHA^{commit}" >/dev/null; then
    RANGE="$LSHA"
    say "  C2 range: the remote has no readable tip; grading the last 50 commits of $LSHA."
    NONMERGE="$(git rev-list --no-merges --max-count=50 "$LSHA")" \
      || die "ABORT -- git rev-list failed over $LSHA. An error is never an empty range."
  else
    RANGE="$RSHA..$LSHA"
    NONMERGE="$(git rev-list --no-merges "$RANGE")" \
      || die "ABORT -- git rev-list failed over $RANGE. An error is never an empty range."
  fi

  OUTSIDE=''
  for c in $NONMERGE; do
    while IFS= read -r p; do
      [ -n "$p" ] || continue
      allowed_driver_path "$p" && continue
      OUTSIDE="$OUTSIDE$(git rev-parse --short "$c") $p
"
    done <<EOF
$(git show --pretty=format: --name-only "$c")
EOF
  done

  if [ -n "$OUTSIDE" ]; then
    say ""
    say "C2 REFUSED -- a NON-MERGE commit in $RANGE writes outside the driver allowlist"
    say "  (.softhouse/, docs/, .claude/):"
    printf '%s' "$OUTSIDE" | while IFS= read -r l; do [ -n "$l" ] && say "    $l"; done
    say ""
    say "  Merge commits are exempt -- they lawfully carry a worker's whole branch, and that"
    say "  branch ran the bar. A non-merge commit on main is the driver's own writing, and over"
    say "  the last 400 such commits it has never lawfully left those three prefixes."
    if bypass_ok; then record_bypass "C2 allowlist" "$LSHA"; else
      say "  If this is a deliberate in-place repair, set SOFTHOUSE_DRIVER_GATE_BYPASS to a reason."
      rc_all=1; continue
    fi
  else
    say "  C2 write-path allowlist: clean ($(printf '%s\n' "$NONMERGE" | LC_ALL=C grep -c . ) non-merge commit(s) examined)."
  fi

  # -------------------------------------------------------------------------------------------
  # C3 -- GRADE IDENTITY.  Instances 1, 2 and 4.
  # -------------------------------------------------------------------------------------------
  KIND="$(attested_kind "$LTREE")" || die "ABORT -- could not read the attestation ledger $ATTEST"
  case "$KIND" in
    *FULL*)
      say "  C3 the pushed tree is ATTESTED FULL. $ATTEST says the bar was run on THIS tree."
      continue ;;
    *CHEAP*)
      say "  C3 the pushed tree already carries a CHEAP attestation from an earlier push attempt."
      continue ;;
  esac

  # Find the newest ancestor whose tree carries a FULL attestation.
  BASE=''; BASETREE=''
  ANCESTORS="$(git rev-list --max-count=400 "$LSHA")" \
    || die "ABORT -- git rev-list failed walking the ancestry of $LSHA."
  for c in $ANCESTORS; do
    t="$(git rev-parse --verify --quiet "$c^{tree}")" || continue
    k="$(attested_kind "$t")" || die "ABORT -- could not read $ATTEST"
    case "$k" in *FULL*) BASE="$c"; BASETREE="$t"; break ;; esac
  done

  if [ -z "$BASE" ]; then
    say ""
    say "C3 REFUSED -- NO GRADED ANCESTOR."
    say "  Nothing in the last 400 commits of $LSHA has a FULL bar attestation on this host, so"
    say "  there is no graded tree to measure this push against. Run:"
    say ""
    say "      bash .softhouse/hooks/bar-attest.sh $LSHA"
    say ""
    # The path below carries no trailing backtick INSIDE the quotes, deliberately: the dead-path
    # census extracts quoted string literals containing `.softhouse/`, and an escaped backtick
    # rides along into the extracted literal, which then resolves to nothing and GROWS THE
    # FRONTIER. Driven: T316-DEADPATH-FRONTIER refused with `+ .softhouse/hooks/driver-push-gate.sh
    # | .softhouse/conformance.sh\` ` before this line was reworded.
    say "  It materialises that exact tree in scratch, runs the bar (.softhouse/conformance.sh)"
    say "  there, and records the attestation only if the bar ends EXIT 0 with the probe line"
    say "  PRESENT and reading \`up\`. Grading the working tree instead is instance 2."
    if bypass_ok; then record_bypass "C3 no graded ancestor" "$LSHA"; continue; fi
    rc_all=1; continue
  fi

  say "  C3 graded ancestor: $(git rev-parse --short "$BASE")  tree=$BASETREE"

  # (j) ADDED and MODIFIED only -- see the STATE set commentary.
  NS="$(git diff --name-status "$BASE" "$LSHA")" \
    || die "ABORT -- git diff --name-status failed. An error is never an empty delta."
  NONSTATE=''
  while IFS=$'\t' read -r st p rest; do
    [ -n "${st:-}" ] || continue
    case "$st" in
      A|M) : ;;
      *)   NONSTATE="$NONSTATE[$st] ${p:-?}
"; continue ;;
    esac
    state_path "$p" && continue
    NONSTATE="$NONSTATE[$st] $p
"
  done <<EOF
$NS
EOF

  if [ -n "$NONSTATE" ]; then
    say ""
    say "C3 REFUSED -- THE PUSHED TREE WAS NEVER GRADED, and its delta from the graded ancestor"
    say "  $(git rev-parse --short "$BASE") leaves the STATE set, so the cheap subset is not"
    say "  licensed to stand in for the bar. Offending entries:"
    printf '%s' "$NONSTATE" | while IFS= read -r l; do [ -n "$l" ] && say "    $l"; done
    say ""
    say "  Run:      bash .softhouse/hooks/bar-attest.sh $LSHA"
    say ""
    say "  The STATE set is *.md/*.txt/*.json/*.log under .softhouse/ (plus .softhouse/LOCK),"
    say "  excluding vectors/, guards/, bin/, toolchain/, conformance.sh and any req/ directory,"
    say "  ADDED or MODIFIED only. Everything else can move a guard whose corpus the cheap subset"
    say "  does not read."
    if bypass_ok; then record_bypass "C3 delta leaves the STATE set" "$LSHA"; continue; fi
    rc_all=1; continue
  fi

  say "  C3 delta from the graded ancestor is confined to the STATE set. Running the cheap subset"
  say "  on the PUSHED TREE (not the working tree -- that substitution is instance 2)."

  SUB="$TOPLEVEL/.softhouse/hooks/cheap-subset.sh"
  if [ ! -f "$SUB" ]; then
    say "C3 REFUSED -- the cheap subset is ABSENT: ${SUB#"$TOPLEVEL"/}"
    say "  It is wired into this gate, so its absence is a refusal and never a pass."
    rc_all=1; continue
  fi
  SUBOUT="$(mktemp "${TMPDIR:-/tmp}/${GATE_NAME}-sub.XXXXXXXXXX")" \
    || die "ABORT -- could not create a scratch file for the cheap subset."
  bash "$SUB" "$LSHA" >"$SUBOUT" 2>&1
  SUBRC=$?
  LC_ALL=C sed -n '1,200p' "$SUBOUT" >&2
  rm -f "$SUBOUT"

  if [ "$SUBRC" -ne 0 ]; then
    say ""
    say "C3 REFUSED -- THE CHEAP SUBSET FAILED ON THE PUSHED TREE (exit $SUBRC)."
    say "  This is instance 1: a directive-zone citation naming a rule that patterns.md does not"
    say "  define. guard_pnumber_citations is HARD, so this push would take the whole bar to"
    say "  EXIT 2 with NO PROBE LINE and no verdict at all."
    if bypass_ok; then record_bypass "C3 cheap subset failed" "$LSHA"; continue; fi
    rc_all=1; continue
  fi

  printf 'CHEAP\t%s\t%s\t%s\t%s\n' "$LTREE" "$LSHA" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "delta-from-$BASE-confined-to-STATE" >>"$ATTEST" \
    || die "ABORT -- could not append the CHEAP attestation."
  say "  C3 PASS -- cheap subset clean; CHEAP attestation recorded for $LTREE."
done

if [ "$pushes_main" -eq 0 ]; then
  say "no update to $GUARDED_REF in this push. Nothing for this gate to decide."
fi

if [ "$rc_all" -ne 0 ]; then
  say ""
  say "PUSH REFUSED. Nothing was sent."
  exit 1
fi

say "PUSH ALLOWED."
exit 0
