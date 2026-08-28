#!/usr/bin/env bash
# T325 instrument 20 — does the wired attestation stay QUIET on ordinary pipeline
# work, and still go RED on damage?
#
# THE ACCEPTANCE CRITERION IS THE FALSE-POSITIVE ARM, not the red one. T318's own
# first draft flagged the sanctioned `git checkout -b softhouse/<task>` as damage
# (its arm G5), and the T325 brief states the consequence plainly: "a check that
# reports ordinary pipeline work as damage will be disabled within two fires."
# So every L-arm below is a legitimate fire behaviour, taken from what
# fire-program.sh and branch_sweep.py actually do, and every one of them must
# come back 0.
#
# It drives `repo-state-attest.sh fire-compare` — THE SAME SUBCOMMAND the wrapper
# calls, with the writ defined once inside the guard. A drive that spelled out its
# own copy of the writ would be proving a green about a writ the fire does not
# use (P-45's shape, one level up).
#
# Every arm runs in its own scratch clone under /private/tmp. The drive REFUSES to
# start if its scratch root resolves inside the repo — with `pwd -P` on BOTH
# sides, the trap that fail-OPENed T304's guard (`/tmp` is a symlink on macOS, so
# a lexical comparison concluded "outside the repo" and returned a measured zero
# for 145 tracked files).

set -uo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd -P)
REPO_ROOT=$(cd -- "$HERE/../../../.." && pwd -P)
GUARD="$REPO_ROOT/.softhouse/guards/repo-state-attest.sh"
[ -r "$GUARD" ] || { echo "REFUSED: guard not readable at $GUARD"; exit 2; }

ROOT=$(mktemp -d /private/tmp/t325-fire-writ-XXXXXX) || exit 2
ROOT=$(cd -- "$ROOT" && pwd -P)
case "$ROOT" in
  "$REPO_ROOT"*) echo "REFUSED: scratch root $ROOT resolves INSIDE the repo $REPO_ROOT"; exit 2 ;;
esac
echo "scratch root: $ROOT"
echo "repo under test (read-only, never written): $REPO_ROOT"
echo "guard: $GUARD"
echo "git: $(git --version)"
echo

PASS=0; FAIL=0
declare -a FAILED=()

# ---------------------------------------------------------------- fixture ---
# A miniature of this repo: the invariant artefacts the guard names, a bare
# origin so `git push` has somewhere to move refs/remotes/origin/* to, and a
# committed baseline.
mk() {
  local name="$1"
  local d="$ROOT/$name"
  mkdir -p "$d" || return 1
  git init -q --bare "$d/origin.git" || return 1
  git init -q -b main "$d/repo" || return 1
  (
    cd "$d/repo" || exit 1
    git config user.name "Buyan"
    git config user.email "buya.vol@gmail.com"
    mkdir -p .softhouse/vectors
    printf '{"tasks":[]}\n'      > .softhouse/tasks.json
    printf '# resume\n'          > .softhouse/RESUME.md
    printf '{"contexts":[]}\n'   > .softhouse/program.json
    printf '# patterns\n'        > .softhouse/patterns.md
    printf 'echo conformance\n'  > .softhouse/conformance.sh
    printf '{"v":1}\n'           > .softhouse/vectors/v1.json
    printf '# CLAUDE\n'          > CLAUDE.md
    printf 'work\n'              > worker-output.txt
    git add -A
    git commit -q -m "baseline"
    git remote add origin "$d/origin.git"
    git push -q origin main
  ) || return 1
  printf '%s' "$d/repo"
}

snap()  { bash "$GUARD" snapshot "$1" "$2" >/dev/null 2>&1; }

