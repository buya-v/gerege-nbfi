#!/bin/bash
# T306 — THE SECOND HALF OF THE UNBLOCK CONDITION, MEASURED.
#
# T320's condition on this task was two clauses, and the second is the one that
# matters: "conformance still shows 11/11 wrong implementations dying with
# LDG-05 admissible."
#
# The claim underneath it is that T306's FIRST-PASS narrowing does not merely
# make LDG-05 inadmissible as a bookkeeping fact -- it withdraws the only kill
# of `ledger-wrong-openingbalance-always-refusing`, T296 arm A, a port that
# REFUSES EVERY OPENING BALANCE and, before T305's capture, stayed green on the
# entire corpus. That is not a restatement to be believed; it is a mutant that
# either dies or survives, and this script runs the arms and reads the answer.
#
# THREE EXIT CODES AND THEY ARE NOT INTERCHANGEABLE. `.softhouse/conformance.sh`
# and this binary share them:
#
#   0  the mutant SURVIVED  -- the corpus did not catch it. A withdrawn kill.
#   1  the mutant was KILLED BY GRADING -- a captured cell disagreed with it.
#      This is the only outcome that counts as a kill.
#   2  the HARNESS REFUSED TO GRADE -- an inadmissible vector, a failed hard
#      guard. NOT a kill: nothing was compared. Counting a 2 as a kill is the
#      mistake this script exists to avoid, and the first draft of it made
#      exactly that mistake.
#
#   ARM A   the ADJUDICATED predicate                    -> 11 killed by grading
#   ARM N   T306's first-pass narrowing                  -> watch for exit 2
#   ARM N'  the first-pass narrowing WITH LDG-05 RETIRED -- what the store looks
#           like one step later, when somebody clears the red bar by removing
#           the vector the gate now refuses. THIS is where a withdrawn kill
#           becomes a SURVIVING MUTANT.
#
# admit.go is patched in place and restored from git, restore VERIFIED by hash.
# Nothing under .softhouse/vectors is touched; no request reaches the oracle.
set -uo pipefail
W="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
. "$W/.softhouse/bin/go-env.sh"

ADMIT="$W/nexus/internal/apps/ledger/conformance/admit.go"
BEFORE=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/t306-mutant.XXXXXXXX") || exit 1
cp -R "$W/.softhouse/vectors" "$SCRATCH/full" || exit 1
cp -R "$W/.softhouse/vectors" "$SCRATCH/no-ldg05" || exit 1
rm -f "$SCRATCH/no-ldg05/ledger/LDG-05-openingbalance-accepted-empty-ledger.json"

restore() {
  git -C "$W" checkout -- "$ADMIT"
  local now
  now=$(shasum -a 256 "$ADMIT" | cut -d' ' -f1)
  echo "T306-RESTORE: before=${BEFORE:0:12} after=${now:0:12} restored=$([ "$BEFORE" = "$now" ] && echo 1 || echo 0)"
}
trap restore EXIT

impls() {
  cd "$W/nexus" || exit 1
  go run ./internal/apps/loanschedule/conformance/cmd/conformance -list-implementations 2>/dev/null |
    grep -oE 'ledger-wrong-[a-z0-9-]+'
}

run_arm() {
  local label="$1" store="$2"
  cd "$W/nexus" || exit 1
  if ! go build -o "$SCRATCH/conf-$label" ./internal/apps/loanschedule/conformance/cmd/conformance 2>"$SCRATCH/b.err"; then
    echo "  ARM $label DID NOT COMPILE:"; cat "$SCRATCH/b.err"; return 1
  fi
  local killed=0 survived=0 refused=0
  for impl in $(impls); do
    "$SCRATCH/conf-$label" -oracle-probe=up -context=ledger -repo-root="$W" \
      -store="$SCRATCH/$store" -ledger-impl="$impl" > "$SCRATCH/$label-$impl.txt" 2>&1
    local rc=$?
    case "$rc" in
      0) survived=$((survived+1))
         printf '  %-52s SURVIVED        exit 0 — THE CORPUS DID NOT CATCH IT\n' "$impl" ;;
      1) killed=$((killed+1))
         printf '  %-52s killed          exit 1 — a captured cell disagreed\n' "$impl" ;;
      *) refused=$((refused+1))
         printf '  %-52s NOT A KILL      exit %d — HARNESS REFUSED TO GRADE\n' "$impl" "$rc" ;;
    esac
  done
  echo "  ---- ARM $label over store '$store': KILLED BY GRADING=$killed  SURVIVED=$survived  HARNESS-REFUSED=$refused ----"
  echo
}

patch_first_pass() {
  python3 - "$ADMIT" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = """		observedShape := openingBalanceCommand ||
			(v.Expect.Kind == "refusal" && (preClosureInputs || futureDatedInputs))"""
new = """		observedShape := v.Expect.Kind == "refusal" &&
			(openingBalanceCommand || preClosureInputs || futureDatedInputs)"""
assert s.count(old) == 1, "the adjudicated predicate is not where this probe expects it"
open(p, "w").write(s.replace(old, new))
print("  patched admit.go -> T306's FIRST-PASS narrowing")
PY
}

echo "registered wrong ledger implementations:"
impls | sed 's/^/  /'
echo

echo "=============================================================="
echo "ARM A — THE ADJUDICATED PREDICATE, full store (this branch)"
echo "=============================================================="
run_arm A full

echo "=============================================================="
echo "ARM N — T306's FIRST-PASS NARROWING, full store."
echo "        LDG-05 goes INADMISSIBLE. Read the exit codes, not a count."
echo "=============================================================="
patch_first_pass
run_arm N full

echo "=============================================================="
echo "ARM Np — the SAME first-pass narrowing, LDG-05 RETIRED."
echo "        One step later: the red bar is cleared by removing the"
echo "        vector the gate refuses. Does the mutant come back?"
echo "=============================================================="
run_arm Np no-ldg05

echo "=============================================================="
echo "CONTROL — the ADJUDICATED predicate, LDG-05 RETIRED."
echo "        Isolates WHICH of the two changes withdraws the kill:"
echo "        the predicate, or the missing vector."
echo "=============================================================="
git -C "$W" checkout -- "$ADMIT"
run_arm Ap no-ldg05

echo "scratch: $SCRATCH"
