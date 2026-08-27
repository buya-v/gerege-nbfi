#!/bin/bash
# T116 — two proofs on the REAL harness, not on a model of it.
#
# Derived from the committed .softhouse/capture/t64-zeroprincipal/src/run-harness-mutations.sh,
# which is read and not edited (T114's ruling).
#
# PROOF 1 — DISCRIMINATING POWER. For the one named wrong implementation in T116-mutations.py this
# runs `.softhouse/conformance.sh` TWICE on a scratch copy of the repository under /tmp:
#
#   BEFORE  the store with the three T116 vectors REMOVED  -> 43 parity vectors
#   AFTER   the store exactly as committed                 -> 46 parity vectors
#
# Green at 43 and RED at 46 means the corpus could not see this defect before T116 and can now. The
# UNMUTATED control is run in both configurations: if it is not green in both, no red/green result
# below means anything (P-64 — before calling an arm RED, prove the arm RAN).
#
# PROOF 2 — THE EXEMPTION IS LOAD-BEARING, NOT VACUOUS (P-22). The two family-B vectors are copied
# into a scratch store with their `invariant_exemptions` array EMPTIED and nothing else changed. If
# the run stays green, the exemption was silencing nothing and the whole promotion route would be
# void — an exemption that changes no outcome is a decoration, and one that changes an outcome
# without saying so is worse. The expected result is a RED run naming the two invariants per vector.
#
#     bash .softhouse/capture/t116-familyb-promotion/src/run-harness-mutations-t116.sh
#
# Nothing here touches the committed tree. "The oracle" is the Fineract reference implementation;
# Oracle Database is a prohibited product and appears nowhere.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
SCRATCH=/tmp/t116-harness
T116_VECTORS=(
  "T116-G8-CLEAN-nonexempt-mnt0pt01-103x600pct.json"
  "T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct.json"
  "T116-G8-FAMB-nonamortizing-mnt0pt01-108x600pct.json"
)
FAMB_VECTORS=(
  "T116-G8-FAMB-nonamortizing-mnt0pt01-104x600pct.json"
  "T116-G8-FAMB-nonamortizing-mnt0pt01-108x600pct.json"
)

