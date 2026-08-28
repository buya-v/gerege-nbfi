#!/usr/bin/env bash
# .softhouse/guards/repo-state-attest.sh — T318 (FU-T304-2)
#
# WHY THIS EXISTS
# ---------------
# This program's damage-detection posture rests on "`git status --porcelain`
# comes back empty". T304 proved that predicate reports SAFE on the worst
# available outcome: `.softhouse/reviews/t288-drive/build-fixture.sh`, run with
# a dead `cd`, re-inited the surrounding repo, rewrote `git config
# user.name`/`user.email`, replaced `tasks.json`/`RESUME.md`/`program.json`,
# `git add -A && git commit`ed the replacement ONTO THE CHECKED-OUT BRANCH and
# `git checkout -b`'d away. `git status --porcelain` came back EMPTY.
# [VERIFIED: T304 handoff, section "And my own verdict predicate was blind".]
#
# WHAT THIS IS
# ------------
# A repo-state ATTESTATION, not a cleanliness predicate. It is DIFFERENTIAL:
#     snapshot BEFORE -> run the operation -> snapshot AFTER -> compare
#         against the operation's DECLARED WRIT.
# "Is the tree clean?" is the wrong question, and it is why the old gate is
# blind. The right question is "does the repo differ from what this operation
# was authorized to change?" -- which cannot be answered by a predicate over a
# single state.
#
# USAGE
#   repo-state-attest.sh snapshot     <repo-dir> <out-file>
#   repo-state-attest.sh compare      <before-file> <after-file> [OPTIONS]
#   repo-state-attest.sh survey       <repo-dir>                     (T325)
#   repo-state-attest.sh fire-compare <before-file> <after-file>     (T325)
#
#   OPTIONS to compare (the WRIT -- what the operation was allowed to do):
#     --writ-branch <name>     this ref may FAST-FORWARD (and only fast-forward).
#                              Repeatable. Default: none may move.
#     --writ-ref <ere>         T325. Any ref whose FULL NAME matches this ERE may
#                              FAST-FORWARD. Repeatable. `--writ-branch main` is
#                              shorthand for `--writ-ref '^refs/heads/main$'`
#                              that also authorizes HEAD to sit on it.
#     --allow-new-ref <ere>    a newly created ref matching this ERE is
#                              authorized. Repeatable. Default: none.
#     --allow-deleted-ref <ere>
#                              T325. A DELETED ref matching this ERE is
#                              authorized ONLY IF its tip is still REACHABLE from
#                              a surviving writ ref (i.e. the branch was merged).
#                              An ERE can never authorize destroying unmerged
#                              work -- reachability is MEASURED, not asserted.
#     --allow-dirty            a non-empty `git status` is expected (e.g. a
#                              mid-operation snapshot). Default: dirty = damage.
#     --scratch-prefix <path>  newly IGNORED files under this path are expected.
#     --writ-artefact <path>   this invariant artefact may change in HEAD.
#                              `ALL` names every one of them.
#     --artefact-advisory      T325. An UNDECLARED invariant-artefact change is
#                              reported as ADVISORY instead of DAMAGE. For gates
#                              whose operation legitimately merges other agents'
#                              branches and therefore cannot enumerate, in
#                              advance, which artefacts will move. See the
#                              rationale at the T7 block -- this is a REDUCTION in
#                              power, taken deliberately, and it is the term that
#                              would otherwise fire on an ordinary merge fire and
#                              get the whole guard switched off.
#
# EXIT CODES  (fail CLOSED -- "I could not measure" is never "clean")
#     0  NO DAMAGE   every observed delta is inside the writ
#     1  DAMAGE      at least one delta outside the writ
#     2  REFUSED     could not measure (bad repo, git not answering, bad args)
#
# T325 -- WHY THERE IS A SINGLE-STATE `survey` NEXT TO THE DIFFERENTIAL `compare`
# -------------------------------------------------------------------------------
# `compare` is the real instrument and nothing here demotes it. But two of the
# five blind gates have NO "before" available to them at the moment they fire:
#   * a fire's PRE-FLIGHT gate runs before anything of this fire has happened, so
#     what it needs is not a delta but a BASELINE READING -- the exact concern
#     FU-T318-5 names, "an undetected clobber from the previous fire silently
#     adopted as the baseline";
#   * the worker-worktree sweep meets worktrees that were CREATED DURING the fire
#     it is ending, so no snapshot of them can exist from before it started.
# `survey` is the subset of the seven terms whose PRESENCE ALONE is unauthorized
# by this program's own protocol, and nothing else. It is deliberately NOT the
# whole guard: a single-state reading cannot tell a legitimate commit from a
# clobber, and pretending otherwise is the mistake this file exists to correct.
#
# EVERY RUN PRINTS THE LEGACY PREDICATE BESIDE THE NEW ONE, so that a report
# claiming this guard fired is always accompanied by what the old gate would
# have said. A green with no matching red is not evidence.
#
# TRAP THIS GUARD IS BUILT TO AVOID (T304 hit it and fail-OPENed):
#   `/tmp` is a symlink on macOS, so a LEXICAL path comparison concluded
#   "outside the repo" and returned a MEASURED ZERO for 145 tracked files.
#   This guard resolves every path with `cd ... && pwd -P` before use and
#   REFUSES (2) on an unresolvable path rather than passing through.