# run an arm: name, expectation (0|1), the operation, and the compare invocation.
#
# An optional `setup_<name>` runs BEFORE the baseline snapshot, and the first
# draft of this drive did not have one. THAT IS WHY THREE DAMAGE ARMS SCORED 0 ON
# THE FIRST RUN [evidence/20-fire-writ-FAILED-FIRST-RUN.txt] and the transcript is
# kept: D8 and D9 created their worker branch and then destroyed it INSIDE the
# attested window, so the branch appears in neither snapshot and no two-point
# differential can see it; D4 committed and reset back to the byte-identical
# starting state, so nothing had moved and 0 was the correct answer to the
# question actually asked. All three were defects in the ARM, not in the guard —
# but the failure is the useful part: it is exactly the residual gap arm R1 below
# now records deliberately, instead of my discovering it by accident twice.
arm() {
  local name="$1" expect="$2" mode="$3"; shift 3
  local d rc out
  d=$(mk "$name") || { echo "ARM $name: REFUSED — fixture build failed"; FAIL=$((FAIL+1)); FAILED+=("$name"); return; }
  if declare -F "setup_$name" >/dev/null 2>&1; then
    ( cd "$d" && "setup_$name" "$d" ) >"$ROOT/$name.setup.log" 2>&1
    local setuprc=$?
    if [ $setuprc -ne 0 ]; then
      echo "ARM $name: REFUSED — the arm's SETUP failed (rc=$setuprc); see $ROOT/$name.setup.log"
      FAIL=$((FAIL+1)); FAILED+=("$name"); return
    fi
  fi
  snap "$d" "$ROOT/$name.before" || { echo "ARM $name: REFUSED — before-snapshot failed"; FAIL=$((FAIL+1)); FAILED+=("$name"); return; }
  ( cd "$d" && "op_$name" "$d" ) >"$ROOT/$name.op.log" 2>&1
  local oprc=$?
  if [ $oprc -ne 0 ]; then
    echo "ARM $name: REFUSED — the arm's own operation failed (rc=$oprc); see $ROOT/$name.op.log"
    FAIL=$((FAIL+1)); FAILED+=("$name"); return
  fi
  snap "$d" "$ROOT/$name.after" || { echo "ARM $name: REFUSED — after-snapshot failed"; FAIL=$((FAIL+1)); FAILED+=("$name"); return; }
  out=$(bash "$GUARD" "$mode" "$ROOT/$name.before" "$ROOT/$name.after" "$@" 2>&1); rc=$?
  printf '%s\n' "$out" > "$ROOT/$name.verdict.txt"
  local legacy
  legacy=$(printf '%s\n' "$out" | grep -m1 'LEGACY PREDICATE' | sed 's/.*: //')
  if [ "$rc" = "$expect" ]; then
    echo "ARM $name: PASS  guard=$rc (expected $expect)   LEGACY=${legacy:-<none>}"
    PASS=$((PASS+1))
  else
    echo "ARM $name: FAIL  guard=$rc (expected $expect)   LEGACY=${legacy:-<none>}"
    printf '%s\n' "$out" | sed 's/^/      /'
    FAIL=$((FAIL+1)); FAILED+=("$name")
  fi
  printf '%s\n' "$out" | grep -E '^  (DAMAGE|ADVISORY)' | sed 's/^/      /'
}

# ============================ LEGITIMATE ARMS ==============================
# Each one is a thing fire-program.sh / branch_sweep.py / a worker DOES.

# L1 — a whole ordinary fire: driver commits, worker branch created and merged,
# merged branch deleted (`git branch -d`, prune sweep), push (moves
# refs/remotes/origin/main), a refs/rescue/<fire>/ ref written by branch_sweep.py
# before it deletes a shadowed ref, and a harness worktree-agent branch created
# and later removed.
#
# The worker branch is created in SETUP, i.e. by an EARLIER fire — which is when
# the branches a prune sweep deletes were in fact created.
setup_L1_ordinary_fire() {
  git checkout -q -b softhouse/T999-worker
  printf 'worker line\n' >> worker-output.txt
  git commit -qam "worker commit"
  git checkout -q main
}
op_L1_ordinary_fire() {
  local d="$1"
  git merge -q --no-ff -m "Merge T999" softhouse/T999-worker
  printf '{"tasks":[{"id":"T999","status":"done"}]}\n' > .softhouse/tasks.json
  printf '# resume — fire ran\n' > .softhouse/RESUME.md
  git commit -qam "softhouse: driver state"
  git branch -q -d softhouse/T999-worker           # merged: prune sweep idiom
  git branch -q worktree-agent-deadbeef            # harness default branch
  git update-ref refs/rescue/20260828-000001/shadow "$(git rev-parse main)"
  git push -q origin main
}

# L2 — nothing happens at all. The null control: a guard that cannot report 0
# here reports nothing anywhere.
op_L2_null_control() { :; }

# L3 — a worker branch created and LEFT ALIVE with commits on it, which is the
# state of ~230 refs in the live repo at any moment.
op_L3_live_worker_branch() {
  git branch -q softhouse/T998-live
  git checkout -q softhouse/T998-live
  printf 'wip\n' >> worker-output.txt
  git commit -qam "wip"
  git checkout -q main
}

