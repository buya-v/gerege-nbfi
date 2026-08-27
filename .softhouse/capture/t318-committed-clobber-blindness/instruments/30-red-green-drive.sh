#!/usr/bin/env bash
# T318 instrument 30 — red/green drive of .softhouse/guards/repo-state-attest.sh
#
# EVERY ARM RECORDS BOTH PREDICATES:
#   LEGACY = `git status --porcelain` empty?      (what the program uses today)
#   GUARD  = repo-state-attest.sh compare exit    (0 no-damage / 1 damage / 2 refused)
#
# A green with no matching red from the SAME instrument is not evidence. The
# arms are therefore paired: A1-A9 are damage the legacy predicate cannot see,
# G1-G5 are legitimate operations the guard must NOT flag. If the guard fired
# on everything it would pass A1-A9 by accident and be useless; G1-G5 is the
# arm that decides adoptability.
#
# NOTHING here touches the real checkout. Every arm runs in its own scratch
# clone under a caller-supplied root, and the root is created before any `cd`
# (T304's dead-`cd` defect, which is the very thing being detected here).

set -uo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || { echo "cannot resolve HERE" >&2; exit 2; }
REPO=$(cd -- "$HERE/../../../.." && pwd -P) || { echo "cannot resolve REPO" >&2; exit 2; }
GUARD="$REPO/.softhouse/guards/repo-state-attest.sh"
[ -r "$GUARD" ] || { echo "guard not readable: $GUARD" >&2; exit 2; }

ROOT="${1:-}"
if [ -z "$ROOT" ]; then
  ROOT=$(mktemp -d "${TMPDIR:-/tmp}/t318-drive.XXXXXX") || { echo "mktemp failed" >&2; exit 2; }
fi
mkdir -p "$ROOT" || { echo "cannot create $ROOT" >&2; exit 2; }
ROOT=$(cd -- "$ROOT" && pwd -P) || { echo "cannot resolve ROOT" >&2; exit 2; }

