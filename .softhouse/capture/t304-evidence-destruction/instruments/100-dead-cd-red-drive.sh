#!/usr/bin/env bash
# T304 instrument 100 — RED-DRIVE the unguarded `cd` in t288-drive/build-fixture.sh.
#
# THE CLAIM UNDER TEST, stated so it can fail:
#   `.softhouse/reviews/t288-drive/build-fixture.sh` takes its scratch root from $1
#   (`BASE="${1:-/tmp/t288-drive}"`), does `cd "$REPO"` at line 27 with NO guard and NO
#   `set -e`, and then writes `.softhouse/tasks.json`, `.softhouse/RESUME.md` and
#   `.softhouse/program.json` with plain `>` redirects. If the cd dies, those three
#   redirects land on the REAL orchestrator control files in the current directory.
#
# This is T238's own M1 -- "a dead absolute path" -- pointed at the three files
# /softhouse-program reads to decide what to do next, and at `git config user.name`.
#
# ARMS, both in a SCRATCH CLONE, never the real checkout:
#   RED   run it with a $1 that cannot be created  -> expect the real tasks.json clobbered
#   GREEN the same, after `cd "$REPO" || exit 2`   -> expect exit non-zero, tree CLEAN
set -u
SRC="${1:-$(git rev-parse --show-toplevel)}"
SC="${2:-/tmp/t304-deadcd}"
F=".softhouse/reviews/t288-drive/build-fixture.sh"

rm -rf "$SC"
git clone --quiet --no-hardlinks "$SRC" "$SC" || exit 2
cd "$SC" || exit 2
echo "scratch clone : $SC"
echo "HEAD          : $(git rev-parse --short HEAD)"
echo

# A $1 whose parent cannot be created: /dev/null is a character device, so
# `mkdir -p /dev/null/x` fails and $REPO never exists.
BADBASE="/dev/null/t304-cannot-exist"

# THE VERDICT PREDICATE, AND WHY IT IS NOT `git status --porcelain`.
# The first run of this instrument used `git status --porcelain` and reported "RED DID NOT
# REPRODUCE", because the fixture builder does not merely overwrite the three control
# files -- it runs `git add -A && git commit` immediately afterwards, so the tree comes
# back CLEAN and the damage is INVISIBLE to every dirty-tree check in this program,
# including instrument 70's. Read the absence, not the value (P-84's shape: "four exit-2
# paths precede the probe ... test for the line's PRESENCE before its value"). So the
# predicate below is HEAD, the branch list, the config identity and the file CONTENT --
# state that a commit cannot launder.
BASE_HEAD=""
BASE_BRANCHES=""
BASE_NAME=""
snapshot_baseline() {
  BASE_HEAD="$(git rev-parse HEAD)"
  BASE_BRANCHES="$(git branch --format='%(refname:short)' | sort | tr '\n' ' ')"
  BASE_NAME="$(git config user.name 2>/dev/null || echo '<unset>')"
}
show_state() {
  local h b n damage=""
  h="$(git rev-parse HEAD)"
  b="$(git branch --format='%(refname:short)' | sort | tr '\n' ' ')"
  n="$(git config user.name 2>/dev/null || echo '<unset>')"
  echo "    HEAD          : $h  $([ "$h" = "$BASE_HEAD" ] && echo '(unchanged)' || { echo '<== MOVED'; damage=y; })"
  echo "    branches      : $b"
  [ "$b" = "$BASE_BRANCHES" ] || { echo "                    <== CHANGED (was: $BASE_BRANCHES)"; damage=y; }
  echo "    git user.name : $n  $([ "$n" = "$BASE_NAME" ] && echo '(unchanged)' || { echo '<== REWRITTEN'; damage=y; })"
  echo "    tasks.json is the fixture? : $(grep -q 't288-fixture' .softhouse/tasks.json 2>/dev/null && { echo 'YES <== CLOBBERED'; damage=y; } || echo no)"
  echo "    dirty tree    : '$(git status --porcelain | head -1)'   <-- note: CLEAN even when clobbered"
  [ -n "$damage" ] && DAMAGE=yes || DAMAGE=no
}

