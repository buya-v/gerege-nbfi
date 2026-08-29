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

# --- where this gate's siblings live ----------------------------------------------------------
# A GATE AND ITS TOOLS ARE ONE UNIT AND MUST TRAVEL TOGETHER. Driven live at
# .softhouse/capture/t412-driver-selfgrading/out/installed-drive/13-I4-RED-bad-citation.txt: the
# gate ran from the install-time snapshot in the shared hooks directory while the pushing
# worktree sat at a commit that did not carry these files yet, and refused for the wrong reason.
# So the directory beside THIS FILE is the primary and $TOPLEVEL is the secondary, which is what
# lets a merged tree's newer copy win.
GATE_HOME="$(cd "$(dirname "$0")" 2>/dev/null && pwd)" || GATE_HOME=''

# beside_gate <basename> -- prints an ABSOLUTE path that EXISTS, or nothing, and returns 1 when
# it found none. Used for every message that tells the driver what to run next.
#
# m-4, AND IT COST A FIRE. C3's refusal used to print the bare string `bash
# .softhouse/hooks/bar-attest.sh`. The installer CHECKS FOR three files and SNAPSHOTS two, so on
# a host whose main checkout had not yet merged that file the message named a remedy that did not
# exist. The driver of fire 20260829-080002 followed it at the T350+T449 merge, found nothing,
# and had to extract the file from an unmerged branch to proceed. A refusal that names a
# nonexistent remedy is a fail-CLOSED that costs a fire, so the path is now RESOLVED AT THE
# MOMENT IT IS PRINTED and the absence is said out loud instead of being spelled as a suggestion.
beside_gate() {
  local n="$1" c
  for c in "${GATE_HOME:+$GATE_HOME/$n}" "$TOPLEVEL/.softhouse/hooks/$n"; do
    [ -n "$c" ] || continue
    if [ -f "$c" ]; then printf '%s' "$c"; return 0; fi
  done
  return 1
}