# --- refuse to run anywhere near the real checkout -------------------------
# T304 fail-OPENed here: /tmp is a symlink on macOS and a LEXICAL comparison
# concluded "outside the repo", returning a measured zero for 145 tracked
# files. Both sides are resolved with `pwd -P` above before comparison.
case "$ROOT" in
  "$REPO"|"$REPO"/*) echo "REFUSING: scratch root $ROOT is inside the real checkout $REPO" >&2; exit 2 ;;
esac

PASS=0; FAIL=0
ARMLOG="$ROOT/arms.tsv"
: > "$ARMLOG"

hdr() { printf '\n=== %s\n' "$*"; }
ok()  { PASS=$((PASS+1)); printf '  PASS  %s\n' "$*"; }
bad() { FAIL=$((FAIL+1)); printf '  FAIL  %s\n' "$*"; }

# build a fresh scratch clone of the real repo (shallow-ish: we only need refs
# and a worktree; a full clone of 7k files is fine and is what makes the
# invariant-artefact terms real).
mk() {
  # NOTE: `local a=$1 b=$ROOT/$a` does NOT work -- bash expands every argument
  # to the `local` builtin BEFORE any of them is assigned, so `$a` is unset at
  # expansion time and `set -u` aborts. Measured, not reasoned: the first run
  # of this instrument failed all 15 arms with "line 52: name: unbound
  # variable". Transcript: evidence/30-drive-FAILED-FIRST-RUN.txt
  local name
  local d
  name="$1"
  d="$ROOT/$name"
  rm -rf "$d"
  git clone -q --no-hardlinks "$REPO" "$d" >/dev/null 2>&1 || return 1
  git -C "$d" config user.name  "SoftFactory"  || return 1
  git -C "$d" config user.email "buya.vol@gmail.com" || return 1
  # give it a stable working branch so the writ has a name
  git -C "$d" checkout -q -B t318-work >/dev/null 2>&1 || return 1
  printf '%s' "$d"
}

legacy() {  # the predicate the program uses today
  local d="$1" o
  o=$(git -C "$d" status --porcelain 2>/dev/null)
  if [ -z "$o" ]; then printf 'CLEAN'; else printf 'DIRTY'; fi
}

# run one arm.
#   $1 arm id   $2 description   $3 expected-legacy  $4 expected-guard-rc
#   $5 mutator function name     $6.. extra args to `compare`
arm() {
  local id="$1" desc="$2" exp_legacy="$3" exp_rc="$4" mut="$5"; shift 5
  local d
  d=$(mk "$id") || { bad "$id  could not build scratch clone"; return; }
  "$GUARD" snapshot "$d" "$ROOT/$id.before" >/dev/null 2>&1 \
    || { bad "$id  before-snapshot refused"; return; }

  ( "$mut" "$d" ) >"$ROOT/$id.mutator.log" 2>&1
  local mrc=$?

  local lg; lg=$(legacy "$d")

  "$GUARD" snapshot "$d" "$ROOT/$id.after" >/dev/null 2>&1
  local src=$?
  if [ $src -ne 0 ]; then
    # a snapshot refusal is itself a legitimate outcome for the fail-closed arm
    printf '%s\t%s\t%s\tSNAPSHOT-REFUSED(%d)\n' "$id" "$desc" "$lg" "$src" >> "$ARMLOG"
    if [ "$exp_rc" = "2" ]; then ok "$id  $desc  [snapshot REFUSED rc=$src, as required]"
    else bad "$id  $desc  [snapshot refused rc=$src, expected a comparison]"; fi
    return
  fi

  local out rc
  out=$("$GUARD" compare "$ROOT/$id.before" "$ROOT/$id.after" "$@" 2>&1)
  rc=$?
  printf '%s\n' "$out" > "$ROOT/$id.compare.log"
  printf '%s\t%s\t%s\t%d\n' "$id" "$desc" "$lg" "$rc" >> "$ARMLOG"

  printf '\n--- %s : %s\n' "$id" "$desc"
  printf '    mutator rc=%d\n' "$mrc"
  printf '    LEGACY (git status --porcelain) : %s   (expected %s)\n' "$lg" "$exp_legacy"
  printf '    GUARD  (repo-state-attest)      : rc=%d (expected %s)\n' "$rc" "$exp_rc"
  printf '%s\n' "$out" | sed 's/^/      | /'

  local good=1
  [ "$lg" = "$exp_legacy" ] || { good=0; bad "$id  legacy predicate was $lg, expected $exp_legacy"; }
  [ "$rc" = "$exp_rc" ]     || { good=0; bad "$id  guard rc=$rc, expected $exp_rc"; }
  [ "$good" = "1" ] && ok "$id  $desc"
}

# ===========================================================================
# RED ARMS — damage the LEGACY predicate reports as CLEAN
# ===========================================================================

# A1 — the headline. Reproduces build-fixture.sh's dead-`cd` shape exactly:
#      re-init, rewrite committer identity, replace the three control files,
#      `git add -A && git commit` ONTO THE CHECKED-OUT BRANCH, then branch away.
m_A1() {
  local d="$1"
  cd "$d" || return 9
  git init -q -b main . >/dev/null 2>&1
  git config user.name  Fixture
  git config user.email fixture@example.invalid
  printf '{"run_id": "t288-fixture", "tasks": []}\n' > .softhouse/tasks.json
  printf '# fixture RESUME\n' > .softhouse/RESUME.md
  printf '{"contexts": []}\n' > .softhouse/program.json
  git add -A >/dev/null 2>&1
  git commit -q -m "fixture: repo with three dead dispatches still marked in_progress" >/dev/null 2>&1
  git checkout -q -b softhouse/t901-committed >/dev/null 2>&1
  git checkout -q t318-work >/dev/null 2>&1
}

# A1b — THE MINIMAL COMMITTED CLOBBER, and the arm that caught my own guard.
#       Same clobber as A1 with the two loud parts REMOVED: no branch-away,
#       no config rewrite. Just `git add -A && git commit` over tasks.json,
#       RESUME.md and program.json, onto the branch that is already checked
#       out. In the FIRST version of the guard this arm came back NO DAMAGE,
#       because the commit is a genuine fast-forward on the writ branch and
#       T7 was informational. It is red only because T7 became a WRIT term.
m_A1b() {
  local d="$1"
  cd "$d" || return 9
  printf '{"run_id": "t288-fixture", "tasks": []}\n' > .softhouse/tasks.json
  printf '# fixture RESUME\n' > .softhouse/RESUME.md
  printf '{"contexts": []}\n' > .softhouse/program.json
  git add -A >/dev/null 2>&1
  git commit -q -m "fixture: three dead dispatches still marked in_progress" >/dev/null 2>&1
}

# A2 — `git stash`. Empties the working tree into refs/stash. The legacy
#      predicate is not merely blind here, it is ACTIVELY MISLED: the stash
#      is what MAKES it report clean.
m_A2() {
  local d="$1"
  cd "$d" || return 9
  printf 'CLOBBERED BY A2\n' > .softhouse/tasks.json
  git stash push -q -m "t318-a2" >/dev/null 2>&1
}

# A3 — `git update-index --assume-unchanged`. Silences `git status --porcelain`
#      without moving HEAD, without any ref, without touching config.
#      This repo documents the trick itself: capture/README-pass3i.md:51.
m_A3() {
  local d="$1"
  cd "$d" || return 9
  git update-index --assume-unchanged .softhouse/tasks.json >/dev/null 2>&1
  printf 'CLOBBERED BY A3 -- and git status will not say so\n' > .softhouse/tasks.json
}

# A4 — commit, then reset --hard to a SIBLING. HEAD ends on a commit that does
#      NOT contain the starting commit. Ancestry catches it; equality would
#      have caught it too, but ancestry is what lets G1 pass.
m_A4() {
  local d="$1"
  cd "$d" || return 9
  local base; base=$(git rev-parse HEAD)
  printf 'A\n' >> CLAUDE.md; git commit -aqm "A" >/dev/null 2>&1
  git reset -q --hard "$base" >/dev/null 2>&1
  printf 'B\n' >> CLAUDE.md; git commit -aqm "B" >/dev/null 2>&1
  git reset -q --hard "$base" >/dev/null 2>&1
  # now rewind one further: HEAD no longer contains where we started
  git reset -q --hard "${base}~1" >/dev/null 2>&1
}

# A5 — `git checkout -b` from the SAME commit. HEAD SHA IS BYTE-IDENTICAL.
#      Only the symbolic ref changed. This is the shape the T318 brief warns
#      about: "a worker this fire put 8 commits on the harness worktree branch
#      instead of its named branch and its output was nearly lost."
m_A5() {
  local d="$1"
  cd "$d" || return 9
  git checkout -q -b worktree-agent-shadow >/dev/null 2>&1
}

# A6 — refs OUTSIDE refs/heads. `git branch --format` (T304's second term)
#      cannot see any of these.
m_A6() {
  local d="$1"
  cd "$d" || return 9
  git tag t318-stray-tag >/dev/null 2>&1
  git notes add -f -m "t318 note" HEAD >/dev/null 2>&1
  git update-ref refs/hidden/t318 HEAD >/dev/null 2>&1
}

# A7 — committer identity rewrite ALONE. No ref moves, no file changes.
#      This is half of what build-fixture.sh did, isolated.
m_A7() {
  local d="$1"
  cd "$d" || return 9
  git config user.name  Fixture
  git config user.email fixture@example.invalid
}

# A8 — scratch leak behind a .gitignore fence. T314's corollary to P-94:
#      "a scratch fence is scoped to the directory and prefix it names, so
#      'no scratch leaked' is never an inference from having written a fence."
#      EXPECTED: ADVISORY, NOT DAMAGE. See the boundary argument.
m_A8() {
  local d="$1"
  cd "$d" || return 9
  mkdir -p .softhouse/capture/t318-scratchtest
  printf 'scratch-*\n' > .softhouse/capture/t318-scratchtest/.gitignore
  git add .softhouse/capture/t318-scratchtest/.gitignore >/dev/null 2>&1
  git commit -qm "fence" >/dev/null 2>&1
  printf 'leaked\n' > .softhouse/capture/t318-scratchtest/scratch-leak.json
}

# A9 — a branch DELETED. Unmerged work destroyed; working tree untouched.
m_A9() {
  local d="$1"
  cd "$d" || return 9
  git branch -q t318-victim >/dev/null 2>&1
  # re-snapshot point is before(); so create it in before? No -- instead delete
  # an existing ref that the clone already had.
  local victim
  victim=$(git for-each-ref --format='%(refname)' refs/remotes/origin \
            | LC_ALL=C grep -v 'HEAD$' | head -1)
  [ -n "$victim" ] && git update-ref -d "$victim" >/dev/null 2>&1
  git branch -q -D t318-victim >/dev/null 2>&1
}

# ===========================================================================
# GREEN ARMS — legitimate operations that must NOT be flagged.
# This is the arm that decides adoptability. A check with no false-positive
# arm is not evidence.
# ===========================================================================

# G1 — AN ORDINARY COMMIT ON THE WRIT BRANCH. The single most common thing a
#      worker does. If this is flagged, the guard gets disabled and the
#      program is worse off than with the blind check.
m_G1() {
  local d="$1"
  cd "$d" || return 9
  mkdir -p .softhouse/capture/t318-ordinary
  printf 'an ordinary worker deliverable\n' > .softhouse/capture/t318-ordinary/notes.md
  git add -A >/dev/null 2>&1
  git commit -qm "T318: an entirely ordinary commit" >/dev/null 2>&1
}

# G2 — THREE ordinary commits, one of which legitimately edits tasks.json.
#      T7 must report it as INFO, not DAMAGE: a fast-forward on the writ
#      branch is allowed to change the invariant artefacts.
m_G2() {
  local d="$1"
  cd "$d" || return 9
  printf 'x\n' >> CLAUDE.md;                git commit -aqm "c1" >/dev/null 2>&1
  printf '{"run_id":"legit"}\n' > .softhouse/tasks.json; git commit -aqm "c2" >/dev/null 2>&1
  printf 'y\n' >> CLAUDE.md;                git commit -aqm "c3" >/dev/null 2>&1
}

# G3 — `git -c user.name=... commit`, the PER-INVOCATION idiom that
#      fire-program.sh:1218 actually uses for its rescue commit. It must not
#      trip T6, because it does not write config. If T6 flagged this, the
#      driver's own rescue path would report damage on every rescue.
m_G3() {
  local d="$1"
  cd "$d" || return 9
  printf 'z\n' >> CLAUDE.md
  git add -A >/dev/null 2>&1
  git -c user.name="Buyan" -c user.email="buya.vol@gmail.com" \
      commit -qm "softhouse: rescue uncommitted deliverables (fire-program.sh idiom)" >/dev/null 2>&1
}

# G4 — nothing happens at all. The trivial null control: if the guard fires
#      here, every figure above it is noise.
m_G4() { : ; }

# G5 — a worker creating its OWN task branch and committing to it, declared
#      in the writ via --allow-new-ref. The sanctioned isolation workflow.
m_G5() {
  local d="$1"
  cd "$d" || return 9
  git checkout -q -b softhouse/T999-legit >/dev/null 2>&1
  printf 'w\n' >> CLAUDE.md
  git commit -aqm "T999 work" >/dev/null 2>&1
}

# ===========================================================================
# FAIL-CLOSED ARMS
# ===========================================================================

# X1 — snapshot a directory that is not a repo. Must REFUSE (2), never 0.
m_X1() {
  local d="$1"
  rm -rf "$d/.git"
}

# Instrument 40 sources this file to reuse the mutator functions and mk().
# Sourced with T318_DRIVE_LIB=1 we stop here rather than running the arms.
if [ -n "${T318_DRIVE_LIB:-}" ]; then
  return 0 2>/dev/null || exit 0
fi

echo "T318 INSTRUMENT 30 — RED/GREEN DRIVE"
echo "guard : $GUARD"
echo "repo  : $REPO"
echo "root  : $ROOT"
echo "date  : $(date -u +%Y-%m-%dT%H:%M:%SZ)"

hdr "RED ARMS — damage that \`git status --porcelain\` reports as CLEAN"
arm A1 "build-fixture dead-cd shape: reinit + config + 3 files + COMMIT + branch away" CLEAN 1 m_A1 --writ-branch t318-work
arm A1b "MINIMAL committed clobber: commit over tasks.json, no branch-away, no config" CLEAN 1 m_A1b --writ-branch t318-work
arm A2 "git stash — empties the tree into refs/stash"                                  CLEAN 1 m_A2 --writ-branch t318-work
arm A3 "update-index --assume-unchanged then clobber the file"                          CLEAN 1 m_A3 --writ-branch t318-work
arm A4 "commit then reset --hard to a non-descendant"                                   CLEAN 1 m_A4 --writ-branch t318-work
arm A5 "checkout -b from the SAME commit (HEAD sha identical, wrong branch)"            CLEAN 1 m_A5 --writ-branch t318-work
arm A6 "refs outside refs/heads: tag + notes + refs/hidden/*"                            CLEAN 1 m_A6 --writ-branch t318-work
arm A7 "git config user.name/user.email rewritten, nothing else"                        CLEAN 1 m_A7 --writ-branch t318-work
arm A9 "a ref DELETED (unmerged work destroyed, tree untouched)"                        CLEAN 1 m_A9 --writ-branch t318-work

hdr "ADVISORY ARM — real, but deliberately NOT blocking (boundary argued)"
arm A8 "scratch leak behind a .gitignore fence (T314's corollary)"                      CLEAN 0 m_A8 --writ-branch t318-work

hdr "GREEN ARMS — legitimate work that must NOT be flagged (adoptability)"
arm G1 "an ordinary commit on the writ branch"                                          CLEAN 0 m_G1 --writ-branch t318-work
arm G2 "three ordinary commits, one legitimately editing tasks.json (declared)"          CLEAN 0 m_G2 --writ-branch t318-work \
    --writ-artefact .softhouse/tasks.json --writ-artefact CLAUDE.md
arm G3 "git -c user.name=... commit (fire-program.sh:1218's own rescue idiom)"          CLEAN 0 m_G3 --writ-branch t318-work \
    --writ-artefact CLAUDE.md
arm G4 "nothing happens at all (null control)"                                          CLEAN 0 m_G4 --writ-branch t318-work
arm G5 "worker creates its own declared task branch and commits"                        CLEAN 0 m_G5 \
    --writ-branch softhouse/T999-legit --allow-new-ref '^refs/heads/softhouse/T999-legit$' \
    --writ-artefact CLAUDE.md
# G6 is A1b's PAIRED GREEN: byte-identical mutation, writ declares the three
# artefacts. Same instrument, same mutation, opposite verdict -- which is the
# only thing that shows T7 is discriminating rather than always-on.
arm G6 "A1b's mutation, but the writ DECLARES the three artefacts"                       CLEAN 0 m_A1b --writ-branch t318-work \
    --writ-artefact .softhouse/tasks.json --writ-artefact .softhouse/RESUME.md \
    --writ-artefact .softhouse/program.json

hdr "FAIL-CLOSED ARM"
arm X1 "repo destroyed between snapshots — must REFUSE, never report clean"             CLEAN 2 m_X1 --writ-branch t318-work

hdr "SUMMARY"
printf '%-4s %-72s %-7s %s\n' ARM DESCRIPTION LEGACY GUARD
while IFS=$'\t' read -r a dsc lg rc; do
  printf '%-4s %-72s %-7s %s\n' "$a" "$dsc" "$lg" "$rc"
done < "$ARMLOG"
echo
echo "PASS=$PASS  FAIL=$FAIL"
echo "scratch kept at: $ROOT"
[ "$FAIL" -eq 0 ] || exit 1
exit 0