# L4 — `git -c user.name=… commit`, the rescue idiom at fire-program.sh's
# exit guard. T318's arm G3: per-invocation identity, config UNTOUCHED. If T6
# matched on committer identity per commit instead of on config state, the
# wrapper's own rescue would report damage every time it rescued.
op_L4_rescue_identity_commit() {
  printf 'rescued\n' >> worker-output.txt
  git add -A
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
      commit -q -m "softhouse: rescue uncommitted deliverables (exit-protocol violation)"
}

# L5 — THE ARM THAT CAUGHT T318'S OWN FIRST DRAFT. A worker in its worktree runs
# the sanctioned `git checkout -b softhouse/<task>-<slug>`; the SHA does not move
# at all, only the ref name. Damage if the writ does not name it (arm D5 below),
# authorized here.
op_L5_sanctioned_checkout_b() {
  git checkout -q -b softhouse/T997-adopt-attestation
}

# L6 — a fire merges a worker branch that legitimately changes an invariant
# artefact the fire could not have declared in advance (this fire alone had
# workers owning conformance.sh, patterns.md and the vector store). Must be 0
# with the change REPORTED as ADVISORY: the concession argued at T7.
op_L6_merge_touches_invariant_artefact() {
  git checkout -q -b softhouse/T996-conformance
  printf 'echo more\n' >> .softhouse/conformance.sh
  printf '# a new pattern\n' >> .softhouse/patterns.md
  git commit -qam "T996: conformance + patterns"
  git checkout -q main
  git merge -q --no-ff -m "Merge T996" softhouse/T996-conformance
  git branch -q -d softhouse/T996-conformance
}

# ============================== DAMAGE ARMS ================================

# D1 — T304's build-fixture shape: reinit, config rewrite, clobber the invariant
# artefacts, COMMIT the clobber, branch away.
op_D1_committed_clobber() {
  git init -q .
  git config user.name "someone else"
  git config user.email "someone@else"
  printf 'CLOBBERED\n' > .softhouse/tasks.json
  printf 'CLOBBERED\n' > .softhouse/RESUME.md
  printf 'CLOBBERED\n' > .softhouse/program.json
  git add -A
  git commit -q -m "fixture setup"
  git checkout -q -b fixture-branch
}

# D2 — `git stash`. Not merely evading the legacy predicate: it is what MAKES it
# report clean. `.claude/skills/softhouse-program/SKILL.md:76` forbids it outright.
op_D2_stash() {
  printf 'uncommitted worker output\n' >> worker-output.txt
  git stash -q
}

# D3 — `git update-index --assume-unchanged`, then clobber the file. No ref
# moves, no HEAD moves, no config changes. T1, T2, T6 and T7 all miss it.
op_D3_assume_unchanged() {
  git update-index --assume-unchanged worker-output.txt
  printf 'destroyed\n' > worker-output.txt
}

# D4 — HEAD reset to a NON-DESCENDANT of where the window started. The committed
# work between the two is now reachable from nothing.
setup_D4_non_ff_reset() {
  printf 'committed work\n' >> worker-output.txt
  git commit -qam "work that a later reset will make unreachable"
}
op_D4_non_ff_reset() {
  git reset -q --hard HEAD~1
}

# D5 — `git checkout -b` to a branch the writ does NOT name. The SHA is
# BYTE-IDENTICAL; only the HEAD-ref term can see it. This is the shape the T318
# brief records happening for real: "a worker this fire put 8 commits on the
# harness worktree branch instead of its named branch and its output was nearly
# lost".
op_D5_undeclared_branch() {
  git checkout -q -b rogue/not-in-the-writ
}

# D6 — a tag, a note and a ref planted outside refs/heads. `git branch --format`
# (T304's "branch list") cannot see any of the three.
op_D6_stray_refs() {
  git tag v-stray
  git notes add -m "note" HEAD
  git update-ref refs/hidden/x "$(git rev-parse HEAD)"
}

# D7 — committer identity rewritten in CONFIG, nothing else touched.
op_D7_config_forgery() {
  git config user.name "not Buyan"
  git config user.email "not@buyan"
}

# D8 — THE ARM THE NEW REACHABILITY CONJUNCT EXISTS FOR. `git branch -D` of an
# UNMERGED worker branch. Its NAME matches --allow-deleted-ref exactly as a
# merged one would; only the measured reachability of its tip separates them.
setup_D8_delete_unmerged_worker_branch() {
  git checkout -q -b softhouse/T995-unmerged
  printf 'irreplaceable worker output\n' >> worker-output.txt
  git commit -qam "worker output that exists nowhere else"
  git checkout -q main
}
op_D8_delete_unmerged_worker_branch() {
  git branch -q -D softhouse/T995-unmerged
}