echo "=============================================================================="
echo "RED — build-fixture.sh AS COMMITTED, with an uncreatable scratch root"
echo "=============================================================================="
echo "  \$ zsh $F $BADBASE      (run from the repo root)"
git checkout -- . 2>/dev/null
snapshot_baseline
out="$(zsh "$F" "$BADBASE" 2>&1)"; rc=$?
echo "    exit=$rc"
echo "    last 3 lines of output:"; printf '%s\n' "$out" | tail -3 | sed 's/^/      /'
echo "    STATE OF THE REAL CONTROL FILES AFTERWARDS:"
show_state
if [ "$DAMAGE" = yes ]; then
  echo
  echo "    >>> RED CONFIRMED. The dead cd let the fixture builder overwrite the LIVE"
  echo "        orchestrator control files AND COMMIT THE OVERWRITE. First 3 lines of"
  echo "        the clobbered tasks.json:"
  head -3 .softhouse/tasks.json | sed 's/^/          /'
  echo "        WHERE THE DAMAGE ACTUALLY WENT. The builder overwrote the three control"
  echo "        files, COMMITTED them, and then ran 'git checkout -b', so the working tree"
  echo "        shows a pristine file while the clobber sits in history on another ref."
  echo "        Every ref carrying the fixture commit:"
  git log --all --oneline --grep='fixture: repo with three dead dispatches' | sed 's/^/          /'
  echo "        ...and which refs contain it:"
  for c in $(git log --all --format='%H' --grep='fixture: repo with three dead dispatches'); do
    git branch --all --contains "$c" 2>/dev/null | sed 's/^/            /'
    echo "            tasks.json AT that commit:"
    git show "$c:.softhouse/tasks.json" 2>/dev/null | head -3 | sed 's/^/              /'
  done
  echo "        reflog (the only place the move is recorded):"
  git reflog -n 6 | sed 's/^/          /'
else
  echo "    >>> RED DID NOT REPRODUCE — the claim is wrong, say so."
fi

# The clone is now corrupted BY DESIGN, so throw it away and take a fresh one.
cd / || exit 2
rm -rf "$SC"
git clone --quiet --no-hardlinks "$SRC" "$SC" || exit 2
cd "$SC" || exit 2
snapshot_baseline

echo
echo "=============================================================================="
echo "GREEN — the same run with the one-line guard  cd \"\$REPO\" || exit 2"
echo "=============================================================================="
/usr/bin/sed -i '' 's%^cd "\$REPO"$%cd "$REPO" || exit 2%' "$F"
grep -n 'cd "\$REPO"' "$F" | sed 's/^/    patched: /'
out="$(zsh "$F" "$BADBASE" 2>&1)"; rc=$?
echo "    exit=$rc"
echo "    STATE OF THE REAL CONTROL FILES AFTERWARDS:"
show_state
if [ "$DAMAGE" = no ] && [ "$rc" -ne 0 ]; then
  echo
  echo "    >>> GREEN. Non-zero exit; HEAD, branches, identity and tasks.json all untouched."
else
  echo
  echo "    >>> GREEN ARM FAILED: rc=$rc damage=$DAMAGE"
fi

echo
echo "=============================================================================="
echo "CONTROL — the guarded build still works on a GOOD scratch root"
echo "=============================================================================="
GOODBASE="$(mktemp -d)/t288"
out="$(zsh "$F" "$GOODBASE" 2>&1)"; rc=$?
echo "    exit=$rc  base=$GOODBASE"
printf '%s\n' "$out" | tail -4 | sed 's/^/      /'
echo "    fixture tasks.json present: $([ -f "$GOODBASE/repo/.softhouse/tasks.json" ] && echo YES || echo NO)"
show_state