prepare() {  # $1 = tag, $2 = mutation id or "" for the control
  local dir="$SCRATCH/$1"
  rm -rf "$dir"
  mkdir -p "$dir"
  cp -R "$ROOT/nexus" "$dir/nexus"
  mkdir -p "$dir/.softhouse"
  cp -R "$ROOT/.softhouse/vectors" "$dir/.softhouse/vectors"
  cp -R "$ROOT/.softhouse/bin" "$dir/.softhouse/bin"
  cp -R "$ROOT/.softhouse/guards" "$dir/.softhouse/guards"
  cp "$ROOT/.softhouse/conformance.sh" "$dir/.softhouse/conformance.sh"
  # admit.go re-reads every vector's provenance.capture_ref and re-digests it, so the capture tree
  # has to be reachable at the same relative path or EVERY parity vector is refused as INADMISSIBLE.
  #
  # T64's version SYMLINKED this. That no longer works, and the way it fails is the P-62 trap: the
  # guards added since T64 derive their POPULATION FLOOR from `git ls-files`, a symlink contributes
  # one path instead of the 58 .java files underneath it, the floor comes back 0, and conformance.sh
  # exits 2 as a HARD-guard failure BEFORE the oracle probe line is ever printed. Every arm then
  # reports exit 2 and a reader who scores by exit code alone concludes the mutation was caught.
  # It was not: the arm never ran. HARDLINKED instead -- the files are real paths for git, cost no
  # space, and nothing in a conformance run writes to the capture tree.
  cp -Rl "$ROOT/.softhouse/capture" "$dir/.softhouse/capture"
  # The floors are derived with `git ls-files`, so the scratch must BE a git repo or every one of
  # them comes back 0. This is a throw-away index under /tmp; the real repository is never touched.
  ( cd "$dir" && git init -q . && git add -A -f >/dev/null 2>&1 ) || exit 1
  if [ -n "$2" ]; then
    python3 - "$dir" "$2" <<'PY' || exit 1
import importlib.util, os, sys
dst, mid = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("m", os.environ["T116_MUTATIONS"])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
_, _, patches, _ = m.BY_ID[mid]
root = os.environ["T116_ROOT"]
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

strip_t116() {  # $1 = tag — remove T116's three vectors, leaving the 43-vector corpus
  local v
  for v in "${T116_VECTORS[@]}"; do
    rm -f "$SCRATCH/$1/.softhouse/vectors/loanschedule/$v"
  done
}

strip_exemptions() {  # $1 = tag — empty invariant_exemptions on the two family-B vectors ONLY
  local dir="$SCRATCH/$1/.softhouse/vectors/loanschedule"
  local v
  for v in "${FAMB_VECTORS[@]}"; do
    python3 - "$dir/$v" <<'PY' || exit 1
import json, sys
p = sys.argv[1]
with open(p) as fh:
    v = json.load(fh)
assert len(v["invariant_exemptions"]) == 2, (p, len(v["invariant_exemptions"]))
v["invariant_exemptions"] = []
with open(p, "w") as fh:
    json.dump(v, fh, indent=1)
    fh.write("\n")
PY
  done
}

run() {  # $1 = tag ; prints "exit n | summary"
  local dir="$SCRATCH/$1"
  local out="$SCRATCH/$1.txt"
  # MUST cd into the scratch root: conformance.FindRepoRoot walks up from the PROCESS's working
  # directory, not from the script's location, so running it from elsewhere silently grades the
  # scratch's binary against the REAL store.
  ( cd "$dir" && bash "$dir/.softhouse/conformance.sh" ) > "$out" 2>&1
  local rc=$?
  local n viol probe
  n="$(grep -E '^    parity vectors' "$out" | head -1 | sed 's/^ *//')"
  viol="$(grep -E '^    invariant violations' "$out" | head -1 | sed 's/^ *//')"
  probe="$(grep -c 'probe = ' "$out")"
  printf 'exit %d  |  %s  |  %s  |  probe line present: %s\n' \
    "$rc" "${n:-<no parity summary>}" "${viol:-<no violation line>}" "$probe"
  # P-62 / P-64. Exit 2 is overloaded across unusable corpus, failed HARD guard, unreachable oracle,
  # wrong repo root and an I-3/I-4 violation, and FOUR of those paths run BEFORE the probe line is
  # printed. An arm whose probe line never appeared did not reach the corpus at all, so it is
  # neither red nor green -- it is UNRUN, and scoring it either way is the defect. Encoded as a
  # distinct return code so the verdicts below cannot silently treat it as a red.
  if [ "$probe" -eq 0 ]; then
    echo "     ^^ THIS ARM DID NOT RUN: no probe line. Not a red, not a green. See $out"
    return 99
  fi
  return $rc
}

export T116_MUTATIONS="$HERE/T116-mutations.py"
export T116_ROOT="$ROOT"

echo "=========================================================================="
echo "CONTROL — the UNMUTATED port, unmutated store. Must be GREEN in both"
echo "configurations, or nothing below is evidence (P-64)."
echo "=========================================================================="
prepare control ""
strip_t116 control
printf '  CONTROL   @43 vectors (T116 removed)   '; run control; c43=$?
prepare control ""
printf '  CONTROL   @46 vectors (as committed)   '; run control; c46=$?
if [ "$c43" -ne 0 ] || [ "$c46" -ne 0 ]; then
  echo
  echo "  CONTROL IS NOT GREEN IN BOTH CONFIGURATIONS. Everything below is VOID and none of it"
  echo "  may be quoted as evidence. Fix the rig, not the report."
  exit 1
fi
echo

echo "=========================================================================="
echo "PROOF 1 — MUTATION G8-FINAL-ROW-SETTLES-THE-BALANCE"
echo "=========================================================================="
mid=G8-FINAL-ROW-SETTLES-THE-BALANCE
prepare "$mid" "$mid" || { echo "  PREPARE FAILED"; exit 1; }
strip_t116 "$mid"
printf '  BEFORE  @43 vectors (T116 removed)     '; run "$mid"; before=$?
prepare "$mid" "$mid" || { echo "  PREPARE FAILED"; exit 1; }
printf '  AFTER   @46 vectors (as committed)     '; run "$mid"; after=$?
if [ "$before" -eq 99 ] || [ "$after" -eq 99 ]; then
  echo "  => UNSCORABLE: an arm did not run. No claim is made either way."
elif [ "$before" -eq 0 ] && [ "$after" -ne 0 ]; then
  echo "  => CLOSED A BLIND SPOT: green at 43, RED at 46."
elif [ "$before" -ne 0 ]; then
  echo "  => already graded before T116 (red at 43); T116 adds cells, not new coverage."
else
  echo "  => SURVIVES BOTH. T116 does NOT grade it. Reported as such."
fi
echo

echo "=========================================================================="
echo "PROOF 2 — IS THE EXEMPTION LOAD-BEARING? (P-22 vacuity check)"
echo "Unmutated port. Only difference: the two family-B vectors'"
echo "invariant_exemptions arrays are EMPTIED."
echo "=========================================================================="
prepare noexempt ""
strip_exemptions noexempt || { echo "  PREPARE FAILED"; exit 1; }
printf '  WITHOUT the exemption  @46 vectors     '; run noexempt; ne=$?
if [ "$ne" -eq 99 ]; then
  echo "  => UNSCORABLE: the arm did not run. No claim is made either way."
elif [ "$ne" -ne 0 ]; then
  echo "  => THE EXEMPTION IS LOAD-BEARING: without it the run is RED."
  grep -E 'invariant .* VIOLATED' "$SCRATCH/noexempt.txt" | sed 's/^/     /' | head -8
else
  echo "  => VACUOUS: the run is green without the exemption. The promotion route is VOID."
fi