# D9 — a worker branch moved NON-fast-forward (a rebase or reset over committed
# worker output). The writ authorizes softhouse/* to fast-forward, and only to
# fast-forward.
setup_D9_worker_branch_rewound() {
  git checkout -q -b softhouse/T994-rewound
  printf 'commit A\n' >> worker-output.txt
  git commit -qam "A"
  printf 'commit B\n' >> worker-output.txt
  git commit -qam "B"
  git checkout -q main
}
op_D9_worker_branch_rewound() {
  git branch -q -f softhouse/T994-rewound HEAD
}

# R1 — THE RESIDUAL GAP, DRIVEN AND DECLARED RATHER THAN DISCOVERED TWICE.
# A ref that is CREATED AND DESTROYED entirely inside one attested window appears
# in NEITHER snapshot, so no two-point differential can see it. This arm expects
# 0 and PASSES when the limitation reproduces; if it ever starts returning 1,
# this row FAILS LOUDLY, because that would mean a term was added that reads
# something other than the two snapshots and this handoff has gone stale.
#
# Closing it would require the reflog (per-clone, expires under gc.reflogExpire,
# absent in a fresh clone, records every legitimate checkout) or `git fsck`
# dangling objects (a commit made and fully `reset --hard` back leaves one while
# every ref is identical — flagging it flags every abandoned `--amend`). T318
# excluded both WITH REASONS and the T325 brief forbids reinstating them without
# arguing against those reasons. I do not argue against them: the gap is real,
# it is narrower than it looks (the destroyed commit's content never existed in
# any snapshot either, so nothing that was VISIBLE became invisible), and the
# path that actually deletes worker branches on this host — the prune sweep —
# is gated on `wt_prune_check` rule 1's merge-base test plus T324's blind-spot
# override, neither of which is a snapshot differential.
op_R1_create_and_delete_inside_window() {
  git checkout -q -b softhouse/T993-ephemeral
  printf 'created and destroyed inside one window\n' >> worker-output.txt
  git commit -qam "ephemeral"
  git checkout -q main
  git branch -q -D softhouse/T993-ephemeral
}

# D10 — A1b, the MINIMAL committed clobber: commit over tasks.json, no branch
# away, no config rewrite. Red under a PER-OPERATION writ (plain `compare`), and
# this arm is what proves T7 still has teeth where a writ can be stated.
op_D10_minimal_artefact_clobber() {
  printf 'CLOBBERED\n' > .softhouse/tasks.json
  git commit -qam "innocuous-looking commit"
}

echo "=== LEGITIMATE ARMS — every one must be 0 ==="
arm L1_ordinary_fire                    0 fire-compare
arm L2_null_control                     0 fire-compare
arm L3_live_worker_branch               0 fire-compare
arm L4_rescue_identity_commit           0 fire-compare
arm L5_sanctioned_checkout_b            0 fire-compare
arm L6_merge_touches_invariant_artefact 0 fire-compare
echo
echo "=== DAMAGE ARMS — every one must be 1 ==="
arm D1_committed_clobber              1 fire-compare
arm D2_stash                          1 fire-compare
arm D3_assume_unchanged               1 fire-compare
arm D4_non_ff_reset                   1 fire-compare
arm D5_undeclared_branch              1 fire-compare
arm D6_stray_refs                     1 fire-compare
arm D7_config_forgery                 1 fire-compare
arm D8_delete_unmerged_worker_branch  1 fire-compare
arm D9_worker_branch_rewound          1 fire-compare
arm D10_minimal_artefact_clobber      1 compare --writ-branch main
echo
echo "=== DECLARED LIMIT — passes while the limitation reproduces ==="
arm R1_create_and_delete_inside_window 0 fire-compare
echo

# ===================== WRIT-MUTATION ROWS ==================================
# A guard that returned 0 unconditionally would pass every L arm above, and one
# that returned 1 unconditionally would pass every D arm. These rows neutralise
# ONE writ term at a time and require the verdict to FLIP — the same discipline
# as T318's instrument 40, applied to the terms T325 adds.
mut() {
  local label="$1" armname="$2" expect="$3"; shift 3
  local out rc
  [ -r "$ROOT/$armname.before" ] || { echo "MUT $label: REFUSED — no snapshots from arm $armname"; FAIL=$((FAIL+1)); FAILED+=("$label"); return; }
  out=$(bash "$GUARD" compare "$ROOT/$armname.before" "$ROOT/$armname.after" "$@" 2>&1); rc=$?
  if [ "$rc" = "$expect" ]; then
    echo "MUT $label: PASS  rc=$rc (expected $expect)"
    PASS=$((PASS+1))
  else
    echo "MUT $label: FAIL  rc=$rc (expected $expect)"
    printf '%s\n' "$out" | sed 's/^/      /'
    FAIL=$((FAIL+1)); FAILED+=("$label")
  fi
}

