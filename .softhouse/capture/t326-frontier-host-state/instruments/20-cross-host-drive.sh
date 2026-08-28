#!/usr/bin/env bash
# T326 -- THE CROSS-HOST DRIVE. The arm T323 could not run, because it and its red drive were on
# one machine in one disk condition.
#
# WHAT IT PROVES. One commit, N DISK CONDITIONS, and the frontier must come out BYTE-IDENTICAL in
# every one of them. The conditions are constructed rather than waited for: the defect was
# "untracked things exist here and not there", so the drive MATERIALISES the untracked things.
#
#   A  BARE            no `.softhouse/toolchain`, no leftover scratch.  (a fresh worktree/clone)
#   B  TOOLCHAIN       `.softhouse/toolchain/{go,gocache,gomodcache}` present.  (Buyan's Mac)
#   C  RESIDUE         B, plus `.../T82-guard-proofs/scratch/` -- untracked residue an earlier
#                      run left behind.  (Buyan's Mac after a run; this is the 24th row, and it
#                      is why "different machine" understates the defect: the SAME machine
#                      disagrees with itself across runs.)
#   D  FRESH CLONE     `git clone` of this worktree into a scratch dir, HEAD checked out clean.
#                      No untracked anything, different absolute path, different inode, and the
#                      one condition nobody can accuse of being condition A renamed.
#
# EACH CONDITION runs the census, and the drive compares the derived FRONTIER ROWS. Byte-equal in
# all conditions => the frontier is a property of the commit. One difference => not fixed.
#
# IT ALSO RUNS THE RETIRED DISK RESOLVER (`legacy_rows.py`, which lives HERE and not behind a
# flag on the graded census -- see that file's header) over the same conditions, and REQUIRES it
# to DIFFER. A drive that only shows the new thing passing has not shown the old thing was
# broken -- a green-only drive is a claim, not a measurement (P-22: "a guard, a canary, or a
# control that cannot fail is worse than none, because it is believed").
#
# EXIT: 0 all arms as expected; 1 an arm came out wrong; 2 the drive could not run.
# PROBE: `T326-CROSSHOST:` printed only on a path that reaches a verdict.

set -u

PROBE="T326-CROSSHOST:"
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SELF_DIR/../../../.." && pwd)

CENSUS="$ROOT/.softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
TOOLCHAIN="$ROOT/.softhouse/toolchain"
RESIDUE="$ROOT/.softhouse/capture/t74-multiplesof/T82-guard-proofs/scratch"

for dep in "$CENSUS"; do
  [ -f "$dep" ] || { echo "ERROR: missing dependency $dep. REFUSING (exit 2)." >&2; exit 2; }
done
command -v python3 >/dev/null 2>&1 || { echo "ERROR: no python3. REFUSING (exit 2)." >&2; exit 2; }
command -v git     >/dev/null 2>&1 || { echo "ERROR: no git. REFUSING (exit 2)." >&2; exit 2; }

# REFUSE to run if either untracked path already exists: the drive CREATES and DELETES them, and
# deleting a real toolchain out from under Buyan's machine would be this instrument doing damage
# to prove a point about instruments doing damage.
for p in "$TOOLCHAIN" "$RESIDUE"; do
  if [ -e "$p" ]; then
    echo "ERROR: $p already exists." >&2
    echo "ERROR: this drive CREATES and REMOVES that path; it will not delete a pre-existing" >&2
    echo "ERROR: one. Run it in a fresh worktree or move the path aside. REFUSING (exit 2)." >&2
    exit 2
  fi
done

SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t326-crosshost.XXXXXX") || {
  echo "ERROR: no scratch dir. REFUSING (exit 2)." >&2; exit 2; }