set -uo pipefail

ME="repo-state-attest.sh"

die()    { printf '%s: REFUSED: %s\n' "$ME" "$*" >&2; exit 2; }
say()    { printf '%s\n' "$*"; }

# ---------------------------------------------------------------------------
# Paths the program cannot afford to lose silently. A committed clobber of any
# of these is the exact shape build-fixture.sh produced. T7 reports WHICH of
# them moved; it is informational, because a legitimate fast-forward moves
# them too -- see the boundary argument in the T318 handoff.
# ---------------------------------------------------------------------------
INVARIANT_PATHS=(
  ".softhouse/tasks.json"
  ".softhouse/RESUME.md"
  ".softhouse/program.json"
  ".softhouse/patterns.md"
  ".softhouse/conformance.sh"
  ".softhouse/vectors"
  "CLAUDE.md"
)

# resolve a directory physically; refuse rather than guess (T304's fail-open)
resolve_dir() {
  local d="$1" r
  [ -d "$d" ] || die "not a directory: $d"
  r=$(cd -- "$d" 2>/dev/null && pwd -P) || die "cannot resolve (pwd -P) : $d"
  [ -n "$r" ] || die "empty resolution for: $d"
  printf '%s' "$r"
}

# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------
cmd_snapshot() {
  [ $# -eq 2 ] || die "usage: $ME snapshot <repo-dir> <out-file>"
  local repo out top
  repo=$(resolve_dir "$1") || exit 2
  out="$2"

  top=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null)
  [ $? -eq 0 ] && [ -n "$top" ] || die "git cannot resolve a worktree at $repo"
  top=$(resolve_dir "$top") || exit 2

  : > "$out" || die "cannot write $out"

  {
    printf '#T318-REPO-STATE-SNAPSHOT v1\n'
    printf 'REPO\t%s\n' "$top"
  } >> "$out"

  # --- T6 repo identity FIRST: if git is not answering we must refuse, not
  #     silently record blanks that later compare "equal". ------------------
  local gitdir commondir
  gitdir=$(git -C "$repo" rev-parse --absolute-git-dir 2>/dev/null) \
    || die "cannot read --absolute-git-dir at $repo"
  commondir=$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) \
    || commondir="$gitdir"
  # physically resolve both -- /tmp symlink trap
  [ -d "$gitdir" ]    && gitdir=$(resolve_dir "$gitdir")
  [ -d "$commondir" ] && commondir=$(resolve_dir "$commondir")
  printf 'CONFIG\tgitcommondir\t%s\n' "$commondir" >> "$out"
  local k v
  for k in user.name user.email core.hooksPath commit.gpgsign core.fsmonitor; do
    v=$(git -C "$repo" config --get "$k" 2>/dev/null) || v="<unset>"
    [ -n "$v" ] || v="<unset>"
    printf 'CONFIG\t%s\t%s\n' "$k" "$v" >> "$out"
  done

  # --- T1 HEAD: sha AND symbolic ref. `checkout -b` from the same commit
  #     leaves the sha IDENTICAL and changes only the name. --------------
  local hs hr rc
  hs=$(git -C "$repo" rev-parse HEAD 2>/dev/null); rc=$?
  if [ $rc -ne 0 ]; then hs="<no-commits>"; fi
  hr=$(git -C "$repo" symbolic-ref -q HEAD 2>/dev/null) || hr="<detached>"
  [ -n "$hr" ] || hr="<detached>"
  printf 'HEAD\tsha\t%s\n'  "$hs" >> "$out"
  printf 'HEAD\tref\t%s\n'  "$hr" >> "$out"

  # --- T2 EVERY ref, not just refs/heads. `git branch` cannot see
  #     refs/tags, refs/notes, refs/stash or a ref planted outside them. ---
  git -C "$repo" for-each-ref --format='REF%09%(refname)%09%(objectname)' 2>/dev/null \
    | LC_ALL=C sort >> "$out"
  rc=${PIPESTATUS[0]}
  [ "$rc" -eq 0 ] || die "git for-each-ref failed (rc=$rc) at $repo"

  # --- T3 the LEGACY term. Still necessary, merely not sufficient. --------
  local st
  st=$(git -C "$repo" status --porcelain -- ':(top)' 2>/dev/null); rc=$?
  [ $rc -eq 0 ] || die "git status failed (rc=$rc) at $repo -- refusing to record a tree as clean"
  if [ -n "$st" ]; then
    printf '%s\n' "$st" | LC_ALL=C sort | sed 's/^/STATUS\t/' >> "$out"
  fi

  # --- T4 IGNORED files. T314's corollary to P-94: "a scratch fence is
  #     scoped to the directory and prefix it names, so 'no scratch leaked'
  #     is never an inference from having written a fence". A file hidden by
  #     a .gitignore is invisible to T3 forever. ADVISORY (see compare). ---
  local ig
  ig=$(git -C "$repo" status --porcelain --ignored=matching -- ':(top)' 2>/dev/null \
        | LC_ALL=C grep '^!! ' ) || true
  if [ -n "$ig" ]; then
    printf '%s\n' "$ig" | LC_ALL=C sort | sed 's/^!! /IGNORED\t/' >> "$out"
  fi

  # --- T5 INDEX SKIP BITS. `git update-index --assume-unchanged` silences
  #     `git status --porcelain` WITHOUT moving HEAD and without touching any
  #     ref or config -- so T1, T2 and T6 all miss it. This repo already
  #     documents the trick: `.softhouse/capture/README-pass3i.md:51`.
  #     `git ls-files -v` marks these with a LOWERCASE letter, or `S` for
  #     skip-worktree. A tracked file with any tag other than `H` is a file
  #     the status gate has been told to stop looking at. -------------------
  local sk
  sk=$(git -C "$repo" ls-files -v 2>/dev/null | LC_ALL=C grep -v '^H ' ) || true
  if [ -n "$sk" ]; then
    printf '%s\n' "$sk" | LC_ALL=C sort | sed 's/^/SKIPBIT\t/' >> "$out"
  fi

  # --- T7 blob identity of the named invariant artefacts ------------------
  local p b
  for p in "${INVARIANT_PATHS[@]}"; do
    b=$(git -C "$repo" rev-parse "HEAD:$p" 2>/dev/null) || b="<absent>"
    printf 'BLOB\t%s\t%s\n' "$p" "$b" >> "$out"
  done

  say "$ME: snapshot written: $out"
  say "$ME:   repo      $top"
  say "$ME:   HEAD      $hs on $hr"
  say "$ME:   refs      $(LC_ALL=C grep -c '^REF	' "$out" || true)"
  say "$ME:   status    $(LC_ALL=C grep -c '^STATUS	' "$out" || true) entries  <-- the LEGACY predicate"
  say "$ME:   ignored   $(LC_ALL=C grep -c '^IGNORED	' "$out" || true)"
  say "$ME:   skipbits  $(LC_ALL=C grep -c '^SKIPBIT	' "$out" || true)"
  return 0
}

# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------
cmd_compare() {
  local before="" after=""
  local -a writ_branches=() allow_new=() writ_artefacts=()
  local -a writ_refs=() allow_deleted=()
  local allow_dirty=0 scratch_prefix="" artefact_advisory=0

  [ $# -ge 2 ] || die "usage: $ME compare <before> <after> [options]"
  before="$1"; shift
  after="$1";  shift
  [ -r "$before" ] || die "cannot read before-snapshot: $before"
  [ -r "$after"  ] || die "cannot read after-snapshot: $after"

  while [ $# -gt 0 ]; do
    case "$1" in
      --writ-branch)    [ $# -ge 2 ] || die "--writ-branch needs a value"
                        writ_branches+=("$2"); shift 2 ;;
      --allow-new-ref)  [ $# -ge 2 ] || die "--allow-new-ref needs a value"
                        allow_new+=("$2"); shift 2 ;;
      --writ-ref)       [ $# -ge 2 ] || die "--writ-ref needs a value"
                        writ_refs+=("$2"); shift 2 ;;
      --allow-deleted-ref)
                        [ $# -ge 2 ] || die "--allow-deleted-ref needs a value"
                        allow_deleted+=("$2"); shift 2 ;;
      --artefact-advisory) artefact_advisory=1; shift ;;
      --scratch-prefix) [ $# -ge 2 ] || die "--scratch-prefix needs a value"
                        scratch_prefix="$2"; shift 2 ;;
      --writ-artefact)  [ $# -ge 2 ] || die "--writ-artefact needs a value"
                        writ_artefacts+=("$2"); shift 2 ;;
      --allow-dirty)    allow_dirty=1; shift ;;
      *) die "unknown option: $1" ;;
    esac
  done

  head -1 "$before" | LC_ALL=C grep -q '^#T318-REPO-STATE-SNAPSHOT v1$' \
    || die "not a v1 snapshot: $before"
  head -1 "$after"  | LC_ALL=C grep -q '^#T318-REPO-STATE-SNAPSHOT v1$' \
    || die "not a v1 snapshot: $after"

  local repo; repo=$(LC_ALL=C awk -F'\t' '$1=="REPO"{print $2; exit}' "$after")
  [ -n "$repo" ] || die "after-snapshot has no REPO line"

  local -a DAMAGE=() ADVISORY=() INFO=()
  local field
  get() { LC_ALL=C awk -F'\t' -v a="$2" -v b="$3" '$1==a && $2==b{print $3; exit}' "$1"; }

  # T325. ONE definition of "does the writ name this ref", used by T1 (where
  # HEAD landed) and by T2 (which refs may move). Before T325 the two asked the
  # question with two hand-rolled loops over `writ_branches` alone, which is why
  # `refs/remotes/origin/main` -- moved by the `git push` that STEP 5.5 itself
  # mandates -- had no way to be authorized. A gate that flags its own protocol's
  # final step is the G5 failure mode, one step further along.
  ref_in_writ() {
    local rn="$1" w pat
    for w in ${writ_branches+"${writ_branches[@]}"}; do
      [ "$rn" = "refs/heads/$w" ] && return 0
      [ "$rn" = "$w" ] && return 0
    done
    for pat in ${writ_refs+"${writ_refs[@]}"}; do
      printf '%s' "$rn" | LC_ALL=C grep -Eq "$pat" && return 0
    done
    return 1
  }

  # ---- T1 HEAD ------------------------------------------------------------
  local hb ha rb ra
  hb=$(get "$before" HEAD sha); ha=$(get "$after" HEAD sha)
  rb=$(get "$before" HEAD ref); ra=$(get "$after" HEAD ref)

  if [ "$rb" != "$ra" ]; then
    # BOUNDARY, corrected by arm G5 of the drive rather than by reasoning:
    # a HEAD ref change is NOT damage per se. The sanctioned worker workflow
    # is exactly `git checkout -b softhouse/<task>-<slug>` -- and a rule that
    # flagged it would fire on every worker, every run, and be turned off.
    # It is damage when HEAD lands on a ref the writ does NOT name.
    # A5 (checkout -b to an UNDECLARED branch) must stay red; G5 (checkout -b
    # to a DECLARED writ branch) must go green. Both are driven.
    local rok=0
    ref_in_writ "$ra" && rok=1
    if [ "$rok" = "1" ]; then
      INFO+=("T1 HEAD ref moved $rb -> $ra, which the writ names (authorized)")
    else
      DAMAGE+=("T1 HEAD ref CHANGED to a ref the writ does NOT name: $rb -> $ra  (a \`git checkout -b\` from the same commit leaves the SHA BYTE-IDENTICAL -- only this term sees it)")
    fi
  fi
  if [ "$hb" != "$ha" ]; then
    # BOUNDARY: ancestry, not equality. An ordinary commit is a fast-forward
    # from where the operation started; a clobber-then-branch-away, an amend,
    # a rebase and a reset are not. This single ruling is what keeps the
    # guard adoptable -- see the T318 handoff's boundary argument.
    local ff=1
    if [ "$hb" = "<no-commits>" ]; then
      ff=1   # first commit in an empty repo: treat as fast-forward
    else
      git -C "$repo" merge-base --is-ancestor "$hb" "$ha" >/dev/null 2>&1
      local mb=$?
      if [ $mb -eq 1 ]; then ff=0
      elif [ $mb -ne 0 ]; then
        DAMAGE+=("T1 HEAD moved $hb -> $ha and \`git merge-base --is-ancestor\` could not answer (rc=$mb) -- REFUSING to call it a fast-forward")
        ff=-1
      fi
    fi
    if [ "$ff" = "0" ]; then
      DAMAGE+=("T1 HEAD moved NON-FAST-FORWARD: $hb -> $ha  (old HEAD is NOT an ancestor of new HEAD: amend / reset / rebase / clobber)")
    elif [ "$ff" = "1" ]; then
      local named=0
      ref_in_writ "$ra" && named=1
      if [ "$named" = "1" ]; then
        INFO+=("T1 HEAD fast-forwarded on the WRIT branch $ra: $hb -> $ha  (authorized)")
      else
        DAMAGE+=("T1 HEAD fast-forwarded on $ra, which is NOT in the writ (--writ-branch was $( [ ${#writ_branches[@]} -eq 0 ] && echo '<none given>' || printf '%s ' "${writ_branches[@]}"))")
      fi
    fi
  fi

  # ---- T2 refs ------------------------------------------------------------
  local tmpb tmpa
  tmpb=$(mktemp) || die "mktemp failed"
  tmpa=$(mktemp) || die "mktemp failed"
  LC_ALL=C awk -F'\t' '$1=="REF"{print $2"\t"$3}' "$before" | LC_ALL=C sort > "$tmpb"
  LC_ALL=C awk -F'\t' '$1=="REF"{print $2"\t"$3}' "$after"  | LC_ALL=C sort > "$tmpa"

  # new refs
  while IFS=$'\t' read -r rname robj; do
    [ -n "$rname" ] || continue
    local ok=0 pat
    for pat in ${allow_new+"${allow_new[@]}"}; do
      if printf '%s' "$rname" | LC_ALL=C grep -Eq "$pat"; then ok=1; break; fi
    done
    if [ "$rname" = "refs/stash" ]; then
      # `git stash` CLEANS THE WORKING TREE and hides the content in a ref.
      # It is a clobber that makes the legacy predicate report SAFE. It is
      # also a protocol violation on its face: `.claude/skills/softhouse-program/SKILL.md:76`
      # -- "if dirty, commit `.softhouse/` state only; NEVER STASH worker WIP."
      DAMAGE+=("T2 refs/stash CREATED -- \`git stash\` empties the working tree into a ref, so \`git status\` reports CLEAN. SKILL.md:76 forbids stashing worker WIP outright.")
    elif [ "$ok" = "1" ]; then
      INFO+=("T2 new ref $rname (authorized by --allow-new-ref)")
    else
      DAMAGE+=("T2 NEW REF created outside the writ: $rname -> $robj")
    fi
  done < <(LC_ALL=C comm -13 <(cut -f1 "$tmpb") <(cut -f1 "$tmpa") \
             | while read -r n; do printf '%s\t%s\n' "$n" "$(LC_ALL=C awk -F'\t' -v n="$n" '$1==n{print $2}' "$tmpa")"; done)

  # deleted refs
  #
  # T325 -- THE FALSE POSITIVE THAT WOULD HAVE KILLED ADOPTION AT THE FIRE GATE.
  # `fire-program.sh`'s prune sweep runs `git branch -d "$BR"` on every worktree
  # branch it has just confirmed MERGED, and `branch_sweep.py` deletes shadowed
  # refs after copying them to `refs/rescue/<fire>/`. Both are sanctioned, both
  # happen on ordinary fires, and T318's unconditional rule called each of them
  # DAMAGE. That is arm G5's lesson exactly: a check that reports ordinary
  # pipeline work as damage is switched off within two fires.
  #
  # But an ERE must not be allowed to authorize destruction on its own, because
  # `softhouse/T318-x` matches the same pattern whether it was merged or not.
  # So the authorization has TWO conjuncts and the second is MEASURED: the
  # deleted tip must still be REACHABLE from a surviving ref the writ names.
  # `git branch -d` (which refuses on unmerged) passes it; `git branch -D` of
  # live worker output does not, and stays red.
  local -a SURVIVING_WRIT_OBJS=()
  local swn swo
  while IFS=$'\t' read -r swn swo; do
    [ -n "$swn" ] || continue
    ref_in_writ "$swn" && SURVIVING_WRIT_OBJS+=("$swo")
  done < "$tmpa"

  while read -r rname; do
    [ -n "$rname" ] || continue
    local dobj dok=0 pat
    dobj=$(LC_ALL=C awk -F'\t' -v n="$rname" '$1==n{print $2}' "$tmpb")
    for pat in ${allow_deleted+"${allow_deleted[@]}"}; do
      if printf '%s' "$rname" | LC_ALL=C grep -Eq "$pat"; then dok=1; break; fi
    done
    if [ "$dok" != "1" ]; then
      DAMAGE+=("T2 REF DELETED: $rname -> $dobj  (a deleted branch destroys unmerged work and leaves \`git status\` clean; no --allow-deleted-ref names it)")
      continue
    fi
    local reach=0 s
    for s in ${SURVIVING_WRIT_OBJS+"${SURVIVING_WRIT_OBJS[@]}"}; do
      if git -C "$repo" merge-base --is-ancestor "$dobj" "$s" >/dev/null 2>&1; then reach=1; break; fi
    done
    if [ "$reach" = "1" ]; then
      INFO+=("T2 ref deleted and its tip is STILL REACHABLE from a surviving writ ref (merged): $rname -> $dobj")
    else
      DAMAGE+=("T2 REF DELETED AND ITS TIP IS UNREACHABLE from every surviving writ ref: $rname -> $dobj  (--allow-deleted-ref matched the NAME, but the pattern cannot authorize destroying unmerged work -- the commit is now reachable from nothing)")
    fi
  done < <(LC_ALL=C comm -23 <(cut -f1 "$tmpb") <(cut -f1 "$tmpa"))

  # moved refs
  while read -r rname; do
    [ -n "$rname" ] || continue
    local ob nb
    ob=$(LC_ALL=C awk -F'\t' -v n="$rname" '$1==n{print $2}' "$tmpb")
    nb=$(LC_ALL=C awk -F'\t' -v n="$rname" '$1==n{print $2}' "$tmpa")
    [ "$ob" = "$nb" ] && continue
    local named=0
    ref_in_writ "$rname" && named=1
    git -C "$repo" merge-base --is-ancestor "$ob" "$nb" >/dev/null 2>&1
    local mb=$?
    if [ "$named" = "1" ] && [ $mb -eq 0 ]; then
      INFO+=("T2 writ branch $rname fast-forwarded $ob -> $nb (authorized)")
    elif [ $mb -eq 0 ]; then
      DAMAGE+=("T2 ref $rname fast-forwarded $ob -> $nb but is NOT in the writ")
    elif [ $mb -eq 1 ]; then
      DAMAGE+=("T2 ref $rname moved NON-FAST-FORWARD $ob -> $nb (work that was on it is now unreachable)")
    else
      DAMAGE+=("T2 ref $rname moved $ob -> $nb and ancestry could not be determined (rc=$mb) -- REFUSING to call it safe")
    fi
  done < <(LC_ALL=C comm -12 <(cut -f1 "$tmpb") <(cut -f1 "$tmpa"))

  # ---- T3 status (the LEGACY term) ---------------------------------------
  local sb sa
  sb=$(LC_ALL=C grep -c '^STATUS	' "$before" || true)
  sa=$(LC_ALL=C grep -c '^STATUS	' "$after"  || true)
  local legacy_verdict
  if [ "$sa" -eq 0 ]; then legacy_verdict="CLEAN (0 entries)"; else legacy_verdict="DIRTY ($sa entries)"; fi
  if [ "$sa" -gt "$sb" ] && [ "$allow_dirty" -eq 0 ]; then
    DAMAGE+=("T3 working tree gained $((sa - sb)) uncommitted entries (the legacy term; still necessary, never sufficient)")
  fi

  # ---- T4 ignored files (ADVISORY -- boundary argued in the handoff) ------
  local ib ia
  ib=$(LC_ALL=C grep -c '^IGNORED	' "$before" || true)
  ia=$(LC_ALL=C grep -c '^IGNORED	' "$after"  || true)
  if [ "$ia" -gt "$ib" ]; then
    local newig
    newig=$(LC_ALL=C comm -13 \
      <(LC_ALL=C awk -F'\t' '$1=="IGNORED"{print $2}' "$before" | LC_ALL=C sort) \
      <(LC_ALL=C awk -F'\t' '$1=="IGNORED"{print $2}' "$after"  | LC_ALL=C sort))
    local n
    while read -r n; do
      [ -n "$n" ] || continue
      if [ -n "$scratch_prefix" ] && case "$n" in "$scratch_prefix"*) true;; *) false;; esac; then
        INFO+=("T4 ignored file under the declared scratch prefix: $n")
      else
        ADVISORY+=("T4 NEW IGNORED FILE, invisible to \`git status\` forever: $n  (T314's corollary to P-94: a scratch fence is scoped to the prefix it names)")
      fi
    done <<< "$newig"
  fi

  # ---- T5 index skip bits -------------------------------------------------
  local kb ka
  kb=$(LC_ALL=C grep -c '^SKIPBIT	' "$before" || true)
  ka=$(LC_ALL=C grep -c '^SKIPBIT	' "$after"  || true)
  if [ "$ka" -gt "$kb" ]; then
    DAMAGE+=("T5 index SKIP BITS went $kb -> $ka. \`git update-index --assume-unchanged\` / \`--skip-worktree\` silences \`git status --porcelain\` WITHOUT moving HEAD, touching a ref, or changing config -- T1, T2 and T6 all miss it.")
  fi

  # ---- T6 repo identity ---------------------------------------------------
  local key vb va
  while IFS= read -r key; do
    vb=$(get "$before" CONFIG "$key"); va=$(get "$after" CONFIG "$key")
    [ "$vb" = "$va" ] && continue
    if [ "$key" = "gitcommondir" ]; then
      DAMAGE+=("T6 GIT DIR CHANGED: $vb -> $va  (a \`git init\` over a live repo, or a snapshot taken against a different repo)")
    else
      DAMAGE+=("T6 config $key REWRITTEN: '$vb' -> '$va'  (no legitimate operation in this program writes committer identity; \`git -c k=v commit\` is per-invocation and does NOT change it)")
    fi
  done < <(LC_ALL=C awk -F'\t' '$1=="CONFIG"{print $2}' "$before" | LC_ALL=C sort -u)

  # ---- T7 invariant blobs -------------------------------------------------
  # DRIVEN CORRECTION (arm A1b). T7 began as INFORMATIONAL, and that was a
  # hole big enough to drive the original defect through: in arm A1 the
  # clobber's OWN COMMIT was scored an authorized fast-forward on the writ
  # branch, and only the stray ref and the config rewrite made it red. A
  # clobber that committed over `tasks.json` and did NOT branch away and did
  # NOT rewrite config would have passed.
  #
  # The reason is worth stating, because it bounds what ANY such guard can
  # do: "a legitimate commit that edits tasks.json" and "a clobber that
  # commits over tasks.json" are THE SAME GIT OPERATION. No amount of ref or
  # index archaeology separates them. The distinguishing information is not
  # in git at all -- it is whether the operation DECLARED it would touch that
  # artefact. So T7 is a WRIT term, not an observation: an invariant artefact
  # may change only if `--writ-artefact` names it.
  local p pb pa
  for p in "${INVARIANT_PATHS[@]}"; do
    pb=$(get "$before" BLOB "$p"); pa=$(get "$after" BLOB "$p")
    [ "$pb" = "$pa" ] && continue
    local aok=0 a
    for a in ${writ_artefacts+"${writ_artefacts[@]}"}; do
      if [ "$a" = "$p" ] || [ "$a" = "ALL" ]; then aok=1; break; fi
    done
    if [ "$aok" = "1" ]; then
      INFO+=("T7 invariant artefact changed in HEAD, and the writ names it: $p  $pb -> $pa")
    elif [ "$artefact_advisory" = "1" ]; then
      # T325 -- A DELIBERATE REDUCTION IN POWER, NAMED SO IT CANNOT BE MISREAD.
      # T7 works by comparing an observation against a DECLARATION, so it is
      # exactly as strong as the caller's ability to declare in advance. A FIRE
      # cannot: it merges whatever worker branches went green, and a worker that
      # legitimately owns `conformance.sh` or `patterns.md` this fire moves that
      # blob. Blocking there would fire on ordinary merge fires -- the G5 shape --
      # and the guard would be off within two fires, taking T1/T2/T5/T6 with it.
      # So at that ONE gate T7 reports and does not block; where the writ IS
      # per-operation (a worker, a driver step, the drives in
      # capture/t325-adopt-attestation/) it stays blocking and arm A1b stays red.
      ADVISORY+=("T7 invariant artefact changed in HEAD and the writ does NOT name it: $p  $pb -> $pa  (ADVISORY at this gate by --artefact-advisory: the operation merges other agents' branches and cannot enumerate artefacts in advance. Attribute it before trusting it.)")
    else
      DAMAGE+=("T7 INVARIANT ARTEFACT CHANGED IN HEAD WITHOUT BEING DECLARED: $p  $pb -> $pa  (pass --writ-artefact '$p' if the operation was supposed to change it)")
    fi
  done

  # ---- report -------------------------------------------------------------
  rm -f "$tmpb" "$tmpa"
  say "================================================================"
  say "$ME: ATTESTATION  before=$before  after=$after"
  say "  repo: $repo"
  say "----------------------------------------------------------------"
  say "  LEGACY PREDICATE  (\`git status --porcelain\` empty?) : $legacy_verdict"
  say "----------------------------------------------------------------"
  local x
  if [ ${#INFO[@]} -gt 0 ]; then
    for x in "${INFO[@]}"; do say "  info      $x"; done
  fi
  if [ ${#ADVISORY[@]} -gt 0 ]; then
    for x in "${ADVISORY[@]}"; do say "  ADVISORY  $x"; done
  fi
  if [ ${#DAMAGE[@]} -gt 0 ]; then
    for x in "${DAMAGE[@]}"; do say "  DAMAGE    $x"; done
    say "----------------------------------------------------------------"
    say "VERDICT: DAMAGE (${#DAMAGE[@]} finding(s)) -- legacy predicate said: $legacy_verdict"
    return 1
  fi
  say "----------------------------------------------------------------"
  say "VERDICT: NO DAMAGE -- every delta is inside the declared writ"
  return 0
}

# ---------------------------------------------------------------------------
# survey  (T325) -- the SINGLE-STATE subset, for the two gates that have no
#                   "before" available to them. See the header for why this is
#                   deliberately weaker than `compare` and must not replace it.
#
#   0  no hidden work found       1  hidden work found       2  refused
#
# The ONLY term that votes is the index skip bit, and that is an argued choice
# rather than caution:
#   * a skip bit is not produced by ANY legitimate operation in this pipeline --
#     `git update-index --assume-unchanged|--skip-worktree` appears nowhere in
#     `.softhouse/bin`, `.softhouse/guards`, `.softhouse/conformance.sh` or
#     `.claude/skills` except inside the two guards that READ the bits (T324's
#     `wt_prune_blindspot_check` and this file) [VERIFIED: grep over those four
#     roots, T325]. Its presence alone is therefore unauthorized, with no writ
#     needed to say so;
#   * and it is the term that blinds the porcelain check, `git worktree remove`
#     and the prune classifier simultaneously (T318 instrument 50).
#
# `refs/stash` is ADVISORY here and NOT a vote, and the reason is a measurement,
# not a preference: `refs/stash` lives in the COMMON git dir, so `for-each-ref`
# inside every linked worktree reports a stash created in any other one
# [VERIFIED: git 2.50.1 probe, evidence/05-stash-scope-probe.txt -- one stash
# taken in the main tree, listed by `git -C wt1 for-each-ref`]. Voting on it in a
# per-worktree survey would report the SAME stash as damage in all 40-odd
# worktrees at once. Stash CREATION is caught where it can be attributed: T2 of
# the differential `compare`, which sees it appear between two snapshots.
# ---------------------------------------------------------------------------
cmd_survey() {
  [ $# -ge 1 ] || die "usage: $ME survey <repo-dir> [--label <text>]"
  local repo label="" top
  repo=$(resolve_dir "$1") || exit 2
  shift
  while [ $# -gt 0 ]; do
    case "$1" in
      --label) [ $# -ge 2 ] || die "--label needs a value"; label="$2"; shift 2 ;;
      *) die "unknown option: $1" ;;
    esac
  done
  top=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) \
    || die "git cannot resolve a worktree at $repo"
  [ -n "$top" ] || die "git cannot resolve a worktree at $repo"

  local sk rc
  sk=$(git -C "$repo" ls-files -v -- ':(top)' 2>/dev/null); rc=$?
  [ $rc -eq 0 ] || die "git ls-files -v failed (rc=$rc) at $repo -- an unreadable index is not an unmarked one"
  local marked
  marked=$(printf '%s\n' "$sk" | LC_ALL=C grep -v '^H ' | LC_ALL=C grep -v '^$') || true

  local st
  st=$(git -C "$repo" status --porcelain -uall -- ':(top)' 2>/dev/null); rc=$?
  [ $rc -eq 0 ] || die "git status --porcelain -uall failed (rc=$rc) at $repo -- refusing to record a tree as clean"

  local stash
  stash=$(git -C "$repo" for-each-ref --format='%(refname)' refs/stash 2>/dev/null); rc=$?
  [ $rc -eq 0 ] || die "git for-each-ref refs/stash failed (rc=$rc) at $repo"

  local ig
  ig=$(git -C "$repo" status --porcelain --ignored=matching -- ':(top)' 2>/dev/null \
        | LC_ALL=C grep -c '^!! ') || ig=0

  local n_skip=0 n_dirty=0 n_ig="$ig"
  [ -n "$marked" ] && n_skip=$(printf '%s\n' "$marked" | LC_ALL=C grep -c '.')
  [ -n "$st" ]     && n_dirty=$(printf '%s\n' "$st"     | LC_ALL=C grep -c '.')

  say "$ME: SURVEY ${label:+[$label] }$top"
  say "  legacy predicate (\`git status --porcelain\` empty?) : $( [ "$n_dirty" -eq 0 ] && echo 'CLEAN (0 entries)' || echo "DIRTY ($n_dirty entries, -uall)" )"
  say "  S3 uncommitted (visible, not hidden)                : $n_dirty"
  say "  S4 ignored files (ADVISORY -- .DS_Store lives here) : $n_ig"
  if [ -n "$stash" ]; then
    say "  ADVISORY  refs/stash EXISTS. \`git stash\` is what MAKES the legacy predicate report clean, and \`.claude/skills/softhouse-program/SKILL.md:76\` forbids stashing worker WIP. NOT attributed to this worktree: refs/stash is COMMON-DIR scoped, so every linked worktree sees it (measured, git 2.50.1)."
  fi
  if [ "$n_skip" -gt 0 ]; then
    say "  HIDDEN WORK  $n_skip index entr(y|ies) carry a NON-'H' tag. \`git update-index --assume-unchanged\` (-> 'h') / \`--skip-worktree\` (-> 'S') switches OFF the working-tree comparison that the porcelain gate, \`git worktree remove\` and the prune classifier ALL depend on -- one bit blinds three checks at once (T318 instrument 50: PRUNE, rc=0, 61 bytes destroyed)."
    printf '%s\n' "$marked" | sed -n '1,5p' | sed 's/^/    /'
    say "VERDICT: HIDDEN WORK PRESENT"
    return 1
  fi
  say "VERDICT: no hidden-work term fired (skip bits 0)"
  return 0
}

# ---------------------------------------------------------------------------
# fire-compare  (T325) -- ONE definition of the fire's writ.
#
# P-45's rule, verbatim (`patterns.md`): "A test-only guard is not a guard. ...
# verify the path that actually executes in CI/conformance calls it, not merely
# that a test does." The corollary that bites here is subtler: if the WRAPPER
# spelled this writ out and the DRIVE spelled its own copy, the drive would be
# proving a green about a writ the fire does not use, and the two would drift
# apart silently. So the writ lives HERE, once; `fire-program.sh` calls this
# subcommand and the false-positive arms in
# `.softhouse/capture/t325-adopt-attestation/` call the SAME subcommand.
#
# EVERY ENTRY BELOW IS A MEASURED FIRE BEHAVIOUR, not a guess -- the census is in
# the T325 handoff, and each line names the code that produces it:
#   refs/heads/main                fast-forwards as the driver commits/merges
#   refs/remotes/origin/*          moves on `git push -q origin main` (STEP 5.5.5)
#   refs/heads/softhouse/*         created by workers, fast-forwards as they commit,
#                                  deleted when merged (prune sweep `git branch -d`)
#   refs/heads/worktree-agent-*    the harness's per-worktree default branch
#   refs/rescue/*                  written by branch_sweep.py before it deletes a
#                                  shadowed ref (T312)
# HEAD itself must stay on `main`: the fire never checks the main tree out
# anywhere else, so a HEAD ref change there is real damage and stays red.
# ---------------------------------------------------------------------------
cmd_fire_compare() {
  [ $# -ge 2 ] || die "usage: $ME fire-compare <before> <after> [extra compare options]"
  local b="$1" a="$2"; shift 2
  cmd_compare "$b" "$a" \
    --writ-branch main \
    --writ-ref '^refs/heads/softhouse/' \
    --writ-ref '^refs/heads/worktree-agent-' \
    --writ-ref '^refs/remotes/origin/' \
    --allow-new-ref '^refs/heads/softhouse/' \
    --allow-new-ref '^refs/heads/worktree-agent-' \
    --allow-new-ref '^refs/remotes/origin/' \
    --allow-new-ref '^refs/rescue/' \
    --allow-deleted-ref '^refs/heads/softhouse/' \
    --allow-deleted-ref '^refs/heads/worktree-agent-' \
    --allow-deleted-ref '^refs/remotes/origin/' \
    --writ-artefact .softhouse/tasks.json \
    --writ-artefact .softhouse/RESUME.md \
    --writ-artefact .softhouse/program.json \
    --artefact-advisory \
    "$@"
}

case "${1:-}" in
  snapshot)     shift; cmd_snapshot     "$@" ;;
  compare)      shift; cmd_compare      "$@" ;;
  survey)       shift; cmd_survey       "$@" ;;
  fire-compare) shift; cmd_fire_compare "$@" ;;
  *) die "usage: $ME {snapshot|compare|survey|fire-compare} ..." ;;
esac