FULL_WRIT=(--writ-branch main
           --writ-ref '^refs/heads/softhouse/'
           --writ-ref '^refs/heads/worktree-agent-'
           --writ-ref '^refs/remotes/origin/'
           --allow-new-ref '^refs/heads/softhouse/'
           --allow-new-ref '^refs/heads/worktree-agent-'
           --allow-new-ref '^refs/remotes/origin/'
           --allow-new-ref '^refs/rescue/'
           --allow-deleted-ref '^refs/heads/softhouse/'
           --allow-deleted-ref '^refs/heads/worktree-agent-'
           --allow-deleted-ref '^refs/remotes/origin/'
           --writ-artefact .softhouse/tasks.json
           --writ-artefact .softhouse/RESUME.md
           --writ-artefact .softhouse/program.json
           --artefact-advisory)

echo "=== WRIT-MUTATION ROWS — is each new term load-bearing, or decoration? ==="
# M0: the full writ reproduces fire-compare's green on L1. If this fails, the
# rows below are testing a writ the wrapper does not use.
mut "M0 full writ == fire-compare on L1"        L1_ordinary_fire 0 "${FULL_WRIT[@]}"
# M1: drop --allow-deleted-ref. The merged `git branch -d` must now be DAMAGE —
# which is what T318's unconditional deleted-ref rule did to every fire.
mut "M1 no --allow-deleted-ref -> L1 goes RED"  L1_ordinary_fire 1 \
    --writ-branch main --writ-ref '^refs/heads/softhouse/' --writ-ref '^refs/heads/worktree-agent-' \
    --writ-ref '^refs/remotes/origin/' --allow-new-ref '^refs/heads/softhouse/' \
    --allow-new-ref '^refs/heads/worktree-agent-' --allow-new-ref '^refs/remotes/origin/' \
    --allow-new-ref '^refs/rescue/' --writ-artefact .softhouse/tasks.json \
    --writ-artefact .softhouse/RESUME.md --writ-artefact .softhouse/program.json --artefact-advisory
# M2: drop the remote writ-ref. The `git push` STEP 5.5 mandates must now be
# DAMAGE — the false positive that would have fired on EVERY fire.
mut "M2 no remote --writ-ref -> L1 goes RED"    L1_ordinary_fire 1 \
    --writ-branch main --writ-ref '^refs/heads/softhouse/' --writ-ref '^refs/heads/worktree-agent-' \
    --allow-new-ref '^refs/heads/softhouse/' --allow-new-ref '^refs/heads/worktree-agent-' \
    --allow-new-ref '^refs/rescue/' --allow-deleted-ref '^refs/heads/softhouse/' \
    --allow-deleted-ref '^refs/heads/worktree-agent-' --writ-artefact .softhouse/tasks.json \
    --writ-artefact .softhouse/RESUME.md --writ-artefact .softhouse/program.json --artefact-advisory
# M3: drop --artefact-advisory. L6 must go RED — proof that T7 keeps its teeth
# wherever the writ CAN be stated per operation, and that the fire gate's
# advisory is a scoped concession rather than a deletion.
mut "M3 no --artefact-advisory -> L6 goes RED"  L6_merge_touches_invariant_artefact 1 \
    --writ-branch main --writ-ref '^refs/heads/softhouse/' --writ-ref '^refs/remotes/origin/' \
    --allow-new-ref '^refs/heads/softhouse/' --allow-deleted-ref '^refs/heads/softhouse/' \
    --writ-artefact .softhouse/tasks.json --writ-artefact .softhouse/RESUME.md \
    --writ-artefact .softhouse/program.json
# M4: D8 with the SAME writ that makes L1's deletion green. Same pattern, same
# `--allow-deleted-ref`, opposite verdict — so the name is NOT what authorized
# L1; the measured reachability of the tip was.
mut "M4 D8 under L1's writ stays RED"           D8_delete_unmerged_worker_branch 1 "${FULL_WRIT[@]}"

echo
echo "================================================================"
echo "TOTAL: PASS=$PASS FAIL=$FAIL"
if [ "$FAIL" -ne 0 ]; then
  echo "FAILED ARMS: ${FAILED[*]}"
  echo "scratch kept for inspection: $ROOT"
  exit 1
fi
echo "scratch kept for inspection: $ROOT"
exit 0