CREATED=""
cleanup() {
  for c in $CREATED; do rm -rf "$c"; done
  rm -rf "$SCRATCH"
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------------------------
# rows_of <tag> <repo-root> [--legacy]   -> writes $SCRATCH/<tag>.rows, returns census status
# ---------------------------------------------------------------------------------------------
rows_of() {
  tag=$1; rroot=$2; legacy=${3:-}
  jsonf="$SCRATCH/$tag.json"; outf="$SCRATCH/$tag.out"; rowsf="$SCRATCH/$tag.rows"
  if [ -n "$legacy" ]; then
    # The retired disk resolver. It walks the SAME corpus and the SAME literals; only the
    # resolution predicate differs, so the arms differ in exactly one variable.
    python3 "$SELF_DIR/legacy_rows.py" "$rroot" >"$rowsf" 2>"$outf"
    rc=$?
    if [ "$rc" -ne 0 ]; then
      echo "ERROR: the legacy resolver refused in condition $tag (exit $rc):" >&2
      sed -n '1,40p' "$outf" >&2
      return 2
    fi
    return 0
  fi
  # NOTE: the census derives its own root from its own location, so it always measures the tree
  # it lives in. Condition D therefore runs the CLONE's copy of the census, which is the right
  # thing: a clone must be graded by what the clone contains.
  cjson="$rroot/.softhouse/capture/t316-dead-path-guards/census_dead_paths.py"
  if [ ! -f "$cjson" ]; then
    echo "ERROR: no census at $cjson for condition $tag. REFUSING." >&2
    return 2
  fi
  python3 "$cjson" --json "$jsonf" >"$outf" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "ERROR: census refused in condition $tag (exit $rc):" >&2
    sed -n '1,40p' "$outf" >&2
    return 2
  fi
  python3 "$SELF_DIR/rows.py" "$jsonf" >"$rowsf" || return 2
  return 0
}

fail=0
pass=0
note() { printf '  %-28s %s\n' "$1" "$2"; }

echo "T326 CROSS-HOST DRIVE -- one commit, four disk conditions"
echo "root: $ROOT"
echo "HEAD: $(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo '(unknown)')"
echo "======================================================================================"

# --- A  BARE ---------------------------------------------------------------------------------
rows_of A_bare "$ROOT" || exit 2
note "A bare" "$(grep -ac '' "$SCRATCH/A_bare.rows") row(s)"
rows_of A_bare_legacy "$ROOT" --legacy || exit 2
note "A bare (legacy resolver)" "$(grep -ac '' "$SCRATCH/A_bare_legacy.rows") row(s)"

# --- B  TOOLCHAIN PRESENT --------------------------------------------------------------------
mkdir -p "$TOOLCHAIN/go" "$TOOLCHAIN/gocache" "$TOOLCHAIN/gomodcache" || exit 2
CREATED="$CREATED $TOOLCHAIN"
rows_of B_toolchain "$ROOT" || exit 2
note "B +toolchain" "$(grep -ac '' "$SCRATCH/B_toolchain.rows") row(s)"
rows_of B_toolchain_legacy "$ROOT" --legacy || exit 2
note "B +toolchain (legacy)" "$(grep -ac '' "$SCRATCH/B_toolchain_legacy.rows") row(s)"

# --- C  + RUN RESIDUE ------------------------------------------------------------------------
mkdir -p "$RESIDUE" || exit 2
CREATED="$CREATED $RESIDUE"
: >"$RESIDUE/17a-capture.json" || exit 2
rows_of C_residue "$ROOT" || exit 2
note "C +toolchain +residue" "$(grep -ac '' "$SCRATCH/C_residue.rows") row(s)"
rows_of C_residue_legacy "$ROOT" --legacy || exit 2
note "C +toolchain +residue (legacy)" "$(grep -ac '' "$SCRATCH/C_residue_legacy.rows") row(s)"

# --- D  FRESH CLONE --------------------------------------------------------------------------
# A clone carries the COMMITTED tree and nothing untracked, at a different absolute path. It is
# the closest thing to "the other fire's host" this drive can construct locally.
CLONE="$SCRATCH/clone"
if git clone --quiet --no-hardlinks --single-branch "$ROOT" "$CLONE" >"$SCRATCH/clone.log" 2>&1; then
  rows_of D_clone "$CLONE" || exit 2
  note "D fresh clone" "$(grep -ac '' "$SCRATCH/D_clone.rows") row(s)"
  have_clone=1
else
  echo "  !! could not clone: $(sed -n '1,3p' "$SCRATCH/clone.log")"
  have_clone=0
fi

echo "--------------------------------------------------------------------------------------"
echo "ARMS"

# --- the arms that must be EQUAL --------------------------------------------------------------
for cond in B_toolchain C_residue; do
  if diff -q "$SCRATCH/A_bare.rows" "$SCRATCH/$cond.rows" >/dev/null 2>&1; then
    echo "  PASS  tracked resolver: A_bare == $cond   (frontier is a property of the COMMIT)"
    pass=$((pass + 1))
  else
    echo "  FAIL  tracked resolver: A_bare != $cond   -- STILL HOST-DEPENDENT."
    diff "$SCRATCH/A_bare.rows" "$SCRATCH/$cond.rows" | sed -n '1,20p'
    fail=$((fail + 1))
  fi
done

if [ "$have_clone" -eq 1 ]; then
  if diff -q "$SCRATCH/A_bare.rows" "$SCRATCH/D_clone.rows" >/dev/null 2>&1; then
    echo "  PASS  tracked resolver: A_bare == D_clone (different path, no untracked content)"
    pass=$((pass + 1))
  else
    echo "  FAIL  tracked resolver: A_bare != D_clone"
    diff "$SCRATCH/A_bare.rows" "$SCRATCH/D_clone.rows" | sed -n '1,20p'
    fail=$((fail + 1))
  fi
else
  echo "  SKIP  D_clone -- clone unavailable. This arm did NOT run; it is not a pass."
  fail=$((fail + 1))
fi

# --- the arms that must DIFFER: the legacy resolver, driven RED --------------------------------
# Without these the drive shows a green thing being green and proves nothing about the defect.
for cond in B_toolchain_legacy C_residue_legacy; do
  if diff -q "$SCRATCH/A_bare_legacy.rows" "$SCRATCH/$cond.rows" >/dev/null 2>&1; then
    echo "  FAIL  legacy resolver: A_bare_legacy == $cond -- the DEFECT DID NOT REPRODUCE, so"
    echo "        this drive has not shown the old resolver was host-dependent. Treat the"
    echo "        PASSes above as unproven."
    fail=$((fail + 1))
  else
    n=$(diff "$SCRATCH/A_bare_legacy.rows" "$SCRATCH/$cond.rows" | grep -ac '^[<>]')
    echo "  PASS  legacy resolver: A_bare_legacy != $cond ($n row(s) move) -- DEFECT REPRODUCED"
    pass=$((pass + 1))
  fi
done

echo "--------------------------------------------------------------------------------------"
if [ "$fail" -eq 0 ]; then
  echo "$PROBE GREEN pass=$pass fail=$fail"
  exit 0
fi
echo "$PROBE RED pass=$pass fail=$fail"
exit 1
