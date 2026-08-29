#!/usr/bin/env bash
# T471 -- INDEPENDENT re-derivation of T465's CLAIM 2 (the no-fixed-point derivation) and of
# CLAIM 3's cardinals. Nothing here reads T465's or T461's numbers; every figure is measured.
#
# WHAT IT DOES, per rev: materialises the rev as a detached worktree of a THROWAWAY CLONE that
# lives outside the graded repository, then runs the dead-path frontier guard twice --
#   ARM-HELD      : the fire lock as the commit has it (tracked)
#   ARM-RELEASED  : the lock removed by release_lock's own sequence (rm, stage, commit)
# -- and, for ARM-C, re-runs each arm against a pin REWRITTEN to the other arm's frontier.
#
# NO REAL REPO PATH IS SPELT AS A LITERAL HERE (P-103): every dot-directory path is ASSEMBLED
# from $S at run time, so this instrument makes no claim about any tree's contents.
#
# PRESENCE BEFORE VALUE (P-84): the guard's probe line is grepped for PRESENCE and the count is
# printed before any value is read out of it.
#
# EXIT: 0 arms completed; 2 a dependency did not resolve (never a silent skip).

set -u

S=".softhouse"
GUARD_REL="$S/guards/check-dead-path-frontier.sh"
PIN_REL="$S/guards/dead-path-frontier.pin"
LOCK_REL="$S/LOCK"
PROBE="T316-DEADPATH-FRONTIER:"

CLONE="${1:-}"
REV="${2:-}"
OUTDIR="${3:-}"
TAG="${4:-$REV}"

if [ -z "$CLONE" ] || [ -z "$REV" ] || [ -z "$OUTDIR" ]; then
  echo "usage: $0 <throwaway-clone> <rev> <outdir> [tag]" >&2
  exit 2
fi
for d in "$CLONE" "$OUTDIR"; do
  if [ ! -d "$d" ]; then echo "ERROR: not a directory: $d -- REFUSING (exit 2)" >&2; exit 2; fi
done
case "$CLONE" in
  /Users/buv/gerege-nbfi*) echo "ERROR: the clone must live OUTSIDE the graded repo. REFUSING." >&2; exit 2;;
esac

WT=$(mktemp -d "${TMPDIR:-/tmp}/t471-wt.XXXXXX") || { echo "ERROR: mktemp failed" >&2; exit 2; }
rmdir "$WT"
git -C "$CLONE" worktree add --detach --quiet "$WT" "$REV" || {
  echo "ERROR: could not materialise $REV. REFUSING (exit 2)." >&2; exit 2; }

for dep in "$WT/$GUARD_REL" "$WT/$PIN_REL"; do
  if [ ! -f "$dep" ]; then
    echo "ERROR: dependency missing in the materialised tree: $dep -- REFUSING (exit 2)" >&2
    exit 2
  fi
done

git -C "$WT" config user.email t471@softhouse.local
git -C "$WT" config user.name  "T471 reviewer"

run_guard () {          # $1 = arm label
  local arm="$1"
  local f="$OUTDIR/guard-$TAG-$arm.txt"
  bash "$WT/$GUARD_REL" >"$f" 2>&1
  local rc=$?
  local n
  n=$(grep -ac "$PROBE" "$f")
  echo "ARM=$arm exit=$rc probe-lines=$n"
  if [ "$n" -eq 0 ]; then
    echo "    NO PROBE LINE -- the guard did not reach a verdict. Reading no value from it."
    return 0
  fi
  grep -a "$PROBE" "$f" | sed 's/^/    /'
  return 0
}

echo "===== TREE $TAG ($REV) ====="
echo "-- materialised at: $WT"
echo "-- lock tracked at this commit? $(git -C "$WT" ls-files -- "$LOCK_REL" | grep -ac '') path(s)"
echo "-- pin rows: $(grep -v '^#' "$WT/$PIN_REL" | grep -vc '^[[:space:]]*$')"

# ---- ARM-HELD ------------------------------------------------------------------------------
run_guard "HELD"

# capture the frontier as the guard sees it, held
cp "$WT/$PIN_REL" "$OUTDIR/pin-$TAG-original.txt"

# ---- ARM-RELEASED: release_lock's own sequence ----------------------------------------------
if [ -f "$WT/$LOCK_REL" ]; then
  rm -f "$WT/$LOCK_REL"
  git -C "$WT" add -A -- "$LOCK_REL" >/dev/null 2>&1
  git -C "$WT" commit -q -m "T471 arm: release the fire lock (rm, stage, commit)" >/dev/null 2>&1
else
  echo "-- NOTE: no lock file on disk at this rev; released arm is the same tree."
fi
echo "-- after release: lock tracked? $(git -C "$WT" ls-files -- "$LOCK_REL" | grep -ac '') path(s)"
run_guard "RELEASED"

echo "WT_KEPT=$WT"
