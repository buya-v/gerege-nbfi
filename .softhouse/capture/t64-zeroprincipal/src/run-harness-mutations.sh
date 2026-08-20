#!/bin/bash
# T64 — prove the four new vectors have DISCRIMINATING POWER, using the REAL harness.
#
# For each named wrong implementation in T64-mutations.py this runs
# `.softhouse/conformance.sh` TWICE on a scratch copy of the repository under /tmp:
#
#   BEFORE  the store with the four T64 vectors REMOVED  -> 32 parity vectors
#   AFTER   the store exactly as committed               -> 36 parity vectors
#
# A mutation that is GREEN at 32 and RED at 36 is a defect the corpus could not
# see before this capture and can see now. A mutation that is green in both adds
# nothing and is reported as adding nothing.
#
# The UNMUTATED control is run in both configurations too: if it is not green in
# both, no red/green result below means anything.
#
#     bash .softhouse/capture/t64-zeroprincipal/src/run-harness-mutations.sh
#
# Nothing here touches the committed tree. "The oracle" is the Fineract reference
# implementation; Oracle Database is a prohibited product and appears nowhere.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
SCRATCH=/tmp/t64-harness
T64_VECTORS=(
  "T64-ZP-A-zero-principal-mnt0pt28-56x21pt6pct.json"
  "T64-ZP-B-early-payoff-dead-rows-mnt0pt28-55x21pt6pct.json"
  "T64-ZP-C-zero-principal-mnt0pt17-34x36pct.json"
  "T64-ZP-D-zero-principal-mnt0pt36-72x16pt8pct.json"
)

prepare() {  # $1 = tag, $2 = mutation id or "" for the control
  local dir="$SCRATCH/$1"
  rm -rf "$dir"
  mkdir -p "$dir"
  # copy only what conformance.sh reads; .git is not needed and is large
  cp -R "$ROOT/nexus" "$dir/nexus"
  mkdir -p "$dir/.softhouse"
  cp -R "$ROOT/.softhouse/vectors" "$dir/.softhouse/vectors"
  cp -R "$ROOT/.softhouse/bin" "$dir/.softhouse/bin"
  cp "$ROOT/.softhouse/conformance.sh" "$dir/.softhouse/conformance.sh"
  # admit.go re-reads every vector's provenance.capture_ref and re-digests it, so
  # the capture tree has to be reachable at the same relative path or EVERY parity
  # vector is refused as INADMISSIBLE. Symlinked, not copied: it is 121 MB and it
  # is read-only here.
  ln -s "$ROOT/.softhouse/capture" "$dir/.softhouse/capture"
  if [ -n "$2" ]; then
    python3 - "$dir" "$2" <<'PY' || exit 1
import importlib.util, os, sys
dst, mid = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "t64mut", os.environ["T64_MUTATIONS"])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
_, _, patches, _ = m.BY_ID[mid]
root = os.environ["T64_ROOT"]
for path, old, new in patches:
    rel = os.path.relpath(path, os.path.join(root, "nexus"))
    tgt = os.path.join(dst, "nexus", rel)
    src = open(tgt).read()
    if src.count(old) != 1:
        sys.exit("ANCHOR MISS applying %s to %s (%d occurrences)" % (mid, rel, src.count(old)))
    open(tgt, "w").write(src.replace(old, new))
PY
  fi
}

strip_t64() {  # $1 = tag
  local v
  for v in "${T64_VECTORS[@]}"; do
    rm -f "$SCRATCH/$1/.softhouse/vectors/loanschedule/$v"
  done
}

run() {  # $1 = tag ; prints "EXIT n | summary line"
  local dir="$SCRATCH/$1"
  local out="$SCRATCH/$1.txt"
  # MUST cd into the scratch root: conformance.FindRepoRoot walks up from the
  # PROCESS's working directory, not from the script's location, so running the
  # scratch script from elsewhere silently grades the scratch's binary against
  # the REAL store. That defect produced a first, wrong run of this file.
  ( cd "$dir" && bash "$dir/.softhouse/conformance.sh" ) > "$out" 2>&1
  local rc=$?
  local n
  n="$(grep -E '^    parity vectors' "$out" | head -1 | sed 's/^ *//')"
  printf 'exit %d  |  %s\n' "$rc" "${n:-<no summary>}"
  return $rc
}

export T64_MUTATIONS="$HERE/T64-mutations.py"
export T64_ROOT="$ROOT"

MUTS=$(python3 -c "
import importlib.util, os
spec = importlib.util.spec_from_file_location('m', os.environ['T64_MUTATIONS'])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(' '.join(x[0] for x in m.MUTATIONS))")

echo "=========================================================================="
echo "CONTROL — the UNMUTATED port. Must be GREEN in both configurations, or"
echo "nothing below is evidence."
echo "=========================================================================="
prepare control ""
strip_t64 control
printf '  CONTROL   @32 vectors (T64 removed)  '; run control
prepare control ""
printf '  CONTROL   @36 vectors (as committed)  '; run control
echo

for mid in $MUTS; do
  echo "=========================================================================="
  echo "MUTATION $mid"
  echo "=========================================================================="
  prepare "$mid" "$mid" || { echo "  PREPARE FAILED"; continue; }
  strip_t64 "$mid"
  printf '  BEFORE  @32 vectors (T64 removed)   '; run "$mid"; before=$?
  prepare "$mid" "$mid" || { echo "  PREPARE FAILED"; continue; }
  printf '  AFTER   @36 vectors (as committed)  '; run "$mid"; after=$?
  if [ "$before" -eq 0 ] && [ "$after" -ne 0 ]; then
    echo "  => CLOSED A BLIND SPOT: green at 32, RED at 36."
  elif [ "$before" -ne 0 ]; then
    echo "  => already graded before this capture (red at 32); T64 adds nothing here."
  else
    echo "  => SURVIVES BOTH. This capture does NOT grade it. Reported as such."
  fi
  echo
done