# attest_hint <commit> -- the exact command to run, or a refusal to pretend there is one.
attest_hint() {
  local p
  if p="$(beside_gate bar-attest.sh)"; then
    say "      bash $p $1"
  else
    say "      *** bar-attest.sh IS NOT ON THIS HOST ***"
    say "      It is absent from BOTH the directory beside this gate ($GATE_HOME) and the main"
    say "      checkout ($TOPLEVEL/.softhouse/hooks/). Printing a command that does not resolve"
    say "      is how this gate cost fire 20260829-080002 a merge. Restore it from"
    say "      .softhouse/hooks/bar-attest.sh on main, or re-run"
    say "      install-driver-push-gate.sh from a checkout that carries it."
  fi
}

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
#
# T453 REBUILT THIS SET AFTER T450 DROVE FOUR STATE-CONFINED DELTAS THROUGH IT AND THE FULL BAR
# THEN WENT EXIT 2 WITH NO PROBE LINE ON EVERY ONE. The reasoning error is worth stating before
# the rules, because the rules are unreadable without it:
#
#   T412 BUILT THIS SET BY ASKING, GUARD BY GUARD, "WHICH FILES DOES IT READ?".
#   That question has a right answer for a guard whose corpus is file CONTENT, and NO ANSWER AT
#   ALL for a guard whose corpus is the tree's INVENTORY.
#
# Three of the fifteen guards are the second kind, and none of them READS the file you touched:
#
#   * guard_dead_path_frontier resolves every quoted `.softhouse/` literal in every tracked
#     `.softhouse/` instrument against `git ls-files` -- the TRACKED UNIVERSE, never the disk
#     [census_dead_paths.py, `tracked_universe`]. ADDING a tracked file can make a pinned-DEAD
#     literal live, SHRINK the frontier, and refuse. Clause (j) already excluded DELETIONS for
#     exactly this reason and stopped one step short of the mirror image.
#   * guard_capture_namespace's whole population is `git ls-files` reduced to the FIRST path
#     component under `.softhouse/capture/` or `.softhouse/reviews/`. A new DIRECTORY there is a
#     new namespace id and can collide undocumented.
#   * guard_no_float_in_capture_requests has had a SECOND ARM since T193: it opens every file a
#     stored parity vector names in `provenance.capture_ref` and grades the numeric tokens inside
#     its RECORDED-REQUEST blocks. All 26 of those paths are `.softhouse/capture/**/*.json`, and
#     clause (h) below described only the FIRST arm -- the guard as it stood before T193. That is
#     not an inventory hazard; it is a READ hazard the table simply had stale.
#
# MEASURED, on this repository, so none of the above is argued from shape alone:
#   `.softhouse/uat.md` is UNTRACKED, is one of the 108 PINNED DEAD LITERALS, and adding it is
#   ordinary driver work nowhere near `capture/`. It is a `*.md` under `.softhouse/`, squarely
#   inside T412's STATE set. The gate allowed it; the bar refused it.
#
# THE RULES, and the guard each is there for. THIS IS THE WHOLE FAIL-OPEN SURFACE OF THE CHEAP
# PATH, enumerated rather than hand-waved, and it now names all fifteen guards run_guards calls.
#
#   (a) `.softhouse/` only                  -- nexus/ Go source is guard_gofmt, guard_ledger_
#                                              invariants and every parity vector.
#   (b) never .softhouse/vectors/**         -- guard_no_float_in_vectors,
#                                              guard_accepting_side_gap_declared, and the
#                                              provenance.capture_ref citation set that
#                                              guard_no_float_in_capture_requests derives.
#   (c) never .softhouse/guards/**          -- guard_guards_dir_registration, and the dead-path
#                                              frontier pin that guard_dead_path_frontier reads.
#   (d) never .softhouse/bin/**             -- guard_reconciler_ownership reads ready-tasks.py.
#   (e) never .softhouse/toolchain/**       -- untracked build root; the frontier's known trap.
#   (f) never .softhouse/conformance.sh     -- changing the grader is never a state edit.
#   (g) extension in md|txt|json|log ONLY   -- guard_no_fail_open_instruments, guard_dead_path_
#                                              frontier and guard_no_host_state_in_lint_corpus
#                                              all select over tracked *.sh / *.py, and
#                                              guard_no_narrow_catch_in_capture_rigs over *.java.
#                                              Restricting the extension removes four corpora at
#                                              once, including every `*.req` wire-bytes artefact.
#   (h) no path segment named `req`         -- guard_no_float_in_capture_requests, FIRST ARM:
#                                              every *.json whose DIRECT parent is `req`.
#   (h2) never .softhouse/capture/**        -- [T453] guard_no_float_in_capture_requests, SECOND
#        never .softhouse/reviews/**           ARM (every `provenance.capture_ref` a vector cites
#                                              is under capture/), and guard_capture_namespace,
#                                              whose entire population is these two subtrees.
#                                              MEASURED COST over the last 400 non-merge
#                                              first-parent commits on `main`: 27 entries, i.e.
#                                              4 percentage points of cheap-path coverage. That
#                                              is what closing a money non-negotiable costs here.
#   (i) `.softhouse/LOCK` is admitted by name -- it has no extension, and the driver ADDS it 34
#                                              times in those 400 commits, at the start of a
#                                              fire, which is the most latency-sensitive push
#                                              there is.
#
# TWO GUARDS ARE NAMED NOWHERE ABOVE AND THAT IS DELIBERATE, NOT THE OMISSION L-8 FOUND:
#   guard_pnumber_citations IS the cheap subset -- it is the one guard actually run, so it needs
#   no exclusion; and guard_graded_root_is_this_tree reads only $CONFORMANCE_REPO_ROOT, an
#   environment variable no tree can carry. guard_cost_census times the others and reads no path.
#
# AND, orthogonally, TWO STATUS CLAUSES in the caller:
#   (j) DELETIONS AND RENAMES TAKE THE FULL BAR. A deletion can redden guards whose corpus it
#       never appears in -- deleting a file some tracked *.sh names by literal GROWS the dead-path
#       frontier; deleting a `req/` json LOWERS a derived float floor; deleting one of the two
#       calibration directories makes guard_capture_namespace's P-72 calibration lapse into a
#       pass.
#   (k) [T453] AN ADDITION IS ADMITTED ONLY IF IT CANNOT MOVE THE DEAD-PATH FRONTIER, and that is
#       DECIDED BY MEASUREMENT AGAINST THE PUSHED TREE'S OWN PIN, not by a table in this file --
#       see `added-path-hazard.py`, invoked from C3 below. A table would rot exactly as clause
#       (h) rotted. The blunt alternative, "modifications only", was rejected with a number: it
#       takes cheap-path coverage from 88% to 71% and blocks `A .softhouse/LOCK`, the single most
#       common addition on main. Trading a fail-open for a freeze is not a fix (P-98). Measured
#       coverage under the rules as written: 84%, with 0 of the 78 historical additions blocked.
state_path() {
  # ONE `case`, AND THE ORDER IS THE ARGUMENT. T412 wrote a second `case` block below the first
  # to handle nested paths; in bash `case` the `*` metacharacter CROSSES `/`, so `.softhouse/*.md`
  # already matched `.softhouse/a/b/c.md` and the second block was unreachable code that read
  # like a rule (L-7). It is gone rather than repaired: two blocks describing one predicate is a
  # second source of truth with no owner.
  case "$1" in
    .softhouse/vectors/*|.softhouse/guards/*|.softhouse/bin/*|.softhouse/toolchain/*) return 1 ;;
    .softhouse/capture/*|.softhouse/reviews/*) return 1 ;;
    .softhouse/conformance.sh) return 1 ;;
    */req/*) return 1 ;;
    .softhouse/LOCK) return 0 ;;
    .softhouse/*.md|.softhouse/*.txt|.softhouse/*.json|.softhouse/*.log) return 0 ;;
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

# --- WHICH BYTES ARE ENFORCING?  [T453, m-5] --------------------------------------------------
# After this branch merges, the installed shim's PRIMARY is the main checkout's WORKING-TREE copy
# of this file. So an UNCOMMITTED edit here changes what is enforced, on every push, with no
# commit and no reviewer -- the same disk-versus-blob gap T454 is closing in the harness. It is
# not made fatal, because the legitimate window is real (this file is edited on a branch before
# it merges, and refusing then would freeze the driver mid-development). It is made LOUD AND
# RECORDED: the sha256 of the bytes that ran is compared with the sha256 of the committed blob,
# the divergence is banner-printed, and the running sha is written into every attestation row
# this gate appends, so `reconcile-pushed-trees.sh` can answer "was this tree graded by a gate
# that was ever committed?" after the fact rather than never.
GATE_SELF="${BASH_SOURCE[0]:-$0}"
GATE_SHA='<unknown>'
if command -v shasum >/dev/null 2>&1 && [ -f "$GATE_SELF" ]; then
  GATE_SHA="$(shasum -a 256 "$GATE_SELF" 2>/dev/null | cut -c1-16)" || GATE_SHA='<unknown>'
fi
GATE_BLOB_SHA='<not-in-HEAD>'
# THE TRACKED PATH IS A VARIABLE AND THE `HEAD:` SPELLING IS ASSEMBLED FROM IT. A quoted literal
# reading `HEAD:.softhouse/...` is a string containing `.softhouse/` that resolves to NOTHING, so
# the dead-path census would count it and the frontier would GROW -- this file has already been
# caught by that guard once, on an escaped backtick (see the C3 comment below).
GATE_TRACKED_PATH='.softhouse/hooks/driver-push-gate.sh'
if BLOBTMP="$(mktemp "${TMPDIR:-/tmp}/${GATE_NAME}-blob.XXXXXXXXXX")"; then
  if git show "HEAD:$GATE_TRACKED_PATH" >"$BLOBTMP" 2>/dev/null; then
    GATE_BLOB_SHA="$(shasum -a 256 "$BLOBTMP" 2>/dev/null | cut -c1-16)" || GATE_BLOB_SHA='<unreadable>'
  fi
  rm -f "$BLOBTMP"
fi
say "  gate bytes: running=$GATE_SHA  HEAD blob=$GATE_BLOB_SHA  ($GATE_SELF)"
if [ "$GATE_BLOB_SHA" != '<not-in-HEAD>' ] && [ "$GATE_SHA" != "$GATE_BLOB_SHA" ]; then
  say ""
  say "  ############################################################################"
  say "  # THE GATE THAT IS ENFORCING IS NOT THE GATE THAT IS COMMITTED."
  say "  # running $GATE_SHA   HEAD blob $GATE_BLOB_SHA"
  say "  # An uncommitted edit to this file changes enforcement with no commit and no"
  say "  # reviewer. This is not fatal -- a branch that has not merged yet is the"
  say "  # legitimate case -- but the running sha is recorded in every attestation row"
  say "  # below so it is RECONCILABLE afterwards rather than invisible."
  say "  ############################################################################"
  say ""
fi

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
  # THE PUSHED RANGE, resolved ONCE, before C1 -- because C1 needs it too now (L-6).
  # -------------------------------------------------------------------------------------------
  if [ "$RSHA" = "$ZERO" ] || ! git rev-parse --verify --quiet "$RSHA^{commit}" >/dev/null; then
    RANGE="$LSHA"
    say "  range: the remote has no readable tip; grading the last 50 commits of $LSHA."
    ALLCOMMITS="$(git rev-list --max-count=50 "$LSHA")" \
      || die "ABORT -- git rev-list failed over $LSHA. An error is never an empty range."
    NONMERGE="$(git rev-list --no-merges --max-count=50 "$LSHA")" \
      || die "ABORT -- git rev-list failed over $LSHA. An error is never an empty range."
  else
    RANGE="$RSHA..$LSHA"
    ALLCOMMITS="$(git rev-list "$RANGE")" \
      || die "ABORT -- git rev-list failed over $RANGE. An error is never an empty range."
    NONMERGE="$(git rev-list --no-merges "$RANGE")" \
      || die "ABORT -- git rev-list failed over $RANGE. An error is never an empty range."
  fi

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

  # C1b -- EVERY COMMIT IN THE RANGE, NOT ONLY THE TIP.  [T453, L-6]
  #
  # The tip scan above answers "is there a gitlink in the tree that lands". It does NOT answer
  # "did this push introduce one anywhere in its history", and the two differ exactly in the case
  # instance 3 actually took: 8c08f7d8 carried the gitlink and c31b0842 reverted it, so a push of
  # both together has a clean tip and a polluted history. A gitlink in history is not cosmetic --
  # it is a tree entry every future `git log --raw`, bisect and archive still carries.
  #
  # `git diff-tree -r` names the MODES on both sides of each change, so a 160000 appearing OR
  # disappearing is visible without listing whole trees. `--root` makes the first commit of a
  # fresh history diff against the empty tree rather than printing nothing. `-m` is REQUIRED and
  # is not decoration: without it `git diff-tree` prints NOTHING AT ALL for a merge commit, and a
  # gate that silently skipped every merge would be blind on exactly the commits C2 is already
  # forced to exempt.
  GLRANGE=''
  RANGE_N=0
  for c in $ALLCOMMITS; do
    RANGE_N=$((RANGE_N + 1))
    DT="$(git diff-tree -r -m --root --no-commit-id "$c")" \
      || die "ABORT -- git diff-tree failed on $c. An error is never a clean commit."
    HIT="$(printf '%s\n' "$DT" | LC_ALL=C awk '$1==":160000"||$2=="160000"{print $NF}')" \
      || die "ABORT -- could not scan $c for gitlinks."
    if [ -n "$HIT" ]; then
      GLRANGE="$GLRANGE$(git rev-parse --short "$c") $HIT
"
    fi
  done
  if [ -n "$GLRANGE" ]; then
    say ""
    say "C1 REFUSED -- A COMMIT IN $RANGE INTRODUCES OR REMOVES A GITLINK (mode 160000):"
    printf '%s' "$GLRANGE" | while IFS= read -r l; do [ -n "$l" ] && say "    $l"; done
    say ""
    say "  The pushed TREE is clean, so the tip scan above passed. That is instance 3 with its"
    say "  revert already applied: the gitlink still ships, in history, in every clone. Rewrite"
    say "  the range (\`git rebase -i\` / \`git reset\` and re-stage explicitly) rather than"
    say "  pushing a history that carries it."
    say ""
    say "  THERE IS NO BYPASS FOR C1."
    rc_all=1; continue
  fi
  say "  C1 gitlinks: none in the pushed tree, and none in any of the $RANGE_N commit(s) of $RANGE."

  # -------------------------------------------------------------------------------------------
  # C2 -- DRIVER WRITE-PATH ALLOWLIST.  The quiet version of instance 3.
  # -------------------------------------------------------------------------------------------
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
    attest_hint "$LSHA"
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

  # (j) ADDED and MODIFIED only, and (k) an ADDITION must additionally be proved harmless to the
  # dead-path frontier -- see the STATE set commentary.
  NS="$(git diff --name-status "$BASE" "$LSHA")" \
    || die "ABORT -- git diff --name-status failed. An error is never an empty delta."
  ADDEDLIST="$(mktemp "${TMPDIR:-/tmp}/${GATE_NAME}-added.XXXXXXXXXX")" \
    || die "ABORT -- could not create a scratch file for the added-path list."
  NONSTATE=''
  NADDED=0
  while IFS=$'\t' read -r st p rest; do
    [ -n "${st:-}" ] || continue
    case "$st" in
      A|M) : ;;
      *)   NONSTATE="$NONSTATE[$st] ${p:-?}
"; continue ;;
    esac
    if ! state_path "$p"; then
      NONSTATE="$NONSTATE[$st] $p
"
      continue
    fi
    if [ "$st" = A ]; then
      printf '%s\n' "$p" >>"$ADDEDLIST" \
        || die "ABORT -- could not record an added path. A list that failed to write is not an empty list."
      NADDED=$((NADDED + 1))
    fi
  done <<EOF
$NS
EOF

  if [ -n "$NONSTATE" ]; then
    rm -f "$ADDEDLIST"
    say ""
    say "C3 REFUSED -- THE PUSHED TREE WAS NEVER GRADED, and its delta from the graded ancestor"
    say "  $(git rev-parse --short "$BASE") leaves the STATE set, so the cheap subset is not"
    say "  licensed to stand in for the bar. Offending entries:"
    printf '%s' "$NONSTATE" | while IFS= read -r l; do [ -n "$l" ] && say "    $l"; done
    say ""
    say "  Run:"
    attest_hint "$LSHA"
    say ""
    say "  The STATE set is *.md/*.txt/*.json/*.log under .softhouse/ (plus .softhouse/LOCK),"
    say "  excluding vectors/, guards/, bin/, toolchain/, capture/, reviews/, conformance.sh and"
    say "  any req/ directory; ADDED or MODIFIED only. Everything else can move a guard whose"
    say "  corpus the cheap subset does not read -- including guards that never READ the file at"
    say "  all and resolve against the tree's INVENTORY."
    if bypass_ok; then record_bypass "C3 delta leaves the STATE set" "$LSHA"; continue; fi
    rc_all=1; continue
  fi

  # -------------------------------------------------------------------------------------------
  # C3(k) -- AN ADDITION IS MEASURED AGAINST THE PUSHED TREE'S OWN DEAD-PATH PIN.  [T453]
  # -------------------------------------------------------------------------------------------
  # This is the clause T412 did not have, and it is a MEASUREMENT rather than another row in the
  # table above -- because the table is what rotted. The helper reads
  # `.softhouse/guards/dead-path-frontier.pin` OUT OF THE PUSHED TREE and asks whether any added
  # path would make a pinned-DEAD literal resolve. Exit 0 is a measured negative; exit 1 names
  # the hazards; ANYTHING ELSE (missing helper, unreadable pin, empty pin, failed selftest) is a
  # REFUSAL, because an empty pin clears every addition it is asked about and that is the exact
  # negative this gate must not be able to emit unmeasured.
  if [ "$NADDED" -gt 0 ]; then
    HAZ=''
    if ! HAZ="$(beside_gate added-path-hazard.py)"; then
      rm -f "$ADDEDLIST"
      say "C3 REFUSED -- added-path-hazard.py is ABSENT from BOTH the directory beside this gate"
      say "  ($GATE_HOME) and the main checkout. It is wired into this gate, so its absence is a"
      say "  refusal and never a pass. Re-run install-driver-push-gate.sh from a checkout that"
      say "  carries it."
      rc_all=1; continue
    fi
    HAZOUT="$(mktemp "${TMPDIR:-/tmp}/${GATE_NAME}-haz.XXXXXXXXXX")" \
      || die "ABORT -- could not create a scratch file for the addition-hazard test."
    # SELFTEST FIRST (P-22). A predicate that has stopped discriminating reports a safe addition
    # in exactly the same words as a safe addition.
    if ! /usr/bin/python3 "$HAZ" --selftest >"$HAZOUT" 2>&1; then
      LC_ALL=C sed -n '1,25p' "$HAZOUT" >&2
      rm -f "$HAZOUT" "$ADDEDLIST"
      say "C3 REFUSED -- the addition-hazard test FAILED ITS OWN SELFTEST. Its verdict on these"
      say "  $NADDED added path(s) is worthless until that is fixed."
      rc_all=1; continue
    fi
    /usr/bin/python3 "$HAZ" --repo "$TOPLEVEL" --commit "$LSHA" --paths-from "$ADDEDLIST" \
      >"$HAZOUT" 2>&1
    HAZRC=$?
    LC_ALL=C sed -n '1,40p' "$HAZOUT" | while IFS= read -r l; do say "  $l"; done
    rm -f "$HAZOUT"
    if [ "$HAZRC" -ne 0 ]; then
      rm -f "$ADDEDLIST"
      say ""
      if [ "$HAZRC" -eq 1 ]; then
        say "C3 REFUSED -- AN ADDED PATH WOULD MOVE THE DEAD-PATH FRONTIER."
        say "  guard_dead_path_frontier resolves every quoted \`.softhouse/\` literal against the"
        say "  TRACKED UNIVERSE and refuses ANY movement, in either direction. Adding a file that"
        say "  a pinned-dead literal names makes that literal live, the frontier LOSES a row, and"
        say "  the full bar goes EXIT 2 with NO PROBE LINE -- which reads like a money"
        say "  non-negotiable violation and is not one. Nothing here READS the added file; its"
        say "  presence in the index is the whole mechanism, which is why the STATE-set table"
        say "  could not see it."
      else
        say "C3 REFUSED -- the addition-hazard test could not answer (exit $HAZRC). An unanswerable"
        say "  question is not a clean answer: an unreadable or empty pin would clear every"
        say "  addition it was asked about."
      fi
      say ""
      say "  Run:"
      attest_hint "$LSHA"
      if bypass_ok; then record_bypass "C3 addition hazard" "$LSHA"; continue; fi
      rc_all=1; continue
    fi
  else
    say "  C3(k) no ADDED paths in this delta; the frontier cannot move. (Test not consulted --"
    say "    it REFUSES an empty question rather than answering it.)"
  fi
  rm -f "$ADDEDLIST"

  say "  C3 delta from the graded ancestor is confined to the STATE set. Running the cheap subset"
  say "  on the PUSHED TREE (not the working tree -- that substitution is instance 2)."

  # THE SUBSET IS RESOLVED BESIDE THIS FILE, NOT FROM THE PUSHING WORKTREE. Driven live at
  # .softhouse/capture/t412-driver-selfgrading/out/installed-drive/13-I4-RED-bad-citation.txt
  # (first run): the gate ran from the install-time snapshot in the shared hooks directory, the
  # pushing worktree was checked out at a commit that does not carry these files yet, and the
  # gate refused with "the cheap subset is ABSENT" -- fail-CLOSED, but for the wrong reason, and
  # it would have refused every driver push until this branch merged. The clone drive could not
  # see this: there the repo copy is always present. A gate and its subset are ONE UNIT and must
  # travel together; $TOPLEVEL is kept only as a secondary so a merged tree's newer subset wins.
  SUB=''
  if ! SUB="$(beside_gate cheap-subset.sh)"; then
    say "C3 REFUSED -- the cheap subset is ABSENT from BOTH the directory beside this gate"
    say "  ($GATE_HOME) and the main checkout ($TOPLEVEL/.softhouse/hooks/)."
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

  # THE ROW NAMES THE GATE THAT WROTE IT. [T453, m-5] An attestation is a claim about who graded
  # what; without the grader's identity in the row, a tree graded by an uncommitted edit of this
  # file is indistinguishable afterwards from one graded by the reviewed bytes.
  printf 'CHEAP\t%s\t%s\t%s\t%s\n' "$LTREE" "$LSHA" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "delta-from-$BASE-confined-to-STATE added=$NADDED gate=$GATE_SHA headblob=$GATE_BLOB_SHA" \
    >>"$ATTEST" \
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
